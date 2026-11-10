"""Bound SDPA memory by tiling queries and retaining the complete key axis."""
import torch
import torch.nn.functional as F
def install(model=None,query_tile=256):
 original=F.scaled_dot_product_attention
 def tiled(query,key,value,attn_mask=None,dropout_p=0.0,is_causal=False,scale=None,enable_gqa=False):
  length=query.shape[-2]
  if length<=query_tile:
   return original(query,key,value,attn_mask=attn_mask,dropout_p=dropout_p,is_causal=is_causal,scale=scale,enable_gqa=enable_gqa)
  assert dropout_p==0.0, 'Tiled inference requires dropout disabled'
  chunks=[]
  for start in range(0,length,query_tile):
   end=min(start+query_tile,length);mask=attn_mask
   if mask is not None and mask.shape[-2]>1:mask=mask[...,start:end,:]
   if is_causal:
    causal=torch.arange(key.shape[-2],device=query.device)[None,:]<=torch.arange(start,end,device=query.device)[:,None]
    if mask is None:mask=causal
    elif mask.dtype==torch.bool:mask=mask & causal
    else:mask=mask.masked_fill(~causal,float('-inf'))
   chunks.append(original(query[...,start:end,:],key,value,attn_mask=mask,dropout_p=0.0,is_causal=False,scale=scale,enable_gqa=enable_gqa))
  return torch.cat(chunks,dim=-2)
 F.scaled_dot_product_attention=tiled
 return [(F,'scaled_dot_product_attention',original)]
