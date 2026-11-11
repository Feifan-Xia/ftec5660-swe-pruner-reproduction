"""Verify required-hint pruning plus lossless recovery without paid model calls."""
import json,os,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'revision_optional/runtime'),str(ROOT)]
import tool_utils as t
import recovery_tool as r
from observation_store import ObservationStore
with tempfile.TemporaryDirectory() as folder:
    os.environ['OBSERVATION_LOG']=str(Path(folder)/'observations.json')
    raw='first\nsecret literal\nlast'
    t._execute_bash_command=lambda command:raw
    t.prune_fn=lambda output,hint:SimpleNamespace(score=.5,origin_token_cnt=9,left_token_cnt=3,model_input_token_cnt=20,pruned_code='first\n(filtered 1 lines)\nlast')
    r.STORE=ObservationStore()
    obs=r.RecoverableExecutor()(t.PrunerBashAction(command='cat file',context_focus_question='Which boundary lines are present?'))
    assert obs.pruned and obs.original_output==raw
    assert obs.line_count==3
    recovered=r.ExpandExecutor()(r.ExpandAction(observation_id=obs.observation_id,start=2,end=2))
    assert recovered.output=='secret literal\n'
    assert 'context_focus_question' not in t.PrunerBashAction.model_json_schema()['required']
    assert 'secret literal' not in ''.join(x.text for x in obs.to_llm_content)
    assert json.loads(Path(os.environ['OBSERVATION_LOG']).read_text())['reads'][0]['returned_chars']==15
out={'pass':True,'checks':['Optional-hint pruning binding','Raw text stored outside visible compressed observation','Exact bounded range expansion','Persisted expansion trace']}
(ROOT/'results/full/optional_binding_test.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
