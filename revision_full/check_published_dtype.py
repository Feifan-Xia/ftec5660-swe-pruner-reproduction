"""Measure the released server's default loading precision on CPU."""
import collections,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'upstream/swe-pruner/src'))
import torch
from swe_pruner.configuration import SwePrunerConfig
from swe_pruner.prune_wrapper import SwePrunerForCodePruning
config=SwePrunerConfig.from_pretrained(ROOT/'models/code-pruner')
before=str(config.dtype)
config.backbone_model_name_or_path=str(ROOT/'models/qwen-backbone')
available=torch.cuda.is_available
torch.cuda.is_available=lambda:False
try:
    model=SwePrunerForCodePruning.from_pretrained(str(ROOT/'models/code-pruner'),config=config)
finally:torch.cuda.is_available=available
counts=collections.Counter()
for name,parameter in model.named_parameters():counts[str(parameter.dtype)]+=parameter.numel()
value={'call':'SwePrunerForCodePruning.from_pretrained(path, config=local_backbone_config); no dtype override, as in released online_serving.py',
       'config_dtype_before':before,'config_dtype_after':str(model.config.dtype),'parameter_counts_by_dtype':dict(counts),'device':str(next(model.parameters()).device),
       'reproduction_override':'torch_dtype=torch.bfloat16','torch':torch.__version__}
(ROOT/'results/full/published_dtype_check.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
print(json.dumps(value,indent=2),flush=True)
