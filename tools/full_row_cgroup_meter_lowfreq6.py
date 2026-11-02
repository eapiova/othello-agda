"""Low-frequency derivative of the full-row service meter; same 4 CPU cap.

The original source is retained unchanged.

No checker, ledger write, source mutation or restart. This records the service's
whole cgroup CPU, including its supervisor, so manual reconciliation can retain
wait4 evidence and account separately for CPU outside the reaped child tree.
The meter itself is bounded by the existing parent controller allowance.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

from run_job import atomic_json, utc

ROOT=Path(__file__).resolve().parents[1]
PRODUCTION=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/full-row-production6-20261018')
OUT=PRODUCTION/'meter-lowfreq'
UNIT='othello6-full-row-meter-lowfreq6-20261018.service'
CPU_LIMIT=4
OUTPUT_CAP=64*1024


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sample(path):
    values=dict(line.split() for line in (path/'cpu.stat').read_text().splitlines())
    return {key:int(values[key]) for key in ['usage_usec','user_usec','system_usec']}


def save(name,data):
    atomic_json(OUT/name,data)
    assert sum(p.stat().st_blocks*512 for p in OUT.iterdir() if p.is_file())<OUTPUT_CAP


def worker():
    plan=json.loads((OUT/'plan.json').read_text())
    assert sha(Path(__file__))==plan['helper_sha256']
    group=Path(plan['cgroup']);identity=plan['cgroup_inode']
    last=None;last_time=None;last_save=0;failure=None;terminal=None
    try:
        while True:
            try:
                assert group.stat().st_ino==identity,'cgroup identity changed'
                current=sample(group)
            except FileNotFoundError:
                break
            assert last is None or current['usage_usec']>=last['usage_usec']
            last=current;last_time=time.monotonic()
            if last_time-last_save>=60:
                usage=resource.getrusage(resource.RUSAGE_SELF)
                save('last-sample.json',dict(recorded_utc=utc(),service=plan['service'],
                    cgroup_cpu=current,meter_own_cpu_seconds=usage.ru_utime+usage.ru_stime,
                    wait4_child_record=plan['outer_record'],ledger_write_performed=False))
                last_save=last_time
            time.sleep(10)
            # A cgroup can persist empty briefly after service termination.
            if (group/'cgroup.events').exists():
                events=dict(line.split() for line in (group/'cgroup.events').read_text().splitlines())
                if events.get('populated')=='0':
                    try:last=sample(group);last_time=time.monotonic()
                    except FileNotFoundError:pass
                    break
        assert last is not None,'no cgroup CPU sample obtained'
        done=subprocess.run(['systemctl','--user','show',plan['service'],
            '--property=CPUUsageNSec,ActiveState,SubState'],capture_output=True,text=True)
        props=dict(line.split('=',1) for line in done.stdout.splitlines() if '=' in line)
        raw=props.get('CPUUsageNSec','')
        candidate=int(raw)/1e9 if raw.isdigit() and int(raw)<2**63 else None
        exact=candidate is not None and candidate+1e-6>=last['usage_usec']/1e6
        total=candidate if exact else last['usage_usec']/1e6+max(0,time.monotonic()-last_time)+1
        path=Path(plan['outer_record']);child=json.loads(path.read_text()) if path.exists() else None
        terminal=dict(recorded_utc=utc(),accepted=True,service=plan['service'],
            terminal_service_properties=props,last_cgroup_cpu=last,
            whole_service_cpu_seconds=total,whole_service_cpu_is_exact=exact,
            cpu_evidence_source='systemd CPUUsageNSec' if exact else
                'conservative bound: last cgroup usage + monotonic gap +1s at CPUQuota100percent',
            outer_record=str(path),outer_record_sha256=sha(path) if child is not None else None,
            outer_wait4_cpu_seconds=child['cpu_seconds'] if child is not None else None,
            uncharged_supervisor_cpu_upper_bound_seconds=max(0,total-child['cpu_seconds'])
                if child is not None else None,
            ledger_write_performed=False,
            reconciliation='Finish the terminal outer wait4 reservation exactly once, then withhold the positive service-minus-wait4 residual from kernel inside the same original50000-second stage envelope. Never charge nested checker records again.',
            mathematical_objective_complete=False)
    except BaseException as error:
        failure=repr(error)
        terminal=dict(recorded_utc=utc(),accepted=False,failure=failure,
            last_cgroup_cpu=last,ledger_write_performed=False,
            mathematical_objective_complete=False)
    usage=resource.getrusage(resource.RUSAGE_SELF)
    terminal['meter_own_cpu_seconds']=usage.ru_utime+usage.ru_stime
    terminal['meter_cpu_hard_cap_seconds']=CPU_LIMIT
    terminal['meter_covered_by_parent_allowance']=plan['parent_allowance_receipt']
    save('report.json',terminal)
    assert failure is None,failure


def launch():
    assert not OUT.exists()
    current=json.loads((ROOT/'results/full-row-production-current6-20261018.json').read_text())
    service=current['unit']
    props=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','--user',
        'show',service,'--property=ActiveState,ControlGroup,MainPID,CPUQuotaPerSecUSec'],
        text=True).splitlines() if '=' in line)
    assert props['ActiveState']=='active' and int(props['MainPID'])>0
    group=Path('/sys/fs/cgroup')/props['ControlGroup'].lstrip('/')
    assert (group/'cpu.max').read_text().split()==['100000','100000']
    OUT.mkdir()
    plan=dict(recorded_utc=utc(),service=service,cgroup=str(group),cgroup_inode=group.stat().st_ino,
        helper_sha256=sha(Path(__file__)),outer_record=current['terminal_outer_record'],
        parent_allowance_receipt=str(ROOT/'results/full-row-production-controller-allowance6-20261018.json'),
        cpu_hard_cap_seconds=CPU_LIMIT,own_output_cap_bytes=OUTPUT_CAP,
        no_proof_or_ledger_mutation=True,all_output_counted_inside_active_production_scratch=True)
    save('plan.json',plan)
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=64M',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=LimitCPU='+str(CPU_LIMIT),
        '--property=CPUQuota=5%','--property=TasksMax=8','--property=RuntimeMaxSec=65000',
        '--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__)),'worker']
    done=subprocess.run(args,capture_output=True,text=True)
    save('dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr))
    assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,observed_service=service,first_cpu_sample=sample(group))))


if __name__=='__main__':
    assert len(sys.argv)==2
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise ValueError(sys.argv[1])
