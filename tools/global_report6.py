#!/usr/bin/env python3
"""AI-assisted conservative report for the bounded global-proof pilot.

Only complete kernel assembly counts as checked root guarantees. The multi-root
sample's reuse is never extrapolated to a population-wide DAG. The per-leaf
compact-data estimate is labelled statistical and excludes exports/interfaces.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

from run_job import atomic_json


def summarize(native,assembly,subset=None):
    if native.get('status')!='complete' or native.get('scalar_replay') is not True:
        raise ValueError('native graph must be complete and scalar-replayed')
    stats=native['stats'];n=native['sample_size'];cases=native['cases']
    if (len(cases)!=n or n<2 or stats['roots']!=n or
        native.get('source_population_kind')!='canonical frontier full-state classes'):
        raise ValueError('inconsistent sample count or unit')
    if (assembly.get('plan_sha256')!=native['plan_sha256'] or
        assembly.get('roots')!=n or assembly.get('direction')!=native['direction'] or
        assembly.get('threshold')!=native['threshold']):
        raise ValueError('kernel assembly belongs to another graph or bound')
    parts=assembly.get('parts',[])
    accepted_parts=[p for p in parts if p['accepted']]
    complete=(assembly.get('accepted') is True and assembly.get('status')=='complete' and
              assembly.get('assembly',{}).get('accepted') is True and
              len(parts)==assembly['part_count'] and len(accepted_parts)==len(parts))
    if complete:
        if sum(p['checked_tokens'] for p in parts)!=stats['checked_tokens']:
            raise ValueError('kernel parts do not cover the recorded graph')
        if sum(p['compact_bytes'] for p in parts)!=stats['global_compact_bytes']:
            raise ValueError('compact payload bytes disagree with the generated graph')
    ab=assembly.get('ab',[]);ab_result=None
    if len(ab)==2 and all(x['accepted'] for x in ab):
        by_variant={p['variant']:p for p in ab}
        if set(by_variant)!={'compact','legacy'}:
            raise ValueError('invalid encoding comparison')
        c,l=by_variant['compact'],by_variant['legacy']
        if min(c['cpu_seconds'],l['cpu_seconds'])<=0:
            raise ValueError('encoding comparison has invalid CPU time')
        ab_result=dict(part=assembly['comparison_part'],
                       compact_cpu_seconds=c['cpu_seconds'],legacy_cpu_seconds=l['cpu_seconds'],
                       legacy_over_compact_cpu_ratio=l['cpu_seconds']/c['cpu_seconds'],
                       compact_peak_rss_gib=c['peak_rss_gib'],legacy_peak_rss_gib=l['peak_rss_gib'],
                       scope='one paired cold target with identical needed dependencies and graph; payload codec differs')
    # This estimate uses separate certificates, whose per-root costs are
    # additive. The combined graph is not an additive population sample.
    sizes=[c['compact_bytes'] for c in cases]
    population=native['source_population']
    if type(population) is not int or population<n:
        raise ValueError('invalid canonical population')
    per_leaf=dict(direction=native['direction'],population=population,sample_size=n,
                  encoded_gib=population*statistics.mean(sizes)/2**30,
                  encoded_gib_sampling_se=population*statistics.stdev(sizes)/n**.5/2**30,
                  scope='separate compact certificates from canonical roots; excludes exports, interfaces and work roots')
    subset_count=0
    if subset is not None:
        if (subset.get('plan_sha256')!=native['plan_sha256'] or
            subset.get('direction')!=native['direction'] or subset.get('threshold')!=native['threshold']):
            raise ValueError('subset belongs to a different graph or bound')
        if subset.get('accepted') is True:
            roots=subset['roots'];subset_count=subset['checked_root_guarantees']
            if (subset.get('assembly',{}).get('accepted') is not True or
                subset_count!=len(roots) or len(set(roots))!=len(roots) or
                not set(roots)<={case['state'] for case in cases}):
                raise ValueError('subset root coverage disagrees with the checked sample')
    return dict(format='othello-global-pilot6-report-v1',
        recommendation='NO_PRODUCTION_GO_FROM_THIS_PILOT',production_authorized=False,
        checked_root_guarantees=n if complete else 0,kernel_assembly_complete=complete,
        checked_subset_root_guarantees=subset_count,kernel_subset=subset,
        accepted_parts=len(accepted_parts),planned_parts=assembly['part_count'],
        direction=native['direction'],threshold=native['threshold'],
        sample_size=n,source_sample_seed=native['source_sample_seed'],
        subsample_seed=native['subsample_seed'],
        graph=dict(union_states=stats['union_canonical_states'],
                   reachable_states=stats['reachable_canonical_states'],entries=stats['entries'],
                   separate_d4_tokens=stats['per_root_d4_tokens'],global_tokens=stats['checked_tokens'],
                   token_reduction_fraction=1-stats['checked_tokens']/stats['per_root_d4_tokens'],
                   separate_compact_bytes=stats['per_root_compact_bytes'],
                   global_compact_bytes=stats['global_compact_bytes'],
                   global_legacy_bytes=stats['global_legacy_bytes'],
                   identical_graph_codec_byte_ratio=stats['global_legacy_bytes']/stats['global_compact_bytes'],
                   exact_baseline_bytes=stats['exact_baseline_bytes'],
                   exact_baseline_over_global_compact_ratio=stats['exact_baseline_bytes']/stats['global_compact_bytes']),
        kernel=dict(accepted_part_cpu_seconds=sum(p['cpu_seconds'] for p in accepted_parts),
                    max_part_rss_gib=max((p['peak_rss_gib'] for p in parts),default=0),
                    assembly=assembly.get('assembly'),controlled_encoding_comparison=ab_result,
                    machine=assembly['machine']),
        per_leaf_compact_data_projection=per_leaf,
        limitations=[f'{n} sampled {native["direction"]} frontier states, not the initial board',
                     'full-population global sharing is unmeasured and is not extrapolated',
                     'lower-bound global proof and full skeleton/joint line are not validated by this pilot',
                     'sampling SE excludes representation, checking and throughput uncertainty',
                     'an encoding-only timing pair is not a controlled full-proof speedup',
                     'the completion-selected checked subset is biased and is not a performance sample',
                     'production gates still require a validated two-sided workflow forecast'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--assembly',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--subset',type=Path)
    args=p.parse_args()
    sources={key:getattr(args,key).read_bytes() for key in ['native','assembly']}
    if args.subset is not None:sources['subset']=args.subset.read_bytes()
    report=summarize(**{key:json.loads(data) for key,data in sources.items()})
    report['input_sha256']={key:hashlib.sha256(data).hexdigest() for key,data in sources.items()}
    args.output.parent.mkdir(parents=True,exist_ok=True);atomic_json(args.output,report)
    print(json.dumps({k:report[k] for k in ['recommendation','checked_root_guarantees',
                                           'checked_subset_root_guarantees','accepted_parts']}))


if __name__=='__main__':main()
