#!/usr/bin/env python3
"""Assemble only covered lower roots, without repeating any accepted shard."""
import argparse
import json
from pathlib import Path
import re

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
from lower_pilot6 import cache_changes, disk_allowed, disk_usage, local_options
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, build_lock, run_job


def run(args):
    previous, output = args.previous.resolve(), args.output.resolve()
    if output.exists() or previous in output.parents:
        raise ValueError('fresh private result root required')
    report = json.loads((previous/'final.json').read_text())
    audit = json.loads((previous/'phase-records.json').read_text())
    verification = json.loads(args.verification.read_text())
    donor = previous/'check'
    identity, pool = source_identity(donor), assembly6.interfaces(donor)
    if (verification['status'] != 'complete' or not verification['exact_logs_recovered'] or
            verification['previous_report_sha256'] != assembly6.sha(previous/'final.json') or
            verification['previous_audit_sha256'] != assembly6.sha(previous/'phase-records.json') or
            verification['interfaces_sha256'] != digest_entries(pool) or
            identity['source_sha256'] != report['source_sha256'] or pool != audit['final_interfaces'] or
            report['status'] != 'part-failed' or report['checked_sample_lower_roots'] != 0):
        raise ValueError('stopped prefix differs from its verification')
    covered = verification['source_covered_roots']
    roots = [row['state'] for row in covered]
    if (len(covered) != 2 or [row['part'] for row in covered] != [24, 37] or
            any(row['group'] != 0 for row in covered) or roots != report['roots'][:2]):
        raise ValueError('only the two recorded covered roots can be claimed')
    last = max(row['part'] for row in covered)
    borrowed = {}
    for name, digest in pool.items():
        match = re.search(r'/Tests/LowerPilot6/Group0/Part(\d+)\.agdai$', name)
        if '/Tests/' not in name or match and int(match[1]) <= last:
            borrowed[name] = digest
    if len(borrowed) != 32+last+1:
        raise ValueError('covered serial cache span differs')
    machine = assembly6.machine_identity(args.agda)
    if machine != report['machine']:
        raise ValueError('same desktop compiler required')
    owners = {row['state']: row['part'] for row in covered}
    source = assembly.assembly_source(roots, owners, 'lower')
    source = source.replace(assembly.PREFIX+'.Check', 'Tests.LowerPrefix6.Bounds', 1)
    source = source.replace(assembly.PREFIX, 'Tests.LowerPilot6.Group0')
    source, wrapped = re.subn(r'(\naccepted\d+ :.*?)(?=\nposition\d+ :|\Z)',
        lambda match: '\nabstract\n'+'\n'.join('  '+line if line else ''
            for line in match[1].lstrip('\n').splitlines())+'\n', source, flags=re.S)
    if wrapped != len(roots):
        raise ValueError('unexpected original-rule guarantee template')
    source = local_options(source)
    runs = previous.parents[2]
    needed = sum((donor/name).stat().st_size for name in borrowed)+16*1024**2
    if not disk_allowed(disk_usage(runs), needed):
        raise ValueError('unchanged study storage/free-space guard')
    output.mkdir(parents=True, exist_ok=False)
    check = output/'check'
    check.mkdir()
    for name, _ in source_files(donor):
        assembly.hardlink(donor/name, check/name)
    target = 'src/Tests/LowerPrefix6/Bounds.agda'
    path = check/target
    path.parent.mkdir(parents=True)
    path.write_text(source)
    manifest = bench6.refresh_manifest(check, origin={k: identity[k] for k in ('revision', 'dirty')})
    for name, digest in borrowed.items():
        copy_interface(donor/name, check/name, digest)
    if assembly6.interfaces(check) != borrowed:
        raise ValueError('private cached prefix differs')
    command = [machine['agda_path'], *assembly6.FLAGS, '--save-metas', '-i', 'src', target,
               '+RTS', '-M1350M', '-c', '-s', '-RTS']
    with build_lock(check):
        record = run_job('covered-lower-bounds', command, output/'records', root=check,
            expected_source_sha256=manifest['source_sha256'], cpu_limit=45, timeout=180,
            rss_limit_gib=1.5, log_limit_mib=2,
            metadata=dict(machine=machine, own_target_cold=True, borrowed_interfaces_sha256=digest_entries(borrowed),
                verified_prefix_report_sha256=verification['previous_report_sha256'],
                verification_sha256=assembly6.sha(args.verification), no_certificate_shards_rechecked=True))
    after = assembly6.interfaces(check)
    changed = cache_changes(borrowed, after)
    own = {name: digest for name, digest in after.items() if name.endswith('/Tests/LowerPrefix6/Bounds.agdai')}
    unexpected = [name for name in after if name not in borrowed and name not in own]
    donor_fixed = source_identity(donor) == identity and assembly6.interfaces(donor) == pool
    accepted = bool(record['accepted'] and len(own) == 1 and not changed and not unexpected and donor_fixed and
        record['source_unchanged'] and record['expected_source_matches'] and
        record['executable_sha256'] == machine['agda_sha256'] and disk_allowed(disk_usage(runs)))
    log = output/'records/covered-lower-bounds.log'
    log_sha = assembly6.sha(log)
    packed = archive(log, log_sha) if accepted else None
    result = dict(format='othello-lower-prefix6-v1', accepted=accepted,
        status='complete' if accepted else 'covered-root-assembly-failed',
        roots=roots, covered=covered, checked_sample_lower_roots=len(roots) if accepted else 0,
        goal='White guarantees White-minus-Black >= 4 under ORIGINAL Rules.game six',
        reused_accepted_parts=last+1, new_certificate_parts_checked=0,
        previous_report_sha256=assembly6.sha(previous/'final.json'),
        previous_audit_sha256=assembly6.sha(previous/'phase-records.json'),
        previous_source_sha256=identity['source_sha256'], previous_interfaces_sha256=digest_entries(pool),
        verification_sha256=assembly6.sha(args.verification), donor_unchanged=donor_fixed,
        generated_source_sha256=assembly6.sha(path), source_sha256=manifest['source_sha256'],
        agda_source_sha256=source_identity(check)['agda_source_sha256'], check_root=str(check),
        cache_changes=changed, unexpected_interfaces=unexpected, machine=machine,
        borrowed_interfaces=borrowed, before_interfaces_sha256=digest_entries(borrowed),
        after_interfaces=after, after_interfaces_sha256=digest_entries(after),
        record=record, record_sha256=assembly6.sha(output/'records/covered-lower-bounds.json'),
        raw_log_sha256=log_sha, archived_log=packed, final_disk=disk_usage(runs),
        original_twenty_root_pilot_complete=False, heldout_group_unmeasured=True,
        initial_problem2_proved=False, production_authorized=False)
    atomic_json(output/'prefix.json', result)
    print(json.dumps({key: result[key] for key in ('status', 'accepted', 'checked_sample_lower_roots',
        'reused_accepted_parts', 'new_certificate_parts_checked')}))
    return accepted


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('previous', 'verification', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--agda', required=True)
    raise SystemExit(0 if run(p.parse_args()) else 2)


if __name__ == '__main__':
    main()
