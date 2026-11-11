"""Replay the released aggregation loop on actual usage, using the pinned SDK."""
import ast,json,subprocess
from pathlib import Path
from types import SimpleNamespace
from openhands.sdk.llm import Metrics
ROOT=Path(__file__).resolve().parents[1]
original=subprocess.check_output(['git','show','HEAD:downstream_eval/multi_turn/sweqa/openhands-qa/main.py'],cwd=ROOT/'upstream').decode()
patched=(ROOT/'revision_glm/runtime/main.py').read_text(encoding='utf-8')
def loop(source):
    nodes=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.For) and 'stats.usage_to_metrics.items()'==ast.unparse(n.iter)]
    assert len(nodes)==1
    return compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'token_aggregation','exec')
released_loop,corrected_loop=loop(original),loop(patched)
ledger=[json.loads(x) for x in (ROOT/'runs/glm/pinned/formal_usage.jsonl').read_text().splitlines()]
sessions=sorted({r['session'] for r in ledger if r['session'].startswith('glm-pinned-')})
rows=[]
for session in sessions:
    calls=[r for r in ledger if r['session']==session]
    metrics=Metrics(model_name='z-ai/glm-4.6')
    expected=0
    for call in calls:
        u=call['usage'];pin=u['prompt_tokens'];pout=u['completion_tokens'];expected+=pin+pout
        metrics.add_token_usage(prompt_tokens=pin,completion_tokens=pout,cache_read_tokens=u.get('prompt_tokens_details',{}).get('cached_tokens',0),cache_write_tokens=0,context_window=204800,response_id=call['request_id'])
    row={'session':session,'ledger_total':expected}
    for label,code in [('released_total',released_loop),('corrected_total',corrected_loop)]:
        ns={'stats':SimpleNamespace(usage_to_metrics={'default':metrics}),'total_prompt_tokens':0,'total_completion_tokens':0}
        exec(code,ns);row[label]=ns['total_prompt_tokens']+ns['total_completion_tokens']
    rows.append(row)
result={'cells':len(rows),'released_equals_double_ledger':all(r['released_total']==2*r['ledger_total'] for r in rows),
        'corrected_equals_ledger':all(r['corrected_total']==r['ledger_total'] for r in rows),
        'scope':'Verified released-code behavior; unpublished January experiment implementation cannot be inferred from this March code release. A shared multiplier leaves relative effects unchanged.', 'rows':rows}
(ROOT/'results/full/accounting_replay.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
