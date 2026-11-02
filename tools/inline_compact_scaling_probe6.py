"""Bounded safe step-only assembly checks, private build and read-only donor pools."""
import sys
import json
from pathlib import Path
import shutil
import subprocess
import contextlib
import fcntl

import citation_diagnostic6 as common
import assembly6
import completion_batch6 as batch
from provenance import source_identity
from run_job import atomic_json,run_job,build_lock,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
SECOND=len(sys.argv)==2 and sys.argv[1].endswith('-fixed2')
if SECOND:sys.argv[1]=sys.argv[1][:-1]
RECOVERY=len(sys.argv)==2 and sys.argv[1].endswith('-fixed')
if RECOVERY:sys.argv[1]=sys.argv[1][:-6]
OUT=ROOT/'results'/('inline-compact-scaling6-20261018-fixed2' if SECOND else ('inline-compact-scaling6-20261018-fixed' if RECOVERY else 'inline-compact-scaling6-20261018'))
CHECK=OUT/'check'
UNIT='othello6-'+OUT.name+'.service'
TARGETS=['Tests/InlineCompactScaling6/Training','Tests/InlineCompactScaling6/Holdout']
HARD=3
RESERVE=45 if SECOND else (55 if RECOVERY else 70)
OUTER=25 if SECOND else (35 if RECOVERY else 60)
common.OUT=OUT;common.HARD_GIB=HARD;common.RESERVATION_CPU=RESERVE


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text());expected={Path(k):tuple(v) for k,v in plan['donors'].items()}
    assert all(common.sha(ROOT/'tools'/n)==h for n,h in plan['helpers'].items())
    with contextlib.ExitStack() as stack:
        for donor in expected:
            f=stack.enter_context((donor/'_build/.study6.lock').open('rb'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stack.enter_context(build_lock(CHECK));stack.enter_context(common.watched())
        before=batch.donor_snapshot(expected);assert source_identity(CHECK)==plan['source'] and not assembly6.interfaces(CHECK)
        phases={}
        for name in TARGETS:
            common.storage(8*2**20)
            args=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(CHECK),str(CHECK),'--proc','/proc','--dev-bind','/dev','/dev','--tmpfs','/tmp','--die-with-parent','--',batch.full_map.AGDA,'--no-libraries','-i','src']
            for donor in expected:args+=['-i',str(donor/'src')]
            args+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules','src/'+name+'.agda','+RTS','-M2G','-s','-RTS']
            r=run_job(name.replace('/','-').lower(),args,OUT/'records',root=CHECK,timeout=240,cpu_limit=25,rss_limit_gib=2.75,log_limit_mib=2,expected_source_sha256=plan['source']['source_sha256'],metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,conditional_theorem_only=True))
            phases[name]={k:r[k] for k in ['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']};atomic_json(OUT/'phase-summary.json',phases)
            if not r['accepted']:break
            from inline_compact_scaling6 import summarize
            phase='training' if name.endswith('/Training') else 'holdout'
            if phase=='holdout':
                assert common.sha(OUT/'forecast-freeze.json')==json.loads((OUT/'holdout-freeze-pin.json').read_text())['sha256']
            summarize(OUT,phase)
            if phase=='training':atomic_json(OUT/'holdout-freeze-pin.json',dict(created_utc=utc(),sha256=common.sha(OUT/'forecast-freeze.json')))
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        intact=batch.donor_snapshot(expected)==before;p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items());same=source_identity(CHECK)==plan['source']
        complete=len(phases)==len(TARGETS) and all(x['accepted'] for x in phases.values())
        atomic_json(OUT/'report.json',dict(phases=phases,all_phases_accepted=complete,accepted_donors_unchanged=intact,p1_unchanged=p1,source_unchanged=same,new_distinct_rows=0,initial_bounds_proved=False,inline_component_calibration_checked=complete,conditional_existing_rows=1400 if complete else 0,mathematical_objective_complete=False,finished_utc=utc()))
        assert intact and p1 and same and complete,'step assembly probe failed; retain exact receipts'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    r=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker-fixed2' if SECOND else ('worker-fixed' if RECOVERY else 'worker')],OUT/'records',root=OUT/'control',timeout=580,cpu_limit=OUTER,rss_limit_gib=2.9,log_limit_mib=2,reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if r['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA
    assert not common.disjoint_checkers()
    live=subprocess.check_output(['systemctl','--user','list-units','--state=activating,running','--type=service','--no-legend','--plain','othello*'],text=True).strip().splitlines()
    assert len(live)<=1 and all(('othello6-reuse-query-layout-lower6-20261018.service' in line or 'othello6-global-reuse-layout-lower6-20261018.service' in line) for line in live),'defer calibration until at most one6GiB native group remains'
    for line in live:
        native_unit=line.strip().split()[0]
        limit=subprocess.check_output(['systemctl','--user','show',native_unit,'-pMemoryMax','--value'],text=True).strip()
        assert int(limit)<=6*2**30
    # At most one native group has6GiB; checker3GiB, combined9GiB below12GiB.
    common.storage(16*2**20)
    from inline_compact_scaling6 import emit
    emit(CHECK)
    shutil.copy2(ROOT/'othello.agda-lib',CHECK/'othello.agda-lib')
    previous=ROOT/'results/inline-entries-probe6-20261018';prior=json.loads((previous/'plan.json').read_text());expected=prior['donors']
    for name in ['inline-entries-probe6-20261018','encoded-step-assembly-probe6-20261018','inline-scaling6-20261018']:
        accepted=ROOT/'results'/name;closed=json.loads((accepted/'closure.json').read_text());assert closed['accepted']
        expected[str(accepted/'check')]=[closed['source_sha256'],closed['interface_pool_sha256']]
    helpers=['inline_scaling6.py','unicode_codec_probe6.py','inline_compact_scaling6.py','directed_probe6.py','directed_scaling6.py','bench6.py','compact_shared6.py','direct_rows_probe6.py','sparse_citation_pilot6.py','inline_compact_scaling_probe6.py','citation_diagnostic6.py','run_job.py','study6.py','provenance.py','completion_batch6.py','assembly6.py']
    atomic_json(OUT/'plan.json',dict(created_utc=utc(),source=source_identity(CHECK),donors=expected,helpers={n:common.sha(ROOT/'tools'/n) for n in helpers},helper_sha256={n:common.sha(ROOT/'tools'/n) for n in helpers},hard_memory_gib=HARD,swap_bytes=0,core_bytes=0,reservation=RESERVE,scope_cpu_cap=200,phase_cpu_cap=25,parallel_native_hard_gib=6,total_hard_memory_gib=9,conditional_theorem_only=True))
    control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    ledger=Ledger(ROOT/'results/study6-ledger.json');summary=Ledger.summary(json.loads(ledger.path.read_text()))
    assert all(x['job'] in ['reuse-query-layout-lower6','global-reuse-layout-lower6'] for x in summary['outstanding'].values())
    if RECOVERY:
        prior=ROOT/'results/inline-compact-scaling6-20261018'
        closed=json.loads((prior/'closure.json').read_text())
        additional=json.loads((ROOT/'results/inline-compact-scaling6-20261018-fixed/closure.json').read_text())['charged_cpu_seconds'] if SECOND else 0
        assert not closed['accepted'] and closed['charged_cpu_seconds']+additional+RESERVE+20<=200
        allowance=dict(reused_from=str(prior/'job.json'),additional_withholding_seconds=0)
    else:
        previous=ROOT/'results/inline-scaling6-20261018'
        closed=json.loads((previous/'closure.json').read_text());assert closed['accepted'] and closed['charged_cpu_seconds']+RESERVE+20<=200
        allowance=dict(reused_from=str(previous/'job.json'),additional_withholding_seconds=0)
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=source_identity(control),unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group','--property=RuntimeMaxSec=620','--property=WorkingDirectory='+str(control),'--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),'/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise-fixed2' if SECOND else ('supervise-fixed' if RECOVERY else 'supervise')]
    done=subprocess.run(args,capture_output=True,text=True);atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0;print(json.dumps(dict(unit=UNIT,reservation=reservation)))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
