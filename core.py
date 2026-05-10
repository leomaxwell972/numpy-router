# numpy_router/core.py
import glob
import inspect
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional
import __main__

logger = logging.getLogger("numpy_router")

DEFAULT_PRE_2 = "1.26.4"
DEFAULT_POST_2 = "2.2.0"

CACHE_DIR = Path(os.environ.get("NUMPY_ROUTER_CACHE", Path.home() / ".numpy_router_cache"))
DOWNLOAD_DIR = CACHE_DIR / "_downloads"


def _download_numpy(version: str) -> Path:
    print(f"[numpy_router] Downloading numpy=={version} ...", flush=True)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    python_exe = sys.executable
    env = os.environ.copy()
    env["NUMPY_ROUTER_DISABLE"] = "1"  # if you ever want to use it in __init__, it's there

    cmd = [
        python_exe,
        "-m", "pip", "download",
        f"numpy=={version}",
        "-d", str(DOWNLOAD_DIR),
        "--no-deps",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)

    print(f"[numpy_router] Download complete.", flush=True)

    if res.returncode != 0:
        raise RuntimeError(
            f"Failed to download numpy=={version}\n"
            f"stdout:\n{res.stdout}\n\nstderr:\n{res.stderr}"
        )

    pattern = DOWNLOAD_DIR / f"numpy-{version}*"
    matches = glob.glob(str(pattern))
    if not matches:
        raise RuntimeError(f"No archive found for numpy=={version} (pattern {pattern})")

    return Path(matches[0])


def _extract_archive(archive_path: Path, dest_dir: Path) -> None:
    s = str(archive_path)
    if s.endswith((".whl", ".zip")):
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(dest_dir)
    else:
        import tarfile
        with tarfile.open(archive_path, "r:*") as tf:
            tf.extractall(dest_dir)


def ensure_numpy_version_path(version: str) -> str:
    target_dir = CACHE_DIR / version

    # Cache hit
    if target_dir.is_dir() and any(target_dir.iterdir()):
        print(f"[numpy_router] Using cached numpy=={version}", flush=True)
        return str(target_dir)

    # Cache miss → fresh download
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    archive_path = _download_numpy(version)
    print(f"[numpy_router] Extracting numpy=={version} ...", flush=True)
    _extract_archive(archive_path, target_dir)
    print(f"[numpy_router] Extraction complete.", flush=True)

    return str(target_dir)



def _find_requirements_file(root: Path) -> Optional[Path]:
    req = root / "requirements.txt"
    if req.is_file():
        return req
    matches = list(root.glob("*requirements*.txt"))
    return matches[0] if matches else None


def _read_requirements_numpy(req_file: Path) -> Optional[str]:
    try:
        text = req_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("numpy"):
            return line
    return None


def _pick_version_from_requirement(req: str) -> str:
    r = req.strip().lower()
    if "==" in r:
        after = r.split("==", 1)[1]
        after = after.split(";", 1)[0].split("[", 1)[0].strip()
        return after
    if "<2" in r:
        return DEFAULT_PRE_2
    if ">=2" in r or " 2." in r or ">= 2" in r:
        return DEFAULT_POST_2
    return DEFAULT_POST_2



def _find_dist_info_for_package(pkg_name: str) -> Optional[Path]:
    for p in sys.path:
        try:
            base = Path(p)
            if not base.is_dir():
                continue
            for d in base.glob(f"{pkg_name.replace('.', '-')}-*.dist-info"):
                return d
        except Exception:
            pass
    return None

def _read_metadata_requires_numpy(dist_info: Path) -> Optional[str]:
    meta = dist_info / "METADATA"
    if not meta.is_file():
        return None

    try:
        text = meta.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    for line in text.splitlines():
        if line.lower().startswith("requires-dist: numpy"):
            return line
    return None

def resolve_numpy_version_for_caller() -> str:
    forced = os.environ.get("NUMPY_ROUTER_VERSION")
    if forced:
        print(f"[numpy_router] Using user-forced version {forced}", flush=True)
        return forced

    main_file = getattr(__main__, "__file__", None)
    main_root = Path(main_file).resolve().parent if main_file else None

    # 1) requirements.txt next to main script
    if main_root:
        req_file = _find_requirements_file(main_root)
        if req_file:
            req_line = _read_requirements_numpy(req_file)
            if req_line:
                return _pick_version_from_requirement(req_line)

    # 2) dist-info metadata for the caller package
    caller_name = Path(main_file).stem if main_file else None
    if caller_name:
        dist = _find_dist_info_for_package(caller_name)
        if dist:
            req_line = _read_metadata_requires_numpy(dist)
            if req_line:
                return _pick_version_from_requirement(req_line)

    # 3) fallback heuristic
    print(f"[numpy_router] No version info found; guessing {DEFAULT_POST_2}", flush=True)
    return DEFAULT_POST_2

