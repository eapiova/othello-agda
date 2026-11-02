#!/usr/bin/env python3
"""User-approved LOWER full data-map pilot only; never game-row production."""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading

from run_job import atomic_json, build_lock, run_job, utc
from provenance import source_identity, digest_entries
import assembly6
from wire_workflow6 import require

FLAG = '--approved-full-map6-20261016'
BASE = Path('/home/eapiova/projects/othello-agda/runs')
NATIVE_ROOT = BASE/'six-wire-layout-initial-20261009/results/initial-layout6'
TT_ROOT = BASE/'six-native-lower20-resume-20261006'
OUT = Path('results/full-map-pilot6')
GIB = 2**30


def storage(root, extra=0):
    used = int(subprocess.check_output(['du','-s','-B1',str(root.parent)],text=True).split()[0])
    free = shutil.disk_usage(root).free
    require(used+extra < 12*GIB and free-extra >= 80*GIB,
            'approved full-map storage limit reached; originals retained')
    return dict(allocated_study_bytes=used,free_bytes=free,reserved_extra_bytes=extra,
                artifact_cap_bytes=12*GIB,free_floor_bytes=80*GIB,checked_utc=utc())


@contextlib.contextmanager
def watched_storage(root, out):
    """Independent watcher interrupts the measured child runner on a breach."""
    stop = threading.Event()
    errors = []
    def watch():
        while not stop.wait(15):
            try:
                atomic_json(out/'storage.json',storage(root,64*2**20))
            except BaseException as error:
                errors.append(str(error))
                os.kill(os.getpid(),signal.SIGTERM)
                return
    thread = threading.Thread(target=watch,daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set();thread.join()
        if errors:
            atomic_json(out/'storage-stop.json',dict(errors=errors,finished_utc=utc()))
    require(not errors,'storage monitor stopped this pilot')


def native_command():
    return ['python3','tools/wire_layout6.py','run','--counts-only',
        '--build',str(NATIVE_ROOT/'pinned'),'--tests',str(NATIVE_ROOT/'pinned-tests.json'),
        '--donor',str(TT_ROOT),'--output',str(OUT/'native.json'),
        '--direction','lower','--native-cpu','900','--max-states','70000000',
        '--inline-limit','256','--max-entries','200','--max-tokens','32000',
        '--layout-limit-mib','512','--wire-output',str(OUT/'initial-lower.wire'),
        '--wire-limit-mib','512']



NATIVE_EXPORT = BASE/'six-full-map-lower-native-20261016'/OUT
GENERATED = BASE/'six-full-map-lower-generate-20261016'/OUT
DONOR = BASE/'six-initial-lower-global-named-resume-20261012/results/initial-lower-global-named6/check'
DONOR_REPORT_SHA = 'd9b784fa425dfa284c550ecaad3305580de471d05754933d1cc9f81a68412220'
DONOR_SOURCE_SHA = 'a6726ce3ab43200d4a35c1fd2e68b3618c45665f2bb990e48be60fc3a39ecc3e'
DONOR_POOL_SHA = 'f0416d11b483c8bf26cdbd86b9adac8b2a5269ae892ea5d6bb3ee8d7eb7ed9e7'
AGDA = '/nix/store/xk75yxsl8rbkkq5g81xli5993k7h7xzh-Agda-2.9.0-bin/bin/agda'
AGDA_SHA = 'c4c5dc2617e7bcb759f0a197b679480e4296d79ea0f78de430e8268b1a02b842'


def closed_phase(out, label):
    root=out.parents[1]
    receipt=json.loads((root/'results'/(label+'.json')).read_text())
    require(receipt['accepted'] and receipt['exit_code']==0 and receipt['stop_reason'] is None
            and receipt['source_unchanged'] and receipt['expected_source_matches']
            and receipt['machine']=='eapiova'
            and source_identity(root)['source_sha256']==receipt['source_sha256'],
            'completed unchanged-source desktop phase required')
    return receipt


def checked_native():
    closed_phase(NATIVE_EXPORT, 'full-map-lower-native-20261016')
    report=json.loads((NATIVE_EXPORT/'native.json').read_text())
    count=report['counts']
    require(report['layout_complete'] and report['wire_complete']
            and report['root_key']=='initial' and report['request']['direction']=='lower'
            and report['request']['threshold']==4 and report['table_unchanged']
            and report['donor_unchanged'] and report['table_sha256']=='7886f35fc835b64ad458e7ccb91475200bf44e4065e8d707d1a6ebcee61497d8'
            and count['layout_records']==6873047 and count['layout_parts']==34366
            and count['layout_source_wire_bytes']==498606513
            and count['layout_max_part_tokens']<32000
            and (NATIVE_EXPORT/'initial-lower.wire').stat().st_size==498606513,
            'complete pinned LOWER native layout required')
    return report


def donor_identity():
    require(assembly6.sha(DONOR.parent/'report.json')==DONOR_REPORT_SHA,
            'accepted donor report differs')
    report=json.loads((DONOR.parent/'report.json').read_text())
    source=source_identity(DONOR)
    pool=assembly6.interfaces(DONOR)
    require(report['accepted'] and source==report['checked_source']
            and source['source_sha256']==DONOR_SOURCE_SHA
            and digest_entries(pool)==DONOR_POOL_SHA,
            'accepted same-machine data donor source/interfaces changed')
    machine=assembly6.machine_identity(AGDA)
    require(machine['hostname']=='eapiova' and machine['agda_sha256']==AGDA_SHA
            and all(report['machine'][k]==machine[k]
                for k in ('hostname','agda_path','agda_sha256','agda_version')),
            'same accepted compiler required')
    return report,source,pool,machine


def generate_worker(root,out):
    import re
    from full_state_map6 import generate
    native=checked_native()
    with build_lock(DONOR):
        prior,source,pool,machine=donor_identity()
        reuse={}
        for j in prior['layout']['needed_parts']:
            module=prior['layout']['sample_prefix']+'.StateData'+str(j)
            path=DONOR/'src'/(module.replace('.','/')+'.agda')
            matched=re.search(r'^text = "([^"\n]*)"$',path.read_text(),re.M)
            require(matched is not None,'accepted state literal missing')
            reuse[j]=dict(module=module,text_sha256=hashlib.sha256(matched[1].encode()).hexdigest())
        require(len(reuse)==2702,'expected accepted lower state chunks')
        generated=generate(NATIVE_EXPORT/'initial-lower.wire',out/'check',
            expected_sha256=native['wire_output_sha256'],expected_rows=6873047,
            expected_parts=34366,prefix='Tests.FullInitialLower6',reuse=reuse,map_batch=32)
        require(source_identity(DONOR)==source and assembly6.interfaces(DONOR)==pool,
                'borrowed donor changed during generation')
        atomic_json(out/'generated.json',dict(complete=True,check_root=str(out/'check'),
            checked_source=source_identity(out/'check'),root_module=generated['root_module'],
            generated_bytes=generated['generated_bytes'],generated_modules=len(generated['generated_sha256'])-1,
            reused_chunks=len(reuse),rows=generated['rows'],parts=generated['parts'],
            donor_source=source,donor_pool_sha256=digest_entries(pool),machine=machine,
            wire_sha256=native['wire_output_sha256'],game_rows_checked=0,
            initial_problem2_proved=False,production_authorized=False,finished_utc=utc()))


def check_maps(root,out):
    from readonly_dependencies6 import command
    closed_phase(GENERATED, 'full-map-lower-generate-20261016')
    generated=json.loads((GENERATED/'generated.json').read_text())
    check=Path(generated['check_root'])
    require(generated['complete'] and check==GENERATED/'check'
            and source_identity(check)==generated['checked_source']
            and not assembly6.interfaces(check),'fresh generated map sources required')
    with build_lock(DONOR):
        prior,source,pool,machine=donor_identity()
        require(source==generated['donor_source']
                and digest_entries(pool)==generated['donor_pool_sha256'],'generation donor differs')
        argv=command(machine,generated['root_module'],check,DONOR)
        require('-M2700M' in argv,'known checker heap option required')
        argv[argv.index('-M2700M')]='-M10G'
        rec=run_job('cold-full-lower-map',argv,out/'records',root=check,
            expected_source_sha256=generated['checked_source']['source_sha256'],
            timeout=2400,cpu_limit=1800,rss_limit_gib=11.5,log_limit_mib=24,
            metadata=dict(own_target_cold=True,checker_binary_sha256=AGDA_SHA,
                borrowed_dependency_root=str(DONOR),game_rows_checked=0,
                initial_problem2_proved=False,production_authorized=False))
        unchanged=source_identity(DONOR)==source and assembly6.interfaces(DONOR)==pool
        atomic_json(out/'agda-result.json',dict(record=rec,donor_unchanged=unchanged,
            rows=generated['rows'],parts=generated['parts'],game_rows_checked=0,
            initial_problem2_proved=False,production_authorized=False,
            generated_interfaces=len(assembly6.interfaces(check)),
            map_checked=bool(rec['accepted'] and unchanged),finished_utc=utc()))
        require(rec['accepted'] and unchanged,'full data-map check did not pass; retained for diagnosis')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase',choices=['native','generate','check','align','rowlink'],required=True)
    p.add_argument(FLAG,action='store_true',required=True)
    p.add_argument('--generate-worker',action='store_true',help=argparse.SUPPRESS)
    args=p.parse_args()
    root=Path.cwd().resolve()
    require(root.parent==BASE,'frozen desktop run required')
    if args.phase=='rowlink':
        job=json.loads((root/'results/remote-job.json').read_text())
        approval=job.get('scope_approval',{})
        require(approval.get('approved') is True and
                approval.get('answer')=='Sì, autorizzo solo questo collegamento' and
                approval.get('cpu_max_seconds')==300 and approval.get('hard_memory_gib')==12
                and approval.get('new_boolean_rows')==0,
                'separate human authorization for row-fact linkage required')
    out=root/OUT
    if args.generate_worker:
        require(args.phase=='generate' and out.is_dir(),'private generator worker only')
        generate_worker(root,out)
        return 0
    out.mkdir(parents=True,exist_ok=False)
    # Serialize all phases of this explicitly approved pilot across frozen roots.
    with (BASE/'.full-map-pilot6.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        initial=storage(root,600*2**20 if args.phase=='native' else 1024*2**20)
        atomic_json(out/'approval.json',dict(approved=True,answer='Sì, autorizzo questo test completo delle mappe',
            total_test_cpu_seconds_max=3600,hard_memory_gib=12,artifact_cap_gib=12,
            free_disk_gib=80,game_rows_checked=0,production_authorized=False,
            initial_problem2_proved=False,created_utc=utc(),storage=initial))
        with watched_storage(root,out):
            if args.phase=='native':
                rec=run_job('native-export',native_command(),out/'records',root=root,
                    timeout=1400,cpu_limit=950,rss_limit_gib=8.25,log_limit_mib=4,
                    metadata=dict(game_rows_checked=0,initial_problem2_proved=False))
                require(rec['accepted'],'native export failed; retained for diagnosis')
            elif args.phase=='generate':
                rec=run_job('stream-generate',['python3','tools/full_map_pilot6.py',
                    '--phase','generate',FLAG,'--generate-worker'],out/'records',root=root,
                    timeout=600,cpu_limit=180,rss_limit_gib=1,log_limit_mib=4)
                require(rec['accepted'],'streaming generation failed; prefix retained')
            elif args.phase=='check':
                check_maps(root,out)
            elif args.phase=='align':
                from full_map_alignment6 import run as align
                align(root,out)
            else:
                from full_row_link6 import run as rowlink
                rowlink(root,out)
        atomic_json(out/'phase-report.json',dict(phase=args.phase,accepted=True,
            game_rows_checked=0,initial_problem2_proved=False,production_authorized=False,
            storage=storage(root),finished_utc=utc()))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
