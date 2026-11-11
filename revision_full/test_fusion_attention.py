"""Compare the bounded fusion calculation with the actual original MHA path."""
import contextlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
import torch.nn.functional as F
from revision_full.fusion_attention import explicit_attention
class FusionTest(unittest.TestCase):
    def test_original_mha_with_padding(self):
        previous_fastpath=torch.backends.mha.get_fastpath_enabled()
        torch.backends.mha.set_fastpath_enabled(False)
        self.addCleanup(torch.backends.mha.set_fastpath_enabled,previous_fastpath)
        cases=[('cpu',torch.float32,None)]+([('cuda',torch.float16,None),('cuda',torch.float32,torch.float16)] if torch.cuda.is_available() else [])
        for device,dtype,autocast in cases:
            torch.manual_seed(5660)
            layer=torch.nn.MultiheadAttention(96,4,batch_first=True,dropout=0).to(device=device,dtype=dtype).eval()
            value=torch.randn(1,601,96,device=device,dtype=dtype)
            padding=torch.zeros(1,601,device=device,dtype=torch.bool);padding[:,-53:]=True
            def context():return torch.autocast(device_type=device,dtype=autocast) if autocast else contextlib.nullcontext()
            with torch.no_grad(),context():expected=layer(value,value,value,key_padding_mask=padding,need_weights=True)[0]
            original=F.scaled_dot_product_attention
            calls=[]
            def replacement(q,k,v,attn_mask=None,dropout_p=0,is_causal=False,**kwargs):
                calls.append(True)
                return explicit_attention(q,k,v,attn_mask,query_tile=127)
            F.scaled_dot_product_attention=replacement
            try:
                with torch.no_grad(),context():actual=layer(value,value,value,key_padding_mask=padding,need_weights=False)[0]
            finally:F.scaled_dot_product_attention=original
            self.assertEqual(len(calls),1)
            high_precision=dtype==torch.float32 and autocast is None
            torch.testing.assert_close(actual,expected,rtol=1e-5 if high_precision else 2e-3,atol=2e-7 if high_precision else 2e-4)
            print(device,str(dtype),'autocast',str(autocast),'max_absolute_difference',float((actual-expected).abs().max()),flush=True)
if __name__=='__main__':unittest.main()
