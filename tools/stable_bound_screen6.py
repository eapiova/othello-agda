"""Untrusted stable-disc screening on existing certificates; no proof claim."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import bench6
import compact_shared6 as compact
import completion_batch6 as batch
import ref
from run_job import atomic_json, utc

AXES = ((1, 0), (0, 1), (1, 1), (1, -1))


def geometry():
    result = []
    for q in range(36):
        r, c = divmod(q, 6)
        axes = []
        for dr, dc in AXES:
            line = [q]
            neighbors = []
            for sign in (-1, 1):
                rr, cc = r + sign*dr, c + sign*dc
                neighbors.append(6*rr+cc if 0 <= rr < 6 and 0 <= cc < 6 else None)
                while 0 <= rr < 6 and 0 <= cc < 6:
                    line.append(6*rr+cc)
                    rr, cc = rr+sign*dr, cc+sign*dc
            axes.append((tuple(line), tuple(neighbors)))
        result.append(tuple(axes))
    return tuple(result)


GEOMETRY = geometry()


def stable(cells, player):
    """Ranked closure: full axis, board edge, or an earlier stable neighbor.

    This implementation is only a prospective heuristic. Soundness has not
    been formalized and its result must never become an Agda premise.
    """
    full = {(q, a): all(cells[t] for t in line)
            for q, axes in enumerate(GEOMETRY) for a, (line, _) in enumerate(axes)}
    known = set()
    while True:
        added = {q for q in range(36) if cells[q] == player and q not in known and
                 all(full[q, a] or any(t is None or t in known for t in neighbors)
                     for a, (_, neighbors) in enumerate(GEOMETRY[q]))}
        if not added:
            return len(known)
        known.update(added)


def screen(case):
    text = case['body_text']
    offset = 0
    nodes = leaves = references = 0
    retained_nodes = cuts = saved_nodes = 0
    cuts_by_empties = {}
    histogram = {}

    def number():
        nonlocal offset
        end = text.index(';', offset)
        offset = end+1

    def node(s, retained=True, depth=0):
        nonlocal offset, nodes, leaves, references, retained_nodes, cuts, saved_nodes
        assert depth < 128 and offset < len(text)
        nodes += 1
        if nodes % 256 == 0:
            assert shutil.disk_usage(batch.ROOT).free >= 80*2**30+2*2**20
        count = stable(s.cells, ref.WHITE) if retained else None
        if count is not None:
            histogram[count] = histogram.get(count, 0)+1
        tag = text[offset]
        offset += 1
        cut = retained and count >= 20 and tag != 'L'
        if cut:
            cuts += 1
            holes = s.cells.count(0)
            cuts_by_empties[holes] = cuts_by_empties.get(holes, 0)+1
        if retained:
            retained_nodes += 1
        else:
            saved_nodes += 1
        descendants = retained and not cut
        if tag == 'L':
            leaves += 1
        elif tag == 'K':
            references += 1
            number()
        elif tag == 'R':
            references += 1
            assert compact.COUNTS.index(text[offset]) <= 7
            offset += 1
            number()
        elif tag == 'P':
            node(ref.State(6, s.cells, 3-s.turn), descendants, depth+1)
        else:
            assert tag in 'CF'
            n = compact.COUNTS.index(text[offset])
            offset += 1
            children = ref.successors(s)
            if tag == 'C':
                assert n < len(children)
                node(children[n], descendants, depth+1)
            else:
                assert n == len(children)
                for child in children:
                    node(child, descendants, depth+1)

    for i in range(case['rows']):
        node(bench6.decode(compact.unpack_state(case['state_text'][13*i:13*i+13])))
    assert offset == len(text) and retained_nodes+saved_nodes == nodes
    return dict(part=case['part'], rows=case['rows'], nodes=nodes, retained_nodes=retained_nodes,
                saved_explicit_descendants=saved_nodes, cuts=cuts, leaves=leaves,
                references=references, cuts_by_empty_count=cuts_by_empties,
                stable_white_histogram=histogram)


def main(out):
    batch.authorized()
    out = Path(out).resolve()
    assert out.parent == batch.ROOT/'results' and out.name == 'stable-bound-screen6-20261018'
    assert not (out/'screen.json').exists()
    sample = batch.OUT/'sample.json'
    cases = json.loads(sample.read_text())['cases']
    started = time.process_time()
    results = []
    for case in cases:
        results.append(screen(case))
        atomic_json(out/'progress.json', dict(cases=results, accepted_proof=False, updated_utc=utc()))
    atomic_json(out/'screen.json', dict(format='othello-stable-bound-screen6-v1',
        created_utc=utc(), cases=results, process_cpu_seconds=time.process_time()-started,
        sample_sha256=hashlib.sha256(sample.read_bytes()).hexdigest(),
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        dependency_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [Path(ref.__file__), Path(bench6.__file__), Path(compact.__file__)]},
        trust='untrusted heuristic screening, not mathematical evidence',
        new_distinct_rows=0, mathematical_objective_complete=False,
        caveat='Explicit sampled bodies only; references hide external subtrees; no full-game forecast.'))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True, type=Path)
    main(p.parse_args().out)
