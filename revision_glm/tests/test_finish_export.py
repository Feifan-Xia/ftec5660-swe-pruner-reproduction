"""Regression for the actual patched author's FinishAction callback."""
import ast,unittest
from pathlib import Path
class MessageEvent: pass
class ActionEvent:
    def __init__(self,action): self.action=action
class FinishAction:
    name=None
    def model_dump(self):return {'kind':'FinishAction','name':None,'message':'A complete final answer.'}
class ExportTest(unittest.TestCase):
    def test_null_name_finish_message_is_exported(self):
        source=Path(__file__).resolve().parents[1]/'runtime/main.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        callback=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='on_event')
        callback.body[0]=ast.Global(names=['answer_data','conversation'])
        tree=ast.fix_missing_locations(ast.Module(body=[callback],type_ignores=[]))
        ns={'MessageEvent':MessageEvent,'ActionEvent':ActionEvent,'answer_data':{'answer':''},'conversation':None,'traj_dir':None}
        exec(compile(tree,str(source),'exec'),ns)
        ns['on_event'](ActionEvent(FinishAction()))
        self.assertEqual(ns['answer_data']['answer'],'A complete final answer.')
if __name__=='__main__':unittest.main()
