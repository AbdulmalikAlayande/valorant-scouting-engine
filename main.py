from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
PID_FILE = LOG_DIR / "worker.pid"
STDOUT_LOG = LOG_DIR / "worker.stdout.log"
STDERR_LOG = LOG_DIR / "worker.stderr.log"


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _read_pid(pid_path: Path) -> Optional[int]:
    if not pid_path.exists():
        return None

    try:
        value = pid_path.read_text(encoding="utf-8").strip()
        return int(value)
    except (ValueError, OSError):
        return None


def _write_pid(pid_path: Path, pid: int) -> None:
    _ensure_log_dir()
    pid_path.write_text(str(pid), encoding="utf-8")


def _remove_pid_file(pid_path: Path) -> None:
    if pid_path.exists():
        pid_path.unlink(missing_ok=True)


def _is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _run_worker_foreground(pid_path: Path) -> int:
    existing_pid = _read_pid(pid_path)
    if existing_pid and existing_pid != os.getpid() and _is_pid_running(existing_pid):
        print(f"Worker is already running with PID {existing_pid}.")
        return 1

    _write_pid(pid_path, os.getpid())
    try:
        from jobs.report_generator import start_worker

        start_worker()
        return 0
    finally:
        current_pid = _read_pid(pid_path)
        if current_pid == os.getpid():
            _remove_pid_file(pid_path)


def _start_background(pid_path: Path) -> int:
    existing_pid = _read_pid(pid_path)
    if existing_pid and _is_pid_running(existing_pid):
        print(f"Worker is already running with PID {existing_pid}.")
        return 1

    if existing_pid and not _is_pid_running(existing_pid):
        _remove_pid_file(pid_path)

    _ensure_log_dir()
    stdout_handle = open(STDOUT_LOG, "a", encoding="utf-8")
    stderr_handle = open(STDERR_LOG, "a", encoding="utf-8")

    command = [
        sys.executable,
        str(PROJECT_ROOT / "main.py"),
        "run",
        "--pid-file",
        str(pid_path),
    ]

    popen_kwargs = {
        "cwd": str(PROJECT_ROOT),
        "stdin": subprocess.DEVNULL,
        "stdout": stdout_handle,
        "stderr": stderr_handle,
        "close_fds": True,
    }

    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen(command, **popen_kwargs)
    time.sleep(0.8)

    if process.poll() is not None:
        print("Worker failed to start. Check logs for details:")
        print(f"  stdout: {STDOUT_LOG}")
        print(f"  stderr: {STDERR_LOG}")
        return 1

    started_pid = _read_pid(pid_path) or process.pid
    print(f"Worker started in background with PID {started_pid}.")
    print(f"Logs: {STDOUT_LOG} | {STDERR_LOG}")
    return 0


def _stop_worker(pid_path: Path) -> int:
    pid = _read_pid(pid_path)
    if pid is None:
        print("Worker is already off (no PID file found).")
        return 0

    if not _is_pid_running(pid):
        _remove_pid_file(pid_path)
        print(f"Worker is already off (stale PID {pid} cleaned up).")
        return 0

    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "Unknown error").strip()
            print(f"Failed to stop worker PID {pid}: {message}")
            return 1
    else:
        os.kill(pid, 15)

    for _ in range(30):
        if not _is_pid_running(pid):
            break
        time.sleep(0.1)

    _remove_pid_file(pid_path)
    print(f"Worker stopped (PID {pid}).")
    return 0


def _worker_status(pid_path: Path) -> int:
    pid = _read_pid(pid_path)
    if pid is None:
        print("Worker status: OFF")
        return 0

    if _is_pid_running(pid):
        print(f"Worker status: ON (PID {pid})")
        return 0

    _remove_pid_file(pid_path)
    print(f"Worker status: OFF (removed stale PID {pid})")
    return 0


def _run_once() -> int:
    from jobs.prompt_router import GeneralPromptRouter
    from jobs.report_generator import process_next_job_once

    worker_id = f"manual-once-{os.getpid()}"
    processed = asyncio.run(process_next_job_once(runtime_worker_id=worker_id, router=GeneralPromptRouter()))
    if processed:
        print("Processed one queued job.")
    else:
        print("No queued jobs available.")
    return 0


def _parse_pid_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        return (PROJECT_ROOT / path).resolve()
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stratigen worker process controller")
    sub = parser.add_subparsers(dest="command", required=True)

    on_cmd = sub.add_parser("on", help="Start worker")
    on_cmd.add_argument("--foreground", action="store_true", help="Run in current terminal session")
    on_cmd.add_argument("--pid-file", default=str(PID_FILE), help="Path to PID file")

    off_cmd = sub.add_parser("off", help="Stop worker")
    off_cmd.add_argument("--pid-file", default=str(PID_FILE), help="Path to PID file")

    status_cmd = sub.add_parser("status", help="Show worker status")
    status_cmd.add_argument("--pid-file", default=str(PID_FILE), help="Path to PID file")

    sub.add_parser("once", help="Process at most one queued job and exit")

    run_cmd = sub.add_parser("run", help=argparse.SUPPRESS)
    run_cmd.add_argument("--pid-file", default=str(PID_FILE), help=argparse.SUPPRESS)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "on":
        pid_path = _parse_pid_path(args.pid_file)
        if args.foreground:
            return _run_worker_foreground(pid_path)
        return _start_background(pid_path)

    if args.command == "off":
        return _stop_worker(_parse_pid_path(args.pid_file))

    if args.command == "status":
        return _worker_status(_parse_pid_path(args.pid_file))

    if args.command == "once":
        return _run_once()

    if args.command == "run":
        return _run_worker_foreground(_parse_pid_path(args.pid_file))

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
