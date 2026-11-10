"""Prepare an isolated corrected runner; preserve the earlier experiment runtime."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
DEST=Path(__file__).resolve().parent/'runtime'
DEST.mkdir(exist_ok=True)
src=ROOT/'upstream/downstream_eval/multi_turn/sweqa/openhands-qa'
text=(src/'main.py').read_text(encoding='utf-8')
old='''                if action_name and (
                    "finish" in action_name.lower() or "final" in action_name.lower()
                ):'''
new='''                if type(action).__name__ == "FinishAction" or (action_name and (
                    "finish" in action_name.lower() or "final" in action_name.lower()
                )):'''
assert old in text
text=text.replace(old,new)
text=text.replace('# Load base paths from environment', 'LLM_CONFIG["max_output_tokens"] = 16384\n\n# Load base paths from environment')
(DEST/'main.py').write_text(text,encoding='utf-8')
tools=(src/'tool_utils.py').read_text(encoding='utf-8')
old_command='''            command, shell=True, capture_output=True, text=True, timeout=10'''
new_command='''            ["bwrap", "--unshare-all", "--die-with-parent",
             "--ro-bind", "/usr", "/usr", "--symlink", "usr/bin", "/bin",
             "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
             "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
             "--dir", "/workspace", "--ro-bind", os.environ["FTEC_REPO_ROOT"], "/workspace",
             "--clearenv", "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/tmp",
             "--chdir", "/workspace", "/bin/sh", "-c", command],
            shell=False, capture_output=True, text=True, timeout=10'''
assert old_command in tools
tools=tools.replace(old_command,new_command).replace('timeout=60.0','timeout=600.0')
(DEST/'tool_utils.py').write_text(tools,encoding='utf-8')
(DEST/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DEST.glob('*.py')},indent=2))
print('Prepared isolated GLM runtime with FinishAction extraction and 16384 output capacity.')
