"""Bounded safe splice/line checks, private build and read-only donor pools."""
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
RECOVERY=len(sys.argv)==2 and sys.argv[1].endswith('-fixed')
if RECOVERY:sys.argv[1]=sys.argv[1][:-6]
OUT=ROOT/'results'/('path-splice-probe6-20261018-fixed' if RECOVERY else 'path-splice-probe6-20261018')
CHECK=OUT/'check'
UNIT='othello6-'+OUT.name+'.service'
TARGETS=['Game/StrategySplice','Game/PathSplice','Othello/PathSplice6']+(['Othello/SpliceLine6'] if RECOVERY else [])
HARD=2
RESERVE=95 if RECOVERY else 150
OUTER=70 if RECOVERY else 125
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
            args+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules','src/'+name+'.agda','+RTS','-M1400M','-s','-RTS']
            r=run_job(name.replace('/','-').lower(),args,OUT/'records',root=CHECK,timeout=140,cpu_limit=35,rss_limit_gib=1.8,log_limit_mib=2,expected_source_sha256=plan['source']['source_sha256'],metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,conditional_theorem_only=True))
            phases[name]={k:r[k] for k in ['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']};atomic_json(OUT/'phase-summary.json',phases)
            if not r['accepted']:break
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        intact=batch.donor_snapshot(expected)==before;p1=all(common.sha(ROOT/n)==h for n,h in history['p1_files'].items());same=source_identity(CHECK)==plan['source']
        complete=len(phases)==len(TARGETS) and all(x['accepted'] for x in phases.values())
        atomic_json(OUT/'report.json',dict(phases=phases,all_phases_accepted=complete,accepted_donors_unchanged=intact,p1_unchanged=p1,source_unchanged=same,new_distinct_rows=0,initial_bounds_proved=False,conditional_same_pair_assembly_checked=complete,mathematical_objective_complete=False,finished_utc=utc()))
        assert intact and p1 and same and complete,'splice probe failed; retain exact receipts'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    r=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker-fixed' if RECOVERY else 'worker'],OUT/'records',root=OUT/'control',timeout=580,cpu_limit=OUTER,rss_limit_gib=1.9,log_limit_mib=2,reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if r['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and common.sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA
    assert not common.disjoint_checkers()
    live=subprocess.check_output(['systemctl','--user','list-units','--state=activating,running','--type=service','--no-legend','--plain','othello*'],text=True).strip().splitlines()
    assert all('othello6-bounded-layout-lower6-20261018.service' in line for line in live),'unexpected active Othello service'
    # Native job has9GiB hard memory; this checker has2GiB, total11<12GiB.
    common.storage(16*2**20)
    CHECK.mkdir(parents=True)
    for name in TARGETS:
        src=ROOT/'src'/(name+'.agda');dst=CHECK/'src'/(name+'.agda');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    shutil.copy2(ROOT/'othello.agda-lib',CHECK/'othello.agda-lib')
    previous=ROOT/'results/inline-entries-probe6-20261018';prior=json.loads((previous/'plan.json').read_text());expected=prior['donors']
    helpers=['path_splice_probe6.py','citation_diagnostic6.py','run_job.py','study6.py','provenance.py','completion_batch6.py','assembly6.py']
    atomic_json(OUT/'plan.json',dict(created_utc=utc(),source=source_identity(CHECK),donors=expected,helpers={n:common.sha(ROOT/'tools'/n) for n in helpers},helper_sha256={n:common.sha(ROOT/'tools'/n) for n in helpers},hard_memory_gib=HARD,swap_bytes=0,core_bytes=0,reservation=RESERVE,scope_cpu_cap=170,phase_cpu_cap=35,parallel_native_hard_gib=9,total_hard_memory_gib=11,conditional_theorem_only=True))
    control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    ledger=Ledger(ROOT/'results/study6-ledger.json');summary=Ledger.summary(json.loads(ledger.path.read_text()))
    assert all(x['job']=='bounded-layout-lower6' for x in summary['outstanding'].values())
    if RECOVERY:
        prior=ROOT/'results/path-splice-probe6-20261018'
        closed=json.loads((prior/'closure.json').read_text());assert not closed['accepted'] and closed['charged_cpu_seconds']+RESERVE+20<=170
        allowance=dict(reused_from=str(prior/'job.json'),additional_withholding_seconds=0)
    else:
        allowance=ledger.withhold('assembly',20,'Strategy splice and conditional SAME-pair line assembly: preparation/audit/closure; no added budget.')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=source_identity(control),unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=2G','--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group','--property=RuntimeMaxSec=620','--property=WorkingDirectory='+str(control),'--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),'/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise-fixed' if RECOVERY else 'supervise']
    done=subprocess.run(args,capture_output=True,text=True);atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0;print(json.dumps(dict(unit=UNIT,reservation=reservation)))

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
