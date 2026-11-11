"""Distinguish request-count changes from observed pruning in the first screen."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'results/precision/effects_r1.json').read_text())
tok=r['effects']['total_tokens'];calls=r['effects']['api_requests']
base=tok['baseline']/calls['baseline'];pruned=tok['pruner']/calls['pruner']
questions=[]
for q in r['question_means']:
    delta=q['pruner']['total_tokens']-q['baseline']['total_tokens']
    questions.append({'index':q['index'],'token_delta':delta,'prune_calls':q['pruner']['prune_calls'],'full_calls':q['baseline']['api_requests'],'pruner_calls':q['pruner']['api_requests']})
out={'screen':'Fixed eight questions, precision r0; all 16 cells included',
     'tokens_per_api_request':{'baseline':base,'pruner':pruned,'relative_percent':100*(pruned/base-1)},
     'request_count_relative_percent':calls['relative_percent'],
     'total_token_relative_percent':tok['relative_percent'],
     'question_deltas':questions,
     'interpretation':'Total-token ratio factorizes exactly into request-count ratio and mean-tokens-per-request ratio. Only one task invoked pruning. Independent online paths and prompt/tool-name differences contribute to the observed contrast; the numerical precision fix alone is not identified as its cause.'}
(ROOT/'results/full/first_screen_explanation.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
