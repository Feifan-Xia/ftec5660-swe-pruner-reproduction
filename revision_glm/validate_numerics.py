"""Repeat the fixed numerical probes at the paper's threshold of 0.5."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
source=(ROOT/'validate_pruner.py').read_text(encoding='utf-8')
source=source.replace('threshold_0_4_disagreements','threshold_0_5_disagreements').replace('base >= .4','base >= .5').replace('other >= .4','other >= .5')
source=source.replace('runs/pruner_numerical_validation.json','runs/glm/pruner_numerical_validation.json')
exec(compile(source,str(ROOT/'validate_pruner.py'),'exec'))
