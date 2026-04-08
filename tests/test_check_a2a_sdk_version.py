"""Tests for scripts/check_a2a_sdk_version.py (imported via importlib)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from packaging.version import Version

ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = ROOT / "scripts" / "check_a2a_sdk_version.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("check_a2a_sdk_version", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def chk():
    return _load_script()


def test_pinned_a2a_sdk_version_parses_extras(chk, tmp_path: Path) -> None:
    pp = tmp_path / "pyproject.toml"
    pp.write_text(
        '[project]\ndependencies = [\n  "httpx>=1",\n  "a2a-sdk[http-server,sqlite]==1.0.0a0",\n]\n'
    )
    assert chk.pinned_a2a_sdk_version(pp) == Version("1.0.0a0")


def test_pinned_missing_raises(chk, tmp_path: Path) -> None:
    pp = tmp_path / "pyproject.toml"
    pp.write_text('[project]\ndependencies = ["httpx>=1"]\n')
    with pytest.raises(ValueError, match="no a2a-sdk"):
        chk.pinned_a2a_sdk_version(pp)


def test_max_version_from_release_keys_skips_invalid(chk) -> None:
    v = chk.max_version_from_release_keys(["not-a-version", "1.0.0", "1.0.1a1"])
    assert v == Version("1.0.1a1")


def test_max_version_from_release_keys_empty_raises(chk) -> None:
    with pytest.raises(ValueError, match="no valid"):
        chk.max_version_from_release_keys([])


def test_main_ok_when_pin_is_latest(chk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pp = tmp_path / "pyproject.toml"
    pp.write_text('[project]\ndependencies = ["a2a-sdk==2.1.0"]\n')
    monkeypatch.setattr(chk, "max_version_on_pypi", lambda package="a2a-sdk": Version("2.1.0"))
    assert chk.main(pp) == 0


def test_main_fails_when_pypi_newer(chk, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pp = tmp_path / "pyproject.toml"
    pp.write_text('[project]\ndependencies = ["a2a-sdk==1.0.0"]\n')
    monkeypatch.setattr(chk, "max_version_on_pypi", lambda package="a2a-sdk": Version("1.0.1"))
    assert chk.main(pp) == 1
