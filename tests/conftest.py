import os
import sys
import subprocess
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ghostlink.constants import HISTORY_DB


@pytest.fixture(scope="session", autouse=True)
def install_cli() -> None:
    """Ensure the package is installed so CLI entry points are available."""
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(repo_root)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@pytest.fixture(autouse=True)
def clean_history_db() -> None:
    db_path = Path.cwd() / HISTORY_DB
    if db_path.exists():
        db_path.unlink()
