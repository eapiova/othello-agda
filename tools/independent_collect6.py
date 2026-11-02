#!/usr/bin/env python3
"""Collector-only Boolean coverage check within the recovery's unused budget."""
import argparse
import json
from pathlib import Path

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
from independent_lower_audit6 import audit
from lower_pilot6 import cache_changes, disk_allowed, disk_usage
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job

TARGET = 'src/Tests/IndependentLower6/CoveredRoot.agda'


def coverage_source(original):
    text = original.replace('module Tests.IndependentLower6.Root where',
                            'module Tests.IndependentLower6.CoveredRoot where', 1)
    if text == original or original.count('open import Game.Shared\n') != 1:
        raise ValueError('wrong original collector')
    text = text.replace('open import Game.Shared\n',
        'open import Game.Shared\nopen import Game.SharedExport using (covered; covered-sound)\n', 1)
    for index in (114, 115, 116, 117):
        before = f'''    importShape : importStates imports ≡ I{index}.imports
    importShape = refl {{x = I{index}.imports}}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = I{index}.sound
      (subst (AllT (Proven Fast.fastGame6 white (lowerGoal 4)))
        importShape (importStates-sound imports))
'''
        after = f'''    coverage : covered keyed6 (importStates imports) I{index}.imports ≡ true
    coverage = refl {{x = true}}

    sound : AllT (Proven Fast.fastGame6 white (lowerGoal 4)) states
    sound = I{index}.sound
      (covered-sound keyed6 Fast.fastGame6 white (lowerGoal 4)
        (importStates imports) I{index}.imports (importStates-sound imports) coverage)
'''
        if text.count(before) != 1:
            raise ValueError('original citation obligation differs')
        text = text.replace(before, after, 1)
    if 'importShape' in text:
        raise ValueError('unreplaced citation equality')
    return text


def run(args):
    previous = args.previous.resolve()
    verified = audit(previous)
    old = json.loads((previous/'final.json').read_text())
    last = old['phases'][-1]
    if (verified['accepted'] or verified['pilot_status'] != 'root-assembly-failed' or
            verified['conditional_parts'] != [114, 115, 116, 117] or verified['negatives_rejected'] != 2 or
            last['stop_reason'] != 'cpu-limit' or last['label'] != 'root-assembly' or
            old['measured_kernel_cpu_seconds'] != 323.60846000000004):
        raise ValueError('different completed conditional prefix or CPU stop')
    # Keep two seconds for sampling overshoot and the earlier 0.081s scope failure.
    left = min(74, 400-old['measured_kernel_cpu_seconds']-2)
    if left < 15:
        raise ValueError('no unused recovery kernel budget')
    donor = Path(old['check_root'])
    origin, pool = source_identity(donor), assembly6.interfaces(donor)
    machine = assembly6.machine_identity(args.agda)
    if machine != old['machine'] or len(pool) != 151:
        raise ValueError('original desktop compiler or checked interface pool differs')
    text = coverage_source((donor/'src/Tests/IndependentLower6/Root.agda').read_text())
    import hashlib
    generated_sha = hashlib.sha256(text.encode()).hexdigest()
    if generated_sha != args.expected_generated_sha256:
        raise ValueError('collector differs from the recorded coordinator transformation')
    output = args.output.resolve()
    runs = args.runs_root.resolve()
    needed = sum((donor/name).stat().st_size for name in pool)+len(text.encode())+16*1024**2
    if output.exists() or runs not in output.parents or not disk_allowed(disk_usage(runs), needed):
        raise ValueError('fresh private root and unchanged study disk guards required')
    output.mkdir(parents=True)
    root = output/'check'
    root.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, root/name)
    path = root/TARGET
    if path.exists():
        raise ValueError('new collector target exists')
    path.write_text(text)
    manifest = bench6.refresh_manifest(root, origin={key: origin[key] for key in ('revision', 'dirty')})
    for name, digest in pool.items():
        copy_interface(donor/name, root/name, digest)
    record = run_job('covered-root', [machine['agda_path'], *assembly6.FLAGS, '--save-metas', '-i', 'src', TARGET,
        '+RTS', '-M2500M', '-c', '-s', '-RTS'], output/'records', root=root,
        expected_source_sha256=manifest['source_sha256'], cpu_limit=left, timeout=240,
        rss_limit_gib=3, log_limit_mib=2,
        metadata=dict(machine=machine, own_target_cold=True, borrowed_interfaces_sha256=digest_entries(pool),
            original_nested_kernel_cpu_seconds=old['measured_kernel_cpu_seconds'],
            aggregate_recovery_kernel_cpu_budget=400, collector_only=True,
            certificates_rechecked=0, prefix_parts_reused=114, conditional_parts_reused=4))
    after = assembly6.interfaces(root)
    changes = cache_changes(pool, after)
    own = {name: digest for name, digest in after.items() if name.endswith('/Tests/IndependentLower6/CoveredRoot.agdai')}
    unexpected = [name for name in after if name not in pool and name not in own]
    fixed = source_identity(donor) == origin and assembly6.interfaces(donor) == pool
    accepted = bool(record['accepted'] and len(own) == 1 and fixed and not changes and not unexpected and
        record['source_unchanged'] and record['expected_source_matches'] and
        record['executable_sha256'] == machine['agda_sha256'] and
        old['measured_kernel_cpu_seconds']+record['cpu_seconds'] <= 400 and disk_allowed(disk_usage(runs)))
    log = output/'records/covered-root.log'
    log_sha = assembly6.sha(log)
    stats = rts_stats(log.read_text())
    packed = archive(log, log_sha) if accepted else None
    result = dict(format='othello-independent-covered-root6-v1', accepted=accepted,
        status='complete' if accepted else 'collector-failed', source_sha256=manifest['source_sha256'],
        agda_source_sha256=source_identity(root)['agda_source_sha256'], generated_sha256=generated_sha,
        previous=str(previous), previous_report_sha256=assembly6.sha(previous/'final.json'),
        previous_audit=verified, check_root=str(root), root=old['root'], checked_lower_roots=int(accepted),
        target=TARGET, certificate_parts_rechecked=0, real_imports_discharged=4 if accepted else 0,
        prefix_parts_reused=114, conditional_parts_reused=[114, 115, 116, 117],
        checked_goal='Guarantees (Rules.game six) white (lowerGoal 4) position',
        record=record, record_sha256=assembly6.sha(output/'records/covered-root.json'),
        raw_log_sha256=log_sha, archived_log=packed, rts=stats,
        donor_unchanged=fixed, cache_changes=changes, unexpected_interfaces=unexpected,
        original_interfaces=pool, final_interfaces=after, interfaces_sha256=digest_entries(after),
        aggregate_nested_kernel_cpu_seconds=old['measured_kernel_cpu_seconds']+record['cpu_seconds'],
        aggregate_recovery_kernel_budget=400, latest_disk=disk_usage(runs),
        postulates=0, heldout_unmeasured=True, initial_problem2_proved=False, production_authorized=False)
    atomic_json(output/'final.json', result)
    print(json.dumps({key: result[key] for key in ('status', 'accepted', 'checked_lower_roots',
        'aggregate_nested_kernel_cpu_seconds')}))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'output', 'runs-root'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--agda', required=True)
    p.add_argument('--expected-generated-sha256', required=True)
    raise SystemExit(0 if run(p.parse_args())['accepted'] else 2)
