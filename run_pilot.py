"""Serial development runs; every request remains subject to proxy budget."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
jobs = [('pruner',43,2), ('recovery',43,1), ('baseline',17,1), ('baseline',26,1),
        ('pruner',17,0), ('recovery',17,0), ('pruner',26,0), ('recovery',26,0)]
for mode, index, repeat in jobs:
    directory = ROOT / f'runs/pilot/{mode}/q{index}_r{repeat}'
    if not (directory / 'exit.json').exists():
        subprocess.run([sys.executable, str(ROOT / 'run_task.py'), '--mode', mode,
                        '--index', str(index), '--repeat', str(repeat)], check=True)
    result = (subprocess.CompletedProcess([], 0) if (directory / 'score.json').exists()
              else subprocess.run([sys.executable, str(ROOT / 'score_results.py'), str(directory)]))
    subprocess.run([sys.executable, str(ROOT / 'summarize_results.py')], stdout=subprocess.DEVNULL)
    if result.returncode:
        print('Scoring incomplete; inspect before continuing pilot.', flush=True)
        break
