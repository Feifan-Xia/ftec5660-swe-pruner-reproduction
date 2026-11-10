import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from revision_glm.run_study import judge,OUT
judge(OUT/'baseline/q41_r0/attempt0')
