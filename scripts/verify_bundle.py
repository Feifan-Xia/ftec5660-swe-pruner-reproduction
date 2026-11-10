"""Verify packaged file hashes and content-addressed raw observations."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def verify(path):
    observations = 0
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read('MANIFEST.json'))
        expected = {row['path'] for row in manifest['files']}
        if len(expected) != len(manifest['files']):
            raise ValueError('Duplicate manifest entry')
        if set(archive.namelist()) != expected | {'MANIFEST.json'}:
            raise ValueError('ZIP contents differ from manifest')
        for row in manifest['files']:
            data = archive.read(row['path'])
            digest = hashlib.sha256(data).hexdigest()
            if digest != row['sha256'] or len(data) != row['bytes']:
                raise ValueError('File hash or size mismatch: ' + row['path'])
            if row['path'].startswith('runs/') and digest != row['source_sha256']:
                raise ValueError('Raw evidence changed: ' + row['path'])
            if row['path'].endswith('/observations.json'):
                store = json.loads(data)
                for key, text in store['observations'].items():
                    if key != 'obs_' + hashlib.sha256(text.encode()).hexdigest()[:16]:
                        raise ValueError('Observation content ID mismatch: ' + row['path'])
                    observations += 1
                for read in store['reads']:
                    lines = store['observations'][read['observation_id']].splitlines(keepends=True)
                    text = ''.join(lines[read['start'] - 1:read['end']])
                    if len(text) != read['returned_chars']:
                        raise ValueError('Recovery length mismatch: ' + row['path'])
    print(f'Verified {len(expected)} files and {observations} raw observation IDs: {path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    verify(parser.parse_args().archive)
