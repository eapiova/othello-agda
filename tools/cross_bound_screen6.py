"""Untrusted, bounded colour/bound reuse screen on closed suffix policy graphs."""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import ref
from census_pilot6 import ccanonical
from generate6 import encode_state
from run_job import atomic_json, utc

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT/'results/global-reuse-layout6-20261018'
PLIES = [26, 24, 22]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(maxsize=200000)
def canonical(s):
    return encode_state(ccanonical(s))


def swap(s):
    return ref.State(6, tuple(3-c if c else 0 for c in s.cells), 3-s.turn)


class Graph:
    def __init__(self, document, lower, root):
        self.lower = lower
        self.rows = {}
        self.states = {}
        self.edges = {}
        self.bounds = {}
        self.active = set()
        for row in document['states']:
            key = ('w' if row['turn'] == 'white' else 'b')+row['position']
            assert key not in self.rows
            self.rows[key] = row
            self.states[key] = ref.State(6, tuple(int(c) for c in row['position']),
                ref.WHITE if row['turn'] == 'white' else ref.BLACK)
        self.root = canonical(root)
        self.bound(self.root)
        assert len(self.bounds) == len(self.rows), 'not a closed reachable policy graph'

    def children(self, key):
        if key in self.edges:
            return self.edges[key]
        s, row = self.states[key], self.rows[key]
        children = ref.successors(s)
        if not children:
            assert row['leaf']
            result = ()
        else:
            assert not row['leaf']
            passed = len(children) == 1 and children[0].cells == s.cells
            own = s.turn == (ref.WHITE if self.lower else ref.BLACK)
            if own and not passed:
                index = row['selected_index']
                assert type(index) is int and 0 <= index < len(children)
                children = [children[index]]
            result = tuple(canonical(t) for t in children)
            assert all(k in self.rows for k in result)
        self.edges[key] = result
        return result

    def bound(self, key):
        if key in self.bounds:
            return self.bounds[key]
        assert key not in self.active
        self.active.add(key)
        children = self.children(key)
        if not children:
            s = self.states[key]
            score = s.cells.count(ref.WHITE)-s.cells.count(ref.BLACK)
            result = score, score
        else:
            pairs = [self.bound(k) for k in children]
            result = min(p[0] for p in pairs), max(p[1] for p in pairs)
        assert result[0] >= 4 if self.lower else result[1] <= 4
        self.active.remove(key)
        self.bounds[key] = result
        return result


def compare(lower, upper, suffix):
    graphs = [lower, upper]
    opposite = {}
    for role, graph in enumerate(graphs):
        for key, state in graph.states.items():
            other = canonical(swap(state))
            if other in graphs[1-role].rows:
                opposite[role, key] = (1-role, other)
    assert all(opposite.get(other) == node for node, other in opposite.items())
    choice, cost, active = {}, {}, set()

    def children(node):
        role, key = node
        return [(role, k) for k in graphs[role].children(key)]

    def base(node):
        return 1+sum(calculate(child) for child in children(node))

    def calculate(node):
        if node in cost:
            return cost[node]
        other = opposite.get(node)
        lo = node if node[0] == 0 else other
        up = node if node[0] == 1 else other
        strong_pair = other is not None and upper.bounds[up[1]][1] <= -4
        token = ('pair', lo[1]) if strong_pair else ('single', node)
        assert token not in active, 'unexpected dependency cycle after pair contraction'
        active.add(token)
        if strong_pair:
            left, right = base(lo), base(up)
            keep, redirect = (lo, up) if left <= right else (up, lo)
            cost[keep] = min(left, right)
            cost[redirect] = cost[keep]+1
            choice[keep], choice[redirect] = None, keep
        else:
            own_cost = base(node)
            if node[0] == 1 and other is not None:
                shared_cost = 1+calculate(other)
                choice[node] = other if shared_cost < own_cost else None
                cost[node] = min(own_cost, shared_cost)
            else:
                choice[node], cost[node] = None, own_cost
        active.remove(token)
        return cost[node]

    roots = [(role, canonical(s)) for role in range(2) for s in suffix]
    assert all(key in graphs[role].rows for role, key in roots)
    for node in roots:
        calculate(node)
    visited, visiting = set(), set()
    new_edges = cross_edges = 0

    def visit(node):
        nonlocal new_edges, cross_edges
        if node in visited:
            return
        assert node not in visiting, 'mixed certificate citations would be circular'
        visiting.add(node)
        target = choice[node]
        if target is not None:
            assert opposite[node] == target
            assert upper.bounds[target[1]][1] <= -4 if node[0] == 0 else lower.bounds[target[1]][0] >= 4
            cross_edges += 1
            successors = [target]
        else:
            successors = children(node)
        new_edges += len(successors)
        for child in successors:
            visit(child)
        visiting.remove(node)
        visited.add(node)
    for node in roots:
        visit(node)
    original = sum(len(g.rows) for g in graphs)
    return dict(original_nodes=original, retained_mixed_nodes=len(visited),
        removed_nodes=original-len(visited), retained_lower_nodes=sum(role == 0 for role, _ in visited),
        retained_upper_nodes=sum(role == 1 for role, _ in visited), retained_edges=new_edges,
        retained_cross_citations=cross_edges, matched_colour_pairs=len(opposite)//2,
        qualifying_strong_pairs=sum(upper.bounds[k][1] <= -4 for role, k in opposite if role == 1),
        original_lower_nodes=len(lower.rows), original_upper_nodes=len(upper.rows),
        suffix_roots_retained=len(set(roots)), acyclic=True,
        metric='Untrusted mixed-obligation DAG nodes, not serialized tokens or Agda cost')


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    build = json.loads((DONOR/'build.json').read_text())
    assert build['binary_sha256'] == sha(DONOR/'census')
    assert json.loads((DONOR/'closure.json').read_text())['lower_counts_complete']
    atomic_json(out/'source-plan.json', dict(created_utc=utc(), plies=PLIES,
        line_sha256=sha(ROOT/'certificates/six-line.json'), native_binary=str(DONOR/'census'),
        native_binary_sha256=build['binary_sha256'], native_source_sha256=sha(DONOR/'census.c'),
        helpers={n:sha(ROOT/'tools'/n) for n in ['cross_bound_screen6.py','ref.py','census_pilot6.py','generate6.py','run_job.py','study6.py']},
        maximum_nodes_per_graph=100000, maximum_pair_nodes=200000, native_cpu_per_graph=8,
        solver_queries='Only to construct fixed baseline suffix policy graphs; comparison and bound annotations make no new solver queries',
        current_native_graphs_are_not_retained=True, accepted_proof=False,
        mathematical_objective_complete=False, full_workflow_forecast_validated=False))


def run(out):
    plan = json.loads((out/'source-plan.json').read_text())
    assert all(sha(ROOT/'tools'/n) == h for n, h in plan['helpers'].items())
    assert sha(Path(plan['native_binary'])) == plan['native_binary_sha256']
    line = json.loads((ROOT/'certificates/six-line.json').read_text())
    assert sha(ROOT/'certificates/six-line.json') == plan['line_sha256']
    states = [ref.State(6, tuple(int(c) for c in s[1:]), ref.BLACK if s[0] == 'b' else ref.WHITE) for s in line['states']]
    cases = []
    for ply in PLIES:
        assert shutil.disk_usage(ROOT).free-2*2**20 >= 80*2**30
        graphs, receipts = [], []
        for direction in ['lower', 'upper']:
            raw = line['states'][ply]
            argv = [plan['native_binary'],'frontier','--position',raw[1:],'--turn','black' if raw[0] == 'b' else 'white',
                '--direction',direction,'--threshold','4','--frontier-discs','36','--max-states','100000',
                '--max-nodes','1000000000','--max-memory-mb','256','--max-cpu-seconds','8',
                '--tt-bits','18','--small','4','--deep-order','5','--emit-states','1']
            done = subprocess.run(argv, capture_output=True, timeout=18)
            assert len(done.stdout) < 48*2**20
            document = json.loads(done.stdout)
            receipt = dict(command=argv, exit_code=done.returncode, stdout_sha256=hashlib.sha256(done.stdout).hexdigest(),
                counts={k:v for k,v in document.items() if k != 'states'}, stderr=done.stderr.decode(errors='replace'))
            atomic_json(out/f'native-ply{ply}-{direction}.json', receipt)
            assert done.returncode == 0 and all(document.get(k) is True for k in ['complete','root_holds','root_validated'])
            graphs.append(Graph(document, direction == 'lower', states[ply]))
            receipts.append(receipt)
        result = compare(*graphs, states[ply:])
        result.update(ply=ply, native_graph_receipts=[f'native-ply{ply}-{d}.json' for d in ['lower','upper']],
            accepted_proof=False, mathematical_objective_complete=False)
        cases.append(result)
        atomic_json(out/'progress.json', dict(cases=cases, accepted_proof=False))
        canonical.cache_clear()
    assert sha(Path(plan['native_binary'])) == plan['native_binary_sha256']
    atomic_json(out/'screen.json', dict(created_utc=utc(), cases=cases,
        all_sample_graphs_complete=True, accepted_proof=False, new_distinct_rows=0,
        bound_propagation_and_colour_transport_require_new_safe_Agda_proofs=True,
        no_initial_board_or_serialized_token_forecast=True, mathematical_objective_complete=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare','run'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    (prepare if args.mode == 'prepare' else run)(args.out.resolve())
