"""Retain untrusted UPPER wire using the exact accepted native layout binary.

No new solver policy or compilation. Original global-native5650 family includes
this necessary data export; no Agda result follows from native success.
"""
import hashlib
import json
from pathlib import Path
import resource
import shutil
import subprocess
import sys

import bounded_layout6 as native
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity
from run_job import atomic_json,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
DONOR=ROOT/'results/global-upper-layout6-20261018'
OUT=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/upper-wire-export6-20261018')
UNIT='othello6-'+OUT.name+'.service'
RESERVE=1400;OUTER=1320;ALLOWANCE=100;OUTPUT_CAP=512*2**20
FILES=['census','census.c','source-plan.json','build.json','fixture.json','upper.json','closure.json']
COUNT_KEYS=['unique_dag_nodes','original_graph_nodes','postprocessed_graph_nodes',
    'postprocessed_tree_nodes','wire_records','wire_bytes','wire_tokens','wire_references',
    'layout_parts','layout_tokens','layout_compact_bytes','layout_source_wire_bytes']
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=9;common.RESERVATION_CPU=RESERVE


def storage(frozen,reserve=0):
    own=batch.allocated(OUT);free=shutil.disk_usage(ROOT).free
    assert own+reserve<=OUTPUT_CAP and frozen['prior_allocated_study_bytes']+own+reserve<12*2**30
    assert free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
    return dict(allocated_study_bytes=frozen['prior_allocated_study_bytes']+own,
        own_output_bytes=own,root_free_bytes=free,root_metadata_reserve_bytes=2**20,
        data_free_bytes=shutil.disk_usage(OUT).free,reserved_bytes=reserve,checked_utc=utc())


def export():
    plan=json.loads((OUT/'plan.json').read_text())
    assert all(native.sha(DONOR/n)==h for n,h in plan['accepted_artifact_sha256'].items())
    pins=native.warm_provenance()
    assert all(native.sha(ROOT/n)==h for n,h in plan['p1_files'].items())
    argv=native.command(DONOR,'initial','black','upper',1250,100000000,25,True)
    argv+=['--wire-output',str(OUT/'initial-upper.wire'),'--wire-limit-mib','512']
    atomic_json(OUT/'request.json',dict(created_utc=utc(),command=argv,
        warm_sha256=native.WARM_SHA,warm_guards=pins,wire_export_explicitly_authorized=True,
        legacy_counts_only_label_retained=True,untrusted_data_only=True,accepted_proof=False))
    result=native.execute(argv,1700)
    complete=native.accepted(result) and result['counts'].get('wire_complete') is True
    same_counts=all(result['counts'].get(k)==plan['expected_counts'][k] for k in COUNT_KEYS)
    atomic_json(OUT/'native-result.json',dict(created_utc=utc(),result=result,
        complete=complete,same_layout_counts_as_accepted_counts_only_run=same_counts,accepted_proof=False))
    assert complete and same_counts,'Censored/different UPPER export; preserve output, no kernel admission'
    wire=OUT/'initial-upper.wire';h=hashlib.sha256();rows=0
    with wire.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):
            h.update(block);rows+=block.count(b'\n')
    assert wire.stat().st_size==plan['expected_counts']['wire_bytes'] and rows==plan['expected_counts']['wire_records']
    assert native.sha(native.WARM)==native.WARM_SHA and all(native.sha(Path(p))==s for p,s in pins.items())
    assert all(native.sha(DONOR/n)==s for n,s in plan['accepted_artifact_sha256'].items())
    assert all(native.sha(ROOT/n)==s for n,s in plan['p1_files'].items())
    atomic_json(OUT/'wire-manifest.json',dict(created_utc=utc(),path=str(wire),bytes=wire.stat().st_size,
        rows=rows,sha256=h.hexdigest(),warm_cache_unchanged=True,p1_unchanged=True,
        exact_accepted_binary_reused=True,policy_unchanged=True,untrusted_data_only=True,
        initial_bounds_proved=False,mathematical_objective_complete=False))


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(native.sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    assert resource.getrlimit(resource.RLIMIT_CORE)==(0,0)
    frozen=json.loads((OUT/'storage-freeze.json').read_text())
    common.storage=lambda reserve=0:storage(frozen,reserve)
    with common.watched():
        storage(frozen,8*2**20)
        result=run_job('export',previous.sandbox()+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'export'],
            OUT/'records',root=OUT/'control',timeout=1750,cpu_limit=1300,rss_limit_gib=8.8,log_limit_mib=2,
            expected_source_sha256=plan['control_source']['source_sha256'],
            metadata=dict(native_binary_sha256=plan['accepted_artifact_sha256']['census'],
                warm_cache_sha256=native.WARM_SHA,untrusted_data_only=True,initial_bounds_proved=False))
        fields=['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),export={k:result[k] for k in fields},
            wire_manifest_exists=(OUT/'wire-manifest.json').exists(),untrusted_data_only=True,
            accepted_proof=False,mathematical_objective_complete=False))
        storage(frozen,8*2**20)
        assert result['accepted'] and (OUT/'wire-manifest.json').exists()


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],
        OUT/'records',root=OUT/'control',timeout=1780,cpu_limit=OUTER,rss_limit_gib=8.9,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior=json.loads((DONOR/'closure.json').read_text())['combined_family_cpu_seconds']
    assert prior+RESERVE+ALLOWANCE<=5650
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    externals={Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in extras|externals)
    assert used+OUTPUT_CAP<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    hashes={n:native.sha(DONOR/n) for n in FILES}
    assert hashes['census']=='c786d2639801ee7867c1141f26e0c80e128d49c14ef7e26eaa1be35b0636880c'
    assert hashes['census.c']=='48021d80f13b792ab78f51861a18221765c48e6dea357fe2b8c2faeb04c409c8'
    expected=json.loads((DONOR/'upper.json').read_text())['result']['counts']
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    OUT.mkdir();control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),legacy_snapshot=legacy,
        extra_roots=[str(p) for p in sorted(extras|externals)],prior_allocated_study_bytes=used,
        own_output_cap_bytes=OUTPUT_CAP,retained_study_cap_gib=12,root_free_floor_gib=80,
        external_physical_bytes_counted=True))
    helpers=list(native.HELPERS)+['upper_wire_export6.py','big_rows_probe6.py','completion_batch6.py']
    plan=dict(created_utc=utc(),control_source=source_identity(control),
        helper_sha256={n:native.sha(ROOT/'tools'/n) for n in helpers},accepted_artifact_sha256=hashes,
        expected_counts={k:expected[k] for k in COUNT_KEYS},p1_files=history['p1_files'],
        authorization='Continuing formalization and all necessary tests within assigned budgets: retain exact existing UPPER-policy data for safe kernel checking',
        original_counts_only_export_plan_superseded_for_this_fresh_output_only=True,
        family_cpu_cap=5650,previous_combined_family_cpu_seconds=prior,
        reservation=RESERVE,outer_cpu_cap=OUTER,native_internal_cpu_cap=1250,
        new_controller_allowance_seconds=ALLOWANCE,combined_reserved_family_envelope=prior+RESERVE+ALLOWANCE,
        hard_memory_gib=9,swap_bytes=0,core_bytes=0,source_or_policy_changes=False,
        new_compilation=False,wire_export_allowed=True,accepted_proof=False,production_go=False,
        all34_line_state_ownership_cuts='OPEN',mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Exact accepted native UPPER binary: retain untrusted wire for necessary kernel checks; preserve global-native5650 family including all previous actuals/controller allowances')
    reservation=ledger.reserve('native',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,
        control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=9G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=1800','--property=WorkingDirectory='+str(control),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,family_envelope=prior+RESERVE+ALLOWANCE,
        retained_study_bytes_before=used,own_cap=OUTPUT_CAP)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','supervise','worker','export']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='supervise':raise SystemExit(supervise())
    elif sys.argv[1]=='worker':worker()
    else:export()
