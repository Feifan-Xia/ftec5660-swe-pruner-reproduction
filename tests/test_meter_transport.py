"""Connection retries may never replay a request after transmission began."""
import ast,json,tempfile,threading,types,unittest
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
class TransportTests(unittest.TestCase):
    def exercise(self,error):
        calls=[]
        def original(*a,**k):
            calls.append(1)
            if len(calls)==1:raise error
            return 'response'
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'runs/full').mkdir(parents=True)
            ns={'original':original,'httpx':httpx,'ROOT':root,'state_lock':threading.Lock(),'pause_until':0,'time':types.SimpleNamespace(time=lambda:100,sleep=lambda seconds:None),'json':json}
            tree=ast.parse((ROOT/'revision_full/meter_transport.py').read_text())
            node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='post')
            exec(compile(ast.Module(body=[node],type_ignores=[]),'<transport>','exec'),ns)
            if isinstance(error,httpx.ConnectError):self.assertEqual(ns['post'](None,'https://example.test'),'response')
            else:
                with self.assertRaises(type(error)):ns['post'](None,'https://example.test')
        return len(calls)
    def test_connect_failure_retries(self):self.assertEqual(self.exercise(httpx.ConnectError('DNS failed')),2)
    def test_post_send_failure_propagates_once(self):self.assertEqual(self.exercise(httpx.ReadError('connection reset')),1)
if __name__=='__main__':unittest.main()
