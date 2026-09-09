"""Installer must provision its own venv, not inherit CI host packages."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('engineering_bootstrap', ROOT/'scripts/bootstrap-engineering.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class EngineeringBootstrapTests(unittest.TestCase):
    def test_python_optimization_cannot_skip_missing_package_probe(self):
        with patch.object(bootstrap.Path, 'read_text', return_value='certainly_missing_aeris_package==0.0.0'), patch.dict(os.environ, {'PYTHONOPTIMIZE':'1'}):
            self.assertFalse(bootstrap.dependencies_ready(ROOT))

    def test_installed_dependencies_do_not_access_network(self):
        with patch.object(bootstrap, 'dependencies_ready', return_value=True), patch.object(bootstrap.subprocess, 'run') as run:
            bootstrap.ensure_dependencies(ROOT, offline=True)
        run.assert_not_called()

    def test_missing_packages_install_only_into_current_venv_with_root_cache(self):
        with patch.object(bootstrap, 'dependencies_ready', side_effect=[False, True]), patch.object(bootstrap.subprocess, 'run') as run:
            bootstrap.ensure_dependencies(ROOT, offline=False)
        args = run.call_args.args[0]
        self.assertEqual(args[:4], [sys.executable, '-m', 'pip', '--isolated'])
        self.assertIn('--only-binary=:all:', args)
        self.assertIn(str(ROOT/'requirements-engineering.txt'), args)
        self.assertIn(str(ROOT/'.aeris/pip-cache'), args)
        self.assertEqual(run.call_args.kwargs['env']['TMP'], str(ROOT/'.aeris/test-temp'))
        self.assertTrue(run.call_args.kwargs['check'])

    def test_offline_never_falls_back_to_network(self):
        with patch.object(bootstrap, 'dependencies_ready', return_value=False), patch.object(bootstrap.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'pip')) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                bootstrap.ensure_dependencies(ROOT, offline=True)
        args = run.call_args.args[0]
        self.assertIn('--no-index', args)
        self.assertIn(str(ROOT/'portable_assets/wheels'), args)
        self.assertEqual(run.call_count, 1)

    def test_successful_pip_without_importable_dependencies_is_failure(self):
        with patch.object(bootstrap, 'dependencies_ready', return_value=False), patch.object(bootstrap.subprocess, 'run'):
            with self.assertRaisesRegex(RuntimeError, 'verification failed'):
                bootstrap.ensure_dependencies(ROOT, offline=False)

    def test_all_install_entrypoints_bootstrap_before_unit_tests(self):
        for name in ('one-click-install.ps1', 'one-click-install.sh', 'bootstrap.ps1', 'bootstrap.sh'):
            with self.subTest(name=name):
                source = (ROOT/'scripts'/name).read_text(encoding='utf-8')
                self.assertLess(source.index('bootstrap-engineering.py'), source.index('-m unittest'))

    def test_non_venv_interpreter_rejected(self):
        with patch.object(bootstrap.sys, 'prefix', str(ROOT)), patch.object(bootstrap, 'ensure_dependencies') as install:
            with self.assertRaisesRegex(RuntimeError, 'root-scoped virtual environment'):
                bootstrap.main([])
        install.assert_not_called()
