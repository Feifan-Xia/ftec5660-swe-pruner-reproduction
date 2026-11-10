"""Score repair must preserve low valid scores and initial truncated responses."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import repair_scores

class ScoreRepairTests(unittest.TestCase):
    def test_only_missing_score_is_filled_and_second_run_is_free(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            question=root/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl'
            question.parent.mkdir(parents=True)
            question.write_text(json.dumps({'question':'Q','ground_truth':'R'})+'\n')
            paths=[]
            for repeat in range(2):
                path=root/f'runs/formal/baseline/q0_r{repeat}'
                (path/'answers').mkdir(parents=True)
                (path/'task.json').write_text(json.dumps({'phase':'formal','mode':'baseline','index':0,'repeat':repeat}))
                (path/'exit.json').write_text('{"returncode":0}')
                (path/'answers/test_answers.jsonl').write_text('{"answer":"A"}\n')
                paths.append(path)
            low_score=json.dumps({'mean':1.0,'scores':{key:1 for key in repair_scores.DIMENSIONS},
                                  'judge_model':'deepseek-v4.1-flash','same_model_judge':True,
                                  'author_filtered_eligible':False}).encode()
            (paths[0]/'score.json').write_bytes(low_score)
            original=b'{"finish_reason":"length","content":""}'
            (paths[1]/'judge_raw.json').write_bytes(original)
            scores={key:7 for key in repair_scores.DIMENSIONS}
            payload={'model':'deepseek-v4.1-flash','choices':[{'message':{'content':json.dumps(scores)}}]}
            response=SimpleNamespace(raise_for_status=lambda:None,json=lambda:payload)
            with patch.object(repair_scores,'ROOT',root), patch.object(repair_scores,'official_prompt',return_value='same official rubric'), patch.object(repair_scores.httpx,'post',return_value=response) as post, patch('sys.argv',['repair_scores']), contextlib.redirect_stdout(io.StringIO()):
                repair_scores.main()
                repair_scores.main()
            self.assertEqual(post.call_count,1)
            self.assertEqual((paths[0]/'score.json').read_bytes(),low_score)
            self.assertEqual((paths[1]/'judge_raw.json').read_bytes(),original)
            self.assertEqual(json.loads((paths[1]/'score.json').read_text())['mean'],7)
            self.assertEqual(len(json.loads((root/'results/judge_repairs.json').read_text())['repaired']),1)

if __name__=='__main__':
    unittest.main()
