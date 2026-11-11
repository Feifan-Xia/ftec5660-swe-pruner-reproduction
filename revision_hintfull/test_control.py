"""The matched control retains the schema while returning the complete observation."""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'revision_hintfull/runtime'))
import tool_utils as t
os.environ['FTEC_REPO_ROOT']=str(Path.home()/'ftec5660-swe-pruner/paper-workspace')
def forbidden(*args,**kwargs):raise AssertionError('Control called the skimmer')
t.prune_fn=forbidden
action=t.PrunerBashAction(command="printf 'keep line 1\\nkeep line 2\\n'",context_focus_question='Which line contains the first item?')
obs=t.PrunerBashExecutor()(action)
assert obs.output==obs.original_output=='keep line 1\nkeep line 2'
assert not obs.pruned and obs.prune_info is None
assert 'context_focus_question' in t.PrunerBashAction.model_json_schema()['required']
out={'pass':True,'checks':['Complete captured output returned','Skimmer never called','Required-hint action schema retained','No fake compression metadata']}
(ROOT/'results/full/hintfull_execution_test.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
