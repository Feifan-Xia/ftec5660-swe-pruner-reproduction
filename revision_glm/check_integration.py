"""Exercise real pruning and exact expansion through the frozen tool executors."""
import sys,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'revision_glm/runtime'),str(ROOT)]
os.environ.update(FTEC_REPO_ROOT='/home/feifa/ftec5660-swe-pruner/glm-repository/streamlink',PRUNE_THRESHOLD='0.5',PRUNER_URL='http://127.0.0.1:8000/prune',OBSERVATION_LOG=str(ROOT/'runs/glm/integration_observations.json'))
from recovery_tool import RecoverableExecutor,ExpandExecutor,ExpandAction,STORE
from tool_utils import PrunerBashAction
result=RecoverableExecutor()(PrunerBashAction(command='cat -n /workspace/src/streamlink/webbrowser/cdp/client.py',context_focus_question='How does fail_unhandled_requests affect request interception?'))
assert result.pruned,'Published skimmer must execute successfully on the long development input'
recovered=ExpandExecutor()(ExpandAction(observation_id=result.observation_id,start=1,end=100))
expected=''.join(result.original_output.splitlines(keepends=True)[:100])
assert recovered.output==expected,'Expansion must reproduce exact original lines'
record={'pruned':result.pruned,'prune_info':result.prune_info,'original_chars':len(result.original_output),'recovered_chars':len(recovered.output),'exact_match':True,'read_records':STORE.reads}
(ROOT/'runs/glm/integration_check.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record))
