"""Offline proof of the released fallback bug using the real BashObservation class."""
import ast,contextlib,io,json,subprocess,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'revision_hint/runtime'),str(ROOT)]
from tool_utils import BashObservation
from revision_full.fix_terminal_history import patch_runtime,visible_observation_text
source=ROOT/'revision_hint/runtime/main.py';patched=ROOT/'runs/full/terminal_repair/patched_hint_main.py';patch_runtime(source,patched)
def function(text):return next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='get_message_history')
upstream=subprocess.check_output(['git','-C',str(ROOT/'upstream'),'show','HEAD:downstream_eval/multi_turn/sweqa/openhands-qa/main.py']).decode()
assert ast.dump(function(upstream))==ast.dump(function(source.read_text(encoding='utf-8')))
class Event:
    def __init__(self,o):self.observation=o
def extract(text,o):
    ns={'json':json,'MessageEvent':type('Message',(),{}),'ActionEvent':type('Action',(),{}),'ObservationEvent':Event,'visible_observation_text':visible_observation_text}
    exec(compile(ast.Module(body=[function(text)],type_ignores=[]),'<history>','exec'),ns)
    with contextlib.redirect_stdout(io.StringIO()):return ns['get_message_history'](types.SimpleNamespace(events=[Event(o)]))[0]['content']
raw=BashObservation(output='visible code',original_output='visible code')
old=extract(source.read_text(encoding='utf-8'),raw);new=extract(patched.read_text(encoding='utf-8'),raw)
assert old=='Observation: []' and new=='Observation: Raw Output: \nvisible code'
pruned=BashObservation(output='kept line',original_output='kept line\nREMOVED_SECRET',pruned=True,prune_info={'score':.7,'left_token_cnt':2,'origin_token_cnt':8})
new_pruned=extract(patched.read_text(encoding='utf-8'),pruned);assert 'kept line' in new_pruned and 'REMOVED_SECRET' not in new_pruned
a=ast.parse(source.read_text(encoding='utf-8'));b=ast.parse(patched.read_text(encoding='utf-8'))
b.body=b.body[1:]
for t in [a,b]:t.body=[n for n in t.body if not isinstance(n,ast.FunctionDef) or n.name!='get_message_history']
assert ast.dump(a)==ast.dump(b)
result={'pass':True,'published_function_identical':True,'legacy_full_observation':old,'corrected_full_observation':new,'corrected_pruned_observation':new_pruned,'raw_removed_text_excluded':True,'all_other_runtime_ast_unchanged':True,'scope':'Terminal fallback only. Active OpenHands tool messages already used to_llm_content correctly. Frozen original runs are preserved; repaired terminal synthesis uses the identical saved trajectory.'}
(ROOT/'results/full/terminal_history_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
