"""Check tiled SDPA against PyTorch on causal, padding-mask and GQA cases."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
try:import torch
except ImportError:torch=None
@unittest.skipIf(torch is None,'Run attention checks in the GPU Python environment')
class AttentionTest(unittest.TestCase):
 def test_mask_and_causal_semantics(self):
  from revision_glm.memory_attention import install
  import torch.nn.functional as F
  torch.manual_seed(5660)
  for causal,padding,gqa in [(True,False,False),(False,True,False),(False,False,True)]:
   q=torch.randn(1,4,601,16);k=torch.randn(1,2 if gqa else 4,601,16);v=torch.randn_like(k)
   mask=torch.ones(1,1,1,601,dtype=torch.bool) if padding else None
   if mask is not None:mask[...,-30:]=False
   expected=F.scaled_dot_product_attention(q,k,v,attn_mask=mask,is_causal=causal,enable_gqa=gqa)
   originals=install(query_tile=127)
   try:actual=F.scaled_dot_product_attention(q,k,v,attn_mask=mask,is_causal=causal,enable_gqa=gqa)
   finally:
    for obj,name,fn in originals:setattr(obj,name,fn)
   torch.testing.assert_close(actual,expected,rtol=2e-5,atol=2e-6)
