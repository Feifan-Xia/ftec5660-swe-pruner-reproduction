"""Restore the authors' masked right padding to 8192 positions."""
def install():
    import torch
    import swe_pruner.prune_wrapper as wrapper
    original=wrapper.build_input_for_llm
    def padded(*args,**kwargs):
        inputs=original(*args,**kwargs)
        maximum=kwargs.get('max_length',args[3] if len(args)>3 else 8192)
        amount=maximum-inputs['input_ids'].shape[1]
        tokenizer=kwargs.get('tokenizer',args[2] if len(args)>2 else None)
        inputs['input_ids']=torch.nn.functional.pad(inputs['input_ids'],(0,amount),value=tokenizer.pad_token_id)
        inputs['attention_mask']=torch.nn.functional.pad(inputs['attention_mask'],(0,amount),value=0)
        return inputs
    wrapper.build_input_for_llm=padded
