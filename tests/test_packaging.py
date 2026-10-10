import subprocess
import tomllib
import zipfile
from pathlib import Path

from blender_runner import blender_binary

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "lighthouse"


def run_extension_command(*args):
    return subprocess.run(
        [blender_binary(), "--factory-startup", "--command", "extension", *args],
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


def built_zip(output_dir):
    result = run_extension_command(
        "build", "--source-dir", str(SOURCE), "--output-dir", str(output_dir)
    )
    assert result.returncode == 0, result.stdout + result.stderr
    (archive,) = output_dir.glob("lighthouse-*.zip")
    return zipfile.ZipFile(archive)


def test_zip_ships_the_gpl3_license(tmp_path):
    with built_zip(tmp_path) as archive:
        text = archive.read("LICENSE").decode()

    assert "GNU GENERAL PUBLIC LICENSE" in text
    assert "Version 3, 29 June 2007" in text


def run_build_script(*args):
    return subprocess.run(
        [str(ROOT / "build.sh"), *args], capture_output=True, text=True
    )


def test_build_script_builds_the_versioned_zip(tmp_path):
    result = run_build_script(str(tmp_path))

    assert result.returncode == 0, result.stdout + result.stderr
    version = tomllib.loads((SOURCE / "blender_manifest.toml").read_text())["version"]
    assert [p.name for p in tmp_path.iterdir()] == [f"lighthouse-{version}.zip"]
