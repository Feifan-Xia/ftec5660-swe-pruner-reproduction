"""Bound memory while preserving the authors' explicit MHA softmax arithmetic.

The original need_weights=True path scales Q, forms half-precision attention
scores, applies softmax in that dtype, then multiplies by V. SDPA may upcast
those intermediates. Query-row tiling preserves that original operation order
without allocating the entire 8192 x 8192 attention matrix.
"""
import math
import torch
import torch.nn.functional as F

def explicit_attention(query,key,value,attn_mask=None,query_tile=256,scale=None):
    batch,heads,length,dimension=query.shape
    q=query.reshape(batch*heads,length,dimension)
    k=key.reshape(batch*heads,key.shape[-2],dimension)
    v=value.reshape(batch*heads,value.shape[-2],value.shape[-1])
    mask=None
    if attn_mask is not None:
        mask=attn_mask.expand(batch,heads,length,key.shape[-2])
    factor=math.sqrt(1.0/dimension) if scale is None else scale
    chunks=[]
    for start in range(0,length,query_tile):
        end=min(start+query_tile,length)
        scaled_query=q[:,start:end]*factor
        if mask is not None:
            block=mask[:,:,start:end,:].reshape(batch*heads,end-start,key.shape[-2])
            if block.dtype==torch.bool:block=torch.zeros_like(block,dtype=q.dtype).masked_fill(~block,float('-inf'))
            scores=torch.baddbmm(block,scaled_query,k.transpose(1,2))
        else:scores=torch.bmm(scaled_query,k.transpose(1,2))
        probabilities=F.softmax(scores,dim=-1)
        chunks.append(torch.bmm(probabilities,v))
    return torch.cat(chunks,dim=1).reshape(batch,heads,length,value.shape[-1])

def install(model,query_tile=256):
    original=F.scaled_dot_product_attention
    dimensions={layer.embed_dim//layer.num_heads for layer in model.model.fusion_layers}
    def attention(query,key,value,attn_mask=None,dropout_p=0.0,is_causal=False,scale=None,enable_gqa=False):
        if query.shape[-1] in dimensions and not is_causal and query.shape[-3]==key.shape[-3]:
            assert dropout_p==0.0
            return explicit_attention(query,key,value,attn_mask,query_tile,scale)
        return original(query,key,value,attn_mask=attn_mask,dropout_p=dropout_p,is_causal=is_causal,scale=scale,enable_gqa=enable_gqa)
    F.scaled_dot_product_attention=attention
    return original
