"""Fixed upper-only timing estimator; predict group 9 before checking it."""
import itertools

from global_assembly6 import partition,tokens


def features(plan,groups):
    entries={e['state']:e for e in plan['entries']};rows=[]
    for group in groups:
        seen,todo=set(),list(group['roots'])
        while todo:
            state=todo.pop()
            if state not in seen:
                seen.add(state);todo.extend(entries[state]['references'])
        local=[e for e in plan['entries'] if e['state'] in seen]
        parts,owners=partition(local,32000,150);ancestors=[]
        if len(parts)!=group['parts']:raise ValueError('different part partition')
        for j,part in enumerate(parts):
            inherited={owners[r] for e in part for r in e['references'] if owners[r]!=j}
            for parent in list(inherited):inherited.update(ancestors[parent])
            ancestors.append(inherited)
            row=dict(group=group['index'],part=j,tokens=sum(tokens(e['certificate']) for e in part),
                     own_exports=len(part),imported_exports=sum(len(parts[p]) for p in inherited))
            row['x']=[row['tokens']/1000,row['own_exports']/150,row['imported_exports']/1000,1]
            rows.append(row)
    return rows


def solve(a,b):
    matrix=[list(row)+[y] for row,y in zip(a,b)];n=len(matrix)
    for col in range(n):
        pivot=max(range(col,n),key=lambda r:abs(matrix[r][col]))
        if abs(matrix[pivot][col])<1e-10:return None
        matrix[col],matrix[pivot]=matrix[pivot],matrix[col]
        value=matrix[col][col];matrix[col]=[v/value for v in matrix[col]]
        for r in range(n):
            if r!=col:
                factor=matrix[r][col]
                matrix[r]=[v-factor*w for v,w in zip(matrix[r],matrix[col])]
    return [row[-1] for row in matrix]


def predict(plan,report):
    if report['completed_groups']!=list(range(9)) or any(p['label'].startswith('group9-') for p in report['phases']):
        raise ValueError('held-out checks must not have started')
    measured={p['label']:p for p in report['phases']};rows=features(plan,report['groups'])
    training=[]
    for row in rows:
        if row['group']==9:continue
        phase=measured[f"group{row['group']}-part{row['part']}"]
        if not phase['accepted']:raise ValueError('incomplete training part')
        training.append(dict(row,cpu_seconds=phase['cpu_seconds']))
    best=None
    for count in range(1,5):
        for active in itertools.combinations(range(4),count):
            a=[[sum(r['x'][i]*r['x'][j] for r in training) for j in active] for i in active]
            b=[sum(r['x'][i]*r['cpu_seconds'] for r in training) for i in active]
            fitted=solve(a,b)
            if fitted is None or min(fitted)<-1e-9:continue
            coeff=[0.0]*4
            for i,value in zip(active,fitted):coeff[i]=max(0,value)
            error=sum((sum(c*x for c,x in zip(coeff,r['x']))-r['cpu_seconds'])**2 for r in training)
            if best is None or error<best[0]:best=(error,coeff)
    if best is None:raise ValueError('no timing fit')
    heldout=[dict(r,predicted_cpu_seconds=sum(c*x for c,x in zip(best[1],r['x']))) for r in rows if r['group']==9]
    return dict(format='othello-warning-upper-cost6-v1',training_groups=list(range(9)),heldout_groups=[9],
        training_parts=len(training),heldout_parts=len(heldout),coefficients=best[1],
        estimator='four-feature nonnegative least squares, fixed before this queue',
        coefficient_units=['s/1000 certificate tokens','s/150 own exports','s/1000 transitive imported exports','s fixed'],
        training_squared_error=best[0],heldout_measured_when_fitted=False,
        heldout_predicted_cpu_seconds=sum(r['predicted_cpu_seconds'] for r in heldout),heldout_rows=heldout,
        scope='upper-only part cost; groups, collector, lower side and production excluded',
        two_sided_production_gate_passed=False,production_authorized=False)
