"""Write installed package versions and runtime facts, without environment secrets."""
import argparse
from importlib import metadata
import json
from pathlib import Path
import platform
import sys

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
args = parser.parse_args()
names = {d.metadata['Name'] for d in metadata.distributions() if d.metadata.get('Name')}
packages = {name: metadata.version(name) for name in names}
result = {'python': sys.version, 'platform': platform.platform(), 'packages': dict(sorted(packages.items()))}
if 'torch' in packages:
    import torch
    result['gpu'] = {'torch': torch.__version__, 'cuda_runtime': torch.version.cuda,
                     'cuda_available': torch.cuda.is_available(),
                     'device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(f'Captured {len(packages)} packages in {args.output}')
