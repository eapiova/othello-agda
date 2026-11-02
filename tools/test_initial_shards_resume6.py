"""Reject mismatched or unreported proofs before reusing a storage-stopped prefix."""
import copy
from pathlib import Path
import unittest

from initial_shards_resume6 import accepted_prefix, argv


class PrefixTests(unittest.TestCase):
    def fixture(self):
        machine = dict(agda_path='/agda', agda_sha256='a', hostname='eapiova')
        source = dict(source_sha256='s')
        names = ['Model'] + ['Routes'+str(i) for i in range(105)] + ['Part'+str(i) for i in range(16)] + ['Root']
        layout = dict(format='othello-initial-global-shards6-v1', side='upper', owned_rows=3125,
                      needed_chunks=3359, owned_parts=list(range(16)), targets=names, prefix='Tests.Global')
        target = 'Tests.Global.Model'
        record = dict(accepted=True, exit_code=0, stop_reason=None, source_unchanged=True,
            expected_source_matches=True, own_target_cold=True, source_sha256='s', expected_source_sha256='s',
            executable_sha256='a', argv=argv(machine,target), machine='eapiova', root='/old', cpu_seconds=2.)
        prior = dict(layout=layout, selected_targets=names, phases=[dict(target=target,record=record,
                     borrowed_interfaces_unchanged=True)], assembly_cpu_seconds=2.)
        pool = {'_build/2.9/agda/src/Tests/Global/Model.agdai':'hash'}
        return prior,pool,source,machine,Path('/old')

    def test_valid_contiguous_prefix(self):
        f = self.fixture()
        targets, phases = accepted_prefix(*f)
        self.assertEqual(len(targets),123)
        self.assertEqual(len(phases),1)

    def test_corrupt_record_and_cache(self):
        for key,value in [('accepted',False),('own_target_cold',False),('source_sha256','wrong'),
                          ('executable_sha256','wrong'),('root','/other'),('argv',['agda']),('cpu_seconds',3.)]:
            f=list(copy.deepcopy(self.fixture()));f[0]['phases'][0]['record'][key]=value
            with self.subTest(key=key), self.assertRaises(ValueError):accepted_prefix(*f)
        for change in ('missing','extra','reordered','bounds','borrowed'):
            f=list(copy.deepcopy(self.fixture()))
            if change=='missing':f[1].clear()
            elif change=='extra':f[1]['_build/2.9/agda/src/Tests/Global/Root.agdai']='unreported'
            elif change=='reordered':f[0]['selected_targets']=list(reversed(f[0]['selected_targets']))
            elif change=='bounds':f[0]['layout']['needed_chunks']=3358
            else:f[0]['phases'][0]['borrowed_interfaces_unchanged']=False
            with self.subTest(change=change),self.assertRaises(ValueError):accepted_prefix(*f)

    def test_chained_prefix_requires_both_verified_roots(self):
        prior,pool,source,machine,old=self.fixture()
        inherited=copy.deepcopy(prior['phases'][0]);inherited['record']['root']='/first'
        next_phase=copy.deepcopy(prior['phases'][0]);next_phase['target']='Tests.Global.Routes0'
        next_phase['record']['argv']=argv(machine,next_phase['target'])
        prior['inherited_accepted_phases']=[inherited];prior['phases']=[next_phase]
        prior['assembly_cpu_seconds']=4.
        pool['_build/2.9/agda/src/Tests/Global/Routes0.agdai']='next'
        with self.assertRaises(ValueError):accepted_prefix(prior,pool,source,machine,old)
        targets,phases=accepted_prefix(prior,pool,source,machine,old,{'/first','/old'})
        self.assertEqual([p['target'] for p in phases],targets[:2])

    def test_named_sample_prefix_and_corruption(self):
        from initial_lazy_samples6 import selection
        for side in ('lower', 'upper'):
            prior,pool,source,machine,old=self.fixture()
            rows,chunks,routes=(3047,2702,85) if side=='lower' else (3125,3359,105)
            helpers=['StateMap'+str(i) for i in range(255)]+['BodyMap255','OwnedMap256']
            parts=selection(side)['selected'];prefix='Tests.InitialGlobalNamed'+side.title()
            names=helpers+['Model']+['Routes'+str(i) for i in range(routes)]
            names+=['Part'+str(i) for i in parts]+['Root']
            prior['layout']=dict(format='othello-initial-global-named6-v1',side=side,
                owned_rows=rows,needed_chunks=chunks,owned_parts=parts,targets=names,prefix=prefix,
                map_helpers=[dict(target=n) for n in helpers],map_batch=32,route_batch=32)
            prior['selected_targets']=names
            target=prefix+'.StateMap0';phase=prior['phases'][0]
            phase['target']=target;phase['record']['argv']=argv(machine,target)
            pool={'_build/2.9/agda/src/'+target.replace('.','/')+'.agdai':'hash'}
            targets,phases=accepted_prefix(prior,pool,source,machine,old)
            self.assertEqual(len(targets),360 if side=='lower' else 380)
            self.assertEqual(len(phases),1)
            for key,value in [('owned_rows',rows-1),('needed_chunks',chunks-1),('map_batch',64),
                              ('owned_parts',list(reversed(parts))),('prefix','Tests.Other')]:
                corrupt=copy.deepcopy(prior);corrupt['layout'][key]=value
                with self.subTest(side=side,key=key),self.assertRaises(ValueError):
                    accepted_prefix(corrupt,pool,source,machine,old)
            extra=dict(pool);extra['_build/2.9/agda/src/'+prefix.replace('.','/')+'/Root.agdai']='extra'
            with self.assertRaises(ValueError):accepted_prefix(prior,extra,source,machine,old)


if __name__=='__main__':unittest.main()
