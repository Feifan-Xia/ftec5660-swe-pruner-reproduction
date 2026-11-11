"""Prepare a separately frozen full-population runtime; preserve the pilot."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
assert not (ROOT/'runs/full/formal/runtime_manifest.json').exists(),'Formal source already frozen; preserve it.'
runtime=HERE/'runtime'
runtime.mkdir(exist_ok=True)
for name in ('main.py','tool_utils.py','LICENSE'):
    text=(ROOT/'revision_glm/runtime'/name).read_text(encoding='utf-8')
    if name=='main.py':
        text=text.replace('LLM_CONFIG["max_output_tokens"] = 16384','LLM_CONFIG["max_output_tokens"] = 16384\nLLM_CONFIG["temperature"] = 0.0')
    (runtime/name).write_text(text,encoding='utf-8')
meter=(ROOT/'revision_glm/meter.py').read_text(encoding='utf-8')
meter=meter.replace("folder=ROOT/'runs/glm/pinned'","folder=ROOT/'runs/full'")
meter=meter.replace("httpx.Client(timeout=240,trust_env=False),", "httpx.Client(timeout=httpx.Timeout(240,connect=15),trust_env=False,proxy=os.getenv('AGENT_HTTPS_PROXY','http://127.0.0.1:7898') or None),")
(HERE/'meter.py').write_text(meter,encoding='utf-8')
runner=(ROOT/'revision_glm/run_study.py').read_text(encoding='utf-8')
runner=runner.replace("MODES=['baseline','pruner','recovery']","MODES=['baseline','pruner']")
runner=runner.replace('runs/glm/pinned/formal','runs/full/formal').replace('glm-pinned-','glm-full-').replace("phase='glm_formal'","phase='full_replication'")
runner=runner.replace('revision_glm/runtime','revision_full/runtime').replace('revision_glm/protocol.json','revision_full/protocol.json')
runner=runner.replace('shift=(number+repeat)%3','shift=(number+repeat)%len(MODES)')
runner=runner.replace('All 72 planned condition/repetition cells processed','All 288 planned replication cells processed')
runner=runner.replace("default=3);args=parser.parse_args()","default=8);parser.add_argument('--limit-questions',type=int);args=parser.parse_args()")
runner=runner.replace("indices=protocol['question_indices']","indices=protocol['question_indices']\n if args.limit_questions:indices=indices[:args.limit_questions]")
runner=runner.replace("frozen=read(OUT/'runtime_manifest.json')","frozen=read(OUT/'runtime_manifest.json')")
runner=runner.replace("f'judge-{task", "f'judge-full-{task") if False else runner
runner=runner.replace('f"judge-{task', 'f"judge-full-{task')
(HERE/'run_study.py').write_text(runner,encoding='utf-8')
freeze=(ROOT/'revision_glm/freeze.py').read_text(encoding='utf-8')
freeze=freeze.replace('revision_glm/run_study.py','revision_full/run_study.py').replace('revision_glm/meter.py','revision_full/meter.py').replace('revision_glm/protocol.json','revision_full/protocol.json').replace('revision_glm/runtime','revision_full/runtime').replace('revision_glm/serve.py','revision_full/serve.py').replace('runs/glm/pinned/formal','runs/full/formal')
freeze=freeze.replace("'serve_pruner.py',","'serve_pruner.py','revision_full/paper_padding.py',")
(HERE/'freeze.py').write_text(freeze,encoding='utf-8')
print('Prepared independent full-population source files.')
