"""Pre-mutation admission for the bounded Gate-06 candidate.

No local deployment/cutover is authorized by this Gate. Hosted CI smoke tests
remain possible in disposable runner checkouts, never the canonical product root.
"""
import json
import os
from pathlib import Path
from .blueprint_compatibility import validate, TARGET


def admit(root, *, ci_smoke=False, environment=None):
    root = Path(root).resolve()
    validate(root)
    policy = json.loads((root/'config/blueprint_compatibility.json').read_text(encoding='utf-8-sig'))
    if policy.get('target_commit') != TARGET or policy.get('runtime_cutover_allowed') is not False:
        raise ValueError('GATE06 deployment policy changed: BLOCKED')
    env = os.environ if environment is None else environment
    canonical = str(root).replace('\\','/').rstrip('/').casefold() == 'c:/0_jn1_aeris'
    runner = env.get('RUNNER_ENVIRONMENT') == 'github-hosted'
    workspace = Path(env.get('GITHUB_WORKSPACE', '.')).resolve()
    if ci_smoke and runner and env.get('GITHUB_ACTIONS') == 'true' and workspace == root and not canonical:
        return {'scope':'DISPOSABLE_HOSTED_CI_ONLY', 'runtime_cutover':False}
    raise ValueError('GATE06 forbids runtime cutover/install/E acceptance; separate Human gate required')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ci-smoke',action='store_true')
    args = parser.parse_args()
    from .config import ROOT
    print(json.dumps(admit(ROOT,ci_smoke=args.ci_smoke)))
