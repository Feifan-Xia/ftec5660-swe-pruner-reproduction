"""Retain the audited analysis definitions for the complete population."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'revision_glm/analyze.py').read_text(encoding='utf-8')
text=text.replace('results/glm','results/full').replace('revision_glm/protocol.json','revision_full/protocol.json').replace('runs/glm/pinned','runs/full').replace('glm-pinned-','glm-full-')
text=text.replace('MODES = ["baseline", "pruner", "recovery"]','MODES = ["baseline", "pruner"]')
text=text.replace('    args = parser.parse_args()','    parser.add_argument("--include-recovery", action="store_true")\n    args = parser.parse_args()\n    if args.include_recovery:\n        MODES.append("recovery")')
text=text.replace('"planned": 72','"planned": len(protocol["question_indices"]) * 3 * len(MODES)')
text=text.replace('len(rows) == 72','len(rows) == len(protocol["question_indices"]) * 3 * len(MODES)')
text=text.replace('for treatment, control in [("pruner", "baseline"), ("recovery", "pruner")]:','for treatment, control in [("pruner", "baseline")] + ([("recovery", "pruner")] if "recovery" in MODES else []):')
(ROOT/'revision_full/analyze.py').write_text(text,encoding='utf-8')
print('Prepared population-aware analyzer.')
