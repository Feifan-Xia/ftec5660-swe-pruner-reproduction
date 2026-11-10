"""Check inference adaptations on fixed probes using the published checkpoint."""
import json
from pathlib import Path
import torch
from serve_pruner import model, ROOT
from swe_pruner.prune_wrapper import build_input_for_llm

def evaluate(inputs, padding=0, weights=False):
    ids = inputs['input_ids'].to('cuda')
    mask = inputs['attention_mask'].to('cuda')
    if padding:
        ids = torch.nn.functional.pad(ids, (0, padding), value=model.tokenizer.pad_token_id)
        mask = torch.nn.functional.pad(mask, (0, padding), value=0)
    originals = []
    for layer in model.model.fusion_layers:
        original = layer.forward
        originals.append((layer, original))
        def forward(*args, _original=original, **kwargs):
            kwargs['need_weights'] = weights
            return _original(*args, **kwargs)
        layer.forward = forward
    try:
        with torch.no_grad(), torch.amp.autocast('cuda', dtype=torch.float16):
            out = model(input_ids=ids, attention_mask=mask)
        return (out.token_logits[0, inputs['doc_start']:inputs['doc_end']].float().sigmoid().cpu(),
                out.score_logits.float().cpu())
    finally:
        for layer, original in originals:
            layer.forward = original

records = []
for query, code in [
    ('Return the addition result', 'def add(a, b):\n    return a + b\n\ndef unused():\n    return None\n'),
    ('Why are current and previous hours accepted?', (ROOT / 'data/streamlink/src/streamlink/plugins/albavision.py').read_text()[:2400]),
]:
    inputs = build_input_for_llm(query, code, model.tokenizer, instruction=model.instruction)
    base, base_score = evaluate(inputs)
    for label, pad, weights in [('original_attention_weights', 0, True),
                                ('masked_padding_256', 256, False),
                                ('masked_padding_8192', 8192 - inputs['input_ids'].shape[1], False)]:
        other, score = evaluate(inputs, pad, weights)
        records.append({'probe': query, 'adaptation': label, 'code_tokens': len(base),
                        'max_probability_delta': float((base-other).abs().max()),
                        'mean_probability_delta': float((base-other).abs().mean()),
                        'threshold_0_4_disagreements': int(((base >= .4) != (other >= .4)).sum()),
                        'score_log_probability_delta': float((base_score-score).abs().max())})
result = {'torch': torch.__version__, 'weight_dtype': str(next(model.parameters()).dtype),
          'autocast_dtype': 'float16 (upstream default)', 'checks': records,
          'scope': 'Two fixed probes; attention-weight kernel and masked padding (256 extra / full 8192) sensitivity checks. Not exhaustive equivalence proof.'}
(ROOT / 'runs/pruner_numerical_validation.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
