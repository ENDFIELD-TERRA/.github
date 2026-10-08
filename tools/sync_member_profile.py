"""Mirror the published public README into the members-only organization view.

Run after publishing profile/README.md. Uses the existing gh login, never stores
credentials, and only writes the fixed private destination below.
"""
import argparse
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PUBLIC = 'ENDFIELD-TERRA/.github'
MEMBER = 'ENDFIELD-TERRA/.github-private'
PROFILE = 'profile/README.md'


def api(endpoint, body=None):
    command = ['gh', 'api', endpoint]
    payload = None
    try:
        if body is not None:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', encoding='utf-8', delete=False) as file:
                json.dump(body, file, ensure_ascii=False)
                payload = Path(file.name)
            command += ['--method', 'PUT', '--input', str(payload)]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return json.loads(result.stdout)
    finally:
        if payload is not None:
            payload.unlink(missing_ok=True)


def content(repository, branch):
    item = api(f'repos/{repository}/contents/{PROFILE}?ref={branch}')
    if item.get('type') != 'file' or item.get('encoding') != 'base64':
        raise RuntimeError(f'Unexpected README response from {repository}')
    return item, base64.b64decode(item['content'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare both published READMEs without writing')
    args = parser.parse_args()
    source_repo = api(f'repos/{PUBLIC}')
    target_repo = api(f'repos/{MEMBER}')
    if source_repo['visibility'] != 'public' or target_repo['visibility'] != 'private':
        raise RuntimeError('Expected a public source and a private member-profile repository')
    source, source_bytes = content(PUBLIC, source_repo['default_branch'])
    target, target_bytes = content(MEMBER, target_repo['default_branch'])
    if source_bytes == target_bytes:
        print(f'Public and member READMEs are identical ({source["sha"]}).')
        return 0
    if args.check:
        print('Public and member READMEs differ; no changes made.')
        return 1
    api(f'repos/{MEMBER}/contents/{PROFILE}', {
        'message': f'Sync member profile from public README {source["sha"][:12]}',
        'branch': target_repo['default_branch'],
        'sha': target['sha'],
        'content': base64.b64encode(source_bytes).decode('ascii'),
    })
    current, current_bytes = content(MEMBER, target_repo['default_branch'])
    if current_bytes != source_bytes:
        raise RuntimeError('Member README verification failed after the update')
    print(f'Member README synchronized and verified ({current["sha"]}).')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
