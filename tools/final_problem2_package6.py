"""AI-assisted private source/evidence closure; never runs Agda or publishes."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path('/home/eapiova/projects/othello-agda-main')
sys.path.insert(0, str(ROOT/'tools'))
from compression import zstd
import final_problem2_ephemeral6 as proof
import full_row_records6 as records
from run_job import atomic_json, run_job, utc
from study6 import Ledger

PRIVATE = proof.PRIVATE
OUT = PRIVATE/'final-proof'
CONTROL = OUT/'control'
AUTH = ROOT/'results/final-problem2-package-authorization6-20261019.json'
RECON = ROOT/'results/final-problem2-ephemeral-reconciliation6-20261019.json'


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return proof.sha(path)


def storage():
    total, _ = proof.physical_census(read(proof.PRODUCTION_PLAN))
    own = proof.allocated(PRIVATE)
    require(own <= 2*2**20 and total+4*2**20 < 12*2**30,
            'private package2MiB or retained12GiB limit reached')
    root_free = shutil.disk_usage(ROOT).free
    data_free = shutil.disk_usage(PRIVATE).free
    require(min(root_free, data_free)-4*2**20 >= 80*2**30,
            'ordinary80GiB free floor reached')
    return {'recorded_utc': utc(), 'allocated_study_bytes': total,
        'private_package_bytes': own, 'private_package_cap_bytes': 2*2**20,
        'root_free_bytes': root_free, 'data_free_bytes': data_free,
        'retained_cap_bytes': 12*2**30, 'stop_reserve_bytes': 4*2**20}


def reference(kind, path, expected=None):
    path = Path(path); pin = sha(path)
    require(expected is None or pin == expected, 'immutable reference changed: '+str(path))
    info = path.stat()
    return {'kind': kind, 'path': str(path), 'sha256': pin,
        'bytes': info.st_size, 'mode': stat.S_IMODE(info.st_mode), 'mtime_ns': info.st_mtime_ns}


def worker():
    proof.no_active_work()
    job = read(OUT/'job.json'); state = read(proof.LEDGER_FILE)
    require(set(state['reservations']) == {job['reservation']['reservation_id']},
            'package must be the only outstanding job')
    plan = read(proof.OUT/'plan.json'); proof.validate_plan(plan)
    report = read(proof.OUT/'report.json'); rec = read(RECON)
    require(report['accepted'] and report['Problem2_checked']
            and rec['status'] == 'reconciled'
            and state['finished'].get(rec['reservation_id']) == rec['finished']
            and rec['run_report_sha256'] == sha(proof.OUT/'report.json'),
            'accepted and reconciled actual Problem2 proof required')
    residual = dict(rec['residual_withholding']); key = residual.pop('withholding_id')
    require(state['withheld'].get(key) == residual, 'proof service CPU residual missing')
    storage()
    private_manifest = read(proof.PRIVATE_MANIFEST)
    require(sha(proof.PRIVATE_MANIFEST) == plan['private_package']['manifest_sha256'],
            'historical source-package manifest changed')
    refs = [reference('selected-core-source', private_manifest['core_archive'],
                      private_manifest['core_archive_sha256']),
            reference('selected-source-graph', private_manifest['source_graph'],
                      private_manifest['source_graph_sha256'])]
    small = {proof.PRIVATE_MANIFEST, RECON, proof.COMPLETE_ROWS, proof.LINEAGE,
             proof.OUT/'plan.json', OUT/'ledger-before-package.json.zst', AUTH,
             ROOT/'results/problem2-proof-boundary-review6-20261019.json'}
    for kind, package in plan['production_packages'].items():
        refs.append(reference(kind, package['archive'], package['archive_sha256']))
        reference(kind+'-manifest', package['manifest'], package['manifest_sha256'])
        small.add(Path(package['manifest']))
    for side, item in plan['complete_rows']['rows'].items():
        refs.append(reference('accepted-'+side+'-Rows', item['path'], item['sha256']))
    receipts = proof.PRODUCTION/'closed-child-records.zip'
    refs.append(reference('all667-row-check-receipts', receipts))
    refs.append(reference('closed-production-progress', proof.PRODUCTION/'progress.json'))
    # Read back the already closed exact receipt cohorts and establish their
    # one-to-one coverage. This checks package evidence, not game rows again.
    import zipfile
    progress = read(proof.PRODUCTION/'progress.json')
    expected_labels = {item['label'] for item in progress['accepted_batches']}
    found = set(); cohort_count = 0
    with zipfile.ZipFile(receipts) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), 'duplicate receipt cohorts')
        for name in archive.namelist():
            blob = archive.read(name); manifest = records.verify_cohort_blob(blob)
            with tarfile.open(fileobj=io.BytesIO(zstd.decompress(blob)), mode='r:') as cohort:
                for item in manifest['entries']:
                    if not item['path'].endswith('.json'):
                        continue
                    record = json.loads(cohort.extractfile('files/'+item['path']).read())
                    if not isinstance(record, dict):
                        continue
                    if record.get('format') != 'othello-job-v2' or record.get('label') not in expected_labels:
                        continue
                    require(record['label'] not in found and record['accepted']
                            and record['exit_code'] == 0 and record['source_unchanged'],
                            'a row proof receipt is duplicate or not accepted')
                    require({'--safe', '--without-K', '--cubical-compatible'}.issubset(record['argv']),
                            'row proof receipt lacks safe flags')
                    found.add(record['label'])
            cohort_count += 1
    require(found == expected_labels and len(found) == 667, 'receipt coverage is not exactly667batches')
    tag = 'tpp-mark-2026-problem1'
    tag_object = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'refs/tags/'+tag], text=True).strip()
    require(tag_object == 'e734d4c3e8a783a5033f7510739d680943a26015', 'P1 tag changed')
    for name, pin in plan['p1_files'].items():
        raw = subprocess.check_output(['git', '-C', str(ROOT), 'show', tag+':'+name])
        require(hashlib.sha256(raw).hexdigest() == pin == sha(ROOT/name), 'P1 tagged source changed')
    sources = OUT/'checked-source/src/Tests'
    (sources/'CompleteUpperRows6').mkdir(parents=True)
    with zipfile.ZipFile(plan['production_packages']['upper-sources']['archive']) as archive:
        raw_result = archive.read('Result.agda')
    result_path = sources/'CompleteUpperRows6/Result.agda'; result_path.write_bytes(raw_result)
    require(sha(result_path) == plan['theorem_source_entries']['Tests.CompleteUpperRows6.Result']['sha256'],
            'materialized checked Result source differs')
    wrapper_path = sources/'FinalProblem2Check6.agda'
    shutil.copy2(proof.CHECK/proof.WRAPPER_RELATIVE, wrapper_path)
    small.update((result_path, wrapper_path))
    small.update(path for path in (proof.OUT/'control').iterdir() if path.is_file())
    for name in ['report.json', 'job.json', 'source-audit.json', 'input-snapshots-begin.json',
                 'input-snapshots-end.json', 'ephemeral-cache-begin.json', 'ephemeral-cache.json',
                 'ephemeral-job.json', 'bwrap-arguments.nul', 'ephemeral-agda-full.log.zst',
                 'cached-row-replay.json', 'view-cleanup.json', 'supervisor-cpu.json',
                 'terminal-systemd.json']:
        small.add(proof.OUT/name)
    small.update((proof.OUT/'outer-records/final-problem2-outer.json',
                  proof.OUT/'records/final-problem2-check6.json',
                  proof.OUT/'records/final-problem2-check6.log'))
    for name in ['full_row_production6.py', 'full_row_resume6.py', 'full_row_stage3_resume6.py',
                 'full_row_records6.py', 'study_archive_fs6.c', 'study_row_archive_fs6.c']:
        small.add(ROOT/'tools'/name)
    for path in ROOT.glob('results/*reconciliation6-20261019.json'):
        if any(token in path.name for token in ['full-row', 'final-problem2']):
            small.add(path)
    small.add(ROOT/'results/final-problem2-ephemeral-cache-pilot-review6-20261019.json')
    row_config = plan['row_view']; small.add(Path(row_config['binary']))
    small.add(Path(plan['filesystem_binary']))
    for item in row_config['metadata'].values():
        small.add(Path(item['path']))
    for key in ['manifest', 'closure', 'reconciliation']:
        small.add(Path(row_config[key]))
    total_bytes = sum(path.stat().st_size for path in small)
    require(total_bytes < 16*2**20, 'small evidence bundle exceeds16MiB restore bound')
    aliases = {str(ROOT/'tools'/name): str(proof.OUT/'control'/name) for name in plan['helper_sha256']}
    descriptor = {'format': 'othello-private-Problem2-final-source-evidence-v1',
        'recorded_utc': utc(), 'accepted_type': 'Tests.CompleteUpperRows6.Result.initial6x6 : Problem2',
        'same_optimal_pair_black16_white20': True, 'raw_white_minus_black': 4,
        'source_modules_audited': 4128, 'project_postulates': 0,
        'references': refs, 'selected_source_graph_decoded_sha256': private_manifest['source_graph_decoded_sha256'],
        'exact_include_order': plan['include_order'], 'donor_pins': plan['donor_beginning'],
        'canonical_helper_aliases_to_frozen_copies': aliases,
        'compiler': {'path': plan['agda'], 'sha256': plan['agda_sha256']},
        'actual_flags': plan['flags'], 'P1_tag': tag, 'P1_tag_object': tag_object,
        'P1_source_sha256': plan['p1_files'], 'row_receipt_cohorts_verified': cohort_count,
        'accepted_row_receipts_verified': len(found), 'row_receipts_are_not_charged_again': True,
        'package_is_local_collection_not_standalone': True,
        'independent_cold_rebuild_performed': False, 'AI_assistance_disclosed': True,
        'no_publication_upload_email_commit_or_push': True}
    descriptor_path = OUT/'reference-manifest.json'; atomic_json(descriptor_path, descriptor)
    small.add(descriptor_path)
    relatives = [str(path.relative_to('/')) for path in sorted(small)]
    blob, manifest = records.cohort_blob(Path('/'), relatives,
        {'purpose': 'exact private final Problem2 proof source/evidence',
         'original_absolute_paths_are_evidence_restore_under_explicit_prefix': True})
    require(len(blob) < 900*2**10, 'final small evidence archive exceeds900KiB')
    archive_path = OUT/'evidence.tar.zst'; records.atomic_bytes(archive_path, blob, mode=0o600)
    records.verify_cohort_blob(archive_path.read_bytes(), manifest)
    decoded = zstd.decompress(archive_path.read_bytes()); restored_count = 0
    with tempfile.TemporaryDirectory(prefix='othello-proof-package-restore-', dir='/dev/shm') as temporary:
        base = Path(temporary)
        with tarfile.open(fileobj=io.BytesIO(decoded), mode='r:') as archive:
            for entry in manifest['entries']:
                relative = Path(entry['path'])
                require(not relative.is_absolute() and '..' not in relative.parts, 'unsafe restoration member')
                raw = archive.extractfile('files/'+entry['path']).read()
                target = base/relative; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw); os.chmod(target, entry['mode'])
                require(sha(target) == entry['sha256'], 'restored evidence bytes differ')
                os.utime(target, ns=(entry['atime_ns'], entry['mtime_ns']))
                info = target.stat()
                require(stat.S_IMODE(info.st_mode) == entry['mode']
                        and info.st_mtime_ns == entry['mtime_ns']
                        and info.st_atime_ns == entry['atime_ns'], 'restored evidence metadata differs')
                restored_count += 1
    require(restored_count == len(manifest['entries']), 'restoration inventory differs')
    # All small evidence bytes still match their captured source snapshot.
    for entry in manifest['entries']:
        require(sha(Path('/')/entry['path']) == entry['sha256'], 'evidence source changed during package closure')
    proof.validate_plan(plan)
    require(proof.batch.donor_snapshot({Path(p): tuple(v) for p, v in plan['donors'].items()})
                == plan['donor_beginning'], 'a borrowed source/cache pool changed')
    restore = OUT/'RESTORE.md'
    restore.write_text('''# Private Problem2 proof: restoration and verification

The accepted theorem is `Tests.CompleteUpperRows6.Result.initial6x6 : Problem2`:
standard initial6x6, Black to move, raw White-minus-Black+4, and the SAME optimal
strategy pair completing a legal play at Black16/White20. The safe flags are
`--safe --without-K --cubical-compatible`; the selected source audit covers4128
non-builtin modules with zero project postulates, explicit holes or escapes.

This directory supplements the unchanged parent source-package manifest,
`core-source.zip` and `source-graph.json.zst`. `reference-manifest.json` pins
four large source/data archives, two accepted Rows archives, the complete row
receipt collection, compiler,68 donor pools and exact include order. These
existing archives/pools are references, not duplicated. The collection is
cache-dependent and is not a standalone distributable or independently cold
rebuilt package. The checker really checked both AllParts records, Result and
the typed Problem2 wrapper; cached Boolean Rows proofs were not recomputed.

`evidence.tar.zst` is a losslessly verified small evidence/source archive.
Its MANIFEST.json records exact bytes/SHA256, modes and nanosecond atime/mtime.
The files were actually restored under a temporary prefix on /dev/shm and
verified against every recorded hash and metadata value, then removed. This
restoration test did not run Agda or restore all external archives.

Restore under an explicit destination prefix, never blindly into `/`: each
`files/<original-absolute-path-without-leading-slash>` records its origin.
Validate MANIFEST hashes, restore modes and ns timestamps from the manifest,
and resolve external references by their recorded hashes. Keep historical
receipt paths unchanged. Core sources use the parent ZIP's `src/` layout;
flat UPPER/LOWER certificate ZIPs belong under
`src/Tests/CompleteUpperRows6` and `src/Tests/CompleteLowerRows6`. Preserve the
data-cache layouts, donor order and exact `othello.agda-lib`.

For the checked replay configuration, use the frozen control sources and plan.
The original archive filesystem serves source/data packages; the separate
row filesystem uses accepted-lineage TSV metadata.1337 Rows interfaces are
individual read-only bindings. New Body/AllParts/Result/wrapper interfaces live
only in512MiB proof and16MiB checker tmpfs mounts, with actual namespace-local
build locks. The complete log is retained losslessly compressed. Runtime was
`+RTS -M9000M -c -F1.2 -s -RTS`, total Othello RAM capped12GiB, swap/core0,
80GiB free-disk floor and12GiB retained-study cap. No replay starts automatically.

AI assistance: Codex helped construct certificates/proofs, controllers, audits,
resource handling, packaging and documentation. Native solver outputs were
untrusted until their certificates were accepted by safe Agda. No publication,
upload, email, commit or push was performed.
''')
    final_storage = storage()
    atomic_json(OUT/'package-report.json', {'format': 'othello-private-final-proof-package-report-v1',
        'finished_utc': utc(), 'accepted': True, 'actual_Problem2_proof_accepted': True,
        'bundle': str(archive_path), 'bundle_sha256': sha(archive_path), 'bundle_bytes': len(blob),
        'bundle_manifest': manifest, 'restored_files': restored_count,
        'exact_restore_bytes_modes_ns_times_verified': True, 'temporary_restore_removed': True,
        'reference_manifest': str(descriptor_path), 'reference_manifest_sha256': sha(descriptor_path),
        'restoration_instructions': str(restore), 'restoration_instructions_sha256': sha(restore),
        'all667row_receipts_verified': True, 'row_receipt_cohort_count': cohort_count,
        'all23P1_sources_match_original_tag': True, 'no_proof_or_source_changes': True,
        'independent_cold_rebuild_performed': False, 'package_is_standalone': False,
        'Agda_dispatched': False, 'no_publication_upload_email_commit_or_push': True,
        'final_storage': final_storage, 'manual_outer_reconciliation_required': True,
        'mathematical_objective_complete': False})


def supervise():
    job = read(OUT/'job.json')
    result = run_job('private-Problem2-package6',
        ['/usr/bin/python3', '-B', str(CONTROL/'final_problem2_package6.py'), 'worker'],
        OUT/'outer-records', root=CONTROL, timeout=160, cpu_limit=55,
        rss_limit_gib=.9, log_limit_mib=.25,
        reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'],
        metadata={'Agda_dispatched': False, 'manual_ledger_finish_required': True,
                  'package_scope_only': True})
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    require(len(sys.argv) == 2 and sys.argv[1] in ('worker', 'supervise'), 'worker or supervise required')
    if sys.argv[1] == 'worker':
        worker()
    else:
        raise SystemExit(supervise())
