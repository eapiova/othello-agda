#!/usr/bin/env python3
"""Bounded, untrusted counts-only native wire/shard-layout experiment.

No graph, certificate or Agda source is retained in counts-only mode. An
optional bounded wire is solely for differential fixtures. Native layout
counts never provide an Agda premise or production authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import canonical_census6 as base
import census_wire6 as wire
import wire_cuts6 as cuts
from run_job import atomic_json, utc

FORMAT = 'othello-wire-layout6-build-v1'
RUN_FORMAT = 'othello-wire-layout6-run-v1'
MAX_LAYOUT_MIB = 512
DEFAULT_ENTRIES = 200
DEFAULT_TOKENS = 32000

DECLARATIONS = r'''
/* Layout instrumentation only: the memo, solver, rules and TT stay intact. */
static const uint32_t LAYOUT_ASSIGNED=UINT32_C(0x40000000);
static const uint32_t LAYOUT_OWNER=UINT32_C(0x3fffffff);
static int layout_counts_only,layout_fuel=80,layout_failed;
static const char *layout_reason="none";
static size_t layout_limit=512*1024*1024,layout_native_bytes,layout_memory_limit;
static size_t layout_live,layout_peak,layout_part_capacity,layout_part_count;
static uint32_t layout_max_entries=200,layout_max_tokens=32000;
static size_t layout_max_records=200000000;
static uint32_t *layout_record_refs,*layout_part_refs,*layout_deps;
static size_t layout_record_ref_count,layout_part_ref_count;
typedef struct {uint64_t *closure;uint32_t entries;} LayoutPart;
static LayoutPart *layout_parts;
static uint64_t layout_records,layout_tokens,layout_compact_bytes,layout_source_wire_bytes;
static uint64_t layout_import_sum,layout_import_max,layout_direct_sum,layout_direct_max;
static uint64_t layout_transitive_parts_sum,layout_transitive_parts_max;
static uint64_t layout_transitive_entries_sum,layout_transitive_entries_max;
static uint64_t layout_part_entries,layout_part_tokens,layout_max_part_entries,layout_max_part_tokens;
static uint64_t layout_assembly_parts,layout_assembly_entries;
static int layout_fail(const char *why) {
  if(!layout_failed)layout_reason=why;layout_failed=1;return 0;
}
static int layout_stop(void) {
  if(oracle_cpu_cap && (double)(clock()-oracle_start)/CLOCKS_PER_SEC>=oracle_cpu_cap) {
    oracle_aborted=1;layout_fail("cpu-bound");return 1;
  }
  if(oracle_stop()){layout_fail("native-bound");return 1;}return layout_failed;
}
static int layout_add(uint64_t *value,uint64_t amount) {
  if(UINT64_MAX-*value<amount)return layout_fail("layout-overflow");*value+=amount;return 1;
}
static void *layout_allocate(size_t bytes) {
  if(!bytes)return NULL;
  if(layout_live>layout_limit || bytes>layout_limit-layout_live ||
     layout_native_bytes>layout_memory_limit || layout_live>layout_memory_limit-layout_native_bytes ||
     bytes>layout_memory_limit-layout_native_bytes-layout_live) {
    layout_fail("layout-memory-bound");return NULL;
  }
  void *p=calloc(1,bytes);if(!p){layout_fail("layout-allocation");return NULL;}
  layout_live+=bytes;if(layout_live>layout_peak)layout_peak=layout_live;return p;
}
static void layout_free(void *p,size_t bytes) {if(p){free(p);layout_live-=bytes;}}
static int layout_initialize(void) {
  size_t bytes=(size_t)layout_max_tokens*sizeof(uint32_t);
  layout_record_refs=layout_allocate(bytes);layout_part_refs=layout_allocate(bytes);
  layout_deps=layout_allocate(bytes);
  return layout_record_refs && layout_part_refs && layout_deps;
}
static int layout_reference(size_t id) {
  if(layout_record_ref_count>=layout_max_tokens || id>=prefix_count ||
     !(wire_indegree[id]&LAYOUT_ASSIGNED))return layout_fail("citation-bound-or-order");
  layout_record_refs[layout_record_ref_count++]=(uint32_t)id;return 1;
}
static int layout_compare(const void *a,const void *b) {
  uint32_t x=*(const uint32_t*)a,y=*(const uint32_t*)b;return (x>y)-(x<y);
}
static size_t layout_words(size_t index) {return (index+63)/64;}
static int layout_flush(void) {
  if(!layout_part_entries)return !layout_failed;
  size_t index=layout_part_count;
  if(index>=LAYOUT_OWNER)return layout_fail("part-owner-bound");
  if(index==layout_part_capacity){
    size_t cap=layout_part_capacity?layout_part_capacity*2:64;
    if(cap>LAYOUT_OWNER || cap>SIZE_MAX/sizeof(LayoutPart))return layout_fail("part-capacity-overflow");
    LayoutPart *p=layout_allocate(cap*sizeof(LayoutPart));if(!p)return 0;
    if(layout_parts)memcpy(p,layout_parts,index*sizeof(LayoutPart));
    layout_free(layout_parts,layout_part_capacity*sizeof(LayoutPart));
    layout_parts=p;layout_part_capacity=cap;
  }
  size_t words=layout_words(index);uint64_t *closure=layout_allocate(words*sizeof(uint64_t));
  if(words && !closure)return 0;
  /* Keep the row owned even if a later guard fails, so teardown is exact. */
  layout_parts[index]=(LayoutPart){closure,(uint32_t)layout_part_entries};layout_part_count++;
  qsort(layout_part_refs,layout_part_ref_count,sizeof(uint32_t),layout_compare);
  size_t imports=0,ndeps=0;uint32_t previous=UINT32_MAX;
  for(size_t j=0;j<layout_part_ref_count;j++){
    if((j&4095)==0 && layout_stop())return 0;
    uint32_t id=layout_part_refs[j];if(id==previous)continue;previous=id;
    uint32_t assigned=wire_indegree[id];size_t owner=assigned&LAYOUT_OWNER;
    if(!(assigned&LAYOUT_ASSIGNED) || owner>index)return layout_fail("citation-owner-order");
    if(owner!=index){imports++;layout_deps[ndeps++]=(uint32_t)owner;}
  }
  qsort(layout_deps,ndeps,sizeof(uint32_t),layout_compare);
  size_t direct=0;previous=UINT32_MAX;
  for(size_t j=0;j<ndeps;j++){
    uint32_t dep=layout_deps[j];if(dep==previous)continue;previous=dep;direct++;
    closure[dep/64]|=UINT64_C(1)<<(dep%64);
    size_t n=layout_words(dep);uint64_t *ancestor=layout_parts[dep].closure;
    for(size_t w=0;w<n;w++){
      if((w&4095)==0 && layout_stop())return 0;closure[w]|=ancestor[w];
    }
  }
  uint64_t transitive_parts=0,transitive_entries=0;
  for(size_t w=0;w<words;w++){
    if((w&4095)==0 && layout_stop())return 0;
    uint64_t bits=closure[w];transitive_parts+=(uint64_t)__builtin_popcountll(bits);
    while(bits){unsigned int bit=(unsigned int)__builtin_ctzll(bits);bits&=bits-1;
      if(!layout_add(&transitive_entries,layout_parts[64*w+bit].entries))return 0;}
  }
  if(!layout_add(&layout_import_sum,imports) || !layout_add(&layout_direct_sum,direct) ||
     !layout_add(&layout_transitive_parts_sum,transitive_parts) ||
     !layout_add(&layout_transitive_entries_sum,transitive_entries))return 0;
  if(imports>layout_import_max)layout_import_max=imports;
  if(direct>layout_direct_max)layout_direct_max=direct;
  if(transitive_parts>layout_transitive_parts_max)layout_transitive_parts_max=transitive_parts;
  if(transitive_entries>layout_transitive_entries_max)layout_transitive_entries_max=transitive_entries;
  if(layout_part_entries>layout_max_part_entries)layout_max_part_entries=layout_part_entries;
  if(layout_part_tokens>layout_max_part_tokens)layout_max_part_tokens=layout_part_tokens;
  layout_assembly_parts=transitive_parts+1;
  layout_assembly_entries=transitive_entries+layout_part_entries;
  layout_part_entries=layout_part_tokens=0;layout_part_ref_count=0;return 1;
}
static void layout_release(void) {
  for(size_t j=0;j<layout_part_count;j++)layout_free(layout_parts[j].closure,layout_words(j)*sizeof(uint64_t));
  layout_free(layout_parts,layout_part_capacity*sizeof(LayoutPart));
  size_t bytes=(size_t)layout_max_tokens*sizeof(uint32_t);
  layout_free(layout_record_refs,bytes);layout_free(layout_part_refs,bytes);layout_free(layout_deps,bytes);
}
'''

RECORD = r'''
static int wire_record(FILE *f,u64 P,u64 O,int turn,WireBuffer *body,WireBuffer *refs,
                       size_t *bytes,size_t *records) {
  size_t n=13+body->n+refs->n+3;
  if(layout_stop() || !body->ok || !refs->ok)return layout_fail("body-or-fuel-bound");
  if(n>wire_record_limit || body->tokens>layout_max_tokens || !body->tokens ||
     layout_records>=layout_max_records || layout_record_ref_count!=refs->n/13 || refs->n%13)
    return layout_fail("record-or-token-bound");
  if(n>SIZE_MAX-*bytes || *records==SIZE_MAX)return layout_fail("wire-overflow");
  if(f && (*bytes>wire_byte_limit || n>wire_byte_limit-*bytes))return layout_fail("wire-byte-bound");
  if(layout_part_entries && (layout_part_tokens+body->tokens>layout_max_tokens ||
                            layout_part_entries>=layout_max_entries))if(!layout_flush())return 0;
  if(layout_record_ref_count>layout_max_tokens-layout_part_ref_count)return layout_fail("part-citation-bound");
  memcpy(layout_part_refs+layout_part_ref_count,layout_record_refs,layout_record_ref_count*sizeof(uint32_t));
  layout_part_ref_count+=layout_record_ref_count;
  if(f){char packed[14];wire_state(P,O,turn,packed);
    if(fwrite(packed,1,13,f)!=13 || fputc('\t',f)==EOF ||
       (body->n && fwrite(body->data,1,body->n,f)!=body->n) || fputc('\t',f)==EOF ||
       (refs->n && fwrite(refs->data,1,refs->n,f)!=refs->n) || fputc('\n',f)==EOF)
      return layout_fail("wire-write");}
  if(!layout_add(&layout_records,1) || !layout_add(&layout_tokens,body->tokens) ||
     !layout_add(&layout_compact_bytes,13+body->n) || !layout_add(&layout_source_wire_bytes,n))return 0;
  layout_part_entries++;layout_part_tokens+=body->tokens;
  *bytes+=n;(*records)++;layout_record_ref_count=0;return 1;
}
'''

REPORT = r'''
  printf(",\"layout_complete\":%s,\"layout_censored\":%s,\"layout_stop_reason\":\"%s\",\"layout_counts_only\":true",
    valid?"true":"false",valid?"false":"true",valid?"none":(layout_failed?layout_reason:"incomplete-native-graph"));
  printf(",\"layout_records\":%llu,\"layout_tokens\":%llu,\"layout_compact_bytes\":%llu,\"layout_source_wire_bytes\":%llu,\"layout_parts\":%zu",
    (unsigned long long)layout_records,(unsigned long long)layout_tokens,
    (unsigned long long)layout_compact_bytes,(unsigned long long)layout_source_wire_bytes,layout_part_count);
  printf(",\"layout_imported_citations_sum\":%llu,\"layout_imported_citations_max\":%llu,\"layout_direct_dependencies_sum\":%llu,\"layout_direct_dependencies_max\":%llu",
    (unsigned long long)layout_import_sum,(unsigned long long)layout_import_max,
    (unsigned long long)layout_direct_sum,(unsigned long long)layout_direct_max);
  printf(",\"layout_transitive_parts_sum\":%llu,\"layout_transitive_parts_max\":%llu,\"layout_transitive_entries_sum\":%llu,\"layout_transitive_entries_max\":%llu",
    (unsigned long long)layout_transitive_parts_sum,(unsigned long long)layout_transitive_parts_max,
    (unsigned long long)layout_transitive_entries_sum,(unsigned long long)layout_transitive_entries_max);
  printf(",\"layout_max_part_entries\":%llu,\"layout_max_part_tokens\":%llu,\"layout_assembly_transitive_parts\":%llu,\"layout_assembly_transitive_entries\":%llu",
    (unsigned long long)layout_max_part_entries,(unsigned long long)layout_max_part_tokens,
    (unsigned long long)layout_assembly_parts,(unsigned long long)layout_assembly_entries);
  printf(",\"layout_limit_bytes\":%zu,\"layout_peak_bytes\":%zu,\"layout_total_peak_bytes\":%zu,\"layout_max_entries\":%u,\"layout_max_tokens\":%u,\"layout_max_records\":%zu,\"layout_body_fuel\":%d",
    layout_limit,layout_peak,layout_native_bytes+layout_peak,layout_max_entries,layout_max_tokens,layout_max_records,layout_fuel);
  printf(",\"initial_problem2_proved\":false,\"optimal_pair_proved\":false,\"production_authorized\":false");
  layout_release();
'''

OPTIONS = r'''
    else if(!strcmp(argv[i],"--counts-only")){if(layout_counts_only)return error("duplicate counts-only");layout_counts_only=1;}
    else if(!strcmp(argv[i],"--layout-limit-mib")){int cap;if(++i==argc || !integer(argv[i],1,512,&cap))return error("invalid layout memory cap");layout_limit=(size_t)cap*1024*1024;}
    else if(!strcmp(argv[i],"--layout-max-entries")){int cap;if(++i==argc || !integer(argv[i],1,200,&cap))return error("invalid layout entry cap");layout_max_entries=(uint32_t)cap;}
    else if(!strcmp(argv[i],"--layout-max-tokens")){int cap;if(++i==argc || !integer(argv[i],1,32000,&cap))return error("invalid layout token cap");layout_max_tokens=(uint32_t)cap;}
    else if(!strcmp(argv[i],"--layout-max-records")){int cap;if(++i==argc || !integer(argv[i],1,200000000,&cap))return error("invalid layout record cap");layout_max_records=(size_t)cap;}
    else if(!strcmp(argv[i],"--wire-record-limit")){int cap;if(++i==argc || !integer(argv[i],16,1048576,&cap))return error("invalid wire record cap");wire_record_limit=(size_t)cap;}
    else if(!strcmp(argv[i],"--wire-body-fuel")){int cap;if(++i==argc || !integer(argv[i],1,80,&cap))return error("invalid body fuel");layout_fuel=cap;}
'''


def generated_source(raw, pins=None):
    """Exact reversible delta atop cuts; original native bytes remain intact."""
    original = cuts.generated_source(raw, pins)
    record_start = original.index('static int wire_record(')
    record_end = original.index('static int wire_report(', record_start)
    patches = [
        ('static const unsigned char wire_inverse', DECLARATIONS + '\nstatic const unsigned char wire_inverse'),
        (original[record_start:record_end], RECORD + '\n'),
        ('if(!fuel || oracle_stop())', 'if(!fuel || layout_stop())'),
        ('    char *p=realloc(b->data,cap);if(!p){b->ok=0;return;}b->data=p;b->capacity=cap;',
         '    char *p=layout_allocate(cap);if(!p){b->ok=0;return;}if(b->data)memcpy(p,b->data,b->n);layout_free(b->data,b->capacity);b->data=p;b->capacity=cap;'),
        ('    char packed[14];wire_state(cp,co,turn,packed);wire_append(refs,packed,13);return;',
         '    if(!layout_reference(id)){body->ok=0;return;}\n    char packed[14];wire_state(cp,co,turn,packed);wire_append(refs,packed,13);return;'),
        ('(i&4095)==0 && oracle_stop()', '(i&4095)==0 && layout_stop()'),
        (cuts.CUTS, cuts.CUTS.replace('oracle_stop()', 'layout_stop()') + r'''
  if(valid){
    for(size_t i=0;i<prefix_count;i++){
      if((i&4095)==0 && layout_stop()){valid=0;break;}
      wire_indegree[i]&=WIRE_CUT;
    }
    if(valid && !layout_initialize())valid=0;
  }
'''),
        ('  FILE *out=valid?fopen(wire_path,"wbx"):NULL;if(valid && !out)valid=0;',
         '  FILE *out=(valid && wire_path)?fopen(wire_path,"wbx"):NULL;if(valid && wire_path && !out){layout_fail("wire-open");valid=0;}'),
        ('wire_body(P,O,turn,lower,threshold,1,80,&body,&refs);',
         'wire_body(P,O,turn,lower,threshold,1,layout_fuel,&body,&refs);'),
        ('    references+=refs.n/13;',
         '    wire_indegree[id]=(wire_indegree[id]&WIRE_CUT)|LAYOUT_ASSIGNED|(uint32_t)layout_part_count;\n    references+=refs.n/13;'),
        ("if(valid && rootTag){body.n=refs.n=0;wire_char(&body,'R');",
         "if(valid && rootTag){body.n=refs.n=0;body.tokens=1;if(!layout_reference(0))body.ok=0;wire_char(&body,'R');"),
        ('  free(body.data);free(refs.data);',
         '  if(valid && !layout_flush())valid=0;\n  layout_free(body.data,body.capacity);layout_free(refs.data,refs.capacity);'),
        ('  return valid;\n}\n\nstatic int integer(', REPORT + '\n  return valid;\n}\n\nstatic int integer('),
        ('    int wire_ok=wire_report(complete,P,O,white_turn,lower,threshold);',
         '    layout_native_bytes=bytes;layout_memory_limit=(size_t)max_memory_mb*1024*1024;\n    int wire_ok=wire_report(complete,P,O,white_turn,lower,threshold);'),
        ('if(argc<2 || strcmp(argv[1],"wire"))', 'if(argc<2 || strcmp(argv[1],"layout"))'),
        ('    else if(!strcmp(argv[i],"--wire-inline-limit"))', OPTIONS + '\n    else if(!strcmp(argv[i],"--wire-inline-limit"))'),
        ('  if(!wire_path)return error("wire output required");',
         '  if(!layout_counts_only)return error("explicit --counts-only required");'),
    ]
    source = original
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError('unexpected layout instrumentation: ' + old[:80])
        source = source.replace(old, new, 1)
    restored = source
    for old, new in reversed(patches):
        if restored.count(new) != 1:
            raise ValueError('ambiguous reversible layout delta')
        restored = restored.replace(new, old, 1)
    if restored != original:
        raise ValueError('layout delta changes unrelated native bytes')
    return source


def instrumentation_hashes():
    return {p.name: wire.solve6.sha256(p) for p in (
        Path(base.__file__), Path(wire.__file__), Path(cuts.__file__), Path(__file__))}


def build(args):
    output = args.output.resolve()
    # A new directory is mandatory; old accepted build identities are untouched.
    output.mkdir(parents=True, exist_ok=False)
    line = json.loads(args.line.read_text()) if args.line else None
    pins = wire.line_pins6.plan(line)['pins'] if line else None
    source = output / 'census.c'
    source.write_text(generated_source(wire.solve6.SOURCE.read_text(), pins))
    compiler = Path(shutil.which('cc')).resolve(strict=True)
    binary = output / 'census'
    command = [str(compiler), *wire.solve6.FLAGS, str(source), '-o', str(binary)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if done.returncode:
        raise ValueError(done.stderr)
    report = dict(format=FORMAT, status='complete', created_utc=utc(),
        reference_source_sha256=wire.solve6.sha256(wire.solve6.SOURCE),
        source_sha256=wire.solve6.sha256(source), binary=str(binary),
        binary_sha256=wire.solve6.sha256(binary), compiler=str(compiler),
        compiler_sha256=wire.solve6.sha256(compiler), flags=list(wire.solve6.FLAGS),
        command=command, compile_stderr=done.stderr, pins=pins,
        line_sha256=wire.solve6.sha256(args.line) if args.line else None,
        instrumentation_sha256=instrumentation_hashes(),
        solver_rules_tt_bytes_unchanged=True, compact_memo=True,
        witness_policy='min-replies with optional fail-closed line pins and bounded inline cuts',
        initial_problem2_proved=False, optimal_pair_proved=False, production_authorized=False)
    atomic_json(output / 'build.json', report)
    print(json.dumps(dict(status='complete', binary_sha256=report['binary_sha256'])))
    return report


def checked_build(path):
    path = path.resolve()
    report = json.loads((path / 'build.json').read_text())
    binary = Path(report['binary'])
    compiler = Path(report['compiler'])
    expected = generated_source(wire.solve6.SOURCE.read_text(), report.get('pins')).encode()
    if (report.get('format') != FORMAT or report.get('status') != 'complete' or
        report.get('solver_rules_tt_bytes_unchanged') is not True or
        report.get('compact_memo') is not True or binary != path / 'census' or
        report.get('reference_source_sha256') != wire.solve6.sha256(wire.solve6.SOURCE) or
        report.get('source_sha256') != hashlib.sha256(expected).hexdigest() or
        (path / 'census.c').read_bytes() != expected or
        report.get('binary_sha256') != wire.solve6.sha256(binary) or
        report.get('compiler_sha256') != wire.solve6.sha256(compiler) or
        report.get('flags') != list(wire.solve6.FLAGS) or
        report.get('command') != [str(compiler), *wire.solve6.FLAGS, str(path / 'census.c'), '-o', str(binary)] or
        report.get('instrumentation_sha256') != instrumentation_hashes() or
        any(report.get(k) is not False for k in ('initial_problem2_proved', 'optimal_pair_proved', 'production_authorized'))):
        raise ValueError('layout build provenance changed')
    return report, binary


def native_options(args):
    """Explicit, bounded flags suitable for canonical_census6.run's override."""
    specs = [('layout_limit_mib', 1, 512), ('max_entries', 1, 200),
             ('max_tokens', 1, 32000), ('max_records', 1, 200000000),
             ('inline_limit', 1, 65536), ('record_limit', 16, 1048576), ('body_fuel', 1, 80)]
    for name, low, high in specs:
        value = getattr(args, name)
        if type(value) is not int or not low <= value <= high:
            raise ValueError('invalid ' + name)
    if getattr(args, 'counts_only', False) is not True:
        raise ValueError('explicit counts-only required')
    return ['--counts-only', '--layout-limit-mib', str(args.layout_limit_mib),
        '--layout-max-entries', str(args.max_entries), '--layout-max-tokens', str(args.max_tokens),
        '--layout-max-records', str(args.max_records), '--wire-inline-limit', str(args.inline_limit),
        '--wire-record-limit', str(args.record_limit), '--wire-body-fuel', str(args.body_fuel)]


def plan_counts(plan, source_wire_bytes):
    """Reduce a real wire_pilot6.emit plan for independent fixture comparison.

    Compact bytes exclude tabs and explicit citation-state payloads. Transitive
    part sums exclude each part itself, as in the Python plan; the assembly
    includes its root part. No conclusion about a larger graph follows.
    """
    parts = [target for target in plan['targets'] if target['kind'] == 'part']
    assembly = [target for target in plan['targets'] if target['kind'] == 'assembly']
    if not parts or len(assembly) != 1:
        raise ValueError('one nonempty real wire plan required')
    result = {'layout_parts': len(parts), 'layout_source_wire_bytes': source_wire_bytes,
        'layout_records': sum(t['entries'] for t in parts),
        'layout_tokens': sum(t['tokens'] for t in parts),
        'layout_compact_bytes': sum(t['compact_bytes'] for t in parts),
        'layout_max_part_entries': max(t['entries'] for t in parts),
        'layout_max_part_tokens': max(t['tokens'] for t in parts),
        'layout_assembly_transitive_parts': assembly[0]['transitive_parts'],
        'layout_assembly_transitive_entries': assembly[0]['transitive_entries']}
    for name, key in (('imported_citations', 'imported_citations'),
                      ('direct_dependencies', 'dependencies'),
                      ('transitive_parts', 'transitive_parts'),
                      ('transitive_entries', 'transitive_entries')):
        values = [len(t[key]) if key == 'dependencies' else t[key] for t in parts]
        result['layout_' + name + '_sum'] = sum(values)
        result['layout_' + name + '_max'] = max(values)
    return result


def run(args):
    """Protect the original immutable TT through canonical_census6.run."""
    options = native_options(args)
    if not 1 <= args.native_cpu <= 7200:
        raise ValueError('invalid native CPU cap')
    root = args.root_key
    if root == 'initial':
        position, turn = 'initial', 'black'
    else:
        wire.compact.pack_state(root)
        position, turn = root[1:], 'black' if root[0] == 'b' else 'white'
    partial = output = None
    if args.wire_output is not None:
        output = args.wire_output.resolve()
        partial = output.with_name(output.name + '.partial')
        if (output.exists() or partial.exists() or 'results' not in output.parts or
            not 1 <= args.wire_limit_mib <= 512):
            raise ValueError('fresh bounded fixture wire required')
        output.parent.mkdir(parents=True, exist_ok=True)
        options += ['--wire-output', str(partial), '--wire-limit-mib', str(args.wire_limit_mib)]
    executed = []
    def native(command, **kwargs):
        command = [command[0], 'layout', *command[2:], *options]
        executed.extend(command)
        return subprocess.run(command, **kwargs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    base.run(args, build_validator=checked_build, execute_native=native, position=position, turn=turn)
    report = json.loads(args.output.read_text())
    counts = report['counts']
    complete = bool(report['native_complete'] and counts.get('layout_complete') is True and
                    counts.get('layout_censored') is False and counts.get('wire_complete') is True)
    if output is not None:
        complete = bool(complete and partial.is_file() and partial.stat().st_size == counts['wire_bytes'] and
                        partial.stat().st_size <= args.wire_limit_mib * 1024**2)
    report.update(format=RUN_FORMAT, command=executed, root_key=root, counts_only=True,
        layout_complete=complete, status='complete-untrusted-layout' if complete else 'censored-untrusted-layout',
        layout_counts_censored=not complete, incomplete_count_extrapolated=False,
        layout_partial_counts_are_exact=False if not complete else True,
        pins_require_kernel_line_validation=True, initial_problem2_proved=False,
        optimal_pair_proved=False, production_authorized=False,
        scope='untrusted native layout statistics; no Agda premise or production GO')
    if output is not None:
        report.update(wire_output=str(output if complete else partial),
            wire_output_sha256=wire.solve6.sha256(partial) if partial.is_file() else None,
            wire_complete=complete)
        if complete:
            partial.rename(output)
    atomic_json(args.output, report)
    return complete


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('build', 'run'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--line', type=Path)
    for name in ('build', 'tests', 'donor', 'wire-output'):
        p.add_argument('--' + name, type=Path)
    p.add_argument('--counts-only', action='store_true')
    p.add_argument('--root-key', default='initial')
    p.add_argument('--direction', choices=('lower', 'upper'), default='lower')
    p.add_argument('--max-states', type=int, default=70000000)
    p.add_argument('--native-cpu', type=int, default=180)
    p.add_argument('--inline-limit', type=int, default=256)
    p.add_argument('--max-entries', type=int, default=DEFAULT_ENTRIES)
    p.add_argument('--max-tokens', type=int, default=DEFAULT_TOKENS)
    p.add_argument('--max-records', type=int, default=200000000)
    p.add_argument('--layout-limit-mib', type=int, default=MAX_LAYOUT_MIB)
    p.add_argument('--record-limit', type=int, default=1048576)
    p.add_argument('--body-fuel', type=int, default=80)
    p.add_argument('--wire-limit-mib', type=int, default=4)
    args = p.parse_args()
    if args.mode == 'build':
        build(args)
        return 0
    if not all((args.build, args.tests, args.donor)):
        p.error('run requires build/tests/donor')
    return 0 if run(args) else 1


if __name__ == '__main__':
    raise SystemExit(main())
