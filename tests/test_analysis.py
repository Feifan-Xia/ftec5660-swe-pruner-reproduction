"""Hand-computed paired effects and failure denominators."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import analyze_results
from run_formal import schedule

class AnalysisTests(unittest.TestCase):
    def test_known_effects_and_failure_retention(self):
        jobs = schedule(list(range(8)))
        rows = []
        for job in jobs:
            mode = job['mode']
            failed = mode == 'baseline' and job['index'] == 0 and job['repeat'] == 0
            tokens = {'baseline': 100, 'pruner': 80, 'recovery': 90}[mode]
            rows.append(dict(question_index=job['index'], repeat=job['repeat'], mode=mode,
                status='failed' if failed else 'answered', completed_answer=not failed,
                total_tokens=tokens, input_tokens=tokens-10, output_tokens=10,
                score=None if failed else 8, seconds=1, author_filtered_eligible=not failed,
                pruned_observations=0, recovery_reads=0, cash_cost=0, go_allowance=0,
                conservative_cost=.01))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'results').mkdir()
            (root/'runs/formal').mkdir(parents=True)
            (root/'results/formal_tasks.json').write_text(json.dumps(rows))
            (root/'runs/formal/schedule.json').write_text(json.dumps(jobs))
            with patch.object(analyze_results, 'ROOT', root), patch('sys.argv', ['analyze_results']), contextlib.redirect_stdout(io.StringIO()):
                analyze_results.main()
            result = json.loads((root/'results/formal_analysis.json').read_text())
            self.assertEqual(result['conditions']['baseline']['attempted'], 24)
            self.assertEqual(result['conditions']['baseline']['completed'], 23)
            self.assertAlmostEqual(result['conditions']['baseline']['mean_score_failure_zero'], 23*8/24)
            self.assertEqual(result['paired']['pruner_minus_baseline']['mean_token_difference'], -20)
            self.assertAlmostEqual(result['paired']['pruner_minus_baseline']['mean_failure_zero_score_difference'], 1/3)
            self.assertEqual(result['paired']['recovery_minus_pruner']['bootstrap_95_percentile'], [10,10])

if __name__ == '__main__':
    unittest.main()
