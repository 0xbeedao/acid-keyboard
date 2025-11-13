"""Watch files for changes and copy them to a CircuitPython drive."""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Watch one or more files and copy them to the location defined by "
            "CIRCUITPYTHON_DEST when they change."
        )
    )
    parser.add_argument(
        "paths",
        metavar="PATH",
        nargs="+",
        help="Files to watch for changes.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Polling interval in seconds (default: 0.5).",
    )
    return parser.parse_args()


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        logging.debug("No .env file found at %s", env_path)
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # Do not overwrite an environment variable that is already set.
        os.environ.setdefault(key, value)


def resolve_paths(paths: Iterable[str]) -> Dict[Path, Optional[float]]:
    resolved_paths: Dict[Path, Optional[float]] = {}
    cwd = Path.cwd()

    for raw in paths:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = (cwd / path).resolve()
        else:
            path = path.resolve()

        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            logging.warning("File %s does not exist; waiting for it to appear.", path)
            mtime = None

        resolved_paths[path] = mtime

    return resolved_paths


def build_destination_path(file_path: Path, dest_root: Path, cwd: Path) -> Path:
    try:
        relative = file_path.relative_to(cwd)
    except ValueError:
        relative = Path(file_path.name)
    return dest_root / relative


def copy_to_destination(
    file_path: Path,
    destination_root: Path,
    cwd: Path,
) -> None:
    destination_path = build_destination_path(file_path, destination_root, cwd)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(file_path, destination_path)
    logging.info("Copied %s -> %s", file_path, destination_path)


def watch_and_copy(
    files: Dict[Path, Optional[float]],
    destination_root: Path,
    interval: float,
) -> None:
    cwd = Path.cwd()
    while True:
        for source, last_mtime in list(files.items()):
            try:
                current_mtime = source.stat().st_mtime
            except FileNotFoundError:
                if last_mtime is not None:
                    logging.warning("File %s was removed.", source)
                    files[source] = None
                continue

            if last_mtime is None or current_mtime != last_mtime:
                copy_to_destination(source, destination_root, cwd)
                files[source] = current_mtime

        time.sleep(interval)


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    project_root = Path(__file__).resolve().parents[1]
    load_env_file(project_root / ".env")

    dest_value = os.environ.get("CIRCUITPYTHON_DEST")
    if not dest_value:
        logging.error(
            "Environment variable CIRCUITPYTHON_DEST is not set. "
            "Set it in your environment or in %s.",
            project_root / ".env",
        )
        return 1

    destination_root = Path(dest_value).expanduser()
    files = resolve_paths(args.paths)

    logging.info(
        "Watching %d file(s). Destination: %s. Poll interval: %.2fs",
        len(files),
        destination_root,
        args.interval,
    )

    try:
        watch_and_copy(files, destination_root, args.interval)
    except KeyboardInterrupt:
        logging.info("Stopping watcher.")
        return 0
    except Exception:
        logging.exception("Unexpected error while watching files.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
