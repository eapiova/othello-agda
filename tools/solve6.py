#!/usr/bin/env python3
"""Untrusted native 6x6 oracle; no solver result is evidence accepted by Agda.

All subprocesses use argument arrays (never a shell). Build products and provenance
are stored under ignored results/native6; public helpers accept scalar ref.State.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import ref

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/native6/solve6.c'
VENDOR = ROOT / 'tools/native6/vendor/solve6b.c'
LICENSE = ROOT / 'tools/native6/vendor/LICENSE'
BUILD = ROOT / 'results/native6'
FLAGS = ('-O3', '-std=c11', '-Wall', '-Wextra')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def build(*, compiler: str | None = None) -> Path:
    """Build if inputs changed; record compiler, source and binary hashes."""
    cc = shutil.which(compiler or os.environ.get('CC', 'cc'))
    if cc is None:
        raise RuntimeError('C compiler not found')
    cc = str(Path(cc).resolve())
    inputs = {'source_sha256': sha256(SOURCE), 'vendor_sha256': sha256(VENDOR),
              'license_sha256': sha256(LICENSE), 'compiler': cc,
              'compiler_sha256': sha256(Path(cc)), 'flags': list(FLAGS)}
    binary = BUILD / 'solve6'
    manifest = BUILD / 'build.json'
    if binary.exists() and manifest.exists():
        previous = json.loads(manifest.read_text())
        if all(previous.get(k) == v for k, v in inputs.items()) and previous.get('binary_sha256') == sha256(binary):
            return binary
    BUILD.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    version = subprocess.run([cc, '--version'], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    fd, temporary = tempfile.mkstemp(prefix='solve6-', dir=BUILD)
    os.close(fd)
    try:
        compiled = subprocess.run([cc, *FLAGS, str(SOURCE), '-o', temporary],
                                  capture_output=True, text=True, timeout=30)
        if compiled.returncode:
            raise RuntimeError(f'compile failed ({compiled.returncode}): {compiled.stderr}')
        os.replace(temporary, binary)
    finally:
        Path(temporary).unlink(missing_ok=True)
    inputs.update({'compiler_version': version, 'binary_sha256': sha256(binary),
                   'compile_exit_code': compiled.returncode, 'compile_stderr': compiled.stderr,
                   'wall_seconds': time.monotonic() - started, 'trust': 'untrusted native solver'})
    manifest.write_text(json.dumps(inputs, indent=2, sort_keys=True) + '\n')
    return binary


CACHE_BUILD_KEYS = ('source_sha256', 'compiler', 'compiler_sha256', 'flags', 'binary_sha256')


def cache_path(value: str | Path) -> Path:
    path = Path(value).resolve()
    if not path.is_relative_to((ROOT / 'results').resolve()):
        raise ValueError('TT checkpoint must be under results/')
    return path


def checkpoint_options(command, load_tt, save_tt, *, tt_bits, small, deep_order):
    """Validate external provenance before exposing an untrusted table to C."""
    if (load_tt is not None or save_tt is not None) and command not in ('solve', 'bounds', 'study', 'frontier'):
        raise ValueError('TT checkpoints unsupported for command')
    build_metadata = json.loads((BUILD / 'build.json').read_text())
    config = {'tt_bits': tt_bits, 'small': small, 'deep_order': deep_order}
    metadata = {'trust': 'untrusted search hints; never proof input'}
    argv = []
    if load_tt is not None:
        path = cache_path(load_tt)
        try:
            manifest = json.loads(Path(str(path) + '.json').read_text())
            digest = sha256(path)
        except (OSError, ValueError) as exc:
            raise ValueError('cannot read TT checkpoint or provenance') from exc
        expected = {key: build_metadata[key] for key in CACHE_BUILD_KEYS}
        if (manifest.get('format') != 'native6-tt-v1' or manifest.get('build') != expected
                or manifest.get('config') != config or manifest.get('cache_sha256') != digest
                or manifest.get('cache_bytes') != path.stat().st_size):
            raise ValueError('TT checkpoint checksum or build/config provenance mismatch')
        metadata['loaded'] = {'path': str(path), 'path_sha256': hashlib.sha256(str(path).encode()).hexdigest(),
                              'cache_sha256': digest}
        argv += ['--load-tt', str(path)]
    if save_tt is not None:
        path = cache_path(save_tt)
        if path.exists() or path.is_symlink() or Path(str(path) + '.json').exists():
            raise ValueError('TT checkpoint destination and sidecar must be absent')
        path.parent.mkdir(parents=True, exist_ok=True)
        argv += ['--save-tt', str(path)]
    return argv, metadata


def checkpoint_created(save_tt, metadata, *, tt_bits, small, deep_order, stage, request):
    if save_tt is None or 'created' in metadata:
        return
    path = cache_path(save_tt)
    if not path.exists():
        return
    build_metadata = json.loads((BUILD / 'build.json').read_text())
    digest = sha256(path)
    manifest = {'format': 'native6-tt-v1', 'cache_sha256': digest,
                'cache_bytes': path.stat().st_size,
                'build': {key: build_metadata[key] for key in CACHE_BUILD_KEYS},
                'config': {'tt_bits': tt_bits, 'small': small, 'deep_order': deep_order},
                'stage': stage, 'request': request,
                'trust': 'untrusted search hints; never proof input'}
    sidecar = Path(str(path) + '.json')
    fd, temporary = tempfile.mkstemp(prefix=sidecar.name + '.tmp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as output:
            json.dump(manifest, output, sort_keys=True, indent=2)
            output.write('\n'); output.flush(); os.fsync(output.fileno())
        # Exclusive publication also protects an arbitrary existing sidecar.
        os.link(temporary, sidecar)
    finally:
        Path(temporary).unlink(missing_ok=True)
    metadata['created'] = {'path': str(path), 'path_sha256': hashlib.sha256(str(path).encode()).hexdigest(),
                           'cache_sha256': digest, 'stage': stage}


def checkpoint_record(metadata, position, turn):
    return {**metadata, 'input_sha256': hashlib.sha256(
        json.dumps({'position': position, 'turn': turn}, sort_keys=True).encode()).hexdigest()}


def position012(state: ref.State) -> str:
    if state.size != 6 or len(state.cells) != 36 or state.turn not in (ref.BLACK, ref.WHITE):
        raise ValueError('requires a scalar 6x6 state with valid turn')
    if any(type(c) is not int or c not in (0, 1, 2) for c in state.cells):
        raise ValueError('cells must be integer 0, 1, or 2')
    return ''.join(map(str, state.cells))


def query(command: str, position: ref.State | str = 'initial', *,
          turn: str | int | None = None, tt_bits: int = 18, small: int = 10,
          depth: int | None = None, direction: str | None = None,
          threshold: int | None = None, deep_order: int = 13, fuel: int = 80, timeout: float = 60,
          load_tt: str | Path | None = None, save_tt: str | Path | None = None) -> dict:
    """Return native JSON including node counters, CPU time and table size.

    ``bounds`` tests White-minus-Black >= threshold (lower) or <= threshold
    (upper); its boolean is sound as an oracle assertion but is not a proof.
    """
    if isinstance(position, ref.State):
        if turn is not None and turn not in (position.turn, 'white' if position.turn == ref.WHITE else 'black'):
            raise ValueError('turn conflicts with scalar state')
        turn = position.turn
        position = position012(position)
    if turn is None:
        turn = 'black'
    if type(turn) is int:
        turn = {ref.BLACK: 'black', ref.WHITE: 'white'}.get(turn, 'invalid')
    argv = [str(build()), command, '--position', position, '--turn', str(turn),
            '--tt-bits', str(tt_bits), '--small', str(small),
            '--deep-order', str(deep_order), '--fuel', str(fuel)]
    for flag, val in (('--depth', depth), ('--direction', direction), ('--threshold', threshold)):
        if val is not None:
            argv.extend((flag, str(val)))
    cache_argv, cache_metadata = checkpoint_options(command, load_tt, save_tt,
        tt_bits=tt_bits, small=small, deep_order=deep_order)
    argv.extend(cache_argv)
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if completed.returncode:
        raise ValueError(f'native query failed ({completed.returncode}): {completed.stderr.strip()}')
    result = json.loads(completed.stdout)
    if not isinstance(result, dict):
        raise RuntimeError('native response must be an object')
    checkpoint_created(save_tt, cache_metadata, tt_bits=tt_bits, small=small,
        deep_order=deep_order, stage='after-' + command, request={'position': position, 'turn': turn})
    if load_tt is not None or save_tt is not None:
        result['checkpoint'] = checkpoint_record(cache_metadata, position, turn)
    return result


def solve(state: ref.State | str = 'initial', **kwargs) -> int:
    return query('solve', state, **kwargs)['value']


def bounds(state: ref.State | str, direction: str, threshold: int, **kwargs) -> bool:
    return query('bounds', state, direction=direction, threshold=threshold, **kwargs)['holds']


def moves(state: ref.State | str = 'initial', **kwargs) -> list[dict]:
    return query('moves', state, **kwargs)['successors']


def successors(state: ref.State) -> tuple[ref.State, ...]:
    return tuple(ref.State(6, tuple(map(int, move['position'])),
                           ref.BLACK if move['turn'] == 'black' else ref.WHITE)
                 for move in moves(state))


def perft(state: ref.State | str, depth: int, **kwargs) -> int:
    return query('perft', state, depth=depth, **kwargs)['count']


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'solve', 'bounds', 'moves', 'perft', 'mirror', 'tt-selftest'))
    parser.add_argument('--load-tt', type=Path)
    parser.add_argument('--save-tt', type=Path)
    parser.add_argument('--position', default='initial')
    parser.add_argument('--turn', choices=('black', 'white'), default='black')
    parser.add_argument('--tt-bits', type=int, default=18)
    parser.add_argument('--small', type=int, default=10)
    parser.add_argument('--deep-order', type=int, default=13)
    parser.add_argument('--fuel', type=int, default=80)
    parser.add_argument('--depth', type=int)
    parser.add_argument('--direction', choices=('lower', 'upper'))
    parser.add_argument('--threshold', type=int)
    parser.add_argument('--timeout', type=float, default=60)
    args = parser.parse_args()
    if args.command == 'build':
        build()
        print((BUILD / 'build.json').read_text(), end='')
    else:
        try:
            result = query(args.command, args.position, turn=args.turn, tt_bits=args.tt_bits,
                           small=args.small, depth=args.depth, direction=args.direction,
                           threshold=args.threshold, deep_order=args.deep_order, fuel=args.fuel, timeout=args.timeout,
                           load_tt=args.load_tt, save_tt=args.save_tt)
        except (ValueError, subprocess.TimeoutExpired) as exc:
            parser.error(str(exc))
        print(json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    main()
