#!/usr/bin/env python3
"""Small fabricated receipts exercise diagnostics; no Agda/interface claims."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import assembly6
from provenance import digest_entries, source_identity
import wire_workflow6 as workflow


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))
    return dict(path=str(path), sha256=assembly6.sha(path))


def snapshot(root):
    files = {p.relative_to(root).as_posix():assembly6.sha(p) for p in root.rglob('*.agda')}
    save(root/'SNAPSHOT.json', dict(files=files, source_sha256=digest_entries(files),
                                  git=dict(revision='fixture', dirty=False)))
    return source_identity(root)['source_sha256']


def fixture(base):
    donor = base/'donor'
    source = donor/'src/Core.agda'; source.parent.mkdir(parents=True)
    source.write_text('{-# OPTIONS --safe --without-K --cubical-compatible #-}\nmodule Core where\n')
    generic_file = donor/'_build/agda/src/Core.agdai'; generic_file.parent.mkdir(parents=True)
    generic_file.write_bytes(b'fixture interface only')
    generic = assembly6.interfaces(donor)
    identity = dict(hostname='fixture-host', agda_sha256='a'*64,
                    donor_source_sha256=snapshot(donor), generic_interfaces_sha256=digest_entries(generic))
    machine = dict(hostname=identity['hostname'], agda_sha256=identity['agda_sha256'])
    line = dict(states=['b'+'0'*36 for _ in range(17)])
    line_spec = save(base/'line.json', line)
    pilots = []
    for ply in (16, 14, 12):
        for direction in ('lower', 'upper'):
            label = f'{direction}-ply{ply}'
            prepared, check = base/label/'prepared', base/label/'check'
            ns = f'Tests/WirePilot6/{direction.capitalize()}'
            targets = [dict(path=f'src/{ns}/Part0.agda', kind='part', root_index=0, part=0,
                            entries=2, tokens=10+ply, compact_bytes=30, dependencies=[],
                            imported_citations=0, transitive_parts=0, transitive_entries=0),
                       dict(path=f'src/{ns}/Check.agda', kind='assembly', root_index=0,
                            transitive_parts=1, transitive_entries=2)]
            hashes = {}
            for t in targets:
                raw = ('{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'+
                       'module '+t['path'][4:-5].replace('/', '.')+' where\n').encode()
                t['source_bytes'] = len(raw)
                for root in (prepared, check):
                    p = root/t['path']; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
                hashes[t['path']] = hashlib.sha256(raw).hexdigest()
            p = check/'src/Core.agda'; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(source.read_bytes())
            p = check/generic_file.relative_to(donor); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(generic_file.read_bytes())
            source_sha = snapshot(check)
            wire = base/label/'wire'; wire.write_bytes(b'fixture untrusted wire')
            wire_spec = dict(path=str(wire), sha256=assembly6.sha(wire))
            native = dict(format='othello-census-wire6-run-v1', status='complete-untrusted-wire',
                          native_complete=True, wire_complete=True, donor_unchanged=True,
                          table_unchanged=True, exit_code=0, production_authorized=False,
                          wire_output_sha256=wire_spec['sha256'], root_key=line['states'][ply],
                          request=dict(direction=direction, threshold=4),
                          build=dict(line_sha256=line_spec['sha256'], pins={'fixture': [1]}),
                          counts=dict(wire_records=2, wire_bytes=wire.stat().st_size))
            native_spec = save(base/label/'native.json', native)
            plan = dict(format=workflow.WIRE, production_authorized=False, scalar_replay_complete=True,
                        packed_export_tables=True, max_entries=2, max_tokens=100,
                        native_report_sha256=native_spec['sha256'], wire_sha256=wire_spec['sha256'],
                        roots=[dict(key=line['states'][ply], direction=direction, entries=2, checked_tokens=10+ply)],
                        targets=targets, generated_hashes=hashes,
                        total_generated_source_bytes=sum(t['source_bytes'] for t in targets))
            plan_spec = save(prepared/'plan.json', plan)
            borrowed, phases = dict(generic), []
            for t in targets:
                record = dict(format='othello-job-v2', accepted=True, exit_code=0, stop_reason=None,
                              own_target_cold=True, source_unchanged=True, expected_source_matches=True,
                              source_sha256=source_sha, expected_source_sha256=source_sha,
                              executable_sha256=identity['agda_sha256'], machine=machine, root=str(check),
                              borrowed_interfaces_sha256=digest_entries(borrowed),
                              argv=['fixture-agda', *assembly6.FLAGS, '--save-metas', t['path']],
                              cpu_seconds=(ply/10 if t['kind']=='part' else .5), peak_rss_gib=.2,
                              cpu_limit_seconds=10, rss_stop_threshold_gib=1.5, **t)
                name = '_build/agda/'+t['path'][:-5]+'.agdai'
                p = check/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'target fixture '+label.encode())
                borrowed[name] = assembly6.sha(p)
                phases.append(dict(target=t, record=record, changed_imports=[]))
            report = dict(format=workflow.WIRE, phase='training', status='complete', accepted=True,
                          production_authorized=False, initial_theorem_proved=False, machine=machine,
                          donor_unchanged=True, generated_sources_unchanged=True,
                          donor_source=dict(source_sha256=identity['donor_source_sha256']),
                          borrowed_interfaces_sha256=identity['generic_interfaces_sha256'],
                          source_sha256=source_sha, plan_sha256=plan_spec['sha256'], check_root=str(check),
                          phases=phases, cpu_seconds=sum(p['record']['cpu_seconds'] for p in phases), cpu_budget=20,
                          final_interfaces_sha256=digest_entries(borrowed))
            report_spec = save(base/label/'report.json', report)
            pilots.append(dict(label=label, ply=ply, direction=direction, report=report_spec,
                               plan=plan_spec, native=native_spec, wire=wire_spec,
                               prepared_root=str(prepared), check_root=str(check)))
    heldout = save(base/'heldout.json', dict(status='complete', accepted=True, production_authorized=False))
    chains = []
    for index, selected in enumerate((pilots[:4], pilots[4:])):
        children = {p['label']:p['report'] for p in selected}
        phases = [dict(label=p['label'], accepted=True, report_sha256=p['report']['sha256'],
                       plan_sha256=p['plan']['sha256']) for p in selected]
        if index == 0:
            children['upper-heldout'] = heldout
            phases.insert(0, dict(label='upper-heldout', accepted=True, report_sha256=heldout['sha256']))
        chain = dict(format='othello-unattended-wire6-v1' if index==0 else 'othello-unattended-wire-advance6-v1',
                     status='complete-pilot' if index==0 else 'complete-earlier-roots',
                     accepted=True, production_authorized=False, initial_problem2_proved=False,
                     phases=phases, machine=machine)
        if index: chain['predecessor_report_sha256'] = chains[0]['sha256']
        spec = save(base/f'chain{index}.json', chain); spec['children'] = children; chains.append(spec)
    counts = {}
    for direction in ('lower', 'upper'):
        c = dict(direction=direction, threshold=4, complete=True, root_validated=True, root_holds=True,
                 sampling_complete=True, count_overflow=False, oracle_aborted=False, line_maintained=False,
                 frontier_discs=36, unique_dag_nodes=10, dag_edges=12)
        s = dict(node_kinds={'leaf':3, 'pass':1, 'forcing':3, 'opponent':3}, sharing_entries=2,
                 reference_edges=5, chosen_edges=12, leaf_occurrences=4, nonidentity_D4_citation_edges=2,
                 ideal_grammar_tokens=16, ideal_grammar_ascii_bytes=63)
        data = dict(format='othello-census-samples6-v1', statistics=s, native_census=c,
                    production_authorized=False)
        data_spec = save(base/f'{direction}-data.json', data)
        receipt = dict(format='othello-census-samples6-run-v1', status='complete-native-census',
                       native_complete=True, exit_code=0, donor_unchanged=True, table_unchanged=True,
                       partial_counts_are_lower_bounds=False, incomplete_count_extrapolated=False,
                       samples_output_sha256=data_spec['sha256'], counts=c, request=dict(position='initial'),
                       production_authorized=False)
        counts[direction] = dict(data=data_spec, receipt=save(base/f'{direction}-receipt.json', receipt))
    return dict(format='othello-wire-workflow6-input-v1', identity=identity, line=line_spec,
                donor_root=str(donor), pilots=pilots, chains=chains, counts=counts,
                bounds=dict(cpu_hours=48, artifacts_gib=10, part_rss_gib=1.5, assembly_rss_gib=3,
                            allocated_artifacts_bytes=1000, free_disk_bytes=200*2**30, min_free_disk_gib=100))


class WireWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)
        self.input = fixture(self.base)

    def run_audit(self):
        return workflow.audit(self.input, self.base)

    def repin_report(self, pilot, report):
        pilot['report'] = save(Path(pilot['report']['path']), report)
        for chain_spec in self.input['chains']:
            if pilot['label'] in chain_spec['children']:
                chain = json.loads(Path(chain_spec['path']).read_text())
                for phase in chain['phases']:
                    if phase['label'] == pilot['label']: phase['report_sha256'] = pilot['report']['sha256']
                chain_spec['children'][pilot['label']] = pilot['report']
                chain_spec['sha256'] = save(Path(chain_spec['path']), chain)['sha256']
        # Keep the explicit predecessor identity consistent with the repinned first chain.
        last = self.input['chains'][1]
        chain = json.loads(Path(last['path']).read_text())
        chain['predecessor_report_sha256'] = self.input['chains'][0]['sha256']
        last['sha256'] = save(Path(last['path']), chain)['sha256']

    def test_positive_fixture_is_honest_incomplete_projection(self):
        result = self.run_audit()
        self.assertEqual(result['recommendation'], 'NEEDS_FULL_PINNED_INITIAL_WORKFLOW_PILOT')
        self.assertTrue(result['accepted_pilot_audit'])
        self.assertEqual(len(result['pilots']), 6)
        self.assertFalse(result['production_authorized'])
        self.assertFalse(result['initial_problem2_proved'])
        self.assertFalse(result['optimal_pair_proved'])
        self.assertIsNone(result['full_workflow_cpu_hours'])
        for c in result['components']:
            self.assertIsNone(c['imported_citations'])
            self.assertIsNone(c['whole_assembly_peak_rss_gib'])
            self.assertGreater(c['token_scaled_compressed_interface_bytes'], 0)

    def test_failed_partial_warm_and_unsafe_receipts_are_rejected(self):
        pilot = self.input['pilots'][0]
        original = json.loads(Path(pilot['report']['path']).read_text())
        for change in ('failed', 'partial', 'warm', 'unsafe', 'compiler', 'changed-imports'):
            report = copy.deepcopy(original)
            if change=='failed': report['phases'][0]['record']['accepted'] = False
            if change=='partial': report['phases'].pop()
            if change=='warm': report['phases'][0]['record']['own_target_cold'] = False
            if change=='unsafe': report['phases'][0]['record']['argv'].remove('--safe')
            if change=='compiler': report['phases'][0]['record']['executable_sha256'] = 'b'*64
            if change=='changed-imports': report['phases'][0]['changed_imports'] = ['Core.agdai']
            self.repin_report(pilot, report)
            with self.subTest(change=change), self.assertRaises(ValueError): self.run_audit()

    def test_changed_source_interface_wire_or_hash_is_rejected(self):
        pilot = self.input['pilots'][0]
        for file in (Path(pilot['wire']['path']), Path(pilot['check_root'])/'src/Core.agda',
                     Path(pilot['check_root'])/'_build/agda/src/Core.agdai'):
            original = file.read_bytes(); file.write_bytes(original+b'changed')
            with self.subTest(file=file), self.assertRaises(ValueError): self.run_audit()
            file.write_bytes(original)
        pilot['plan']['sha256'] = '0'*64
        with self.assertRaises(ValueError): self.run_audit()

    def test_bad_counts_and_missing_bounds_are_rejected(self):
        spec = self.input['counts']['lower']
        data = json.loads(Path(spec['data']['path']).read_text())
        data['statistics']['ideal_grammar_tokens'] += 1
        spec['data'] = save(Path(spec['data']['path']), data)
        receipt = json.loads(Path(spec['receipt']['path']).read_text())
        receipt['samples_output_sha256'] = spec['data']['sha256']
        spec['receipt'] = save(Path(spec['receipt']['path']), receipt)
        with self.assertRaisesRegex(ValueError, 'grammar'): self.run_audit()
        del self.input['bounds']['cpu_hours']
        with self.assertRaisesRegex(ValueError, 'cpu_hours'): self.run_audit()

    def test_partial_counts_or_chain_and_cross_machine_are_rejected(self):
        receipt_spec = self.input['counts']['lower']['receipt']
        receipt = json.loads(Path(receipt_spec['path']).read_text()); receipt['native_complete'] = False
        self.input['counts']['lower']['receipt'] = save(Path(receipt_spec['path']), receipt)
        with self.assertRaises(ValueError): self.run_audit()
        self.input = fixture(self.base/'other')
        self.input['identity']['hostname'] = 'different-machine'
        with self.assertRaises(ValueError): self.run_audit()
        self.input = fixture(self.base/'third')
        self.input['chains'].pop()
        with self.assertRaises(ValueError): self.run_audit()

    def test_actual_failed_resource_gate_is_no_go(self):
        self.input['bounds']['allocated_artifacts_bytes'] = 11*2**30
        result = self.run_audit()
        self.assertEqual(result['recommendation'], 'NO_GO')
        self.assertEqual(result['failed_gates'], ['current-artifact-allocation'])
        self.assertFalse(result['production_authorized'])


if __name__ == '__main__': unittest.main()
