"""Exercise the authors' patched fallback function with a recording API stub."""
import ast
import contextlib
import io
from pathlib import Path
from types import SimpleNamespace
import unittest

class FallbackRouteTests(unittest.TestCase):
    def test_canonical_model_and_task_session_reach_client(self):
        source = Path(__file__).resolve().parents[1]/'upstream/downstream_eval/multi_turn/sweqa/openhands-qa/main.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=='generate_answer_from_history')
        calls=[]
        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Measured answer'))],
                                   usage=SimpleNamespace(prompt_tokens=10,completion_tokens=3,total_tokens=13))
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        namespace={'api_type':'openai','openai':SimpleNamespace(OpenAI=lambda **kwargs:client)}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        config={'api_key':'test-placeholder','base_url':'http://127.0.0.1:8877/v1',
                'model':'openai/deepseek-v4.1-flash','extra_headers':{'x-opencode-session':'formal-test'}}
        with contextlib.redirect_stdout(io.StringIO()):
            answer=namespace['generate_answer_from_history'](config,'Question',[{'role':'tool','content':'Code'}])
        self.assertEqual(calls[0]['model'],'deepseek-v4.1-flash')
        self.assertEqual(calls[0]['extra_headers']['x-opencode-session'],'formal-test')
        self.assertEqual(calls[0]['temperature'],.3)
        self.assertIn('Measured answer',answer)

if __name__=='__main__':
    unittest.main()
