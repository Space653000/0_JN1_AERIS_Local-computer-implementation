"""Install the pinned free numerical runtime in the caller's root-scoped venv.

Offline means no index and no network fallback; stage compatible wheels under
portable_assets/wheels beforehand. Installation is not professional acceptance.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


def dependencies_ready(root: Path) -> bool:
    requirements = [line.strip() for line in (root/'requirements-engineering.txt').read_text().splitlines()
                    if line.strip() and not line.lstrip().startswith('#')]
    # A subprocess avoids reporting a previously imported package after pip changed it.
    pairs = [line.split('==') for line in requirements]
    probe = ('import importlib,sys\n'
             f'for name, version in {pairs!r}:\n'
             '    module = importlib.import_module(name)\n'
             '    if module.__version__ != version: sys.exit(1)\n')
    result = subprocess.run([sys.executable, '-B', '-c', probe], cwd=root,
                            capture_output=True, check=False)
    return result.returncode == 0


def ensure_dependencies(root: Path, *, offline: bool) -> None:
    if dependencies_ready(root):
        print('ENGINEERING_DEPENDENCIES=AVAILABLE_PINNED_VERSIONS')
        return
    cache = root/'.aeris/pip-cache'
    temporary = root/'.aeris/test-temp'
    cache.mkdir(parents=True, exist_ok=True)
    temporary.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary),
               PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-m', 'pip', '--isolated', '--require-virtualenv', 'install', '--disable-pip-version-check',
               '--no-input', '--only-binary=:all:', '--cache-dir', str(cache),
               '-r', str(root/'requirements-engineering.txt')]
    if offline:
        command += ['--no-index', '--find-links', str(root/'portable_assets/wheels')]
    subprocess.run(command, cwd=root, env=env, check=True)
    if not dependencies_ready(root):
        raise RuntimeError('Engineering dependency import/version verification failed')
    print('ENGINEERING_DEPENDENCIES=INSTALLED_AND_IMPORT_VERIFIED')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('auto', 'offline', 'local', 'cloud'), default='auto')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    if Path(sys.prefix).resolve() != (root/'.venv').resolve():
        raise RuntimeError('Use the root-scoped virtual environment, not system Python')
    ensure_dependencies(root, offline=args.mode == 'offline')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
