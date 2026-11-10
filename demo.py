"""Deterministic local pruning and exact recovery demonstration (no paid API)."""
import argparse
import json
from pathlib import Path
import httpx
from observation_store import ObservationStore

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/demo.json')
    args = parser.parse_args()
    source = ROOT / 'data/streamlink/src/streamlink/plugins/albavision.py'
    code = source.read_text(encoding='utf-8')
    store = ObservationStore()
    key = store.put(code)
    response = httpx.post('http://127.0.0.1:8000/prune', trust_env=False, timeout=90,
        json={'query': 'How does transform_token handle current and previous hour timestamps?',
              'code': code, 'threshold': .4})
    response.raise_for_status()
    result = response.json()
    if result.get('error_msg'):
        raise RuntimeError(result['error_msg'])
    lines = code.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines, 1) if 'def transform_token' in line)
    end = min(start + 24, len(lines))
    recovered = store.expand(key, start, end)
    exact = recovered == ''.join(lines[start-1:end])
    artifact = {'source': str(source.relative_to(ROOT)), 'observation_id': key,
                'pruning': result, 'recovered_start': start, 'recovered_end': end,
                'recovered_text': recovered, 'exact_match': exact, 'manifest': store.manifest(),
                'scope': 'Scripted component demonstration; recovery range is chosen by the demo, not by an LLM.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Original: {result['origin_token_cnt']} tokens / {len(lines)} lines")
    print(f"Pruned: {result['left_token_cnt']} tokens")
    print('\n--- Pruned observation ---\n' + result['pruned_code'])
    print(f'\n--- Expand {key}, lines {start}-{end} ---\n{recovered}')
    print(f'Exact original recovery: {exact}; evidence: {args.output}')
    assert exact

if __name__ == '__main__':
    main()
