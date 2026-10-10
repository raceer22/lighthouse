import pytest

from blender_runner import run_in_blender
from test_packaging import run_extension_command


def test_runner_uses_the_blender_named_by_the_environment(monkeypatch):
    monkeypatch.setenv("BLENDER", "/nonexistent/blender-for-test")

    with pytest.raises(FileNotFoundError, match="blender-for-test"):
        run_in_blender("report(1)")


def test_extension_commands_use_the_blender_named_by_the_environment(monkeypatch):
    monkeypatch.setenv("BLENDER", "/nonexistent/blender-for-test")

    with pytest.raises(FileNotFoundError, match="blender-for-test"):
        run_extension_command("validate", ".")
