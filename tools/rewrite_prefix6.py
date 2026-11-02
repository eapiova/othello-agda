#!/usr/bin/env python3
"""Recreate accepted lower certificate prefixes without duplicate warning text.

The two checked filter-pilot parts are reused, as are all generic proofs.
Remaining certificate checks are repeated only to create new locally filtered
interfaces. Original donors and all conditional root2/root3/root5 parts stay
untouched. This is the fixed-sample study, not production or an initial proof.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import assembly6
import bench6
from cache_resume6 import copy_interface
from compact_logs6 import archive
import global_assembly6 as assembly
import owner_cuts6 as cuts
from memory_probe6 import rts_stats
from provenance import digest_entries, source_files, source_identity
import rewrite_filter6 as filtered
from run_job import atomic_json, positive, run_job, utc
from warning_tables6 import census_with_warnings

FAMILIES=[('global',filtered.OLD,filtered.PREFIX,122),
          ('local4','Tests.LowerLocal6.Root4.Group0','Tests.RewriteLocal6',114)]


def generated(donor):
    sources,targets={},[]
    for family,old,new,count in FAMILIES:
        for j in range(count):
            name='src/'+old.replace('.','/')+f'/Part{j}.agda'
            target='src/'+new.replace('.','/')+f'/Part{j}.agda'
            text=filtered.filtered_source((donor/name).read_text(),old=old,namespace=new,part=j)
            if old in text or 'Tests.LowerPilot6.Group0.' in text:
                raise ValueError('an old certificate dependency remains')
            sources[target]=text
            targets.append(dict(label=f'{family}-part{j}',family=family,part=j,target=target,
                original_source=name,certificate_data_and_proof_terms_unchanged=True,
                reused=family=='global' and j<2))
    return sources,targets


def verified_pilot(args,donor,pool,machine,sources):
    previous=args.pilot.resolve()
    if assembly6.sha(previous/'final.json') != args.expected_pilot_sha256:
        raise ValueError('local filter pilot report differs')
    r=json.loads((previous/'final.json').read_text())
    root=Path(r['check_root']);identity=source_identity(root);cache=assembly6.interfaces(root)
    generic={n:d for n,d in pool.items() if '/src/Tests/' not in n}
    expected={p:s for p,s in sources.items() if p.endswith(('/Part0.agda','/Part1.agda')) and '/RewriteFilter6/' in p}
    if (r['format']!='othello-rewrite-filter6-v1' or not r['accepted'] or r['status']!='complete' or
            r['machine']!=machine or r['previous_report_sha256']!=args.expected_previous_sha256 or
            r['borrowed_interfaces']!=generic or len(cache)!=len(generic)+2 or cache!=r['final_interfaces'] or
            digest_entries(cache)!=r['interfaces_sha256'] or identity['source_sha256']!=r['source_sha256'] or
            not r['donor_unchanged'] or not r['generated_sources_unchanged'] or
            r['generated_source_hashes']!=cuts.pilot.source_hashes(expected)):
        raise ValueError('requires the unchanged accepted local filter pilot and original compiler')
    before=dict(generic)
    for j,phase in enumerate(r['phases']):
        rec=phase['record'];path=previous/'records'/(phase['label']+'.json')
        packed=phase['archived_log'];archive_path=previous/'records'/packed['archive_name']
        raw=gzip.decompress(archive_path.read_bytes())
        if (phase['label']!=f'Part{j}' or not phase['expected_outcome_met'] or not rec['accepted'] or
                phase['cache_changes'] or phase['unexpected_interfaces'] or len(phase['own_interfaces'])!=1 or
                assembly6.sha(path)!=phase['record_sha256'] or json.loads(path.read_text())!=rec or
                rec['borrowed_interfaces_sha256']!=digest_entries(before) or
                not rec['own_target_cold'] or not rec['source_unchanged'] or not rec['expected_source_matches'] or
                rec['source_sha256']!=r['source_sha256'] or rec['executable_sha256']!=machine['agda_sha256'] or
                not all(f in rec['argv'] for f in assembly6.FLAGS+['--save-metas','-M1350M']) or
                rec['rss_stop_threshold_gib']!=1.5 or phase['interface']['warnings']!=0 or
                assembly6.sha(archive_path)!=packed['archive_sha256'] or
                hashlib.sha256(raw).hexdigest()!=phase['raw_log_sha256'] or len(raw)!=rec['log_bytes']):
            raise ValueError('local pilot receipt or archive differs')
        before.update(phase['own_interfaces'])
    if len(r['phases'])!=2 or before!=cache or any(assembly6.sha(root/n)!=d for n,d in r['generated_source_hashes'].items()):
        raise ValueError('unrecorded interface or changed pilot source')
    return root,identity,cache


def run(args):
    previous=args.previous.resolve()
    old,donor,identity,pool,machine=cuts.verified_donor(previous,args.expected_previous_sha256,args.agda)
    sources,targets=generated(donor)
    base,base_identity,borrowed=verified_pilot(args,donor,pool,machine,sources)
    output,runs=args.output.resolve(),args.runs_root.resolve()
    needed=sum((base/n).stat().st_size for n in borrowed)+sum(len(t.encode()) for t in sources.values())+48*1024**2
    if output.exists() or runs not in output.parents or not cuts.pilot.disk_allowed(cuts.pilot.disk_usage(runs),needed):
        raise ValueError('fresh study root and unchanged storage headroom required')
    output.mkdir(parents=True);root=output/'check';root.mkdir()
    for name,_ in source_files(base):assembly.hardlink(base/name,root/name)
    for name,text in sources.items():
        path=root/name
        if path.exists():
            if path.read_text()!=text:raise ValueError('accepted pilot source differs')
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    manifest=bench6.refresh_manifest(root,origin={k:identity[k] for k in ('revision','dirty')})
    for name,digest in borrowed.items():copy_interface(base/name,root/name,digest)
    report=dict(format='othello-rewrite-prefix6-v1',status='checking',accepted=False,created_utc=utc(),
        previous=str(previous),previous_report_sha256=args.expected_previous_sha256,
        pilot=str(args.pilot.resolve()),pilot_report_sha256=args.expected_pilot_sha256,
        check_root=str(root),source_sha256=manifest['source_sha256'],agda_source_sha256=source_identity(root)['agda_source_sha256'],
        machine=machine,borrowed_interfaces=borrowed,borrowed_interfaces_sha256=digest_entries(borrowed),
        generated_source_hashes=cuts.pilot.source_hashes(sources),targets=targets,phases=[],
        nested_cpu_seconds=0.,nested_cpu_budget=args.kernel_cpu_budget,
        certificate_parts_reused=2,certificate_parts_rechecked=0,conditional_parts_rechecked=0,
        checked_sample_lower_roots=5,postulates=0,heldout_measured=False,initial_problem2_proved=False,
        production_authorized=False,warning_filter=filtered.WARNING,warning_filter_scope='new module OPTIONS only')
    atomic_json(output/'preflight.json',report)
    for row in targets:
        if row['reused']:continue
        left=args.kernel_cpu_budget-report['nested_cpu_seconds']
        if left<10 or not cuts.pilot.disk_allowed(cuts.pilot.disk_usage(runs),8*1024**2):
            report['status']='cpu-stop' if left<10 else 'disk-stop';break
        before=assembly6.interfaces(root);target,label=row['target'],row['label']
        suffix='/'+target.removeprefix('src/').removesuffix('.agda')+'.agdai'
        if any(n.endswith(suffix) for n in before):raise ValueError('own target not cold')
        cap=min(90,left-2)
        rec=run_job(label,[args.agda,*assembly6.FLAGS,'--save-metas','-i','src',target,
            '+RTS','-M1350M','-c','-s','-RTS'],output/'records',root=root,
            expected_source_sha256=manifest['source_sha256'],cpu_limit=cap,timeout=cap*2+30,
            rss_limit_gib=1.5,log_limit_mib=2,metadata=dict(machine=machine,own_target_cold=True,
                warning_filter=filtered.WARNING,borrowed_interfaces_sha256=digest_entries(before)))
        after=assembly6.interfaces(root);changes=cuts.pilot.cache_changes(before,after)
        own={n:d for n,d in after.items() if n.endswith(suffix)}
        unexpected=[n for n in after if n not in before and n not in own]
        log=output/'records'/(label+'.log');text=log.read_text();digest=assembly6.sha(log)
        footprint=census_with_warnings(root/next(iter(own)),next(iter(own.values()))) if len(own)==1 else None
        accepted=bool(rec['accepted'] and len(own)==1 and not changes and not unexpected and rec['source_unchanged'] and
            rec['expected_source_matches'] and rec['executable_sha256']==machine['agda_sha256'] and footprint['warnings']==0)
        packed=archive(log,digest) if accepted else None
        report['phases'].append(dict(row,expected_outcome_met=accepted,record=rec,
            record_sha256=assembly6.sha(output/'records'/(label+'.json')),cache_changes=changes,
            unexpected_interfaces=unexpected,own_interfaces=own,raw_log_sha256=digest,
            archived_log=packed,rts=rts_stats(text),interface=footprint))
        report['nested_cpu_seconds']+=rec['cpu_seconds']
        report['certificate_parts_rechecked']+=int(accepted)
        atomic_json(output/'running.json',report)
        print(json.dumps(dict(label=label,accepted=accepted,cpu_seconds=rec['cpu_seconds'],
            rss_gib=rec['peak_rss_gib'],checked=report['certificate_parts_rechecked'])),flush=True)
        if not accepted:report['status']='phase-failed';break
    report.update(donor_unchanged=source_identity(donor)==identity and assembly6.interfaces(donor)==pool,
        pilot_unchanged=source_identity(base)==base_identity and assembly6.interfaces(base)==borrowed,
        generated_sources_unchanged=all(assembly6.sha(root/n)==d for n,d in report['generated_source_hashes'].items()),
        final_interfaces=assembly6.interfaces(root),latest_disk=cuts.pilot.disk_usage(runs))
    report['interfaces_sha256']=digest_entries(report['final_interfaces'])
    report['accepted']=bool(report['certificate_parts_rechecked']==234 and len(report['phases'])==234 and
        all(p['expected_outcome_met'] for p in report['phases']) and report['donor_unchanged'] and
        report['pilot_unchanged'] and report['generated_sources_unchanged'] and cuts.pilot.disk_allowed(report['latest_disk']))
    if report['accepted']:report['status']='complete'
    atomic_json(output/'final.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['previous','pilot','output','runs-root']:
        p.add_argument('--'+name,type=Path,required=True)
    for name in ['previous','pilot']:p.add_argument('--expected-'+name+'-sha256',required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--kernel-cpu-budget',type=positive,required=True)
    raise SystemExit(0 if run(p.parse_args())['accepted'] else 2)
