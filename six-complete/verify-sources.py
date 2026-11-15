#!/usr/bin/env python3
"""Read-only identity checks, not an Agda run. Python stdlib only."""
from pathlib import Path
import hashlib,json,sys,zlib

def require(v,m):
    if not v: raise ValueError(m)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def verify(root):
    root=root.resolve();inv=json.loads((root/'SOURCE-INVENTORY.json').read_text());files=inv['files']
    require(len(files)==4129 and inv['selected_count']==4128,'source cardinality')
    actual=set()
    for p in (root/'src').rglob('*'):
        require(not p.is_symlink(),'source symlink')
        if p.is_file() and p.suffix=='.agda':actual.add(p.relative_to(root).as_posix())
    require(actual==set(files),'missing or extra Agda source')
    selected={};modules={}
    for name,r in files.items():
        rel=Path(name);require(not rel.is_absolute() and '..' not in rel.parts,'unsafe path')
        require(name=='src/'+r['module'].replace('.','/')+'.agda','module path')
        require(r['module'] not in modules,'duplicate module');modules[r['module']]=r
        p=root/name;require(type(r['bytes']) is int and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'source identity: '+name)
        if r['provider']!='final-wrapper':selected[r['module']]=r['sha256']
    audit=json.loads((root/'evidence/source-audit.json').read_text())
    require(len(selected)==4128 and digest(selected)==audit['source_inventory_sha256']==inv['historical_inventory_sha256'],'accepted inventory binding')
    require(sum(r['bytes'] for r in modules.values() if r['provider']!='final-wrapper')==audit['selected_source_bytes']==837183925,'byte count')
    g=json.loads(zlib.decompress((root/'DEPENDENCY-GRAPH.json.zlib').read_bytes()))
    require({n:r['sha256'] for n,r in g['selected_modules'].items()}==selected,'graph identities')
    seen=set();todo=['Tests.CompleteUpperRows6.Result'];builtins=set(inv['builtin_modules'])
    while todo:
        n=todo.pop()
        if n in seen or n in builtins:continue
        require(n in selected,'unresolved dependency '+n);seen.add(n);todo.extend(g['dependency_edges'][n])
    require(seen==set(selected),'exact closure')
    receipt=json.loads((root/'evidence/checker-receipt.json').read_text())
    w='src/Tests/FinalProblem2Check6.agda';identity=digest({'othello.agda-lib':sha(root/'othello.agda-lib'),w:sha(root/w)})
    require(identity==receipt['wrapper_source_identity']['source_sha256']==inv['wrapper_source_identity'],'wrapper identity')
    require(receipt['accepted'] is True and type(receipt['exit_code']) is int and receipt['exit_code']==0,'historical checker acceptance')
    c=json.loads((root/'evidence/completion.json').read_text())
    for key,n in [('actual_final_theorem_report','theorem-report.json'),('actual_checker_record','checker-receipt.json'),('source_audit','source-audit.json')]:require(sha(root/'evidence'/n)==c[key]['sha256'],'completion pin '+key)
    report=json.loads((root/'evidence/theorem-report.json').read_text())
    require(report['Problem2_checked'] is True and report['same_optimal_pair_black16_white20'] is True,'endpoint acceptance')
    print(json.dumps({'verified':True,'selected_modules':4128,'with_wrapper':4129,'dependency_closure_exact':True,'Agda_executed':False,'cold_rebuild_performed':False,'Problem3_complete':False}))
if __name__=='__main__':
    try:verify(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent)
    except Exception as e:print('VERIFICATION FAILED: '+str(e),file=sys.stderr);sys.exit(1)
