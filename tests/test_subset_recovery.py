"""Exercise recovery decisions without running paid jobs or importing CLI entrypoints."""
import ast,json,tempfile,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TREE=ast.parse((ROOT/'revision_full/resume_subset.py').read_text())
def load(name,namespace):
    node=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<recovery-function>','exec'),namespace)
    return namespace[name]
class RecoveryFlowTests(unittest.TestCase):
    def test_budget_checked_before_new_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            called=[]
            def stop():raise RuntimeError('headroom')
            f=load('guarded_run',{'run':types.SimpleNamespace(OUT=Path(d)), 'preflight':stop,'original_run':lambda *a:called.append(a)})
            with self.assertRaises(RuntimeError):f({'mode':'pruner','index':11,'repeat':0},2)
            self.assertEqual(called,[])
    def test_third_attempt_only_for_two_budget_interruptions(self):
        for reason,expected in [('budget_guard_interruption',[0,1,2]),('missing_answer',[0,1])]:
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as d:
                attempted=[];selected=[]
                fake=types.SimpleNamespace(MODES=['pruner'],OUT=Path(d),read=lambda p:{'qualified':False,'reasons':[reason]},write=lambda p,v:selected.append(v))
                def execute(job,attempt):attempted.append(attempt);return attempt
                f=load('block',{'run':fake,'guarded_run':execute,'qualify':lambda a:a==2,'judge':lambda a:None})
                f(0,11,1)
                self.assertEqual(attempted,expected)
                self.assertEqual(selected[-1]['selected_attempt'],2 if reason=='budget_guard_interruption' else None)
    def test_qualified_low_score_is_kept(self):
        with tempfile.TemporaryDirectory() as d:
            attempted=[];selected=[]
            fake=types.SimpleNamespace(MODES=['pruner'],OUT=Path(d),write=lambda p,v:selected.append(v))
            def execute(job,a):attempted.append(a);return a
            f=load('block',{'run':fake,'guarded_run':execute,'qualify':lambda a:True,'judge':lambda a:1})
            f(0,11,1)
            self.assertEqual(attempted,[0]);self.assertEqual(selected[-1]['selected_attempt'],0)
if __name__=='__main__':unittest.main()
