from pathlib import Path
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.ui


def test_react_components_and_production_build():
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    assert npm, "Install Node.js and run npm ci --prefix frontend before pytest"
    cwd = Path(__file__).resolve().parents[1] / "frontend"
    for script in ("test", "build"):
        result = subprocess.run([npm, "run", script], cwd=cwd, capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stdout + result.stderr
