"""Add a schema-matched full-output control for the fixed activation experiment."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'revision_hintfull';(dest/'runtime').mkdir(parents=True,exist_ok=True)
assert not (ROOT/'runs/hintfull/formal/runtime_manifest.json').exists()
main=(ROOT/'revision_hint/runtime/main.py').read_text(encoding='utf-8')
(dest/'runtime/main.py').write_text(main,encoding='utf-8')
text=(ROOT/'revision_hint/runtime/tool_utils.py').read_text(encoding='utf-8')
tree=ast.parse(text);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PrunerBashExecutor')
fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__call__')
lines=text.splitlines(keepends=True)
replacement='''    def __call__(self, action: PrunerBashAction, conversation=None) -> BashObservation:
        # Schema-matched control: execute the same command and return all captured text.
        original_output = _execute_bash_command(action.command)
        return BashObservation(output=original_output, pruned=False, original_output=original_output)
'''
lines[fn.lineno-1:fn.end_lineno]=[replacement]
(dest/'runtime/tool_utils.py').write_text(''.join(lines),encoding='utf-8')
for name in ['run_study.py','freeze.py','analyze.py']:
    value=(ROOT/'revision_hint'/name).read_text(encoding='utf-8')
    value=value.replace('revision_hint/','revision_hintfull/').replace('runs/hint/','runs/hintfull/').replace('results/hint','results/hintfull').replace('glm-hint-','glm-hintfull-').replace('judge-hint-','judge-hintfull-').replace("phase='required_hint_ablation'","phase='schema_matched_full_control'")
    if name=='analyze.py':value=value.replace('range(3)',"range(protocol['repeats'])").replace('* 3 *',"* protocol['repeats'] *").replace('len(g) == 3',"len(g) == protocol['repeats']")
    (dest/name).write_text(value,encoding='utf-8')
p=json.loads((ROOT/'revision_hint/protocol.json').read_text(encoding='utf-8'))
p.update(version='schema-matched-full-control-v1',repeats=1,planned_cells=8,
    intervention='Same required nonempty hint action and tool description as revision_hint. The executor returns the entire captured command output; it never calls the skimmer. All other runtime code remains identical.',
    interpretation='Mechanism control separating the tool-interface/agent-path contrast from active filtering. Compare all eight questions to the required-hint arm at repeat0. Outcomes were not inspected when this control was specified.',
    primary_analysis='All eight fixed question clusters, one execution per question; paired bootstrap is descriptive. Report independent ordering and shared full/optional controls explicitly.',
    comparator='runs/hint/formal/pruner/*_r0; full and optional-reference rows from precision repeat0',
    order='This control is run after the original required-hint first screen was launched; it is a diagnostic stage, with all eight fixed questions included. Time ordering is a limitation.',
    modification_phase='Recovery remains a separate extension; this stage is a mechanism control.')
(dest/'protocol.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
a=ast.parse(text);b=ast.parse((dest/'runtime/tool_utils.py').read_text(encoding='utf-8'))
for t in [a,b]:
    c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='PrunerBashExecutor')
    c.body=[n for n in c.body if not isinstance(n,ast.FunctionDef) or n.name!='__call__']
assert ast.dump(a)==ast.dump(b)
assert (dest/'runtime/main.py').read_bytes()==(ROOT/'revision_hint/runtime/main.py').read_bytes()
(ROOT/'results/full/hintfull_contract_test.json').write_text(json.dumps({'pass':True,'scope':'Only PrunerBashExecutor.__call__ changed; all schemas, descriptions and main runtime identical.'},indent=2),encoding='utf-8')
print('Prepared eight-question schema-matched full-output control; AST isolation passes.')
