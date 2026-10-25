import sys, json, random, time, statistics, platform, subprocess, os, itertools
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src/Python'), str(ROOT/'tools')]
import algorithms as a
from public_validate import check
T = ROOT/'tests'
records = []

def verify(x, expected, reason):
    y = getattr(a, x['task'])(x)
    assert check(x, y, expected), (x, y, expected)
    records.append({'input': x, 'expected': expected, 'actual': y, 'reason': reason})
    return y

for task in ['dsu','kruskal','prim','scc','topo']:
    expected = {'dsu':{'states':[]},'kruskal':{'cost':0,'edge_ids':[],'components':0},'prim':{'cost':0,'edge_ids':[],'components':0},'scc':{'component':[],'condensation':[]},'topo':{'acyclic':True,'order':[]}}[task]
    verify({'task':task,'n':0,'operations':[],'edges':[]}, expected, 'Empty graph has no components or operations.')
verify({'task':'dsu','n':4,'operations':[[0,0],[0,1],[1,0],[2,3],[1,3]]}, {'states':[[4,1],[3,2],[3,2],[2,2],[1,4]]}, 'Only unions between distinct sets change counts.')
for task in ['kruskal','prim']:
    verify({'task':task,'n':5,'edges':[[0,0,-99],[0,1,3],[0,1,-4],[1,2,2],[0,2,2],[3,3,-8]]}, {'cost':-2,'components':3}, 'Component 0,1,2 needs weights -4 and 2; 3 and 4 are isolates.')
verify({'task':'scc','n':5,'edges':[[0,1],[1,0],[1,2],[1,2],[2,2],[3,4]]}, {'component':[0,0,1,2,3]}, 'Only 0 and 1 are mutually reachable; condensation deduplicates 1->2.')
verify({'task':'topo','n':4,'edges':[[0,1],[2,3],[3,2]]}, {'acyclic':False,'order':[]}, 'Disconnected component contains a cycle.')
verify({'task':'dag','n':4,'source':0,'edges':[[0,1,1],[2,3,-1],[3,2,0]]}, {'acyclic':False,'distance':[],'parent_edge':[]}, 'Cycle outside source reachability still invalidates the whole graph.')
x={'task':'dag','n':5,'source':0,'edges':[[0,1,3],[0,1,3],[0,2,8],[1,2,-7],[2,3,4]]}
y=verify(x, {'acyclic':True,'distance':[0,3,-4,0,None],'parent_edge':[-1,0,3,4,-1]}, 'Relaxation gives 3,-4,0; vertex 4 is unreachable; parallel edges tie.')
routes=[]
for target, expected in [(3,[0,1,2,3]),(0,[0]),(4,[]),(1,[0,1])]:
    route=a.reconstruct_route(x['edges'],y['parent_edge'],0,target)
    assert route==expected
    ids=[y['parent_edge'][v] for v in route[1:]]
    weight=sum(x['edges'][i][2] for i in ids)
    if route: assert weight==y['distance'][target]
    routes.append({'target':target,'route':route,'edge_ids':ids,'cost':weight if route else None})
(T/'routes.json').write_text(json.dumps({'request':x,'answer':y,'calls':routes},indent=2))

witness=[]
for task,x,e,valid,invalid in [
 ('forest',{'task':'kruskal','n':3,'edges':[[0,1,1],[1,2,1],[0,2,1]]},{'cost':2,'components':1},{'cost':2,'components':1,'edge_ids':[0,2]},{'cost':2,'components':1,'edge_ids':[0,0]}),
 ('scc',{'task':'scc','n':3,'edges':[[0,1],[1,0],[1,2]]},{'component':[0,0,1]},{'component':[8,8,9],'condensation':[[8,9]]},{'component':[8,8,8],'condensation':[]}),
 ('topo',{'task':'topo','n':3,'edges':[[0,2],[1,2]]},{'acyclic':True},{'acyclic':True,'order':[1,0,2]},{'acyclic':True,'order':[2,0,1]}),
 ('dag',{'task':'dag','n':2,'source':0,'edges':[[0,1,2],[0,1,2]]},{'acyclic':True,'distance':[0,2]},{'acyclic':True,'distance':[0,2],'parent_edge':[-1,1]},{'acyclic':True,'distance':[0,2],'parent_edge':[-1,-1]})]:
    assert check(x,valid,e) and not check(x,invalid,e)
    witness.append({'kind':task,'input':x,'expected':e,'alternative_valid':valid,'invalid':invalid,'accepted_valid':True,'rejected_invalid':True})
print(json.dumps({'witness_checks': witness}, indent=2))

rng=random.Random(31025)
for trial in range(60):
    n=rng.randrange(1,7)
    edges=[[rng.randrange(n),rng.randrange(n),rng.randrange(-5,6)] for _ in range(rng.randrange(9))]
    groups=[{i} for i in range(n)]
    for u,v,w in edges:
        gu=next(s for s in groups if u in s); gv=next(s for s in groups if v in s)
        if gu is not gv: gu.update(gv); groups.remove(gv)
    c=len(groups); best=None
    for ids in itertools.combinations(range(len(edges)),n-c):
        sets=[{i} for i in range(n)]; cost=0; ok=True
        for i in ids:
            u,v,w=edges[i]; su=next(s for s in sets if u in s); sv=next(s for s in sets if v in s)
            if su is sv: ok=False; break
            su.update(sv); sets.remove(sv); cost+=w
        if ok and (best is None or cost<best): best=cost
    for task in ['kruskal','prim']:
        verify({'task':task,'n':n,'edges':edges},{'cost':best,'components':c},'Independent exhaustive enumeration of every possible forest on a small graph.')

(T/'my_cases.jsonl').write_text(''.join(json.dumps(r['input'])+'\n' for r in records))
(T/'expected.jsonl').write_text(''.join(json.dumps(r['expected'])+'\n' for r in records))
(T/'actual.jsonl').write_text(''.join(json.dumps(r['actual'])+'\n' for r in records))
(T/'case_reasons.json').write_text(json.dumps([r['reason'] for r in records],indent=2))
requests=[r['input'] for r in records]*2
p=subprocess.run([sys.executable,str(ROOT/'src/Python/main.py')],input=''.join(json.dumps(x)+'\n' for x in requests),text=True,capture_output=True,check=True)
answers=[json.loads(line) for line in p.stdout.splitlines()]
assert len(answers)==len(requests)
assert all(check(x,y,r['expected']) for x,y,r in zip(requests,answers,records*2))

scale=[]
n=100000
operations=[[i,i+1] for i in range(n-1)]
operations += [[0,0]]*(250000-len(operations))
y=a.dsu({'n':n,'operations':operations}); assert y['states'][-1]==[1,n]
scale.append({'task':'dsu','n':n,'q':len(operations),'last_state':y['states'][-1]})
edges=[[i,i+1,10**9] for i in range(n-1)]
edges += [[0,n-1,10**9]]*(250000-len(edges))
for task in ['kruskal','prim']:
    y=getattr(a,task)({'n':n,'edges':edges})
    assert check({'task':task,'n':n,'edges':edges},y,{'cost':(n-1)*10**9,'components':1})
    scale.append({'task':task,'n':n,'m':len(edges),'cost':y['cost'],'selected':len(y['edge_ids'])})
directed=[[u,v] for u,v,w in edges]
y=a.scc({'n':n,'edges':directed}); assert len(set(y['component']))==n and len(y['condensation'])==n-1+1
scale.append({'task':'scc','n':n,'m':len(directed),'components':n,'condensation':len(y['condensation'])})
y=a.topo({'n':n,'edges':directed}); assert y=={'acyclic':True,'order':list(range(n))}
scale.append({'task':'topo','n':n,'m':len(directed),'order_length':len(y['order'])})
weighted=[[u,v,-10**9] for u,v in directed]
y=a.dag({'n':n,'edges':weighted,'source':0}); assert y['distance']==[-i*10**9 for i in range(n)]
assert a.reconstruct_route(weighted,y['parent_edge'],0,n-1)==list(range(n))
scale.append({'task':'dag','n':n,'m':len(weighted),'last_distance':y['distance'][-1],'route_length':n})
(T/'scale_results.json').write_text(json.dumps(scale,indent=2))

benchmark=[]
for n,m in [(1000,2500),(10000,25000),(100000,250000)]:
    rng=random.Random(31025+n)
    edges=[[i,i+1,rng.randint(-10**9,10**9)] for i in range(n-1)]
    edges += [[rng.randrange(n),rng.randrange(n),rng.randint(-10**9,10**9)] for _ in range(m-len(edges))]
    request={'n':n,'edges':edges}
    k=a.kruskal(request); p=a.prim(request)
    assert k['cost']==p['cost'] and k['components']==p['components']
    for task,y in [('kruskal',k),('prim',p)]:
        assert check(dict(request,task=task),y,k)
    row={'n':n,'m':m,'seed':31025+n,'cost':k['cost']}
    for task in ['kruskal','prim']:
        fn=getattr(a,task)
        fn(request)
        samples=[]
        for _ in range(3):
            start=time.perf_counter(); fn(request); samples.append(time.perf_counter()-start)
        row[task]={'seconds':samples,'median':statistics.median(samples)}
    benchmark.append(row)
env={'python':sys.version,'platform':platform.platform(),'processor':platform.processor(),'logical_cpus':os.cpu_count(),'timer':'time.perf_counter','warmup':'one untimed call per method per size; correctness calls also precede timing','boundary':'Entire algorithm function including adjacency/DSU construction and result construction; excludes input generation, JSON parsing, IO, validation and compilation.'}
(T/'benchmark_results.json').write_text(json.dumps({'environment':env,'results':benchmark},indent=2))
print(json.dumps({'own_cases':len(records),'mixed_requests':len(requests),'scale':scale,'benchmark':benchmark},indent=2))
