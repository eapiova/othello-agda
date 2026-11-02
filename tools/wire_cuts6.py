#!/usr/bin/env python3
"""Bound inline bodies in native certificates by adding child-first citations.

This changes only untrusted export instrumentation. Existing solver, rules,
TT, wire builds and checked proofs remain intact. All new records still need
independent replay and the safe Agda checker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import census_wire6 as wire
from run_job import atomic_json, utc

FORMAT='othello-wire-cuts6-build-v1'
CUTS = r'''
/* Once indegrees are counted, reuse their array: high bit = exported;
   remaining bits = conservative inline size. No extra graph-sized allocation.
   The completion order is child-before-parent. Original census counters stay
   untouched. Citations cost at most two tokens, including a D4 tag. */
  size_t extra_cuts=0;
  if(valid)for(size_t q=0;q<wire_order_count;q++){
    if((q&4095)==0 && oracle_stop()){valid=0;break;}
    size_t id=wire_order[q];
    if(prefix[id].key&CENSUS_LEAF){wire_indegree[id]=1;continue;}
    int shared=id==0 || wire_indegree[id]>=2;
    size_t children[36];int n=wire_children(id,lower,threshold,children);
    uint64_t size=1;
    for(int j=0;j<n;j++){
      size_t child=children[j];
      if(child==SIZE_MAX || child==id){valid=0;break;}
      uint32_t cost=wire_indegree[child];
      size+=(cost&WIRE_CUT)?2:cost;
    }
    if(!valid || !n || size>=WIRE_CUT){valid=0;break;}
    int cut=shared || size>wire_inline_limit;
    if(cut && !shared)extra_cuts++;
    wire_indegree[id]=(uint32_t)size | (cut?WIRE_CUT:0);
  }
  printf(",\"wire_inline_limit\":%u,\"wire_body_bound\":%u,\"wire_extra_cuts\":%zu",
    wire_inline_limit,1+36*(wire_inline_limit<2?2:wire_inline_limit),extra_cuts);
'''


def generated_source(raw,pins=None):
    original=wire.generated_source(raw,pins)
    patches=[
      ('static int wire_enabled;', 'static const uint32_t WIRE_CUT=UINT32_C(0x80000000);\nstatic uint32_t wire_inline_limit=256;\nstatic int wire_enabled;'),
      ('wire_indegree[id]>=2))', '(wire_indegree[id]&WIRE_CUT)))'),
      ('  FILE *out=valid?fopen(wire_path,"wbx"):NULL;', CUTS+'\n  FILE *out=valid?fopen(wire_path,"wbx"):NULL;'),
      ('wire_indegree[id]<2))continue;', '!(wire_indegree[id]&WIRE_CUT)))continue;'),
      ('    else if(!strcmp(argv[i],"--wire-limit-mib"))',
       '    else if(!strcmp(argv[i],"--wire-inline-limit")){int cap;if(++i==argc || !integer(argv[i],1,65536,&cap))return error("invalid inline cap");wire_inline_limit=(uint32_t)cap;}\n    else if(!strcmp(argv[i],"--wire-limit-mib"))')]
    source=original
    for old,new in patches:
        if source.count(old)!=1:raise ValueError('unexpected wire layout: '+old[:80])
        source=source.replace(old,new,1)
    restored=source
    for old,new in reversed(patches):restored=restored.replace(new,old,1)
    if restored!=original:raise ValueError('cut delta changes unrelated source')
    return source


def build(args):
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    line=json.loads(args.line.read_text()) if args.line else None
    pins=wire.line_pins6.plan(line)['pins'] if line else None
    source=output/'census.c';source.write_text(generated_source(wire.solve6.SOURCE.read_text(),pins))
    compiler=Path(shutil.which('cc')).resolve(strict=True);binary=output/'census'
    command=[str(compiler),*wire.solve6.FLAGS,str(source),'-o',str(binary)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError(result.stderr)
    report=dict(format=FORMAT,status='complete',created_utc=utc(),
      reference_source_sha256=wire.solve6.sha256(wire.solve6.SOURCE),source_sha256=wire.solve6.sha256(source),
      binary=str(binary),binary_sha256=wire.solve6.sha256(binary),compiler=str(compiler),
      compiler_sha256=wire.solve6.sha256(compiler),flags=list(wire.solve6.FLAGS),command=command,
      compile_stderr=result.stderr,pins=pins,line_sha256=wire.solve6.sha256(args.line) if args.line else None,
      solver_rules_tt_bytes_unchanged=True,witness_policy='min-replies with optional fail-closed line pins and bounded inline cuts',
      compact_memo=True,production_authorized=False,initial_problem2_proved=False)
    atomic_json(output/'build.json',report)
    print(json.dumps(dict(status='complete',binary_sha256=report['binary_sha256'])))


def checked_build(path):
    path=path.resolve();report=json.loads((path/'build.json').read_text());binary=Path(report['binary'])
    expected=generated_source(wire.solve6.SOURCE.read_text(),report.get('pins')).encode()
    if (report.get('format')!=FORMAT or report.get('status')!='complete' or
        report.get('solver_rules_tt_bytes_unchanged') is not True or
        report['reference_source_sha256']!=wire.solve6.sha256(wire.solve6.SOURCE) or
        report['source_sha256']!=hashlib.sha256(expected).hexdigest() or
        (path/'census.c').read_bytes()!=expected or report['binary_sha256']!=wire.solve6.sha256(binary)):
        raise ValueError('cut build provenance changed')
    return report,binary


def run(args):
    if not 1<=args.inline_limit<=65536:raise ValueError('invalid inline cutoff')
    return wire.run(args,build_validator=checked_build,
        extra_native_options=['--wire-inline-limit',str(args.inline_limit)])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('build','run'))
    p.add_argument('--output',type=Path,required=True);p.add_argument('--line',type=Path)
    for name in ('build','tests','donor','wire-output'):p.add_argument('--'+name,type=Path)
    p.add_argument('--root-key',default='initial');p.add_argument('--wire-limit-mib',type=int,default=4)
    p.add_argument('--max-states',type=int,default=500000);p.add_argument('--native-cpu',type=int,default=180)
    p.add_argument('--direction',choices=('lower','upper'),default='lower')
    p.add_argument('--inline-limit',type=int,default=256)
    args=p.parse_args()
    if args.mode=='build':build(args);return 0
    if not all((args.build,args.tests,args.donor,args.wire_output)):p.error('run requires build/tests/donor/wire-output')
    if not 1<=args.native_cpu<=7200:p.error('invalid native CPU cap')
    return 0 if run(args) else 1


if __name__=='__main__':raise SystemExit(main())
