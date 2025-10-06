import os
import sys
import time
import signal
import threading
import subprocess
import webbrowser
from pathlib import Path

# Root of the repo
ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv311" / "Scripts" / "python.exe"

# Frontend static dirs
TRADECRAFT_DIST = ROOT / "tradecraft-console-main" / "tradecraft-console-main" / "dist"
LEGACY_FRONTEND = ROOT / "frontend"
STATIC_DIR = TRADECRAFT_DIST if TRADECRAFT_DIST.exists() else LEGACY_FRONTEND


BACKEND_CMD = [
    str(VENV_PY), "-m", "uvicorn", "backend.app:app",
    "--host", "127.0.0.1", "--port", "5001", "--reload",
]
# Use custom SPA server that serves index.html for all routes
FRONTEND_CMD = [
    str(VENV_PY), str(ROOT / "spa_server.py"), "3000", "-d", str(STATIC_DIR)
]

WIN = os.name == "nt"
CREATE_NEW_PROCESS_GROUP = 0x00000200 if WIN else 0


def _print_prefixed(name: str, line: str) -> None:
    sys.stdout.write(f"[{name}] {line}")
    sys.stdout.flush()


def spawn(name: str, cmd: list[str], cwd: Path) -> subprocess.Popen:
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=CREATE_NEW_PROCESS_GROUP,
        )
        return proc
    except FileNotFoundError as e:
        print(f"ERROR starting {name}: {e}")
        print("Hint: Ensure the .venv311 virtual environment exists and dependencies are installed.")
        raise


def stream_output(name: str, proc: subprocess.Popen, ready_event: threading.Event | None, ready_patterns: tuple[str, ...]):
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            _print_prefixed(name, line)
            if ready_event and any(pat in line for pat in ready_patterns):
                ready_event.set()
    except Exception as e:
        print(f"[{name}] output reader error: {e}")


def graceful_kill(proc: subprocess.Popen, name: str, timeout: float = 5.0):
    if proc.poll() is not None:
        return
    try:
        if WIN:
            try:
                os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
            except Exception:
                proc.terminate()
        else:
            proc.send_signal(signal.SIGINT)
        t0 = time.time()
        while proc.poll() is None and time.time() - t0 < timeout:
            time.sleep(0.1)
        if proc.poll() is None:
            proc.kill()
    except Exception as e:
        print(f"WARN: failed to terminate {name}: {e}")


def check_prereqs() -> None:
    if not VENV_PY.exists():
        print(f"ERROR: Could not find Python 3.11 virtualenv interpreter at: {VENV_PY}")
        print("Create it with: 'C:\\Program Files\\Python311\\python.exe -m venv .venv311' and install pinned deps.")
        sys.exit(1)
    print(f"Serving frontend from: {STATIC_DIR}")



def main(open_browser: bool = True) -> int:
    check_prereqs()

    print("Starting MT5 trading workstation...")

    # Backend
    be_ready = threading.Event()
    be_proc = spawn("backend", BACKEND_CMD, ROOT)
    be_thread = threading.Thread(
        target=stream_output,
        args=("backend", be_proc, be_ready, ("Application startup complete", "Uvicorn running")),
        daemon=True,
    )
    be_thread.start()

    # Frontend
    fe_ready = threading.Event()
    fe_proc = spawn("frontend", FRONTEND_CMD, ROOT)
    fe_thread = threading.Thread(
        target=stream_output,
        args=("frontend", fe_proc, None, ()),
        daemon=True,
    )
    fe_thread.start()

    # Wait for readiness
    print("Waiting for services to become ready...")
    be_ready.wait(timeout=30)

    # Frontend readiness via HTTP polling
    def _poll_frontend(timeout: float = 20.0) -> bool:
        import urllib.request, urllib.error
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                with urllib.request.urlopen("http://127.0.0.1:3000") as r:
                    if r.status == 200:
                        return True
            except Exception:
                pass
            time.sleep(0.25)
        return False

    fe_ok = _poll_frontend(20.0)

    if be_ready.is_set():
        print("Backend is up: http://127.0.0.1:5001")
    else:
        print("WARN: backend did not report ready within timeout; it may still be starting.")

    if fe_ok:
        print("Frontend is up: http://127.0.0.1:3000")
    else:
        print("WARN: frontend did not report ready within timeout; it may still be starting.")

    if open_browser and fe_ok:
        try:
            webbrowser.open("http://127.0.0.1:3000")
        except Exception as e:
            print(f"WARN: could not open browser automatically: {e}")

    # Monitor processes
    code = 0
    try:
        while True:
            if be_proc.poll() is not None:
                print(f"Backend exited with code {be_proc.returncode}")
                code = be_proc.returncode or 0
                break
            if fe_proc.poll() is not None:
                print(f"Frontend exited with code {fe_proc.returncode}")
                code = fe_proc.returncode or 0
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nCtrl+C received. Shutting down services...")
    finally:
        graceful_kill(be_proc, "backend")
        graceful_kill(fe_proc, "frontend")
        print("All services stopped.")

    return code


if __name__ == "__main__":
    sys.exit(main(open_browser=True))


