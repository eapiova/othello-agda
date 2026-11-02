"""Separately authorized multi-part canonical-state/semantic-join experiment.

No native search or production. The coordinator charges one enclosing receipt;
all nested safe-checker receipts are diagnostics included in that CPU usage.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import resource

import assembly6
from canonical_join6 import emit_join
from canonical_multi_prepare6 import prepare
import canonical_state_pilot6 as canonical
import full_map_pilot6 as pilot
import new_row_bridge6 as bridge
from owner_continue6 import nnls
from provenance import digest_entries, source_identity
from run_job import atomic_json, build_lock, run_job, utc
from wire_workflow6 import require

SCOPE = 'canonical-multi-row-join-pilot6-v1-floor60'
ANSWER = 'Sì, autorizzo il test su quattro parti con soglia 60 GiB'
PARTS = [380, 17924, 21836, 29329]
TRAIN = [380, 17924]
HELD = [21836, 29329]
SAMPLE_SHA = '3a2e89ec9fae596ab97b3474bb10f247035c846af05e6afb2c0e2dfe5d8e166b'
CANONICAL = pilot.BASE/'six-canonical-state-floor60-20261018/results/canonical-state-pilot6'
PRIOR_ROW = CANONICAL/'row-check'
PRIOR_BRIDGE = CANONICAL/'bridge-check'
PREFIX = 'Tests.CanonicalMulti6'
JOINT_PREFIX = 'Tests.CanonicalMultiCombined6'


def approved(raw, approval):
    spec = json.loads(raw)
    fields = dict(scope=SCOPE, cpu_max_seconds=600, hard_memory_gib=12,
                  artifact_cap_gib=12, free_disk_gib=60, repeated_boolean_rows=800,
                  new_distinct_game_rows=0, joint_owned_rows=1000,
                  temporary_disk_floor_exception=True, one_heavy_job=True,
                  native_search_allowed=False, production_authorized=False)
    require(all(type(spec.get(k)) is type(v) and spec.get(k) == v for k,v in fields.items()),
            'exact reviewed multi-part scope/resources required')
    require(spec.get('parts') == PARTS and spec.get('training') == TRAIN
            and spec.get('held_out') == HELD
            and spec.get('sample_sha256') == SAMPLE_SHA
            and spec.get('full_manifest_sha256') == canonical.FULL_MANIFEST_SHA,
            'exact reviewed selection and retained inputs required')
    require(approval.get('approved') is True and approval.get('answer') == ANSWER
            and approval.get('plan_sha256') == hashlib.sha256(raw).hexdigest()
            and isinstance(approval.get('question_item'),str) and approval['question_item']
            and all(type(approval.get(k)) is type(v) and approval.get(k) == v
                    for k,v in fields.items()),
            'distinct explicit multi-part800-row/semantic-join consent required')
    return spec


def _limits():
    cap = resource.getrlimit(resource.RLIMIT_CPU)[0]
    require(cap != resource.RLIM_INFINITY and 0 < cap <= 540, '540CPU capped outer required')
    groups = [s[3:] for s in Path('/proc/self/cgroup').read_text().splitlines() if s.startswith('0::')]
    require(len(groups) == 1, 'one hard memory cgroup required')
    cg = Path('/sys/fs/cgroup')/groups[0].lstrip('/')
    maximum = (cg/'memory.max').read_text().strip()
    require(maximum.isdigit() and 0 < int(maximum) <= 12*2**30
            and (cg/'memory.swap.max').read_text().strip() == '0',
            'hard12GiB memory with no swap required')


def _units(layout):
    units = [dict(part=u['part'],rows=u['rows'],row_prefix=u['row_layout']['prefix'],
                  bridge_prefix=u['bridge_layout']['prefix']) for u in layout['layouts']]
    units.append(dict(part=34176, rows=200, row_prefix=canonical.ROW_PREFIX,
                      bridge_prefix=canonical.BRIDGE_PREFIX))
    return units


def checker_command(machine, target, check, *, dependencies=(), heap='-M1200M'):
    argv = canonical._command(machine,target,check,heap=heap)
    i = argv.index('--')+1
    includes = [arg for p in dependencies for arg in ('-i',str(Path(p)/'src'))]
    argv[i+4:i+4] = includes
    return argv


def run(current,out,plan_path,approval_path,sample_path,full_path):
    raw=plan_path.read_bytes();spec=approved(raw,json.loads(approval_path.read_text()));_limits()
    require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==spec['worker_sha256'],
            'reviewed worker changed')
    require(not out.exists() and not any(p.is_symlink() for p in (out,*out.parents)),
            'fresh private output required; no automatic retry')
    canonical.storage(current,64*2**20,floor=60)
    expected={pilot.DONOR:(pilot.DONOR_SOURCE_SHA,pilot.DONOR_POOL_SHA),
              bridge.FULL:(bridge.FULL_SOURCE_SHA,bridge.FULL_POOL_SHA),
              bridge.ALIGNED:(bridge.ALIGNED_SOURCE,bridge.ALIGNED_POOL),
              PRIOR_ROW:('557f80013fd6153a30bfdc1566d8cdc97271aa40eb8b6d8d350a781d3cbda7ba',
                         '4ea31db916f8b87d904212e1f29d1dd5ae170cf02169127d68fca9a9a9b4fc04'),
              PRIOR_BRIDGE:('f080e480340be7d74b86c08be9d085534a2c71067c68251671463220544382e6',
                            'f482462390677858f2e73226a983688ec347266437eca86172c09f5a1c6453aa')}
    with contextlib.ExitStack() as stack:
        for donor in sorted(expected):stack.enter_context(build_lock(donor))
        before={}
        for donor,(source_sha,pool_sha) in expected.items():
            source,pool=source_identity(donor),assembly6.interfaces(donor)
            require(source['source_sha256']==source_sha and digest_entries(pool)==pool_sha,
                    'immutable accepted donor differs')
            before[donor]=source,pool
        _,_,_,machine=pilot.donor_identity()
        prior_path=CANONICAL/'report.json'
        require(assembly6.sha(prior_path)==spec['prior_report_sha256'],'accepted canonical baseline changed')
        prior=json.loads(prior_path.read_text())
        require(prior['accepted'] and prior['repeated_boolean_rows']==200
                and prior['row_record']['cpu_seconds']==22.877007
                and prior['bridge_record']['cpu_seconds']==46.120688,
                'exact previously measured canonical training baseline required')
        layout=prepare(sample_path,full_path,parts=PARTS,output=out/'prepared',prefix=PREFIX,
            expected_sample_sha256=SAMPLE_SHA,expected_full_sha256=canonical.FULL_MANIFEST_SHA)
        require(layout['generated_sha256']==spec['prepared_generated_sha256'],
                'generated per-part sources differ from reviewed prototype')
        joint=emit_join(out/'semantic-joint',json.loads(full_path.read_text()),_units(layout),prefix=JOINT_PREFIX)
        require(joint['generated_sha256']==spec['joint_generated_sha256'],
                'generated semantic joint differs from reviewed prototype')
        cases={u['part']:u for u in layout['layouts']}
        report=dict(format='othello-canonical-multi-row-join-pilot6-v1',accepted=False,
            status='checking-training',created_utc=utc(),plan_sha256=hashlib.sha256(raw).hexdigest(),
            phases=[],layout=layout,joint_layout=joint,prior_report_sha256=spec['prior_report_sha256'],
            repeated_boolean_rows=800,new_distinct_game_rows=0,joint_owned_rows=1000,
            free_disk_gib=60,temporary_disk_floor_exception=True,native_search_allowed=False,
            production_authorized=False,initial_problem2_proved=False,optimal_initial_pair_proved=False,
            full_workflow_gate_validated=False,charge='sole outer receipt only; nested CPU included')
        save=lambda:atomic_json(out/'report.json',report)
        save();fresh={}
        for u in layout['layouts']:
            for side in ('row','bridge'):
                p=out/'prepared'/u[side+'_root'];stack.enter_context(build_lock(p))
                fresh[p]=(source_identity(p),{})
        joint_root=out/'semantic-joint';stack.enter_context(build_lock(joint_root))
        fresh[joint_root]=(source_identity(joint_root),{})
        def check(label,target,root,deps,modules,cpu,rss,heap):
            canonical.storage(current,64*2**20,floor=60)
            require(not assembly6.interfaces(root),'each owned target cache must start cold')
            rec=run_job(label,checker_command(machine,target,root,dependencies=deps,heap=heap),
                out/'records',root=root,locked=True,expected_source_sha256=fresh[root][0]['source_sha256'],
                timeout=400,cpu_limit=cpu,rss_limit_gib=rss,log_limit_mib=4,
                metadata=dict(checker_binary_sha256=pilot.AGDA_SHA,own_target_cold=True,
                              native_search_allowed=False,production_authorized=False))
            pool=assembly6.interfaces(root);seen=canonical.checked_modules((out/'records'/(label+'.log')).read_text())
            ok=bool(rec['accepted'] and len(pool)==len(modules) and set(seen)==set(modules))
            entry=dict(label=label,record=rec,accepted=ok,checked_modules=seen,
                own_interfaces=len(pool),interface_pool_sha256=digest_entries(pool))
            report['phases'].append(entry);save()
            atomic_json(out/(label+'-interfaces.json'),pool)
            require(ok,'safe phase did not pass; originals retained; no retry')
            fresh[root]=(fresh[root][0],pool)
            return rec
        training={
            'row':[dict(x=[5608/1000,503/1000,1.],cpu_seconds=22.877007)],
            'bridge':[dict(x=[503/1000,1.],cpu_seconds=46.120688)]}
        forecast=None
        with canonical.watched_storage(current,out,floor=60):
            for split,ids in [('training',TRAIN),('held_out',HELD)]:
                if split=='held_out':
                    models={side:nnls(training[side],3 if side=='row' else 2) for side in training}
                    predictions={}
                    for j in HELD:
                        f=cases[j]['features'];d=f['state_dependencies']/1000
                        xs={'row':[f['tokens']/1000,d,1.],'bridge':[d,1.]}
                        predictions[str(j)]={side:sum(c*x for c,x in zip(models[side]['coefficients'],xs[side]))
                                             for side in models}
                    require(all(v>0 for p in predictions.values() for v in p.values()),'nonpositive forecast')
                    forecast=dict(models=models,predictions=predictions,frozen_utc=utc(),
                        held_out_measured=False,relative_error_limit=.30,
                        prior34176_is_observed_training=True,whole_workflow_validated=False)
                    atomic_json(out/'forecast.json',forecast);report['forecast_sha256']=assembly6.sha(out/'forecast.json')
                    report['status']='checking-held-out';save()
                for j in ids:
                    u=cases[j];r=out/'prepared'/u['row_root'];b=out/'prepared'/u['bridge_root']
                    rp=u['row_layout']['prefix'];bp=u['bridge_layout']['prefix']
                    rr=check('rows-'+str(j),rp+'.Part'+str(j),r,[],
                        [rp+'.Family',rp+'.BodyData'+str(j),rp+'.Part'+str(j)],60,1.5,'-M1200M')
                    batch_count=u['bridge_layout']['source_modules']-1
                    br=check('bridge-'+str(j),bp+'.Root',b,[r],
                        [bp+'.Root']+[bp+'.Batch'+str(i) for i in range(batch_count)],120,11.5,'-M10G')
                    if split=='training':
                        f=u['features'];d=f['state_dependencies']/1000
                        training['row'].append(dict(x=[f['tokens']/1000,d,1.],cpu_seconds=rr['cpu_seconds']))
                        training['bridge'].append(dict(x=[d,1.],cpu_seconds=br['cpu_seconds']))
            require(forecast and assembly6.sha(out/'forecast.json')==report['forecast_sha256'],
                    'prospective forecast changed')
            report['status']='checking-semantic-joint';save()
            dependencies=[out/'prepared'/u[k+'_root'] for u in layout['layouts'] for k in ('row','bridge')]
            dependencies += [PRIOR_ROW,PRIOR_BRIDGE]
            jr=check('semantic-joint',joint['root_module'],joint_root,dependencies,
                     [joint['root_module']],120,11.5,'-M10G')
        intact=all(source_identity(p)==s and assembly6.interfaces(p)==cache for p,(s,cache) in before.items())
        new_intact=all(source_identity(p)==s and assembly6.interfaces(p)==cache for p,(s,cache) in fresh.items())
        gates={}
        for side in ('row','bridge'):
            predicted=sum(forecast['predictions'][str(j)][side] for j in HELD)
            labels={('rows-' if side=='row' else 'bridge-')+str(j) for j in HELD}
            measured=sum(p['record']['cpu_seconds'] for p in report['phases'] if p['label'] in labels)
            error=abs(measured-predicted)/predicted
            gates[side]=dict(predicted_cpu_seconds=predicted,measured_cpu_seconds=measured,
                            relative_error=error,within30percent=error<=.30)
        report.update(accepted=bool(intact and new_intact and len(report['phases'])==9),
            status='complete' if intact and new_intact else 'dependencies-changed',
            all_five_donors_unchanged=intact,all_new_sources_and_caches_unchanged=new_intact,
            joint_partial_coverage_agda_checked=True,prediction_gates=gates,
            prediction_gate_passed=all(g['within30percent'] for g in gates.values()),
            storage=canonical.storage(current,floor=60),finished_utc=utc())
        save();require(report['accepted'],'immutable proof pool changed; no production')
        return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','approval','sample','full','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    run(Path.cwd().resolve(),args.output.absolute(),args.plan,args.approval,args.sample,args.full)
