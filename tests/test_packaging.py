import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "lighthouse"


def run_extension_command(*args):
    return subprocess.run(
        ["blender", "--factory-startup", "--command", "extension", *args],
        capture_output=True,
        text=True,
    )


def test_manifest_validates():
    result = run_extension_command("validate", str(SOURCE))

    assert result.returncode == 0, result.stdout + result.stderr


def test_build_produces_installable_zip(tmp_path):
    result = run_extension_command(
        "build", "--source-dir", str(SOURCE), "--output-dir", str(tmp_path)
    )

    assert result.returncode == 0, result.stdout + result.stderr
    built = list(tmp_path.glob("lighthouse-*.zip"))
    assert len(built) == 1
    with zipfile.ZipFile(built[0]) as archive:
        assert {"blender_manifest.toml", "__init__.py"} <= set(archive.namelist())
