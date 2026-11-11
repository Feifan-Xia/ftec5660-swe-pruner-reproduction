"""Validate the complete, minimal activation intervention before paid runs."""
import ast,importlib.util,json,sys
from pathlib import Path
from pydantic import ValidationError
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
new=load('required_tools',ROOT/'revision_hint/runtime/tool_utils.py')
assert (ROOT/'revision_subset/runtime/main.py').read_bytes()==(ROOT/'revision_hint/runtime/main.py').read_bytes()
a=ast.parse((ROOT/'revision_subset/runtime/tool_utils.py').read_text())
b=ast.parse((ROOT/'revision_hint/runtime/tool_utils.py').read_text())
for tree in [a,b]:tree.body=[node for node in tree.body if not isinstance(node,ast.ClassDef) or node.name!='PrunerBashAction']
assert ast.dump(a)==ast.dump(b),'Only the action contract may change'
for kwargs in [{},{'context_focus_question':None},{'context_focus_question':''}]:
    try:new.PrunerBashAction(command='ls',**kwargs)
    except ValidationError:pass
    else:raise AssertionError(f'Accepted invalid hint {kwargs}')
assert new.PrunerBashAction(command='ls',context_focus_question='Which files contain the API?').context_focus_question
schema=new.PrunerBashAction.model_json_schema()
assert 'context_focus_question' in schema['required']
assert schema['properties']['context_focus_question']['minLength']==1
out={'status':'pass','checks':['Main identical','All code except action declaration identical','Omitted/null/empty hint rejected','Nonempty hint accepted','Required minLength=1 schema'],'new_action_schema':schema}
(ROOT/'results/full/required_hint_contract_test.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('PASS: required-hint contract and isolation, five checks.')
