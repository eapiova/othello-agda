#!/usr/bin/env python3
"""Prepare, build and measure an external driver for the safe Agda checker.

No native solver participates. The generated Haskell adapter calls MAlonzo's
Bool exports directly. GHC compilation and that foreign boundary require an
actual build/run; preparation alone is not validation of compiled execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from provenance import source_identity
from run_job import run_job

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(command):
    found = shutil.which(command)
    if not found:
        raise FileNotFoundError(command)
    path = Path(found).resolve()
    version = subprocess.run([str(path), '--version'], capture_output=True,
                             text=True, check=True, timeout=10).stdout.strip()
    return {'path': str(path), 'sha256': digest(path), 'version': version}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def symbols(path):
    text = path.read_text()
    found = {}
    for name in ('search80', 'shardAccepted'):
        matches = re.findall(r'^(' + r'd_' + name + r'_\d+)\s*::\s*([^\n]+)', text, re.M)
        if len(matches) != 1:
            raise ValueError(f'expected one exported {name} signature in {path}')
        found[name] = {'symbol': matches[0][0], 'signature': matches[0][1]}
    return found


def prepare(out, fixture_bytes=0, malonzo=None):
    out.mkdir(parents=True, exist_ok=True)
    generated = out / 'generated'
    generated.mkdir(exist_ok=True)
    fixture = None
    if fixture_bytes:
        # One String literal, never a numeral or a recursively expanded Nat.
        fixture = generated / 'CompiledStringFixture.agda'
        fixture.write_text('{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
                           'module CompiledStringFixture where\n'
                           'open import Agda.Builtin.String using (String)\n'
                           'fixture : String\nfixture = "' + '0' * fixture_bytes + '"\n')
    hs = malonzo or out / 'MAlonzo/Code/Tests/Compiled6.hs'
    exports = symbols(hs) if hs.exists() else None
    if exports:
        adapter = '''module Main where
import qualified MAlonzo.Code.Tests.Compiled6 as Checker
import qualified Data.Text as T
import qualified Data.Text.IO as TIO
import Control.Exception (evaluate)
import System.Environment (getArgs)
import System.CPUTime (getCPUTime)
import GHC.Clock (getMonotonicTimeNSec)
import Text.Read (readMaybe)

main :: IO ()
main = do
  args <- getArgs
  case args of
    [mode, bound, threshold, input] -> case (bound, readMaybe threshold :: Maybe Integer) of
      (b, Just n) | b == "lower" || b == "upper" -> do
        text <- TIO.readFile input
        _ <- evaluate (T.length text)
        let lower = b == "lower"
            negative = n < 0
            magnitude = abs n
            result = case mode of
              "search" -> Checker.SEARCH text lower negative magnitude
              "shard" -> Checker.SHARD text lower negative magnitude
              _ -> error "mode must be search or shard"
        w0 <- getMonotonicTimeNSec
        c0 <- getCPUTime
        accepted <- evaluate result
        c1 <- getCPUTime
        w1 <- getMonotonicTimeNSec
        putStrLn ("{\\"accepted\\":" ++ (if accepted then "true" else "false") ++
          ",\\"wall_seconds\\":" ++ show (fromIntegral (w1-w0) / 1e9 :: Double) ++
          ",\\"cpu_seconds\\":" ++ show (fromIntegral (c1-c0) / 1e12 :: Double) ++ "}")
      _ -> error "bound must be lower/upper and threshold a signed integer"
    _ -> error "usage: compiled6 search|shard lower|upper SIGNED_THRESHOLD INPUT_FILE"
'''.replace('Checker.SEARCH', 'Checker.' + exports['search80']['symbol']).replace(
            'Checker.SHARD', 'Checker.' + exports['shardAccepted']['symbol'])
        (out / 'Main.hs').write_text(adapter)
    manifest = {'format': 'othello-compiled6-prepare-v1', **source_identity(ROOT),
                'fixture_bytes': fixture_bytes,
                'fixture': str(fixture) if fixture else None,
                'fixture_sha256': digest(fixture) if fixture else None,
                'exports': exports, 'adapter_ready': bool(exports),
                'adapter_sha256': digest(out / 'Main.hs') if exports else None}
    write_json(out / 'prepare.json', manifest)
    return manifest


def build(args):
    out = args.output.resolve()
    prepare(out, args.fixture_bytes)
    agda, ghc = identity(args.agda), identity(args.ghc)
    metadata = {'agda_identity': agda, 'ghc_identity': ghc,
                'boundary': 'safe Agda compiled via MAlonzo; external Haskell IO adapter',
                'trust': 'timings and compiled Bool are untrusted measurements, not Agda proofs'}
    jobs = []
    def job(label, command):
        result = run_job(label, command, out, root=ROOT, timeout=args.timeout,
                         cpu_limit=args.cpu_limit, rss_limit_gib=args.rss_limit_gib,
                         metadata=metadata)
        jobs.append(result)
        if not result['accepted']:
            raise RuntimeError(f'{label} failed; inspect {out / (label + ".json")}')
    flags = ['--no-libraries', '--safe', '--without-K', '--cubical-compatible', '--compile',
             '--no-main', '--ghc-dont-call-ghc', '--compile-dir=' + str(out),
             '-i', 'src', '-i', str(out / 'generated')]
    if args.fixture_bytes:
        job('fixture-agda', [agda['path'], *flags,
            str(out / 'generated/CompiledStringFixture.agda'), '+RTS', '-M1500M', '-RTS'])
    job('checker-agda', [agda['path'], *flags, 'src/Tests/Compiled6.agda',
                         '+RTS', '-M1500M', '-RTS'])
    prepare(out, args.fixture_bytes)
    # Explicitly compile the fixture too: its large literal reaches GHC.
    sources = [str(out / 'Main.hs')]
    if args.fixture_bytes:
        sources.append(str(out / 'MAlonzo/Code/CompiledStringFixture.hs'))
    job('checker-ghc', [ghc['path'], '--make', '-O2', '-rtsopts', '-i' + str(out),
                        '-outputdir', str(out / 'ghc'), '-o', str(out / 'compiled6'), *sources])
    hs_hashes = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob('*.hs'))}
    write_json(out / 'build.json', {'format': 'othello-compiled6-build-v1',
        **source_identity(ROOT), **metadata, 'binary_sha256': digest(out / 'compiled6'),
        'generated_haskell_sha256': hs_hashes, 'jobs': [j['label'] for j in jobs],
        'fixture_bytes': args.fixture_bytes})


def run(args):
    out = args.output.resolve()
    build_info = json.loads((out / 'build.json').read_text())
    binary = out / 'compiled6'
    if digest(binary) != build_info['binary_sha256']:
        raise ValueError('compiled binary changed since build')
    if source_identity(ROOT)['agda_source_sha256'] != build_info['agda_source_sha256']:
        raise ValueError('Agda source changed since build')
    input_path = args.input.resolve()
    result = run_job(args.label, [str(binary), args.mode, args.bound, str(args.threshold),
        str(input_path), '+RTS', '-M1500M', '-RTS'], out, root=ROOT,
        timeout=args.timeout, cpu_limit=args.cpu_limit, rss_limit_gib=args.rss_limit_gib,
        metadata={'build': build_info, 'input_sha256': digest(input_path),
                  'input_bytes': input_path.stat().st_size})
    if result['accepted']:
        measured = json.loads((out / (args.label + '.log')).read_text())
        if not isinstance(measured.get('accepted'), bool):
            raise ValueError('driver did not return a Bool JSON result')
        result['checker_result'] = measured
        write_json(out / (args.label + '.json'), result)
    print(json.dumps(result, indent=2))
    return 0 if result['accepted'] else 1


def validate(args):
    """Differential fixtures and per-state timings; results remain untrusted."""
    out = args.output.resolve()
    build_info = json.loads((out / 'build.json').read_text())
    binary = out / 'compiled6'
    if digest(binary) != build_info['binary_sha256']:
        raise ValueError('compiled binary changed since build')
    if source_identity(ROOT)['agda_source_sha256'] != build_info['agda_source_sha256']:
        raise ValueError('Agda source changed since build')
    line = json.loads((ROOT / 'certificates/six-line.json').read_text())['states']
    fixtures = []
    for direction in ('lower', 'upper'):
        fixtures += [dict(label='terminal-' + direction, mode='search', text=line[-1],
                          direction=direction, threshold=4, expected=True),
                     dict(label='p26-' + direction, mode='search', text=line[26],
                          direction=direction, threshold=4, expected=True),
                     dict(label='wrong-bound-' + direction, mode='search', text=line[26],
                          direction=direction, threshold=5 if direction == 'lower' else 3,
                          expected=False)]
    for label, mode, text in [('bad-state','search','x'), ('bad-shard','shard','b000'),
                              ('unknown-constructor','shard',line[-1]+'X'),
                              ('missing-reply','shard',line[26]+'F0;')]:
        fixtures.append(dict(label=label, mode=mode, text=text, direction='lower',
                             threshold=4, expected=False))
    # An early terminal with unfilled cells checks signed raw scoring directly.
    negative = 'w1' + '0' * 35
    for direction in ('lower', 'upper'):
        fixtures.append(dict(label='negative-' + direction, mode='search', text=negative,
                             direction=direction, threshold=-1, expected=True))
    for part in ('Lower0', 'Lower1', 'Upper0', 'Upper1'):
        encoded = re.findall(r'encoded\s*=\s*"([^"]*)"',
                             (ROOT / f'src/Othello/Data6/{part}.agda').read_text())
        if len(encoded) != 1:
            raise ValueError('expected a single compact pilot shard String')
        fixtures.append(dict(label='shard-' + part.lower(), mode='shard', text=encoded[0],
                             direction='lower' if part.startswith('Lower') else 'upper',
                             threshold=4, expected=True))
    if args.dataset:
        dataset = json.loads(args.dataset.read_text())
        selected = [r for r in dataset['states'] if r['value'] is not None and
                    all(d in r['mirror'] for d in ('lower', 'upper'))]
        if args.limit is not None:
            selected = selected[:args.limit]
        for row in selected:
            for direction in ('lower', 'upper'):
                fixtures.append(dict(label=row['id'] + '-' + direction, mode='search',
                                     text=row['state'], direction=direction,
                                     threshold=row['value'], expected=True,
                                     native_W=row['mirror'][direction]['nodes'],
                                     empties=row['empties'], split=row['split']))
    directory = out / ('validation-' + args.label)
    directory.mkdir(parents=True, exist_ok=False)
    summary = {'format': 'othello-compiled6-validation-v1', 'build_sha256': digest(out/'build.json'),
               'binary_sha256': digest(binary), 'cases': [], 'accepted': False,
               'trust': 'untrusted compiled measurements; no native result enters Agda proofs'}
    failed = False
    for case in fixtures:
        input_path = directory / (case['label'] + '.txt')
        input_path.write_text(case['text'])
        record = run_job(case['label'], [str(binary), case['mode'], case['direction'],
                         str(case['threshold']), str(input_path), '+RTS', '-M1200M', '-RTS'],
                         directory, root=ROOT, timeout=args.timeout, cpu_limit=args.cpu_limit,
                         rss_limit_gib=args.rss_limit_gib,
                         metadata={'fixture': case, 'input_sha256': digest(input_path),
                                   'build_sha256': summary['build_sha256']})
        measured = None
        if record['accepted']:
            measured = json.loads((directory/(case['label']+'.log')).read_text())
        ok = measured is not None and measured.get('accepted') is case['expected']
        item = {**case, 'measurement': record, 'checker_result': measured, 'matches_expected': ok}
        if measured and case.get('native_W'):
            item['cN_cpu_seconds_per_node'] = measured['cpu_seconds'] / case['native_W']
        summary['cases'].append(item)
        failed = failed or not ok
        write_json(directory/'validation.json', summary)
        if not record['accepted']:
            break  # Resource failures stop the ladder; retain the rejected case.
    summary['accepted'] = not failed and len(summary['cases']) == len(fixtures)
    write_json(directory/'validation.json', summary)
    print(json.dumps({'cases': len(summary['cases']), 'accepted': summary['accepted'],
                      'report': str(directory/'validation.json')}))
    return 0 if summary['accepted'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'build', 'run', 'validate'):
        p = sub.add_parser(name)
        p.add_argument('--output', type=Path, default=ROOT / 'results/compiled6')
        if name in ('prepare', 'build'):
            p.add_argument('--fixture-bytes', type=int, choices=(0, 1048576), default=0)
        if name == 'prepare':
            p.add_argument('--malonzo', type=Path, help='existing generated module (or structural stub)')
        else:
            p.add_argument('--timeout', type=float, default=60)
            p.add_argument('--cpu-limit', type=float, default=30)
            p.add_argument('--rss-limit-gib', type=float, default=2)
        if name == 'build':
            p.add_argument('--agda', default='agda')
            p.add_argument('--ghc', default='ghc')
        if name == 'run':
            p.add_argument('--label', required=True)
            p.add_argument('--mode', choices=('search', 'shard'), required=True)
            p.add_argument('--bound', choices=('lower', 'upper'), required=True)
            p.add_argument('--threshold', type=int, required=True)
            p.add_argument('--input', type=Path, required=True)
        if name == 'validate':
            p.add_argument('--label', required=True)
            p.add_argument('--dataset', type=Path)
            p.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(args.output.resolve(), args.fixture_bytes, args.malonzo), indent=2))
    elif args.command == 'build':
        build(args)
    elif args.command == 'run':
        return run(args)
    else:
        return validate(args)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
