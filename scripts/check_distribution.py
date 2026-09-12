"""Check distribution contents and install the wheel outside the source tree.

Run after python -m build. --native also builds the extracted sdist and runs
its headless example against the installed wheel. Artifacts stay in artifacts/.
"""
import argparse
from email.parser import Parser
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    stem = f"chromium_bsu_rl-{project['version']}"
    wheel = root / "dist" / f"{stem}-py3-none-any.whl"
    sdist = root / "dist" / f"{stem}.tar.gz"
    licenses = project["license-files"]
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        for path in root.joinpath("chromium_rl").glob("*.py"):
            assert f"chromium_rl/{path.name}" in names, f"Missing module: {path.name}"
        assert "chromium_rl/py.typed" in names
        assert all(n.startswith(("chromium_rl/", f"{stem}.dist-info/")) for n in names)
        for path in licenses:
            assert archive.read(f"{stem}.dist-info/licenses/{path}") == (root / path).read_bytes()
        metadata = Parser().parsestr(archive.read(f"{stem}.dist-info/METADATA").decode())
        assert metadata["Name"] == project["name"]
        assert metadata["Version"] == project["version"]
        assert metadata["License-Expression"] == project["license"]
        assert metadata["Requires-Python"] == project["requires-python"]

    with tarfile.open(sdist) as archive:
        names = set(archive.getnames())
        expected = ["README.md", "README.zh-CN.md", "pyproject.toml", "MANIFEST.in", "Dockerfile", *licenses]
        for directory in ("game", "chromium_rl", "scripts", "examples", "docs", "tests", ".github"):
            expected.extend(p.relative_to(root).as_posix() for p in (root / directory).rglob("*")
                            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".pyo"))
        missing = [p for p in expected if f"{stem}/{p}" not in names]
        assert not missing, f"Source distribution is incomplete: {missing}"
        assert not any(set(Path(n).parts[1:]) & {".venv", "build", "artifacts", "__pycache__", ".git"} for n in names)

    artifacts = root / "artifacts"
    artifacts.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    with tempfile.TemporaryDirectory(prefix="package-", dir=artifacts) as temporary:
        work = Path(temporary)
        venv = work / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, env=env)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                        "--no-index", "--no-deps", str(wheel)], check=True, cwd=work, env=env)
        subprocess.run([str(python), "-c",
                        "import sys, chromium_rl; from pathlib import Path; "
                        "from chromium_rl import GameClient, PowerUpState, EpisodeEvents; "
                        "assert Path(chromium_rl.__file__).is_relative_to(sys.prefix); "
                        "print('Installed wheel imports independently of the checkout')"],
                       check=True, cwd=work, env=env)
        if args.native:
            with tarfile.open(sdist) as archive:
                archive.extractall(work, filter="data")
            source = work / stem
            log_path = artifacts / "sdist-native-build.log"
            with log_path.open("w") as log:
                result = subprocess.run(["bash", "scripts/build_chromium_rl.sh"], cwd=source,
                                        env=env, stdout=log, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f"Source distribution native build failed:\n{log_path.read_text()[-8000:]}")
            subprocess.run([str(python), str(source / "examples/headless_rollout.py"),
                            "--binary", str(source / "build/install/bin/chromium-bsu-rl"),
                            "--data-dir", str(source / "game/data"), "--seed", "7"],
                           check=True, cwd=work, env=env)
    print("PASS: distribution contents, notices and isolated wheel installation" +
          ("; extracted sdist native build and headless rollout" if args.native else ""))


if __name__ == "__main__":
    main()
