"""Read installed SDK metric implementation without network access."""
import inspect
from openhands.sdk import LLM
from openhands.sdk.llm import Metrics
print('LLM location:',inspect.getfile(LLM))
print('Metrics location:',inspect.getfile(Metrics))
source=inspect.getsource(Metrics)
for i,line in enumerate(source.splitlines(),1):
    if 'token_usages' in line or 'accumulated_token_usage' in line:
        print(i,line)
