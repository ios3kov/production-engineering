#!/usr/bin/env python3
"""Opt-in corrected REA runner. Local integrity checking is not an OS sandbox.

The ordinary 6.5.0 adapter stays quarantined. This entrypoint accepts only the
exact separately qualified runtime manifest pinned in profile.json. Run with
read-only runtime/input mounts and network disabled; no installation occurs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import resource
import signal
import stat
import subprocess
import sys

HERE = Path(__file__).resolve().parent
COMMANDS = {
    'javascript': 'analyze-javascript-application',
    'view': 'inspect-analysis-view',
    'feature-trace': 'trace-application-feature',
    'semantic-trace': 'trace-javascript-semantics',
    'compare-applications': 'compare-application-versions',
}
MAX_JSON = 8 * 1024 * 1024


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def load(path):
    with Path(path).open('rb') as f:
        data = f.read(MAX_JSON + 1)
    if len(data) > MAX_JSON:
        raise ValueError('JSON input exceeds the explicit 8 MiB profile')
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON')))


def digest_file(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def verify_tree(root, manifest_path, expected_digest):
    """Verify an externally pinned manifest, its bytes and all listed entries."""
    root = Path(root)
    if not root.is_absolute() or any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('Runtime root must be an absolute unlinked directory')
    if not root.is_dir() or digest_file(manifest_path) != expected_digest:
        raise ValueError('Runtime manifest is not the reviewed exact manifest')
    manifest = load(manifest_path)
    if manifest.get('runtime_id') != 'rea-6.5.0-patch3552.1':
        raise ValueError('Unknown corrected runtime identity')
    seen = set()
    entries = manifest.get('entries')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Runtime manifest has no entries')
    for entry in entries:
        relative = entry.get('path')
        if not isinstance(relative, str) or '\\' in relative or '\x00' in relative:
            raise ValueError('Invalid runtime path')
        p = PurePosixPath(relative)
        if p.is_absolute() or '..' in p.parts or str(p) != relative or relative in seen:
            raise ValueError('Unsafe or duplicate runtime path')
        seen.add(relative)
        full = root.joinpath(*p.parts)
        if any(x.is_symlink() for x in full.parents if x != root and x.is_relative_to(root)):
            raise ValueError('Linked runtime ancestor')
        mode = full.lstat().st_mode
        if 'link' in entry:
            if not stat.S_ISLNK(mode) or os.readlink(full) != entry['link']:
                raise ValueError('Runtime link differs: ' + relative)
            if not full.resolve(strict=True).is_relative_to(root):
                raise ValueError('Runtime link escapes prefix')
        elif not stat.S_ISREG(mode) or full.stat().st_size != entry['bytes'] or digest_file(full) != entry['sha256']:
            raise ValueError('Runtime file differs: ' + relative)
    # Additional entries in the covered runtime roots invalidate this copy.
    roots = {PurePosixPath(p).parts[0] for p in seen}
    actual = set()
    for name in roots:
        top = root / name
        if top.is_symlink() or top.is_file():
            actual.add(name)
        else:
            for directory, dirs, files in os.walk(top, followlinks=False):
                for link in list(dirs):
                    q = Path(directory) / link
                    if q.is_symlink():
                        actual.add(q.relative_to(root).as_posix()); dirs.remove(link)
                actual.update((Path(directory) / f).relative_to(root).as_posix() for f in files)
    if actual != seen:
        raise ValueError('Runtime inventory differs from the qualified copy')
    return manifest


def child_limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024 * 1024, 256 * 1024 * 1024))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify', 'run'])
    parser.add_argument('--runtime-root', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--node', default='/usr/local/bin/node')
    parser.add_argument('--operation', choices=sorted(COMMANDS))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path, help='New output directory; never overwrites an earlier run')
    args = parser.parse_args(argv)
    try:
        profile = load(HERE / 'profile.json')['corrected_runtime']
        if sys.platform != 'linux' or platform.machine() not in ('x86_64', 'AMD64'):
            raise ValueError('This qualified runtime is Linux x64; use its pinned container')
        manifest = verify_tree(args.runtime_root, args.manifest, profile['manifest_sha256'])
        identity = manifest['runtime_id']
        if args.action == 'verify':
            print(json.dumps({'runtime_id': identity, 'integrity': 'MATCH', 'product_readiness': 'NOT_ASSESSED'})); return 0
        if not args.operation or not args.input or not args.output:
            raise ValueError('run requires operation, input and a new output directory')
        if not args.input.is_absolute() or not args.input.exists() or any(p.is_symlink() for p in (args.input, *args.input.parents)):
            raise ValueError('Input must be an existing absolute unlinked path')
        if args.operation != 'javascript' and not isinstance(load(args.input), dict):
            raise ValueError('This operation requires a complete structured Evidence request')
        if not args.output.is_absolute() or args.output.exists() or any(p.is_symlink() for p in args.output.parents):
            raise ValueError('Output must be a new absolute unlinked directory')
        node = Path(args.node)
        if not node.is_absolute() or not node.is_file():
            raise ValueError('Explicit trusted Node executable required')
        version = subprocess.run([str(node), '--version'], capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        if version != profile['node']:
            raise ValueError('Node version differs from the qualified runtime')
        args.output.mkdir(mode=0o700)
        home = args.output / 'home'; home.mkdir(mode=0o700)
        temp = args.output / 'tmp'; temp.mkdir(mode=0o700)
        command = [str(node), str(args.runtime_root / 'scripts/rea.mjs'), COMMANDS[args.operation], str(args.input), '--json']
        env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(home), 'TMPDIR': str(temp), 'NO_COLOR': '1', 'REA_LOG_LEVEL': 'silent'}
        timed_out = False
        with (args.output / 'stdout.json').open('xb') as stdout, (args.output / 'stderr.txt').open('xb') as stderr:
            process = subprocess.Popen(command, cwd=args.output, env=env, stdout=stdout, stderr=stderr,
                                       start_new_session=True, preexec_fn=child_limits)
            try:
                code = process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait(timeout=10)
        receipt = {'runtime_id': identity, 'manifest_sha256': profile['manifest_sha256'], 'command': command,
                   'exit_code': code, 'timed_out': timed_out, 'stdout_sha256': digest_file(args.output / 'stdout.json'),
                   'stderr_sha256': digest_file(args.output / 'stderr.txt'), 'analysis_status': 'NEEDS_REVIEW' if code == 0 else 'FAILED_OR_INCOMPLETE',
                   'product_readiness': 'NOT_ASSESSED', 'limitations': ['No runtime/application correctness certification',
                   'Use only newly collected corrected-runtime Evidence; old 6.5.0 JS observations stay quarantined',
                   'Filesystem integrity is not producer authentication or OS isolation']}
        (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(receipt)); return 0 if code == 0 else 1
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'BLOCKED', 'error': str(error)}), file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())
