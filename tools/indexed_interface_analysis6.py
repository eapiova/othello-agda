#!/usr/bin/env python3
"""Read pinned interface counters; never change or import them into a proof."""
import hashlib
import json
from pathlib import Path

from archive_indexed_support6 import FROZEN, SOURCE
from remote6 import ssh
from run_job import atomic_json
from study6 import Ledger

LABEL='indexed-interface-analysis-20261009'
CODE=r'''
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'tools'))
import assembly6
from interface_census6 import census_file,decompress,warning_fields
from provenance import source_identity,digest_entries
from run_job import atomic_json,utc
runs=root.parent;output=root/'results/indexed-interface-analysis6.json';assert not output.exists()
records={};identities={}
spec=[('indexed-warning-mode-20261009','indexed-cache-mode6','c33de5896ca5bca467469d896241c5e3354255d824b6dddf1027ddce4f60eab9'),
      ('indexed-family-mode-20261009','indexed-family6','c3105af3b5177a686a2f2a33d57c6c42e81bc6fa4fe2df0f0671a9d115d70a6e'),
      ('indexed-named-shapes-fixed-20261009','indexed-shape-mode6','27706d7422fea6e0a9cfe919f93de2be1e3dc4eaf8bcd1eafe3b2f6b41065351')]
for label,folder,expected in spec:
 outer=runs/('six-'+label);check=outer/'results'/folder/'check';report=check.parent/'report.json'
 assert assembly6.sha(report)==expected
 d=json.loads(report.read_text());source=source_identity(check);pool=assembly6.interfaces(check)
 assert d['accepted'] and d['checked_source']==source and digest_entries(pool)==d['last_interface_pool_sha256']
 identities[str(check)]={'source':source,'pool':pool}
 selected=['Part60','Part120']
 if label=='indexed-family-mode-20261009':selected+=['Family','Shape','StateData60','BodyData60']
 for name in selected:
  suffix='/Tests/IndexedWire6/'+name+'.agdai';paths=[n for n in pool if n.endswith(suffix)];assert len(paths)==1
  path=check/paths[0];data=census_file(path,pool[paths[0]])
  data.update(warning_fields(decompress(path.read_bytes())))
  records[label+'/'+name]=data
assert all(source_identity(pathlib.Path(p))==d['source'] and assembly6.interfaces(pathlib.Path(p))==d['pool'] for p,d in identities.items())
result={'format':'othello-indexed-interface-analysis6-v1','created_utc':utc(),'records':records,
 'sources_and_interfaces_unchanged':True,'scope':'read-only encoded counters; no new kernel acceptance or graph-size attribution',
 'initial_problem2_proved':False,'production_authorized':False}
atomic_json(output,result)
print(json.dumps({n:{k:r[k] for k in ('compressed_bytes','payload_bytes','signature_definitions','saved_meta_bindings','node_words','string_characters','lazy_text_bytes','strict_text_bytes','warnings')} for n,r in records.items()}))
'''


def main():
    root=Path(__file__).resolve().parents[1];out=root/'results/remote6'/LABEL
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger(root/'results/study6-ledger.json')
    reservation=ledger.reserve('native',12,LABEL)
    digest=hashlib.sha256(CODE.encode()).hexdigest()
    wrapper='''import json,pathlib,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'tools'))
from run_job import run_job
r=run_job(sys.argv[2],['python3','-c',sys.argv[4],str(root)],root/'results',root=root,
 timeout=40,cpu_limit=10,rss_limit_gib=.5,log_limit_mib=1,reservation_id=sys.argv[3],expected_source_sha256=sys.argv[5],
 metadata={'purpose':'read-only pinned interface counters','inline_code_sha256':sys.argv[6]})
print(json.dumps(r))
'''
    atomic_json(out/'job.json',dict(label=LABEL,host='desktop',remote_root=FROZEN,source_sha256=SOURCE,
                reservation_id=reservation['reservation_id'],category='native',mode='capped read-only interface analysis',
                inline_code_sha256=digest))
    record=json.loads(ssh('desktop',['python3','-c',wrapper,FROZEN,LABEL,reservation['reservation_id'],CODE,SOURCE,digest]).stdout)
    atomic_json(out/(LABEL+'.json'),record);ledger.finish(reservation['reservation_id'],out/(LABEL+'.json'))
    for name in (LABEL+'.log','indexed-interface-analysis6.json'):
        (out/name).write_bytes(ssh('desktop',['cat',FROZEN+'/results/'+name]).stdout)
    print(json.dumps({k:record[k] for k in ('accepted','cpu_seconds','wall_seconds','peak_rss_gib')}))
    if not record['accepted']:raise SystemExit('interface analysis stopped; preserve the receipt')


if __name__=='__main__':main()
