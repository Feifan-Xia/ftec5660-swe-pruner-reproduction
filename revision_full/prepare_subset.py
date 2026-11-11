"""Prepare the fixed eight-question, artifact-aligned diagnostic before expansion."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'revision_subset';(dest/'runtime').mkdir(parents=True,exist_ok=True)
assert not (ROOT/'runs/subset/formal/runtime_manifest.json').exists()
for name in ['main.py','tool_utils.py','LICENSE']:
    (dest/'runtime'/name).write_bytes((ROOT/'revision_full/runtime'/name).read_bytes())
runner=(ROOT/'revision_full/run_study.py').read_text(encoding='utf-8')
runner=runner.replace('runs/full/formal','runs/subset/formal').replace('glm-full-','glm-subset-').replace('judge-full-','judge-subset-')
runner=runner.replace('revision_full/runtime','revision_subset/runtime').replace('revision_full/protocol.json','revision_subset/protocol.json')
runner=runner.replace("REPO=Path(os.environ.get('FTEC_CLEAN_REPO',str(Path.home()/'ftec5660-swe-pruner/glm-repository/streamlink')))","WORKSPACE=Path.home()/'ftec5660-swe-pruner/paper-workspace'\nREPO=WORKSPACE/'swe-repos/streamlink'")
runner=runner.replace('FTEC_REPO_ROOT=str(REPO)','FTEC_REPO_ROOT=str(WORKSPACE)')
runner=runner.replace("MAX_ITERATION_PER_RUN='250'","MAX_ITERATION_PER_RUN='50'").replace('max_iterations=250','max_iterations=50')
runner=runner.replace("phase='full_replication'","phase='artifact_aligned_subset'")
runner=runner.replace('def block(number,index):\n for repeat in range(3):','def block(number,index,repeats=3):\n for repeat in range(repeats):')
runner=runner.replace("parser.add_argument('--limit-questions',type=int);","parser.add_argument('--limit-questions',type=int);parser.add_argument('--repeats',type=int,choices=[1,3],default=3);")
runner=runner.replace('pool.submit(block,n,index)','pool.submit(block,n,index,args.repeats)')
runner=runner.replace('len(indices)*3*len(MODES)','len(indices)*args.repeats*len(MODES)').replace('full target is 288','fixed subset target is 48')
(dest/'run_study.py').write_text(runner,encoding='utf-8')
protocol=json.loads((ROOT/'revision_full/protocol.json').read_text(encoding='utf-8'))
protocol.update(version='artifact-aligned-fixed-subset-v1',question_indices=[41,14,30,8,11,46,33,29],population_size=8,planned_cells=48,
 max_interaction_rounds=50,population='Same eight questions selected before the initial model runs; all remain included. This is a diagnostic subset before any expansion.',
 order='Three repeat executions, alternating condition order by question ordinal and repetition. First complete repetition 0 over all eight questions; then assess configuration and continue repeats 1–2.',
 workspace='Clean copies of Conan, Reflex and Streamlink at ./swe-repos/{repository}, matching the recorded shared source-root layout. Authors unpublished helper files and evaluation materials are absent.',
 artifact_reference={'full_input_plus_output':142256.58333333334,'pruner_input_plus_output':101199.875,'relative_change_percent':100*(101199.875/142256.58333333334-1),
                     'fixed_eight_full':190204,'fixed_eight_pruner':95309.625},
 scope_change='User requested fixed-subset verification before expansion; USD 28 has not been approved. Existing USD 12 meter remains authoritative.',
 expected_behavior='Lower end-to-end tokens with comparable mean quality; report all fixed questions and interpret quality uncertainty, activation and missing evidence before scaling.',
 repeat_semantics='First 16 cells are a diagnostic screen. Remaining 32 continue the same immutable configuration only after reviewing alignment; any repair creates a new version retaining all previous results.',
 modification_phase='After matched reproduction behavior has been investigated, freeze and evaluate lossless recovery independently.')
protocol['unresolved_alignment']=['Original model served as azure/glm-4.6 through a ByteDance gateway; this run uses the accessible Z.AI endpoint via OpenRouter.','Authors exact inference kernel and checkpoint revision unrecorded; published checkpoint replay is measured.','Released Streamlink and Reflex token columns cross-match the paper rows; preserve both sources.','Authors snapshot included additional unshared helper files.','Judge provider and inference details remain incompletely specified.']
(dest/'protocol.json').write_text(json.dumps(protocol,indent=2,ensure_ascii=False),encoding='utf-8')
freeze=(ROOT/'revision_full/freeze.py').read_text(encoding='utf-8').replace('revision_full/run_study.py','revision_subset/run_study.py').replace('revision_full/protocol.json','revision_subset/protocol.json').replace('revision_full/runtime','revision_subset/runtime').replace('runs/full/formal','runs/subset/formal')
(dest/'freeze.py').write_text(freeze,encoding='utf-8')
analysis=(ROOT/'revision_full/analyze.py').read_text(encoding='utf-8').replace('results/full','results/subset').replace('revision_full/protocol.json','revision_subset/protocol.json').replace('runs/full/formal/','runs/subset/formal/').replace('glm-full-','glm-subset-')
(dest/'analyze.py').write_text(analysis,encoding='utf-8')
print('Prepared same fixed eight questions; matched 50-step cap and recorded source-root layout.')
