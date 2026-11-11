"""Freeze a complete population and a score-independent balanced schedule."""
import hashlib,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl'
rows=[json.loads(x) for x in source.read_text(encoding='utf-8').splitlines()]
indices=list(range(len(rows)));random.Random(5660).shuffle(indices)
protocol={
 'version':'full-streamlink-paper-padding-v1','question_indices':indices,'population_size':len(rows),
 'question_file_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'repeats':3,'conditions':['baseline','pruner'],'planned_cells':len(rows)*3*2,
 'agent_model':'z-ai/glm-4.6','agent_provider':{'only':['z-ai'],'allow_fallbacks':False},
 'judge_model':'openai/gpt-5','judge_provider':{'only':['openai'],'allow_fallbacks':False},
 'temperature':0,'top_p':1,'prune_threshold':.5,'agent_max_output_tokens':16384,
 'max_interaction_rounds':250,'max_seconds_per_question':1800,'pruner_chunk_tokens':8192,
 'pruner_padding':'Original right padding to 8192 with attention mask; no shortened input tensor.',
 'attention':'SDPA with query-axis tiles of 256 and full key/value context; tested against untiled SDPA.',
 'population':'All 48 released Streamlink questions, including earlier development and pilot questions; report prior-exposed and additional-question strata transparently.',
 'order':'Seed-5660 shuffled question blocks, 3 repetitions, alternating full/pruner order within each block. Up to 8 concurrent blocks.',
 'repeat_semantics':'Independent executions at temperature zero; original paper does not publish executable provider seeds.',
 'judge_prompt':'Exact released five-dimensional SWE-QA rubric; low reasoning, max output 4096; unchanged from the prior study.',
 'metrics':['provider cumulative input+output tokens including cached input','5-dimensional quality / 10','author round count','agent API request count','reasoning tokens','pruning activation','source tokens retained','latency','provider cost'],
 'paper_target':'Table 2, Streamlink, GLM-4.6, full and SWE-Pruner rows.',
 'paper_reference':{'baseline':{'score':8.56,'rounds':18.2,'tokens':318200},'pruner':{'score':8.56,'rounds':25.0,'tokens':145100}},
 'primary_analysis':'All 48 paired question clusters; preserve all three executions. Paired cluster bootstrap 10000 resamples seed 5660. Also report released stats.py score-one exclusion as a labeled secondary analysis.',
 'token_accounting':'Independent API ledger, checked against corrected runner. Report a separate 2x replay of the released double-counting metric, with unknown linkage to the published table.',
 'retry_policy':'One additional attempt only for demonstrated infrastructure/export/pruning-service failure. Retain all attempts. Low scores never trigger replacement.',
 'modification_phase':'Evaluate after reproduction diagnostics; use the same 48 questions and 3 executions. Freeze the modification and its plan before any calls. Earlier recovery study remains pilot evidence.',
 'unresolved_alignment':['Original provider/deployment/quantization not published','Exact January experiment code not in released history; SWE-QA code first added March 8','GPT-5 route/reasoning settings not fully published','Read-only isolated source snapshot, common to all conditions','Finite output and wall-clock safeguards recorded explicitly'],
}
target=ROOT/'revision_full/protocol.json'
assert not target.exists(),'Preserve protocol; changes need a versioned revision'
target.write_text(json.dumps(protocol,indent=2,ensure_ascii=False),encoding='utf-8')
print('Frozen question order:',indices)
