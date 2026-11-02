#!/usr/bin/env python3
"""Factor oversized untrusted entries into bounded, exact-state citations."""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import assembly6
import bench6
import compact_shared6 as compact
from generate6 import encode_state
import global_assembly6 as assembly
from global_shared6 import replay_many
import ref
import shared6
from run_job import atomic_json
import symmetry_stats6 as symmetry


@dataclass
class Piece:
    text: str
    tokens: int
    refs: set
    state: object


def factor(plan, cap=32000):
    assembly.validate_plan(plan)
    if cap < 2:
        raise ValueError('positive branch capacity required')
    entries, known, cuts = [], set(), []
    originals = {entry['state'] for entry in plan['entries']}

    def parse(text, offset, state):
        start = offset
        tag = text[offset]
        offset += 1
        if tag in 'LK':
            refs = {encode_state(state)} if tag == 'K' else set()
            return Piece(tag, 1, refs, state), offset
        if tag in 'SRCF':
            end = text.index(';', offset)
            digits = text[offset:end]
            if not digits or not digits.isascii() or not digits.isdecimal():
                raise ValueError('invalid numeric field')
            number, offset = int(digits), end+1
            if tag in 'SR':
                if tag == 'R' and number >= 8:
                    raise ValueError('invalid symmetry tag')
                refs = {encode_state(symmetry.transform(state, number))} if tag == 'R' else set()
                return Piece(text[start:offset], 1, refs, state), offset
        elif tag != 'P':
            raise ValueError('invalid certificate token')
        prefix = text[start:offset]
        successors = ref.successors(state)
        if tag == 'P':
            if ref.placements(state) or len(successors) != 1:
                raise ValueError('not a compulsory pass')
            children = successors
        elif tag == 'C':
            if not 0 <= number < len(successors):
                raise ValueError('invalid chosen successor')
            children = [successors[number]]
        else:
            if number != len(successors):
                raise ValueError('do not omit an opponent reply')
            children = successors
        pieces = []
        for child in children:
            piece, offset = parse(text, offset, child)
            pieces.append(piece)
        count = 1+sum(piece.tokens for piece in pieces)
        while count > cap:
            index = max(range(len(pieces)), key=lambda j: pieces[j].tokens)
            child = pieces[index]
            key = encode_state(child.state)
            if key in known or key in originals or not child.refs <= known:
                raise ValueError('citation would duplicate or forward-reference a state')
            entries.append(dict(state=key, certificate=child.text, references=sorted(child.refs)))
            known.add(key)
            cuts.append(dict(state=key, tokens=child.tokens,
                certificate_sha256=hashlib.sha256(child.text.encode()).hexdigest()))
            count += 1-child.tokens
            pieces[index] = Piece('K', 1, {key}, child.state)
        return Piece(prefix+''.join(piece.text for piece in pieces), count,
                     set().union(*(piece.refs for piece in pieces)), state), offset

    for entry in plan['entries']:
        if assembly.tokens(entry['certificate']) <= cap:
            changed = entry.copy()
        else:
            state = bench6.decode(entry['state'])
            body, end = parse(entry['certificate'], 0, state)
            if end != len(entry['certificate']):
                raise ValueError('unconsumed original certificate')
            changed = dict(state=entry['state'], certificate=body.text, references=sorted(body.refs))
        if changed['state'] in known or not set(changed['references']) <= known:
            raise ValueError('non-acyclic factored entry')
        entries.append(changed)
        known.add(changed['state'])
    result = dict(plan, entries=entries)
    assembly.validate_plan(result)
    original_tokens = sum(assembly.tokens(entry['certificate']) for entry in plan['entries'])
    factored_tokens = sum(assembly.tokens(entry['certificate']) for entry in entries)
    if factored_tokens != original_tokens+len(cuts):
        raise ValueError('factoring did more than introduce one citation per cut')
    if any(assembly.tokens(entry['certificate']) > cap for entry in entries):
        raise ValueError('entry still exceeds the declared cap')
    return result, cuts


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    plan_sha, report_sha = assembly6.sha(args.plan), assembly6.sha(args.report)
    original = json.loads(args.plan.read_text())
    report = json.loads(args.report.read_text())
    if (report.get('status') != 'complete' or not report.get('scalar_replay') or
            report['plan_sha256'] != plan_sha or report.get('direction') != 'lower' or
            report.get('sample_size') != 20 or report.get('subsample_seed') != 2026100701):
        raise ValueError('different original lower sample')
    result, cuts = factor(original)
    entries = [(bench6.decode(entry['state']), entry['certificate']) for entry in result['entries']]
    roots = [bench6.decode(state) for state in result['roots']]
    if not replay_many(entries, roots, 'lower', 4):
        raise ValueError('scalar replay rejected factored entries')
    if assembly6.sha(args.plan) != plan_sha or assembly6.sha(args.report) != report_sha:
        raise ValueError('original native input changed')
    args.output.mkdir(parents=True, exist_ok=False)
    atomic_json(args.output/'plan.json', result)
    report = dict(report, source_plan_sha256=plan_sha, source_report_sha256=report_sha,
        source_stats=report['stats'], factoring=dict(entry_token_cap=32000, cuts=cuts,
            new_citations=len(cuts), original_entries=len(original['entries']),
            original_certificates_retained_at=str(args.plan),
            operation='exact-state subtree factorization; every original move and reply retained'),
        plan_sha256=assembly6.sha(args.output/'plan.json'), scalar_replay=True)
    wire = compact.encode(entries)
    tokens = sum(assembly.tokens(entry['certificate']) for entry in result['entries'])
    report['stats'] = dict(report['stats'], entries=len(result['entries']),
        checked_tokens=tokens, citations=report['stats']['citations']+len(cuts),
        global_compact_bytes=len(wire.encode()), global_legacy_bytes=len(shared6.encode(entries).encode()),
        global_token_gain=report['stats']['per_root_d4_tokens']/tokens,
        global_compact_byte_gain=report['stats']['per_root_compact_bytes']/len(wire.encode()))
    atomic_json(args.output/'report.json', report)
    print(json.dumps(dict(status='complete', cuts=len(cuts), entries=len(result['entries']),
        checked_tokens=report['stats']['checked_tokens'], plan_sha256=report['plan_sha256'])))


if __name__ == '__main__':
    main()
