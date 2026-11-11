"""Keep agent-visible tool evidence in the published terminal-summary branch."""
import ast
from pathlib import Path
def visible_observation_text(observation):
    blocks=getattr(observation,'to_llm_content',None)
    if blocks is not None:
        return '\n'.join(str(x.text) for x in blocks if hasattr(x,'text'))
    output=getattr(observation,'output',None)
    if output is not None:return str(output)
    message=getattr(observation,'message',None)
    if message:return str(message)
    content=getattr(observation,'content',None)
    if isinstance(content,str):return content
    if content:return '\n'.join(str(x.text) for x in content if hasattr(x,'text'))
    return ''

def patch_runtime(source:Path,destination:Path):
    text=source.read_text(encoding='utf-8');tree=ast.parse(text)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='get_message_history')
    old=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and ast.unparse(n.test)=="hasattr(observation, 'message')")
    lines=text.splitlines(keepends=True)
    indent=' '*(old.col_offset)
    lines[old.lineno-1:old.end_lineno]=[indent+'observation_info = "Observation: " + visible_observation_text(observation)\n']
    result='from revision_full.fix_terminal_history import visible_observation_text\n'+''.join(lines)
    ast.parse(result);destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(result,encoding='utf-8')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('destination',type=Path);a=p.parse_args();patch_runtime(a.source,a.destination)
