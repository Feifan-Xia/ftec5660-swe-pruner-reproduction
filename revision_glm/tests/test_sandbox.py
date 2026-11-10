"""Exercise repository visibility and host-data exclusion in the real shell boundary."""
import ast,os,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
@unittest.skipUnless(os.name=='posix','Requires the WSL runner environment')
class SandboxTest(unittest.TestCase):
 def test_read_repo_without_host_files_network_or_repo_writes(self):
  tree=ast.parse((ROOT/'revision_glm/runtime/tool_utils.py').read_text())
  node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_execute_bash_command')
  ns={'subprocess':subprocess,'os':os};exec(compile(ast.Module(body=[node],type_ignores=[]),'sandbox','exec'),ns)
  os.environ['FTEC_REPO_ROOT']='/home/feifa/ftec5660-swe-pruner/glm-repository/streamlink'
  output=ns['_execute_bash_command']('test -f /workspace/src/streamlink/__init__.py && test ! -e /mnt/c && test ! -e /home/feifa && test -z "$OPENAI_API_KEY" && ! touch /workspace/forbidden && echo ISOLATED')
  self.assertEqual(output,'ISOLATED')
