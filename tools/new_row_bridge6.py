#!/usr/bin/env python3
"""Untrusted bridge from an accepted new lower part to the complete state map.

Generated code checks routes and proof specialization only. It creates no new
row acceptance equation, and does not close initial-board certificate coverage.
The desktop run requires separate approval for its full-map memory allowance.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import resource
import shutil

import assembly6
import full_map_pilot6 as pilot
from full_map_alignment6 import FULL_SOURCE_SHA, FULL_POOL_SHA, route
from full_state_map6 import _namespace
from initial_global_alignment6 import _tree
from provenance import source_identity, digest_entries
from readonly_dependencies6 import command
from run_job import atomic_json, build_lock, run_job, utc
from wire_workflow6 import require

HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
PART = 34176
SCOPE = 'new-part34176-full-map-bridge6-v1'
ANSWER = 'Sì, autorizzo il collegamento'
ROW_BASE = pilot.BASE / 'six-wire-new-lower-1600-20261017/results/new-wire-pilot6'
ROW_SOURCE = '040cba814569d903e94ada45534da410cb84e28e1fa9885b83df9331a36c9125'
ROW_POOL = '4abf035d08b93ced858716005770ad43793f17df961e731fa4917620cde6d3e1'
ROW_REPORT = '3f1e68dbea67e014cfdb6bb99e084c8c14e19e19897e9369a7902eeb4153aa62'
FULL = pilot.BASE / 'six-full-map-lower-generate-20261016/results/full-map-pilot6/check'
ALIGNED = pilot.BASE / 'six-full-map-lower-alignment-20261016/results/full-map-pilot6/check'
ALIGNED_SOURCE = '1ba50cc7e5c94ee9b0e43dde0b417264bf252adb5704d9a5a7d6ec6a9d219a39'
ALIGNED_POOL = 'd97befd01b6db69e6262fc9ca94e0ffa8f7fa185dc831c5fcfc466d8505324ea'


def emit(check, full, sample, *, part=PART, row_prefix=None,
         prefix='Tests.NewLowerFullBridge6', batch_size=32, state_exports=None):
    _namespace(prefix)
    _namespace(full['prefix'])
    row_prefix = row_prefix or 'Tests.FullWireNewLower' + str(part)
    _namespace(row_prefix)
    require(type(part) is int and type(batch_size) is int and 1 <= batch_size <= 64,
            'bounded part and batch required')
    require(full['complete'] and full['rows_per_part'] == 200 and 1 <= full['rows'] <= 8000000
            and full['parts'] == (full['rows'] + 199) // 200 and 0 <= part < full['parts'],
            'complete contiguous200-row full map required')
    require(full['wire_sha256'] == sample['wire_sha256']
            and sample['wire_rows'] == full['rows'], 'wire epochs differ')
    require(prefix not in (full['prefix'], row_prefix), 'distinct namespaces required')
    chunks = {c['part']: c for c in full['chunks']}
    require(len(chunks) == len(full['chunks']) == full['parts'], 'complete unique chunk manifest required')
    cases = [c for c in sample['cases'] if c['part'] == part]
    require(len(cases) == 1, 'exactly one selected case required')
    case = cases[0]
    needed = case['dependencies']
    require(isinstance(needed, list) and 1 <= len(needed) <= 8192
            and all(type(j) is int and 0 <= j <= part for j in needed)
            and needed == sorted(set(needed)) and part in needed,
            'sorted bounded demands required')
    require(case['rows'] == min(200, full['rows'] - 200 * part)
            and set(needed) == {part} | {r // 200 for r in case['references']},
            'owned rows or reference demands differ')
    states = sample['states']
    for j in needed:
        require(j in states and j in chunks, 'demanded chunk absent')
        n = min(200, full['rows'] - 200 * j)
        text = states[j]['text']
        require(states[j]['rows'] == chunks[j]['rows'] == n and len(text) == n * 13
                and hashlib.sha256(text.encode()).hexdigest() == chunks[j]['text_sha256'],
                'new and full state literals differ')
    require(case['state_text'] == states[part]['text'], 'own state literal differs')
    if state_exports is not None:
        require(isinstance(state_exports, dict) and set(state_exports) == set(needed)
                and all(state_exports[j] == chunks[j]['module'] for j in needed),
                'exact canonical full-map state exports required')
        for module in state_exports.values():
            _namespace(module)
    check = Path(check).absolute()
    require(not check.exists() and 'results' in check.parts
            and not any(p.is_symlink() for p in (check, *check.parents)),
            'fresh private nonsymlink source root required')
    common = '''open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatMapRoute as R
import Game.Indexed as I
import Othello.LazyIndexed6 as Lazy using (states)
open import Othello.Board using (State; six; initial)
'''
    common += f'import {full["prefix"]}.Root as Full using (stateMap)\n'
    sources = {}
    owners = {}
    def add(name, body):
        relative = 'src/' + prefix.replace('.', '/') + '/' + name + '.agda'
        raw = (HEADER + '-- Reuse accepted row facts; no new row checker reductions.\nmodule '
               + prefix + '.' + name + ' where\n\n' + body).encode()
        require(sum(map(len, sources.values())) + len(raw) < 8 * 2**20,
                'bounded bridge source output exceeded')
        sources[relative] = raw
    for start in range(0, len(needed), batch_size):
        batch = needed[start:start + batch_size]
        name = 'Batch' + str(start // batch_size)
        body = common + ''.join('import ' + (state_exports[j] if state_exports is not None
                  else row_prefix + '.StateData' + str(j)) + f' as S{j} using (text)\n' for j in batch)
        for j in batch:
            owners[j] = name
            n = chunks[j]['rows']
            xs = f'(Lazy.states {n} S{j}.text)'
            body += f'''path{j} : R.Route Full.stateMap {200*j} {n} {xs}
path{j} = {route(0, full['parts'], j)}
aligned{j} : ∀ G → Laws.Compatible Full.stateMap G →
  Laws.Aligned (M.rows {200*j} {n} {xs}) G
aligned{j} G same = R.aligned G path{j} same
'''
        add(name, body)
    body = common + f'''import {row_prefix}.Part{part} as Part using (states; bodies; linked)
import {row_prefix}.BodyData{part} as Body using (bodies)
import {row_prefix}.Family as Family using (module A)
open import Othello.CompactShared6 using (decodeCompactState)
'''
    body += ''.join(f'import {prefix}.Batch{i} as B{i}\n' for i in range((len(needed)+batch_size-1)//batch_size))
    def aligned(j):
        return f'(B{owners[j][5:]}.aligned{j} G sameStates)'
    def combine(tree):
        if isinstance(tree, int):
            return aligned(tree)
        return '(' + combine(tree[1]) + ' , ' + combine(tree[2]) + ')'
    body += f'''
bodyPath : R.Route Part.bodies {200*part} {case['rows']} Body.bodies
bodyPath = R.here
symbolic : ∀ G C → Laws.Compatible Full.stateMap G →
  Laws.Compatible Part.bodies C → Family.A.Partial G C Part.states
symbolic G C sameStates sameBodies = Part.linked G C
  {combine(_tree(needed))}
  {aligned(part)}
  (R.aligned C bodyPath sameBodies)

-- A terminal fallback is used for future complete coverage. No terminal or
-- initial-board theorem is asserted by this partial-row bridge.
fallback : State six
fallback = fromMaybe (initial six) (decodeCompactState "wQQQQQQQQQQQQ")
G : ℕ → State six
G = Laws.totalize Full.stateMap fallback
C : ℕ → I.IndexedCertificate ℕ
C = Laws.totalize Part.bodies I.indexedLeaf
abstract
  partial : Family.A.Partial G C Part.states
  partial = symbolic G C (Laws.self-compatible Full.stateMap fallback)
    (Laws.self-compatible Part.bodies I.indexedLeaf)
'''
    add('Root', body)
    require(all(b'accepted = refl' not in raw and b'postulate' not in raw for raw in sources.values()),
            'new row acceptance or assumption refused')
    check.mkdir(parents=True)
    shutil.copy2(Path(__file__).resolve().parents[1] / 'othello.agda-lib', check / 'othello.agda-lib')
    for name, raw in sources.items():
        p = check / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(raw)
    return dict(format='othello-new-lower-full-map-bridge-layout6-v1', prefix=prefix,
                root_module=prefix+'.Root', part=part, owned_rows=case['rows'],
                demanded_state_chunks=len(needed), aligned_encoded_rows=sum(chunks[j]['rows'] for j in needed),
                new_boolean_rows=0, rechecked_row_facts=0, agda_checked=False,
                initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
                generated_sha256={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},
                generated_bytes=sum(map(len, sources.values())), source_modules=len(sources),
                uses_terminal_fallback_data=True, closes_only_partial_coverage=True)


def approved(plan_raw, approval):
    require(approval.get('approved') is True and approval.get('answer') == ANSWER
            and approval.get('scope') == SCOPE
            and approval.get('plan_sha256') == hashlib.sha256(plan_raw).hexdigest()
            and approval.get('cpu_max_seconds') == 300 and approval.get('hard_memory_gib') == 12
            and approval.get('artifact_cap_gib') == 12 and approval.get('free_disk_gib') == 80
            and approval.get('part') == PART and approval.get('new_boolean_rows') == 0
            and approval.get('native_search_allowed') is False
            and approval.get('production_authorized') is False,
            'separate approved12-GiB part34176 bridge scope required')


def run(current, out, plan_path, approval_path):
    plan_raw = plan_path.read_bytes()
    spec = json.loads(plan_raw)
    approved(plan_raw, json.loads(approval_path.read_text()))
    cap = resource.getrlimit(resource.RLIMIT_CPU)[0]
    require(cap != resource.RLIM_INFINITY and 0 < cap <= 270, 'capped outer runner required')
    paths = [s[3:] for s in Path('/proc/self/cgroup').read_text().splitlines() if s.startswith('0::')]
    require(len(paths) == 1, 'one memory cgroup required')
    maximum = (Path('/sys/fs/cgroup') / paths[0].lstrip('/') / 'memory.max').read_text().strip()
    require(maximum.isdigit() and 0 < int(maximum) <= 12 * 2**30, 'at-most12-GiB hard cgroup required')
    require(not out.exists(), 'fresh pilot output required')
    row = ROW_BASE / ('part-' + str(PART))
    expected = {FULL:(FULL_SOURCE_SHA,FULL_POOL_SHA), ALIGNED:(ALIGNED_SOURCE,ALIGNED_POOL), row:(ROW_SOURCE,ROW_POOL)}
    with contextlib.ExitStack() as stack:
        for donor in sorted([*expected, pilot.DONOR]):
            stack.enter_context(build_lock(donor))
        _, old_source, old_pool, machine = pilot.donor_identity()
        before = {}
        for donor,(source_sha,pool_sha) in expected.items():
            source = source_identity(donor)
            pool = assembly6.interfaces(donor)
            require(source['source_sha256'] == source_sha and digest_entries(pool) == pool_sha,
                    'accepted bridge donor identity differs')
            before[donor] = source,pool
        require(assembly6.sha(ROW_BASE/'report.json') == ROW_REPORT, 'accepted new-row report differs')
        accepted = json.loads((ROW_BASE/'report.json').read_text())
        require(accepted['accepted'] and accepted['new_rows_accepted'] == 1600,
                'complete accepted new-row pilot required')
        sample_path = ROW_BASE/'extract/results/sample.json'
        require(assembly6.sha(sample_path) == accepted['sample_sha256'], 'existing sample changed')
        sample = json.loads(sample_path.read_text())
        sample['states'] = {int(j):v for j,v in sample['states'].items()}
        full = json.loads((FULL/'results/full-state-map6.json').read_text())
        require(full['rows'] == 6873047 and full['parts'] == 34366
                and full['prefix'] == 'Tests.FullInitialLower6', 'exact full lower map required')
        pilot.storage(current,64*2**20)
        out.mkdir(parents=True)
        layout = emit(out/'check', full, sample)
        require(layout['generated_sha256'] == spec['generated_sha256'],
                'generated bridge differs from the reviewed source prototype')
        source = source_identity(out/'check')
        report = dict(format='othello-new-part34176-full-map-bridge6-v1',accepted=False,status='checking',
                      layout=layout,checked_source=source,plan_sha256=hashlib.sha256(plan_raw).hexdigest(),
                      created_utc=utc(),new_boolean_rows=0,rechecked_row_facts=0,reused_row_facts=200,
                      initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False)
        atomic_json(out/'report.json',report)
        argv = command(machine, layout['root_module'], out/'check', pilot.DONOR)
        i = argv.index('--')+1
        argv[i+4:i+4] = ['-i',str(FULL/'src'),'-i',str(ALIGNED/'src'),'-i',str(row/'src')]
        argv[argv.index('-M2700M')] = '-M10G'
        with pilot.watched_storage(current,out):
            rec = run_job('bridge-part34176',argv,out/'records',root=out/'check',
                expected_source_sha256=source['source_sha256'],timeout=500,cpu_limit=240,
                rss_limit_gib=11.5,log_limit_mib=4,
                metadata=dict(own_target_cold=True,checker_binary_sha256=pilot.AGDA_SHA,
                              new_boolean_rows=0,rechecked_row_facts=0))
        unchanged = (source_identity(pilot.DONOR) == old_source and assembly6.interfaces(pilot.DONOR) == old_pool
                     and all(source_identity(p) == s and assembly6.interfaces(p) == cache for p,(s,cache) in before.items()))
        own = assembly6.interfaces(out/'check')
        atomic_json(out/'interface-map.json',own)
        report.update(record=rec,accepted=bool(rec['accepted'] and unchanged),
                      status='complete' if rec['accepted'] and unchanged else 'not-accepted',
                      all_four_donors_unchanged=unchanged,own_interfaces=len(own),
                      own_interface_pool_sha256=digest_entries(own),storage=pilot.storage(current),finished_utc=utc())
        atomic_json(out/'report.json',report)
        require(report['accepted'],'bridge not accepted; originals retained, no automatic retry')
        return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--approval',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    run(Path.cwd().resolve(),args.output.absolute(),args.plan,args.approval)
