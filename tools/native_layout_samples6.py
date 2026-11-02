#!/usr/bin/env python3
"""Bounded untrusted native samples; no Agda premise or production authority.

Numeric ranks reserve 200 slots per layout part. Raw bodies omit citation payloads;
references give the payloads in parser order. Only selected rows and needed state
chunks leave the native process. All graph instrumentation is reversibly patched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import wire_layout6 as layout
import compact_shared6 as compact
from run_job import atomic_json, utc

FORMAT = 'othello-native-layout-samples6-build-v1'
ALPHABET = compact.COUNTS
MAX_BYTES = 32 * 1024**2

DECLARATIONS = r'''
#include <sys/types.h>
#include <unistd.h>
extern int truncate(const char *, off_t);
static const char *sample_path;
static FILE *sample_file;
static uint32_t sample_selected[16];
static size_t sample_selected_count,sample_record_cap=8000000;
static size_t sample_output_limit=16*1024*1024,sample_output_bytes;
static char *sample_states;
static unsigned char *sample_needed;
static uint64_t sample_rows;
static int sample_is_selected(size_t p) {
  for(size_t i=0;i<sample_selected_count;i++)if(sample_selected[i]==p)return 1;return 0;
}
static int sample_parts_option(const char *s) {
  if(sample_selected_count || !*s)return 0;
  for(;;){uint32_t n=0;size_t digits=0;
    while(*s>='0' && *s<='9'){if(++digits>5)return 0;n=n*10+(unsigned)(*s++-'0');}
    if(!digits || n>=40000 || sample_selected_count>=16)return 0;
    if(sample_is_selected(n))return 0;sample_selected[sample_selected_count++]=n;
    if(!*s)return 1;if(*s++!=',' || !*s)return 0;
  }
}
static int sample_write(const char *s,size_t n) {
  if(layout_stop())return 0;
  if(sample_output_bytes>sample_output_limit || n>sample_output_limit-sample_output_bytes)
    return layout_fail("sample-output-bound");
  if(n && fwrite(s,1,n,sample_file)!=n)return layout_fail("sample-write");
  sample_output_bytes+=n;return 1;
}
static int sample_put(const char *s){return sample_write(s,strlen(s));}
static int sample_num(uint64_t n){char buf[32];int k=snprintf(buf,sizeof(buf),"%llu",(unsigned long long)n);
  return k>0 && (size_t)k<sizeof(buf) && sample_write(buf,(size_t)k);}
static int sample_initialize(void) {
  if(!sample_path)return 1;
  sample_file=fopen(sample_path,"wbx");if(!sample_file)return layout_fail("sample-open");
  sample_states=layout_allocate(sample_record_cap*13);sample_needed=layout_allocate(40000);
  return sample_states && sample_needed;
}
static int sample_record(u64 P,u64 O,int turn,WireBuffer *body,WireBuffer *refs) {
  if(!sample_path)return 1;
  size_t p=layout_part_count,row=(size_t)layout_part_entries,rank=p*200+row;
  if(p>=40000 || row>=200 || rank>=sample_record_cap)return layout_fail("sample-rank-bound");
  char state[14];wire_state(P,O,turn,state);memcpy(sample_states+13*rank,state,13);
  for(size_t j=0;j<layout_record_ref_count;j++){
    size_t id=layout_record_refs[j];if(id>=prefix_count)return layout_fail("sample-reference-id");
    uint32_t assigned=wire_indegree[id],ref=assigned&LAYOUT_OWNER;
    if(!(assigned&LAYOUT_ASSIGNED) || ref>=rank || ref>=sample_record_cap || ref/200>=40000)
      return layout_fail("sample-reference-order");
    if(ref/200<p && ref%200>=layout_parts[ref/200].entries)return layout_fail("sample-reference-row");
    if(memcmp(sample_states+13*ref,refs->data+13*j,13))return layout_fail("sample-reference-state");
  }
  if(!sample_is_selected(p))return 1;
  for(size_t i=0;i<body->n;i++)if(!strchr("LKRPCF0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_",body->data[i]))
    return layout_fail("sample-body-alphabet");
  sample_needed[p]=1;
  if(!sample_put("{\"kind\":\"row\",\"part\":") || !sample_num(p) ||
     !sample_put(",\"row\":") || !sample_num(row) || !sample_put(",\"state\":\"") ||
     !sample_write(state,13) || !sample_put("\",\"body\":\"") ||
     !sample_write(body->data,body->n) || !sample_put("\",\"references\":["))return 0;
  for(size_t j=0;j<layout_record_ref_count;j++){
    size_t id=layout_record_refs[j];if(id>=prefix_count)return layout_fail("sample-reference-id");
    uint32_t assigned=wire_indegree[id],ref=assigned&LAYOUT_OWNER;
    if(!(assigned&LAYOUT_ASSIGNED) || ref>=rank || ref>=sample_record_cap || ref/200>=40000)
      return layout_fail("sample-reference-order");
    if(ref/200<p && ref%200>=layout_parts[ref/200].entries)return layout_fail("sample-reference-row");
    sample_needed[ref/200]=1;
    if((j && !sample_put(",")) || !sample_num(ref))return 0;
  }
  if(!sample_put("]}\n"))return 0;sample_rows++;return 1;
}
static int sample_finish(int valid) {
  if(!sample_path)return valid;
  if(valid)for(size_t i=0;i<sample_selected_count;i++)if(sample_selected[i]>=layout_part_count){
    layout_fail("sample-selected-part");valid=0;break;}
  if(valid)for(size_t p=0;p<layout_part_count;p++)if(sample_needed[p]){
    size_t rows=layout_parts[p].entries;
    if(!sample_put("{\"kind\":\"states\",\"part\":") || !sample_num(p) ||
       !sample_put(",\"rows\":") || !sample_num(rows) || !sample_put(",\"text\":\"") ||
       !sample_write(sample_states+13*p*200,13*rows) || !sample_put("\"}\n")){valid=0;break;}
  }
  off_t marker=(off_t)sample_output_bytes;
  if(valid && fflush(sample_file)!=0){layout_fail("sample-flush");valid=0;}
  if(valid){
    if(!sample_put("{\"kind\":\"complete\",\"parts\":") || !sample_num(layout_part_count) ||
       !sample_put(",\"records\":") || !sample_num(layout_records) ||
       !sample_put(",\"tokens\":") || !sample_num(layout_tokens) ||
       !sample_put(",\"selected_rows\":") || !sample_num(sample_rows) ||
       !sample_put(",\"record_cap\":") || !sample_num(sample_record_cap) ||
       !sample_put(",\"output_limit_bytes\":") || !sample_num(sample_output_limit) ||
       !sample_put(",\"max_entries\":") || !sample_num(layout_max_entries) ||
       !sample_put(",\"max_tokens\":") || !sample_num(layout_max_tokens) ||
       !sample_put(",\"selected\":["))valid=0;
    for(size_t i=0;valid && i<sample_selected_count;i++)
      if((i && !sample_put(",")) || !sample_num(sample_selected[i]))valid=0;
    if(valid && !sample_put("]}\n"))valid=0;
  }
  if(sample_file && fclose(sample_file)!=0){layout_fail("sample-close");valid=0;}
  sample_file=NULL;
  if(!valid && marker && truncate(sample_path,marker)!=0)layout_fail("sample-truncate");
  layout_free(sample_states,sample_record_cap*13);layout_free(sample_needed,40000);
  return valid && !layout_failed;
}
'''

OPTIONS = r'''
    else if(!strcmp(argv[i],"--sample-parts")){if(++i==argc || !sample_parts_option(argv[i]))return error("invalid sample parts");}
    else if(!strcmp(argv[i],"--sample-output")){if(++i==argc || sample_path)return error("one sample output required");sample_path=argv[i];}
    else if(!strcmp(argv[i],"--sample-record-cap")){int cap;if(++i==argc || !integer(argv[i],1,8000000,&cap))return error("invalid sample record cap");sample_record_cap=(size_t)cap;}
    else if(!strcmp(argv[i],"--sample-output-limit-mib")){int cap;if(++i==argc || !integer(argv[i],1,32,&cap))return error("invalid sample output cap");sample_output_limit=(size_t)cap*1024*1024;}
'''


def generated_source(raw, pins=None):
    original = layout.generated_source(raw, pins)
    patches = [
        ('static int wire_record(', DECLARATIONS + '\nstatic int wire_record('),
        ('size_t owner=assigned&LAYOUT_OWNER;', 'size_t owner=(assigned&LAYOUT_OWNER)/200;'),
        ('  layout_part_entries++;layout_part_tokens+=body->tokens;',
         '  if(!sample_record(P,O,turn,body,refs))return 0;\n  layout_part_entries++;layout_part_tokens+=body->tokens;'),
        ('|LAYOUT_ASSIGNED|(uint32_t)layout_part_count;',
         '|LAYOUT_ASSIGNED|(uint32_t)(layout_part_count*200+layout_part_entries-1);'),
        ('    if(valid && !layout_initialize())valid=0;',
         '    if(valid && !layout_initialize())valid=0;\n    if(valid && !sample_initialize())valid=0;'),
        ('  printf(",\\\"wire_complete', '  valid=sample_finish(valid);\n  printf(",\\\"wire_complete'),
        ('    else if(!strcmp(argv[i],"--wire-inline-limit"))', OPTIONS + '\n    else if(!strcmp(argv[i],"--wire-inline-limit"))'),
        ('  if(!layout_counts_only)return error("explicit --counts-only required");',
         '  if(!layout_counts_only)return error("explicit --counts-only required");\n  if(wire_path)return error("full wire output forbidden for samples");\n  if(!sample_path || !sample_selected_count)return error("sample output and selected parts required");'),
    ]
    source = original
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError('unexpected sample instrumentation: ' + old[:80])
        source = source.replace(old, new, 1)
    restored = source
    for old, new in reversed(patches):
        if restored.count(new) != 1:
            raise ValueError('ambiguous reversible sample delta')
        restored = restored.replace(new, old, 1)
    if restored != original:
        raise ValueError('sample delta changes unrelated native bytes')
    return source


def require(test, message):
    if not test:
        raise ValueError(message)


def integer(value, low, high, what):
    require(type(value) is int and low <= value <= high, 'invalid ' + what)
    return value


def number(n):
    """Same base37 numeric syntax as nat_indexed_pilot6, without proof imports."""
    integer(n, 0, 19999999, 'numeric ID')
    digits = ''
    while n:
        n, d = divmod(n, 37)
        digits = ALPHABET[d] + digits
    return (digits or '0') + ';'


def convert_body(text, references):
    """Validate one bounded raw body and insert IDs at K/R placeholders."""
    require(isinstance(text, str) and 0 < len(text) <= 1048576, 'invalid body size')
    require(isinstance(references, list), 'invalid references')
    pos = ref = tokens = 0
    output = []
    pending = 1
    while pending:
        pending -= 1
        require(pos < len(text), 'truncated body')
        tag = text[pos];pos += 1;tokens += 1;output.append(tag)
        require(tokens <= 32000, 'body token cap')
        if tag == 'L':
            continue
        if tag in 'RCF':
            require(pos < len(text) and text[pos] in ALPHABET, 'missing body count')
            count = ALPHABET.index(text[pos]);output.append(text[pos]);pos += 1
            require(count <= {'R': 7, 'C': 35, 'F': 36}[tag], 'body count cap')
        if tag in 'KR':
            require(ref < len(references), 'missing reference')
            output.append(number(references[ref]));ref += 1
        elif tag in 'PC':
            pending += 1
        elif tag == 'F':
            pending += count
        else:
            raise ValueError('unsafe or unknown body token')
    require(pos == len(text) and ref == len(references), 'trailing body or references')
    return ''.join(output), tokens


def decode_samples(path):
    """Fail closed on partial/duplicated/inconsistent bounded JSONL artifacts."""
    path = Path(path)
    require(0 < path.stat().st_size <= MAX_BYTES, 'sample file byte cap')
    rows = {};states = {};complete = None;phase = 'rows';last_row_part = last_state_part = -1
    with path.open('r', encoding='ascii') as stream:
        for line in stream:
            require(line.endswith('\n') and len(line) <= 2 * 1048576, 'truncated or oversized sample line')
            require(complete is None, 'data after complete')
            try:
                # Duplicate object keys are also rejected.
                def pairs(items):
                    result = {}
                    for k, v in items:
                        require(k not in result, 'duplicate JSON key');result[k] = v
                    return result
                item = json.loads(line, object_pairs_hook=pairs)
            except (UnicodeError, json.JSONDecodeError) as error:
                raise ValueError('invalid sample JSON') from error
            require(isinstance(item, dict), 'invalid sample object')
            kind = item.get('kind')
            if kind == 'row':
                require(phase == 'rows' and set(item) == {'kind','part','row','state','body','references'}, 'invalid row object/order')
                p = integer(item['part'], 0, 39999, 'part')
                r = integer(item['row'], 0, 199, 'row')
                require(p >= last_row_part, 'row part order');last_row_part = p
                require(len(rows) < 16 or p in rows, 'selected part cap')
                part = rows.setdefault(p, [])
                require(r == len(part), 'duplicate or noncontiguous row')
                compact.unpack_state(item['state'])
                require(isinstance(item['references'], list), 'invalid references')
                for n in item['references']:
                    integer(n, 0, p*200+r-1, 'earlier reference')
                    require(n < 8000000, 'reference rank cap')
                body, tokens = convert_body(item['body'], item['references'])
                part.append(dict(item, numeric_body=body, tokens=tokens))
            elif kind == 'states':
                phase = 'states'
                require(set(item) == {'kind','part','rows','text'}, 'invalid states object')
                p = integer(item['part'], 0, 39999, 'state part')
                n = integer(item['rows'], 1, 200, 'state rows')
                require(p > last_state_part, 'state chunk order');last_state_part = p
                require(p not in states, 'duplicate state chunk')
                text = item['text']
                require(isinstance(text, str) and len(text) == 13*n, 'state chunk size')
                for i in range(n):compact.unpack_state(text[13*i:13*(i+1)])
                states[p] = {'rows':n, 'text':text}
            elif kind == 'complete':
                complete = item
            else:
                raise ValueError('unknown sample kind')
    require(complete is not None, 'missing complete marker')
    require(set(complete) == {'kind','parts','records','tokens','selected_rows','record_cap','output_limit_bytes','max_entries','max_tokens','selected'}, 'invalid complete object')
    np = integer(complete['parts'], 1, 40000, 'complete parts')
    nr = integer(complete['records'], 1, 8000000, 'complete records')
    cap = integer(complete['record_cap'], 1, 8000000, 'record cap')
    entries = integer(complete['max_entries'], 1, 200, 'entry cap')
    token_cap = integer(complete['max_tokens'], 1, 32000, 'token cap')
    integer(complete['tokens'], nr, nr*token_cap, 'complete tokens')
    limit = integer(complete['output_limit_bytes'], 1024**2, MAX_BYTES, 'output cap')
    require(limit % 1024**2 == 0 and path.stat().st_size <= limit, 'output size inconsistency')
    require(np <= nr <= np*entries and (np-1)*200 < cap, 'complete count inconsistency')
    selected = complete['selected']
    require(isinstance(selected, list) and 1 <= len(selected) <= 16, 'selected cap')
    for p in selected:integer(p, 0, np-1, 'selected part')
    require(len(set(selected)) == len(selected) and set(selected) == set(rows), 'selected mismatch')
    integer(complete['selected_rows'], 1, 3200, 'selected row count')
    require(complete['selected_rows'] == sum(map(len, rows.values())), 'selected row count mismatch')
    needed = set(rows)
    cases = []
    for p in sorted(rows):
        part = rows[p];refs = [n for row in part for n in row['references']]
        deps = sorted({p} | {n//200 for n in refs});needed.update(deps)
        require(p in states and len(part) == states[p]['rows'], 'selected chunk row mismatch')
        require(len(part) <= entries and sum(row['tokens'] for row in part) <= token_cap, 'selected layout cap')
        for row in part:
            require(row['state'] == states[p]['text'][13*row['row']:13*(row['row']+1)], 'selected state mismatch')
        cases.append(dict(part=p,rows=len(part),state_text=states[p]['text'],
            body_text=''.join(row['numeric_body'] for row in part),references=refs,
            dependencies=deps,tokens=sum(row['tokens'] for row in part)))
    require(set(states) == needed, 'missing or surplus needed chunk')
    for p, chunk in states.items():
        require(p < np and chunk['rows'] <= entries and p*200+chunk['rows'] <= cap, 'chunk cap inconsistency')
    require(sum(c['rows'] for c in states.values()) <= nr, 'state count inconsistency')
    require(sum(c['tokens'] for c in cases) <= complete['tokens'], 'token count inconsistency')
    for case in cases:
        for n in case['references']:
            require(n//200 in states and n%200 < states[n//200]['rows'], 'reference row missing')
    return dict(cases=cases, states=states, complete=complete)


def instrumentation_hashes():
    paths = [Path(layout.base.__file__), Path(layout.wire.__file__), Path(layout.cuts.__file__), Path(layout.__file__), Path(__file__)]
    return {p.name: layout.wire.solve6.sha256(p) for p in paths}


def build(args):
    output = args.output.resolve();output.mkdir(parents=True, exist_ok=False)
    line = json.loads(args.line.read_text()) if args.line else None
    pins = layout.wire.line_pins6.plan(line)['pins'] if line else None
    source = output/'census.c';source.write_text(generated_source(layout.wire.solve6.SOURCE.read_text(), pins))
    compiler = Path(shutil.which('cc')).resolve(strict=True);binary = output/'census'
    command = [str(compiler), *layout.wire.solve6.FLAGS, str(source), '-o', str(binary)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if done.returncode:raise ValueError(done.stderr)
    sha = layout.wire.solve6.sha256
    report = dict(format=FORMAT,status='complete',created_utc=utc(),
        reference_source_sha256=sha(layout.wire.solve6.SOURCE),source_sha256=sha(source),
        binary=str(binary),binary_sha256=sha(binary),compiler=str(compiler),compiler_sha256=sha(compiler),
        flags=list(layout.wire.solve6.FLAGS),command=command,compile_stderr=done.stderr,pins=pins,
        line_sha256=sha(args.line) if args.line else None,instrumentation_sha256=instrumentation_hashes(),
        solver_rules_tt_bytes_unchanged=True,compact_memo=True,initial_problem2_proved=False,
        optimal_pair_proved=False,production_authorized=False,
        scope='bounded untrusted selected rows and state chunks; no Agda premise')
    atomic_json(output/'build.json',report)
    print(json.dumps(dict(status='complete',binary_sha256=report['binary_sha256'])))
    return report


def checked_build(path):
    path = path.resolve();report = json.loads((path/'build.json').read_text())
    binary = Path(report['binary']);compiler = Path(report['compiler']);sha = layout.wire.solve6.sha256
    expected = generated_source(layout.wire.solve6.SOURCE.read_text(),report.get('pins')).encode()
    require(report.get('format') == FORMAT and report.get('status') == 'complete' and
        report.get('solver_rules_tt_bytes_unchanged') is True and report.get('compact_memo') is True and
        binary == path/'census' and report.get('reference_source_sha256') == sha(layout.wire.solve6.SOURCE) and
        report.get('source_sha256') == hashlib.sha256(expected).hexdigest() and
        (path/'census.c').read_bytes() == expected and report.get('binary_sha256') == sha(binary) and
        report.get('compiler_sha256') == sha(compiler) and report.get('flags') == list(layout.wire.solve6.FLAGS) and
        report.get('command') == [str(compiler),*layout.wire.solve6.FLAGS,str(path/'census.c'),'-o',str(binary)] and
        report.get('instrumentation_sha256') == instrumentation_hashes() and
        all(report.get(k) is False for k in ('initial_problem2_proved','optimal_pair_proved','production_authorized')),
        'sample build provenance changed')
    return report,binary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('build',));p.add_argument('--output',type=Path,required=True)
    p.add_argument('--line',type=Path);build(p.parse_args())


if __name__ == '__main__':main()
