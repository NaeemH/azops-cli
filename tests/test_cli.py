"""Smoke tests for the CLI surface."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from __PKG_NAME__ import __version__
from __PKG_NAME__.cli import _path_hint, app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_subcommands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "__CLI_NAME__" in result.stdout
    # Replace `hello` once the placeholder command is removed.
    assert "hello" in result.stdout


def test_hello_default() -> None:
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "world" in result.stdout


def test_hello_named() -> None:
    result = runner.invoke(app, ["hello", "--name", "naeem"])
    assert result.exit_code == 0
    assert "naeem" in result.stdout


@pytest.fixture()
def fake_local_bin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fake HOME whose ~/.local/bin holds an installed console script."""
    monkeypatch.setenv("HOME", str(tmp_path))
    local_bin = tmp_path / ".local" / "bin"
    local_bin.mkdir(parents=True)
    (local_bin / "__CLI_NAME__").write_text("#!/bin/sh\n")
    return local_bin


def test_path_hint_when_local_bin_missing_from_path(fake_local_bin: Path) -> None:
    hint = _path_hint("/usr/bin:/bin")
    assert hint is not None
    assert "pipx ensurepath" in hint
    assert str(fake_local_bin) in hint


def test_path_hint_silent_when_local_bin_on_path(fake_local_bin: Path) -> None:
    path_env = os.pathsep.join(["/usr/bin", str(fake_local_bin)])
    assert _path_hint(path_env) is None


def test_path_hint_matches_unexpanded_tilde_entry(fake_local_bin: Path) -> None:
    """A literal ``~/.local/bin`` PATH entry should count as present."""
    assert _path_hint(os.pathsep.join(["/usr/bin", "~/.local/bin"])) is None


def test_path_hint_none_when_not_installed_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".local" / "bin").mkdir(parents=True)
    assert _path_hint("/usr/bin") is None


def test_root_prints_hint_to_output(fake_local_bin: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "pipx ensurepath" in " ".join(result.output.split())
