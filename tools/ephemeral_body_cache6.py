"""AI-assisted private tmpfs cache for safe Agda data-module interfaces.

Accepted Boolean Rows interfaces are individual read-only bind mounts. New
interfaces exist only in bounded tmpfs mounts in the checker's namespace.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
from compression import zstd

ROOT = Path('/home/eapiova/projects/othello-agda-main')
if str(ROOT/'tools') not in sys.path:
    sys.path.append(str(ROOT/'tools'))
from run_job import atomic_json, utc

PROOF_CAP = 512*2**20
CHECK_CAP = 16*2**20


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def prepare(prefix, *, out, check, proof, control, row_views, lineage,
            agda_command, agda_sha256, expected_body_modules):
    """Return a short launcher command; retain the exact bwrap argument bytes."""
    out, check, proof, control = map(Path, (out, check, proof, control))
    require(prefix[0] == '/usr/bin/bwrap' and prefix[-1] == '--',
            'sandbox prefix must name bwrap and end at the command boundary')
    arguments = list(prefix[1:-1])
    arguments += ['--size', str(PROOF_CAP), '--tmpfs', str(proof/'_build'),
                  '--size', str(CHECK_CAP), '--tmpfs', str(check/'_build')]
    seeded = {}
    for side in ('upper', 'lower'):
        namespace = 'Complete'+side.title()+'Rows6'
        relative = Path('2.9.0/agda/src/Tests')/namespace
        arguments += ['--dir', str(proof/'_build'/relative)]
        for key, entry in sorted(lineage.items()):
            if not key.startswith(side+'/'):
                continue
            name = key.split('/', 1)[1]
            target = proof/'_build'/relative/name
            arguments += ['--ro-bind', str(Path(row_views[side])/name), str(target)]
            seeded[str(target)] = entry['new_sha256']
    require(len(seeded) == 1337, 'exactly1337 accepted Rows bindings are required')
    job_path = out/'ephemeral-job.json'
    inner_command = ['/usr/bin/python3', '-B',
                     str(control/'ephemeral_body_cache6.py'), 'inner', str(job_path)]
    raw = b'\0'.join(os.fsencode(part) for part in arguments)+b'\0'
    args_path = out/'bwrap-arguments.nul'
    require(not args_path.exists() and not job_path.exists(), 'ephemeral dispatch already prepared')
    args_path.write_bytes(raw)
    job = {'format': 'othello-ephemeral-body-cache-job-v1', 'created_utc': utc(),
        'out': str(out), 'check': str(check), 'proof': str(proof),
        'inner_command': inner_command,
        'argument_file': str(args_path), 'argument_file_sha256': sha(args_path),
        'seeded_rows': seeded, 'seeded_rows_digest': digest(seeded),
        'proof_tmpfs_cap_bytes': PROOF_CAP, 'check_tmpfs_cap_bytes': CHECK_CAP,
        'host_build_devices': {str(root/'_build'): (root/'_build').stat().st_dev
                               for root in (check, proof)},
        'agda_command': agda_command, 'agda_sha256': agda_sha256,
        'expected_body_modules': sorted(expected_body_modules),
        'helper_sha256': sha(control/'ephemeral_body_cache6.py'),
        'persistent_interface_writes_authorized': False,
        'private_ephemeral_interface_writes_authorized': True}
    atomic_json(job_path, job)
    return ['/usr/bin/python3', '-B', str(control/'ephemeral_body_cache6.py'),
            'launch', str(job_path)], job


def launch(job_path):
    job = read(job_path)
    require(sha(__file__) == job['helper_sha256'], 'ephemeral helper changed')
    require(sha(job['argument_file']) == job['argument_file_sha256'], 'bwrap arguments changed')
    descriptor = os.open(job['argument_file'], os.O_RDONLY)
    os.set_inheritable(descriptor, True)
    os.execv('/usr/bin/bwrap', ['/usr/bin/bwrap', '--args', str(descriptor),
                              '--', *job['inner_command']])


def namespace_mounts():
    result = {}
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        fields = line.split(); split = fields.index('-')
        result[fields[4]] = {'options': fields[5].split(','), 'fstype': fields[split+1]}
    return result


def seeded_snapshot(job):
    result = {path: sha(path) for path in job['seeded_rows']}
    require(result == job['seeded_rows'], 'a seeded accepted Rows interface changed')
    return digest(result)


def private_usage(roots):
    result = {}
    for root, cap in roots.items():
        info = os.statvfs(root)
        used = (info.f_blocks-info.f_bfree)*info.f_frsize
        require(info.f_blocks*info.f_frsize <= cap and used <= cap,
                'private tmpfs capacity or usage exceeds its finite cap')
        result[root] = used
    return result


def inner(job_path):
    job = read(job_path); out = Path(job['out'])
    require(sha(__file__) == job['helper_sha256'], 'inner helper changed')
    require(sha(job['agda_command'][0]) == job['agda_sha256'], 'Agda binary changed')
    roots = {str(Path(job['proof'])/'_build'): job['proof_tmpfs_cap_bytes'],
             str(Path(job['check'])/'_build'): job['check_tmpfs_cap_bytes']}
    mounts = namespace_mounts()
    require(all(mounts.get(root, {}).get('fstype') == 'tmpfs'
                and os.stat(root).st_dev != job['host_build_devices'][root]
                for root in roots), 'actual build directories are not private tmpfs mounts')
    require(all('ro' in mounts.get(path, {}).get('options', [])
                for path in job['seeded_rows']), 'every seeded Rows file must be mounted read-only')
    before = seeded_snapshot(job); initial_usage = private_usage(roots)
    stop = threading.Event(); failures = []; peak = dict(initial_usage)
    locks = []; result = None
    with contextlib.ExitStack() as stack:
        # Deliberately take the actual namespace-local locks directly. An
        # inherited host-build lock describes a different inode after tmpfs.
        for root in roots:
            path = Path(root)/'.study6.lock'
            lock = stack.enter_context(path.open('a'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            info = os.fstat(lock.fileno())
            locks.append({'path': str(path), 'device': info.st_dev, 'inode': info.st_ino})
        atomic_json(out/'ephemeral-cache-begin.json', {
            'recorded_utc': utc(), 'seeded_Rows_count': len(job['seeded_rows']),
            'seeded_Rows_digest': before, 'seeded_Rows_all_readonly': True,
            'actual_private_build_locks': locks, 'initial_tmpfs_bytes': initial_usage,
            'private_mounts': {root: mounts[root] for root in roots},
            'Agda_command': job['agda_command'], 'mathematical_objective_complete': False})
        process = subprocess.Popen(job['agda_command'], cwd=job['check'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        def watch():
            while not stop.wait(1):
                try:
                    for root, value in private_usage(roots).items():
                        peak[root] = max(peak[root], value)
                except BaseException as error:
                    failures.append(repr(error)); process.send_signal(signal.SIGTERM)
                    atomic_json(out/'ephemeral-cache-stop.json', {'recorded_utc': utc(),
                        'reason': repr(error)})
                    return
        thread = threading.Thread(target=watch, daemon=True); thread.start()
        raw_log = bytearray(); pending = b''

        def summary(line):
            if any(token in line for token in (b'Checking ', b'Heap exhausted',
                                               b'Failed to ', b'error:')):
                os.write(1, line+b'\n')
        try:
            while True:
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                raw_log.extend(chunk); pending += chunk
                lines = pending.split(b'\n'); pending = lines.pop()
                for line in lines:
                    summary(line)
                if len(raw_log) > 8*2**20:
                    failures.append('complete Agda log exceeds8MiB uncompressed cap')
                    process.kill()
                    break
            if pending:
                summary(pending)
            result = process.wait()
        finally:
            stop.set(); thread.join()
            process.stdout.close()
        log_path = out/'ephemeral-agda-full.log.zst'
        compressed_log = zstd.compress(bytes(raw_log), level=3)
        require(len(compressed_log) <= 512*2**10, 'compressed Agda log exceeds512KiB cap')
        log_path.write_bytes(compressed_log)
        require(zstd.decompress(log_path.read_bytes()) == bytes(raw_log),
                'complete compressed Agda log readback differs')
        after = seeded_snapshot(job); final_usage = private_usage(roots)
        generated = {}
        for root in roots:
            for path in sorted(Path(root).rglob('*.agdai')):
                if str(path) in job['seeded_rows']:
                    continue
                generated[str(path)] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
        body_modules = set()
        for path in generated:
            relative = Path(path).relative_to(Path(job['proof'])/'_build') if (
                Path(path).is_relative_to(Path(job['proof'])/'_build')) else None
            if relative is not None and relative.name.startswith('Body'):
                body_modules.add('Tests.'+relative.parent.name+'.'+relative.stem)
        expected = set(job['expected_body_modules'])
        accepted = result == 0 and not failures and before == after and body_modules == expected
        atomic_json(out/'ephemeral-cache.json', {
            'recorded_utc': utc(), 'accepted': accepted, 'Agda_exit_code': result,
            'failure': failures, 'private_mounts': {root: mounts[root] for root in roots},
            'actual_private_build_locks': locks, 'seeded_Rows_count': len(job['seeded_rows']),
            'seeded_Rows_before_digest': before, 'seeded_Rows_after_digest': after,
            'seeded_Rows_all_readonly': True, 'seeded_Rows_unchanged': before == after,
            'data_only_Body_interfaces': len(body_modules), 'expected_Body_interfaces': len(expected),
            'generated_interface_count': len(generated), 'generated_interfaces_digest': digest(generated),
            'generated_interface_bytes': sum(item['bytes'] for item in generated.values()),
            'full_Agda_log': str(log_path), 'full_Agda_log_sha256': sha(log_path),
            'full_Agda_log_decoded_sha256': hashlib.sha256(raw_log).hexdigest(),
            'full_Agda_log_decoded_bytes': len(raw_log),
            'full_Agda_log_lossless_readback_verified': True,
            'stdout_is_progress_summary_full_bytes_are_retained_compressed': True,
            'initial_tmpfs_bytes': initial_usage, 'peak_tmpfs_bytes': peak,
            'final_tmpfs_bytes': final_usage, 'new_interfaces_are_namespace_private': True,
            'private_mounts_disappear_when_bwrap_exits': True,
            'persistent_interface_writes_authorized': False,
            'mathematical_objective_complete': False})
    return 0 if accepted else 1


if __name__ == '__main__':
    require(len(sys.argv) == 3 and sys.argv[1] in ('launch', 'inner'), 'action and job path required')
    if sys.argv[1] == 'launch':
        launch(Path(sys.argv[2]))
    else:
        raise SystemExit(inner(Path(sys.argv[2])))
