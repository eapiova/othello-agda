"""Share only exact closed pilot copies, excluding every archived original inode."""
import json
import os
from pathlib import Path
import subprocess

import assembly6
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, utc
from wire_workflow6 import require

MANIFEST = Path('/home/eapiova/Documents/Codex/2026-10-14/othello-archive-copy/archive-evidence-20261014/source-manifest.json')
MANIFEST_SHA = 'b79d54eeb6f3e3edfaba61d65b1c1fcedb2b66cfc3fe5f20549b9777340f0665'
LABEL = 'initial-lower-global-closed-retry-20261015'
REPORT_SHA = '707efe3f8eff0a0c86f0ab2de7b63e9e2b986278e4412a987045ecf412c68a35'
RECEIPT_SHA = 'd24052a1b9cad2b9403ad30218f3a36e66cb778eb6c8becea81bcdc423c0de2c'


def attributes(path):
    return {n: os.getxattr(path, n) for n in os.listxattr(path)}


def candidate(target, canonical, protected):
    require(not target.is_symlink() and not canonical.is_symlink(), 'regular copies only')
    a, b = target.stat(), canonical.stat()
    if ((a.st_dev, a.st_ino) in protected or (b.st_dev, b.st_ino) in protected
            or a.st_ino == b.st_ino or a.st_nlink != 1):
        return False
    keys = ('st_dev', 'st_size', 'st_mtime_ns', 'st_mode', 'st_uid', 'st_gid')
    return (all(getattr(a, k) == getattr(b, k) for k in keys)
            and attributes(target) == attributes(canonical))


def recover(current, donor_outer, output):
    runs = current.parent
    target_outer = runs / ('six-' + LABEL)
    target = target_outer / 'results/initial-lower-global-closed6/check'
    donor = donor_outer / 'results/initial-lower-global-named6/check'
    receipt = target_outer / 'results' / (LABEL + '.json')
    require(assembly6.sha(MANIFEST) == MANIFEST_SHA, 'archive original manifest differs')
    manifest = json.loads(MANIFEST.read_text())
    protected = {tuple(v['source_inode']) for v in manifest['entries'].values()}
    del manifest
    checks, pins = {}, {str(receipt): RECEIPT_SHA, str(target.parent / 'report.json'): REPORT_SHA,
                       str(MANIFEST): MANIFEST_SHA}
    require(all(assembly6.sha(Path(p)) == h for p, h in pins.items()), 'closed evidence differs')
    for label, check in ((LABEL, target), (donor_outer.name.removeprefix('six-'), donor)):
        state = subprocess.run(['systemctl', '--user', 'show', 'othello6-' + label + '.service',
            '-p', 'ActiveState', '-p', 'MainPID'], capture_output=True, text=True).stdout
        require('MainPID=0' in state and 'ActiveState=active' not in state
                and 'ActiveState=activating' not in state, 'only terminal cache copies')
        report = json.loads((check.parent / 'report.json').read_text())
        source, pool = source_identity(check), assembly6.interfaces(check)
        require(report['accepted'] and report['status'] == 'complete'
                and source == report['checked_source']
                and digest_entries(pool) == report['last_interface_pool_sha256'], 'closed cache differs')
        checks[str(check)] = dict(source=source, pool=pool)
    require(json.loads(receipt.read_text())['accepted'], 'accepted final receipt required')
    tpool, dpool = checks[str(target)]['pool'], checks[str(donor)]['pool']
    tsources, dsources = dict(source_files(target)), dict(source_files(donor))
    replacements = []
    for name in list(tpool) + list(tsources):
        interface = name in tpool
        if (dpool.get(name) != tpool[name] if interface else dsources.get(name) != tsources[name]):
            continue
        a, b = target / name, donor / name
        if not candidate(a, b, protected):
            continue
        if interface:
            source = name.split('/agda/', 1)[1][:-1]
            require(tsources[source] == dsources[source], 'interface source differs')
        h = assembly6.sha(a)
        require(assembly6.sha(b) == h, 'copy bytes differ')
        s = a.stat()
        replacements.append(dict(path=str(a), canonical=str(b), sha256=h,
            original_inode=s.st_ino, mtime_ns=s.st_mtime_ns, mode=s.st_mode,
            allocated_bytes=s.st_blocks * 512))
    result = dict(format='othello-closed-pilot-allocation6-v1', status='prepared', created_utc=utc(),
        replacements=replacements, protected_manifest_sha256=MANIFEST_SHA,
        protected_original_inode_count=len(protected), archived_original_inodes_excluded=True,
        protected_receipts=pins, initial_allocated_bytes=allocated(runs),
        future_writes='copy2 into private inodes; all shared historical paths remain immutable')
    atomic_json(output, result)
    for row in replacements:
        a, b = Path(row['path']), Path(row['canonical'])
        require(candidate(a, b, protected) and assembly6.sha(a) == assembly6.sha(b) == row['sha256'],
                'selected copies changed')
        tmp = a.with_name(a.name + '.narrow-share-tmp')
        require(not tmp.exists(), 'fresh sharing temporary required')
        os.link(b, tmp)
        os.replace(tmp, a)
    require(all(source_identity(Path(p)) == v['source'] and assembly6.interfaces(Path(p)) == v['pool']
                for p, v in checks.items()), 'closed source or interface bytes changed')
    require(all(assembly6.sha(Path(p)) == h for p, h in pins.items()), 'closed receipts changed')
    result.update(status='complete', finished_utc=utc(), final_allocated_bytes=allocated(runs),
        recovered_allocated_bytes=sum(r['allocated_bytes'] for r in replacements),
        source_and_interface_bytes_unchanged=True, receipts_unchanged=True)
    atomic_json(output, result)
    return {k: v for k, v in result.items() if k != 'replacements'}
