from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"


@pytest.fixture
def examples_dir() -> Path:
    return EXAMPLES


@pytest.fixture
def tmp_state(tmp_path: Path) -> Path:
    d = tmp_path / "state"
    d.mkdir()
    return d
