import pytest


@pytest.fixture(autouse=True)
def _data_dir(tmp_path, monkeypatch):
    """No test ever writes to the real data directory (conventions: tests and temp dirs)."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
