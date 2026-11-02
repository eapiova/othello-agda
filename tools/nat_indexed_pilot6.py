#!/usr/bin/env python3
"""Measure numeric IDs on three real, independently checked descendant parts.

This is a bounded feasibility test, not production. Accepted historical proof
interfaces are never imported by a row check. Data caches are copied privately.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil

import assembly6
from cache_resume6 import copy_interface
from data_only_pilot6 import borrowed_sources
from indexed_family6 import shared_part
from indexed_shape_mode6 import read_shape
from indexed_wire_resume6 import closed, pinned
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require

PREFIX = 'Tests.NatPilot6'
OLD = 'Tests.IndexedWire6'
ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
COMMON = '''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Agda.Builtin.String using (String)
open import Game.Core using (white)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Othello.NatIndexed6 as D
open import Othello.Board using (State; six)
open import Othello.Statements using (lowerGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6)
import Othello.Fast6 as Fast
'''


def number(n):
    require(0 <= n < 20000000, 'numeric ID out of parser range')
    digits = ''
    while n:
        n, d = divmod(n, 37)
        digits = ALPHABET[d] + digits
    return (digits or '0') + ';'


def convert_wire(text, leaves):
    paths = {n['path']: n for n in leaves}
    references, chunks = [], []
    position = 0
    def code(bound):
        nonlocal position
        require(position < len(text) and text[position] in ALPHABET, 'missing grammar count')
        digit = text[position];position += 1
        require(ALPHABET.index(digit) <= bound, 'grammar count exceeds bound')
        chunks.append(digit)
        return ALPHABET.index(digit)
    def reference():
        nonlocal position
        start = position
        while position < len(text) and text[position] in 'ab':position += 1
        path = text[start:position]
        require(path in paths, 'unknown citation path')
        digits = text[position:position+2];position += 2
        require(len(digits)==2 and all(d in ALPHABET for d in digits), 'missing citation row')
        leaf = paths[path]
        local = 37 * ALPHABET.index(digits[0]) + ALPHABET.index(digits[1])
        require(local < leaf['size'], 'citation row out of bounds')
        rank = leaf['leaf'] * 200 + local
        references.append(rank)
        chunks.append(number(rank))
    def body():
        nonlocal position
        require(position < len(text), 'truncated certificate')
        token = text[position];position += 1;chunks.append(token)
        if token == 'L':return
        if token == 'K':reference();return
        if token == 'R':code(7);reference();return
        if token == 'P':body();return
        if token == 'C':code(35);body();return
        if token == 'F':
            for _ in range(code(36)):body()
            return
        if token == 'S':
            start = position
            while position < len(text) and text[position].isdigit():position += 1
            require(start<position and position<len(text) and text[position]==';', 'invalid solve fuel')
            require(int(text[start:position])<=128,'solve fuel exceeds bound')
            position += 1;chunks.append(text[start:position]);return
        raise ValueError('unknown certificate token: '+token)
    while position < len(text):body()
    return ''.join(chunks), references


def resolver(node, deps):
    if not any(node['lo'] <= d < node['hi'] for d in deps):
        return 'M.absent'
    if 'leaf' in node:
        j = node['leaf']
        return f'(M.rows {200*j} {node["size"]} S{j}.states)'
    pivot = node['right']['lo'] * 200
    return f'(M.branch {pivot} {resolver(node["left"],deps)} {resolver(node["right"],deps)})'


def generate(old, check, parts):
    root, leaves = read_shape((old/'src/Tests/IndexedWire6/Shape.agda').read_text())
    sources = {}
    def emit(name, body):
        sources['src/'+PREFIX.replace('.', '/')+'/'+name+'.agda'] = (
            HEADER+'-- AI-assisted; all row facts are checked by safe Agda.\nmodule '+PREFIX+'.'+name+' where\n\n'+body)
    emit('Family', COMMON+'\nmodule Lower = D.Checking Fast.fastGame6 white (lowerGoal 4) lowerTransport6\n')
    cases = []
    for j in parts:
        original = (old/f'src/Tests/IndexedWire6/Part{j}.agda').read_text()
        deps = sorted(map(int,re.findall(r'^import Tests\.IndexedWire6\.StateData(\d+) as S\d+$',original,re.M)))
        require(j in deps and not re.search(r'^import .*\.Part\d+',original,re.M), 'data-only original required')
        body_source = old/f'src/Tests/IndexedWire6/BodyData{j}.agda'
        text = re.search(r'^text = "([^"]*)"$',body_source.read_text(),re.M)[1]
        changed, references = convert_wire(text, leaves)
        require(set(n//200 for n in references) <= set(deps), 'missing actual reference dependency')
        control = shared_part(original).replace('module '+OLD+f'.Part{j} where','module '+PREFIX+f'.Control{j} where',1)
        control = HEADER + control[control.index('\n')+1:]
        sources[f'src/Tests/NatPilot6/Control{j}.agda'] = control
        emit('Body'+str(j), COMMON+f'\ntext : String\ntext = "{changed}"\n')
        imports = ''.join(f'import {OLD}.StateData{d} as S{d}\n' for d in deps)
        n = leaves[j]['size']
        emit('Part'+str(j), COMMON+imports+f'''import {PREFIX}.Family as Family
import {PREFIX}.Body{j} as Body

embed : B.Fin {n} → ℕ
embed i = {200*j} + B.finToNat i
table : M.Map (State six)
table = {resolver(root,set(deps))}
L : I.Resolver ℕ (State six)
L = M.lookup table

abstract
  accepted : Family.Lower.checkPart L embed S{j}.text Body.text ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Family.Lower.V.Compatible L G →
    (∀ i → G (embed i) ≡ B.lookupVec S{j}.states i) →
    (∀ i → C (embed i) ≡ B.lookupVec (D.bodies {n} Body.text) i) →
    ∀ i → Family.Lower.V.TreeOK G (embed i) (G (embed i)) (C (embed i))
  linked = Family.Lower.linkPart L embed S{j}.text Body.text accepted
''')
        cases.append(dict(part=j,rows=n,dependencies=deps,references=len(references),
            original_body_bytes=len(text),numeric_body_bytes=len(changed),
            original_part_source_sha256=assembly6.sha(old/f'src/Tests/IndexedWire6/Part{j}.agda')))
    for name,text in sources.items():
        path=check/name;require(not path.exists(),'refusing source overwrite');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    return cases


def run(args):
    current=Path.cwd();previous=args.previous.resolve();base=previous/'results/indexed-slices-resume6';old=base/'check'
    label=previous.name.removeprefix('six-')
    actual=pinned(previous/'results'/(label+'.json'),args.expected_receipt_sha256)
    require(actual.get('finished_utc') and actual['source_unchanged'] and actual['expected_source_matches']
        and source_identity(previous)['source_sha256']==actual['source_sha256'], 'closed unchanged donor required')
    state=closed(actual);prior=pinned(base/'report.json',args.expected_report_sha256)
    pool=pinned(base/'interface-map.json',args.expected_map_sha256);machine=assembly6.machine_identity(args.agda)
    old_source=source_identity(old)
    require(prior['accepted_parts']==267 and old_source==prior['checked_source'] and prior['machine']==machine
        and machine['hostname']=='eapiova' and machine['agda_sha256']==args.expected_agda_sha256
        and assembly6.interfaces(old)==pool and digest_entries(pool)==prior['last_interface_pool_sha256'], 'exact accepted data cache required')
    parts=[60,120,231];deps=set(parts)
    for j in parts:
        text=(old/f'src/Tests/IndexedWire6/Part{j}.agda').read_text()
        deps.update(map(int,re.findall(r'^import Tests\.IndexedWire6\.StateData(\d+) as',text,re.M)))
    data={f'src/Tests/IndexedWire6/StateData{d}.agda' for d in deps}
    data.update(f'src/Tests/IndexedWire6/BodyData{j}.agda' for j in parts)
    data.update(['src/Tests/IndexedWire6/Shape.agda','src/Tests/IndexedWire6/Family.agda'])
    borrowed={n:h for n,h in pool.items() if '/Tests/' not in n or n.split('/agda/',1)[1][:-1] in data}
    require(not any('/Part' in n or '/Node' in n for n in borrowed), 'proof imports forbidden in this comparison')
    names=borrowed_sources(borrowed)|data|{'othello.agda-lib'}
    extra=['src/Game/NatOrder.agda','src/Game/NatMap.agda','src/Othello/NatIndexed6.agda','src/Tests/NatIndexed6.agda']
    estimate=sum((old/n).stat().st_blocks*512 for n in names)+sum((old/n).stat().st_blocks*512 for n in borrowed)+8*2**20
    out=args.output.resolve();require(not out.exists() and 'results' in out.parts,'fresh isolated experiment required');out.mkdir(parents=True)
    report=dict(format='othello-nat-indexed-pilot6-v1',accepted=False,status='preparing',created_utc=utc(),
        machine=machine,donor_closed_service=state,donor_report_sha256=args.expected_report_sha256,donor_source=old_source,
        phases=[],kernel_cpu_seconds=0.,initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False,
        scope='same real rows, balanced and numeric IDs, data caches only; no descendant root assembly')
    def save():atomic_json(out/'report.json',report)
    def guard(extra_bytes=0):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used+extra_bytes<10*2**30 and free-extra_bytes>=100*2**30,'storage gate reached; donor preserved')
    guard(estimate)
    check=out/'check';check.mkdir()
    for name in sorted(names):
        dst=check/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,dst)
    for name in extra:
        dst=check/name;require(not dst.exists(),'new generic module overlaps donor');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(current/name,dst)
    for name,h in borrowed.items():copy_interface(old/name,check/name,h)
    report['cases']=generate(old,check,parts);source=source_identity(check);report['checked_source']=source;save()
    targets=['Tests.NatIndexed6',PREFIX+'.Family']
    targets += [PREFIX+'.'+variant+str(j) for j in parts for variant in ['Control','Part']]
    for index,target in enumerate(targets):
        guard();before=assembly6.interfaces(check);suffix='/'+target.replace('.','/')+'.agdai'
        require(not any(n.endswith(suffix) for n in before),'own target unexpectedly warm')
        remaining=args.kernel_cpu_limit-report['kernel_cpu_seconds'];require(remaining>1,'nested CPU cap reached')
        rec=run_job('target'+str(index),[args.agda,'--no-libraries','-i','src','--safe','--without-K',
            '--cubical-compatible','--save-metas','src/'+target.replace('.','/')+'.agda',
            '+RTS','-M1350M','-c','-s','-RTS'],out/'records',root=check,expected_source_sha256=source['source_sha256'],
            timeout=300,cpu_limit=min(180,remaining),rss_limit_gib=1.5,log_limit_mib=2,
            metadata=dict(target=target,own_target_cold=True,child_proof_imports=False,numeric_ids='Control' not in target))
        after=assembly6.interfaces(check);unchanged=all(after.get(n)==h for n,h in before.items())
        phase=dict(target=target,record=rec,borrowed_interfaces_unchanged=unchanged)
        if rec['accepted']:
            own=[n for n in after if n.endswith(suffix)];require(len(own)==1,'accepted target interface missing')
            phase['interface']=dict(path=own[0],bytes=(check/own[0]).stat().st_size,sha256=after[own[0]])
        report['phases'].append(phase);report['kernel_cpu_seconds']+=rec['cpu_seconds']
        report['status']='checking';report['last_interface_pool_sha256']=digest_entries(after)
        atomic_json(out/'interface-map.json',after);save()
        require(rec['accepted'] and unchanged,'comparison target or cache failed: '+target)
    require(source_identity(old)==old_source and assembly6.interfaces(old)==pool,'accepted donor changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),donor_unchanged=True);save()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-receipt-sha256','expected-report-sha256','expected-map-sha256'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--kernel-cpu-limit',type=float,default=650.)
    run(p.parse_args())


if __name__=='__main__':main()
