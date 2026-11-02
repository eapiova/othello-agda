#!/usr/bin/env python3
"""Bounded native AND/OR prefix measurements, never Agda proof evidence.

S counts all proof-tree occurrences (including root and leaves), L counts unique
frontier/terminal states, and H counts forcing-node witness occurrences. The
same bounds and full state are required for deduplication. Partial runs report
lower bounds; allocation caps cover native tables, not process overhead.
"""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
import solve6
import ref


def query(position: ref.State | str = 'initial', *, turn: str = 'black',
          direction: str = 'lower', threshold: int = 0, frontier_discs: int = 26,
          max_states: int = 1000000, max_nodes: int = 10000000,
          max_memory_mb: int = 512, max_cpu_seconds: int = 20,
          tt_bits: int = 18, small: int = 10, deep_order: int = 13,
          emit_states: bool = False, timeout: float = 30,
          load_tt: str | Path | None = None, save_tt: str | Path | None = None) -> dict:
    if isinstance(position, ref.State):
        turn = 'white' if position.turn == ref.WHITE else 'black'
        position = solve6.position012(position)
    options = {'position': position, 'turn': turn, 'direction': direction,
               'threshold': threshold, 'frontier-discs': frontier_discs,
               'max-states': max_states, 'max-nodes': max_nodes,
               'max-memory-mb': max_memory_mb, 'max-cpu-seconds': max_cpu_seconds,
               'tt-bits': tt_bits, 'small': small, 'deep-order': deep_order,
               'emit-states': int(emit_states)}
    argv = [str(solve6.build()), 'frontier']
    for key, value in options.items():
        argv.extend(('--' + key, str(value)))
    cache_argv, cache_metadata = solve6.checkpoint_options('frontier', load_tt, save_tt,
        tt_bits=tt_bits, small=small, deep_order=deep_order)
    argv.extend(cache_argv)
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if completed.returncode:
        raise ValueError(f'native frontier failed ({completed.returncode}): {completed.stderr.strip()}')
    result = json.loads(completed.stdout)
    if 'states' in result:
        # Concrete JSON encoding size, not an estimate of Agda proof-file size.
        result['encoded_states_json_bytes'] = len(json.dumps(
            result['states'], separators=(',', ':'), ensure_ascii=True).encode('ascii'))
    solve6.checkpoint_created(save_tt, cache_metadata, tt_bits=tt_bits, small=small,
        deep_order=deep_order, stage='after-frontier', request=options)
    if load_tt is not None or save_tt is not None:
        result['checkpoint'] = solve6.checkpoint_record(cache_metadata, position, turn)
    result['request'] = options
    return result


def study(position: ref.State | str = 'initial', *, turn: str = 'black',
          threshold: int = 4, frontier_grid: str = '18,20,22,24,26,28',
          baseline_cpu_seconds: int = 7200, max_states: int = 1000000,
          max_nodes: int = 10000000, max_memory_mb: int = 512,
          max_cpu_seconds: int = 20, tt_bits: int = 18, small: int = 10,
          deep_order: int = 13, emit_states: bool = False,
          load_tt: str | Path | None = None, save_tt: str | Path | None = None):
    """Yield flushed exact, per-case, and summary records from one native process.

    Baseline has a CPU cap and no node cap. Each prefix has independent caps;
    TT survives between cases. An outer ledger job must cap total resource use.
    """
    if isinstance(position, ref.State):
        turn = 'white' if position.turn == ref.WHITE else 'black'
        position = solve6.position012(position)
    binary = solve6.build()
    options = {'position': position, 'turn': turn, 'threshold': threshold,
               'frontier-grid': frontier_grid, 'baseline-cpu-seconds': baseline_cpu_seconds,
               'max-states': max_states, 'max-nodes': max_nodes,
               'max-memory-mb': max_memory_mb, 'max-cpu-seconds': max_cpu_seconds,
               'tt-bits': tt_bits, 'small': small, 'deep-order': deep_order,
               'emit-states': int(emit_states)}
    argv = [str(binary), 'study']
    for key, value in options.items():
        argv.extend(('--' + key, str(value)))
    cache_argv, cache_metadata = solve6.checkpoint_options('study', load_tt, save_tt,
        tt_bits=tt_bits, small=small, deep_order=deep_order)
    argv.extend(cache_argv)
    metadata = json.loads((solve6.BUILD / 'build.json').read_text())
    # Native errors are short and emitted only at validation/allocation failures.
    with subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, bufsize=1) as process:
        try:
            for line in process.stdout:
                record = json.loads(line)
                if record.get('record_type') == 'exact' and record.get('complete'):
                    solve6.checkpoint_created(save_tt, cache_metadata, tt_bits=tt_bits, small=small,
                        deep_order=deep_order, stage='after-exact-before-frontier', request=options)
                if load_tt is not None or save_tt is not None:
                    record['checkpoint'] = solve6.checkpoint_record(cache_metadata, position, turn)
                if record.get('record_type') == 'exact':
                    record['build_metadata'] = metadata
                    record['request'] = options
                if 'states' in record:
                    record['encoded_states_json_bytes'] = len(json.dumps(
                        record['states'], separators=(',', ':')).encode('ascii'))
                yield record
            returncode = process.wait()
            if returncode:
                raise ValueError(f'native study failed ({returncode}): {process.stderr.read().strip()}')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--load-tt', type=Path)
    parser.add_argument('--save-tt', type=Path)
    parser.add_argument('--position', default='initial')
    parser.add_argument('--turn', choices=('black', 'white'), default='black')
    parser.add_argument('--direction', choices=('lower', 'upper'), default='lower')
    parser.add_argument('--threshold', type=int, default=None)
    parser.add_argument('--study', action='store_true')
    parser.add_argument('--frontier-grid', default='18,20,22,24,26,28')
    parser.add_argument('--baseline-cpu-seconds', type=int, default=7200)
    parser.add_argument('--output', type=Path)
    for name, default in (('frontier-discs', 26), ('max-states', 1000000),
                          ('max-nodes', 10000000), ('max-memory-mb', 512),
                          ('max-cpu-seconds', 20), ('tt-bits', 18),
                          ('small', 10), ('deep-order', 13)):
        parser.add_argument('--' + name, type=int, default=default)
    parser.add_argument('--emit-states', action='store_true')
    parser.add_argument('--timeout', type=float, default=30)
    options = vars(parser.parse_args())
    is_study = options.pop('study')
    output = options.pop('output')
    if output is not None:
        output = output.resolve()
        if not output.is_relative_to((solve6.ROOT / 'results').resolve()):
            parser.error('--output must be under results/')
        output.parent.mkdir(parents=True, exist_ok=True)
    if is_study:
        options.pop('direction'); options.pop('frontier_discs'); options.pop('timeout')
        if options['threshold'] is None:
            options['threshold'] = 4
        records = study(**options)
    else:
        options.pop('frontier_grid'); options.pop('baseline_cpu_seconds')
        if options['threshold'] is None:
            options['threshold'] = 0
        records = iter((query(**options),))
    target = output.open('w') if output is not None else None
    try:
        for record in records:
            line = json.dumps(record, sort_keys=True)
            print(line, flush=True)
            if target is not None:
                target.write(line + '\n'); target.flush()
    finally:
        if target is not None:
            target.close()


if __name__ == '__main__':
    main()
