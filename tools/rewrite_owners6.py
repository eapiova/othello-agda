#!/usr/bin/env python3
"""Assemble root5 from checked warning-filtered certificate prefixes.

Preserve every conditional certificate and original rule/goal. The only new
owner-source changes are namespace references and the measured local filter.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import assembly6
import bench6
import global_assembly6 as assembly
import owner_cuts6 as cuts
import owner_pruned6 as pruned
from provenance import digest_entries, source_files, source_identity
import rewrite_filter6 as filtered
import rewrite_prefix6 as prefix
from run_job import positive

PREFIX='Tests.RewriteOwners6'
DIRECTORY='src/Tests/RewriteOwners6'


def generated(donor):
    originals,phases,partition=pruned.generated(donor)
    mapping={pruned.PREFIX:PREFIX,filtered.OLD:filtered.PREFIX,
        'Tests.LowerLocal6.Root4.Group0':'Tests.RewriteLocal6'}
    sources={}
    for name,original in originals.items():
        text=original
        for old,new in mapping.items():text=text.replace(old,new)
        if filtered.WARNING in text or text.count(' -WnoUnsupportedIndexedMatch #-}')!=1:
            raise ValueError('original owner warning mode differs')
        text=text.replace(' -WnoUnsupportedIndexedMatch #-}',
            ' -WnoUnsupportedIndexedMatch '+filtered.WARNING+' #-}',1)
        restored=text.replace(' '+filtered.WARNING,'',1)
        for old,new in mapping.items():restored=restored.replace(new,old)
        if restored!=original:
            raise ValueError('owner change beyond namespaces and warning output')
        sources[name.replace(pruned.DIRECTORY,DIRECTORY)]=text
    for binding in partition['bindings']:
        binding['imports'] = [next((name.replace(old, new) for old, new in mapping.items()
            if name == old or name.startswith(old+'.')), name) for name in binding['imports']]
    partition.update(filtered_prefixes_used=True,conditional_parts_rechecked=0,
        certificate_data_and_owner_proof_terms_unchanged=True,warning_filter=filtered.WARNING)
    return sources,phases,partition


def verified_prefix(args,original_pool,machine,sources):
    previous=args.filtered_prefix.resolve()
    if assembly6.sha(previous/'final.json')!=args.expected_filtered_prefix_sha256:
        raise ValueError('filtered prefix report differs')
    r=json.loads((previous/'final.json').read_text())
    root=Path(r['check_root']);identity=source_identity(root);pool=assembly6.interfaces(root)
    original=Path(json.loads((args.previous.resolve()/'final.json').read_text())['check_root'])
    expected,targets=prefix.generated(original)
    base,base_identity,borrowed=prefix.verified_pilot(
        type('Args',(),dict(pilot=Path(r['pilot']),expected_pilot_sha256=r['pilot_report_sha256'],
            expected_previous_sha256=args.expected_previous_sha256))(), original,original_pool,machine,expected)
    if (r['format']!='othello-rewrite-prefix6-v1' or not r['accepted'] or r['status']!='complete' or
            r['machine']!=machine or r['previous_report_sha256']!=args.expected_previous_sha256 or
            r['borrowed_interfaces']!=borrowed or r['targets']!=targets or
            r['generated_source_hashes']!=cuts.pilot.source_hashes(expected) or
            r['certificate_parts_reused']!=2 or r['certificate_parts_rechecked']!=234 or
            r['conditional_parts_rechecked']!=0 or not r['donor_unchanged'] or not r['pilot_unchanged'] or
            not r['generated_sources_unchanged'] or source_identity(root)['source_sha256']!=r['source_sha256'] or
            pool!=r['final_interfaces'] or digest_entries(pool)!=r['interfaces_sha256'] or
            any(assembly6.sha(root/n)!=d for n,d in r['generated_source_hashes'].items())):
        raise ValueError('requires the complete, unchanged 236-part prefix and original compiler')
    before=dict(borrowed)
    for phase,target in zip(r['phases'],[t for t in targets if not t['reused']],strict=True):
        rec=phase['record'];record=previous/'records'/(phase['label']+'.json')
        pack=phase['archived_log'];log=previous/'records'/pack['archive_name']
        raw=gzip.decompress(log.read_bytes())
        if (any(phase[k]!=v for k,v in target.items()) or not phase['expected_outcome_met'] or not rec['accepted'] or
                phase['cache_changes'] or phase['unexpected_interfaces'] or len(phase['own_interfaces'])!=1 or
                rec['borrowed_interfaces_sha256']!=digest_entries(before) or not rec['own_target_cold'] or
                not rec['source_unchanged'] or not rec['expected_source_matches'] or rec['source_sha256']!=r['source_sha256'] or
                rec['executable_sha256']!=machine['agda_sha256'] or
                not all(f in rec['argv'] for f in assembly6.FLAGS+['--save-metas','-M1350M']) or
                rec['rss_stop_threshold_gib']!=1.5 or phase['interface']['warnings']!=0 or
                assembly6.sha(record)!=phase['record_sha256'] or json.loads(record.read_text())!=rec or
                assembly6.sha(log)!=pack['archive_sha256'] or hashlib.sha256(raw).hexdigest()!=phase['raw_log_sha256'] or
                len(raw)!=rec['log_bytes']):
            raise ValueError('filtered prefix receipt, safe flags or archive differs')
        before.update(phase['own_interfaces'])
    if len(r['phases'])!=234 or before!=pool:
        raise ValueError('incomplete or unrecorded prefix interface')
    # Reuse only the required original conditional parts and generic coverage
    # helper. Their imports refer to generic modules, never the old prefixes.
    modules=['Tests.DirectCitations6.Coverage','Tests.IndependentLower6.Checker',
        'Tests.IndependentLower6.Part114']+[f'Tests.OwnerLower6.Root5.Part{i}' for i in range(27)]
    selected={'_build/2.9.0/agda/src/'+m.replace('.','/')+'.agdai':
        original_pool['_build/2.9.0/agda/src/'+m.replace('.','/')+'.agdai'] for m in modules}
    merged=args.output.resolve().with_name(args.output.name+'-checked-prefix')
    if merged.exists() or args.runs_root.resolve() not in merged.parents:
        raise ValueError('fresh immutable staging root inside study runs required')
    merged.mkdir()
    for name,_ in source_files(root):assembly.hardlink(root/name,merged/name)
    joined={**pool,**selected}
    for name,digest in joined.items():
        origin=root if name in pool else original
        if assembly6.sha(origin/name)!=digest:raise ValueError('selected proof interface differs')
        source='src/'+name.split('/agda/src/',1)[1].removesuffix('.agdai')+'.agda'
        if (root/source).read_bytes()!=(origin/source).read_bytes():
            raise ValueError('selected conditional source differs')
        assembly.hardlink(origin/name,merged/name)
    bench6.refresh_manifest(merged,origin={k:identity[k] for k in ('revision','dirty')})
    if (assembly6.interfaces(merged)!=joined or source_identity(root)!=identity or assembly6.interfaces(root)!=pool or
            source_identity(base)!=base_identity or assembly6.interfaces(base)!=borrowed or
            assembly6.interfaces(original)!=original_pool):
        raise ValueError('staging changed a checked donor')
    return dict(previous=str(previous),report_sha256=args.expected_filtered_prefix_sha256,
        root=str(merged),identity=source_identity(merged),interfaces=joined,
        interfaces_sha256=digest_entries(joined),skip_phases=0,immutable_staging_only=True,
        filtered_certificate_parts_reused=236,conditional_parts_reused=28,
        selected_original_interfaces=selected,original_generic_caches_reused=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['previous','filtered-prefix','output','runs-root']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-previous-sha256',required=True)
    p.add_argument('--expected-filtered-prefix-sha256',required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--kernel-cpu-budget',type=positive,required=True)
    raise SystemExit(0 if cuts.run(p.parse_args(),generator=generated,directory=DIRECTORY,
        report_format='othello-rewrite-owners6-v1',prefix_validator=verified_prefix)['accepted'] else 2)
