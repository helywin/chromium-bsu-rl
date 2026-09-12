"""Single-owner POSIX subprocess client. License: Clarified Artistic, game/COPYING."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import threading
import time
from types import TracebackType
from typing import Mapping, Sequence

from .action import Action
from .state import Capabilities, Snapshot, StepResult, boolean, integer, mapping, text


class ProtocolError(RuntimeError):
    """Transport failure; this connection must not be reused."""


class RemoteError(RuntimeError):
    """A valid error response; the connection remains usable."""


class _JsonProcess:
    """Bounded JSON-lines transport; stderr goes to a file, never an undrained pipe."""

    def __init__(self, command: Sequence[str], env: Mapping[str, str], log: Path, timeout: float) -> None:
        self.timeout = timeout
        self._request_id = 0
        self._pending = bytearray()
        self._lock = threading.Lock()
        self._closed = False
        self._selector = selectors.DefaultSelector()
        self._log_path = log
        with log.open("wb") as output:
            self.process = subprocess.Popen(command, env=dict(env), stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=output, bufsize=0)
        assert self.process.stdin is not None and self.process.stdout is not None
        self._selector.register(self.process.stdout, selectors.EVENT_READ)

    def call(self, command: str, **arguments: object) -> object:
        with self._lock:
            if self._closed:
                raise ProtocolError("Game connection is closed")
            self._request_id += 1
            wire = json.dumps({**arguments, "protocol_version": 1, "request_id": self._request_id,
                               "command": command}, allow_nan=False).encode() + b"\n"
            if len(wire) > 8192:
                raise ValueError("Request is too large")
            try:
                assert self.process.stdin is not None and self.process.stdout is not None
                self.process.stdin.write(wire)
                deadline = time.monotonic() + self.timeout
                while b"\n" not in self._pending:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not self._selector.select(remaining):
                        raise TimeoutError(f"Timed out waiting for {command}")
                    chunk = os.read(self.process.stdout.fileno(), 65536)
                    if not chunk:
                        raise EOFError("Game closed the response pipe")
                    self._pending.extend(chunk)
                    if len(self._pending) > 1024 * 1024:
                        raise ValueError("Response exceeds 1 MiB")
                line, _, rest = self._pending.partition(b"\n")
                self._pending = bytearray(rest)
                response = mapping(json.loads(line))
                if integer(response["protocol_version"]) != 1 or integer(response["request_id"]) != self._request_id:
                    raise ValueError("Protocol version/request ID mismatch")
                if not boolean(response["ok"]):
                    error = mapping(response["error"])
                    raise RemoteError(f"{text(error['code'])}: {text(error['message'])}")
                return response["result"]
            except RemoteError:
                raise
            except (OSError, ValueError, KeyError, EOFError, TimeoutError) as exc:
                self.stop()
                with self._log_path.open("rb") as log:
                    log.seek(0, os.SEEK_END)
                    log.seek(max(0, log.tell() - 4096))
                    tail = log.read().decode(errors="replace")
                raise ProtocolError(f"{exc}\nGame log tail:\n{tail}") from exc

    def stop(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self._selector.close()
        if self.process.stdout is not None:
            self.process.stdout.close()


class GameClient:
    """Own a live GUI or a synchronous first-level runtime (optionally headless).

    Defaults locate an editable source checkout's local build. For an installed
    wheel pass binary and data_directory explicitly; game assets are not in the wheel.
    Each instance uses its own temporary preferences/score directory.
    """

    def __init__(self, *, binary: Path | None = None, data_directory: Path | None = None,
                 video_driver: str | None = None, timeout: float = 10.0, debug: bool = False,
                 synchronous: bool = False, render_each_step: bool = True, headless: bool = False) -> None:
        if os.name != "posix":
            raise OSError("GameClient requires Linux/POSIX subprocess pipes. On Windows use WSL2 or Docker; see docs/installation.md.")
        if type(headless) is not bool or (headless and (not synchronous or render_each_step)):
            raise ValueError("headless=True requires synchronous=True and render_each_step=False")
        if type(synchronous) is not bool:
            raise ValueError("synchronous must be a boolean")
        if type(render_each_step) is not bool or (not synchronous and not render_each_step):
            raise ValueError("render_each_step=False requires synchronous=True")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        root = Path(__file__).resolve().parents[1]
        binary = (binary or root / "build/install/bin/chromium-bsu-rl").resolve()
        data_directory = (data_directory or root / "game/data").resolve()
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise FileNotFoundError(f"Build first with scripts/build_chromium_rl.sh: {binary}")
        if not (data_directory / "png").is_dir():
            raise FileNotFoundError(f"Game assets not found: {data_directory}")
        if len(os.fsencode(data_directory)) >= 180:
            raise ValueError("Asset path exceeds the upstream safe path limit")
        self._state = tempfile.TemporaryDirectory(prefix="chromium-rl-")
        self._transport: _JsonProcess | None = None
        state = Path(self._state.name)
        env = os.environ.copy()
        env.update(CHROMIUM_BSU_RL_PROTOCOL="1", CHROMIUM_BSU_RL_STATE_DIR=str(state),
                   CHROMIUM_BSU_SCORE=str(state / "scores"), CHROMIUM_BSU_DATA=str(data_directory),
                   CHROMIUM_BSU_RL_SYNCHRONOUS="1" if synchronous else "0",
                   CHROMIUM_BSU_RL_RENDER="1" if render_each_step else "0",
                   CHROMIUM_BSU_RL_HEADLESS="1" if headless else "0")
        if headless:
            env.pop("DISPLAY", None)
            env.pop("WAYLAND_DISPLAY", None)
        if video_driver is not None:
            env["SDL_VIDEODRIVER"] = video_driver
        command = [str(binary), "--window", "--vidmode", "1", "--noaudio"]
        if debug:
            command.append("--debug")
        try:
            self._transport = _JsonProcess(command, env, state / "game.log", timeout)
            self.capabilities = Capabilities.parse(self._transport.call("hello"))
            if headless and not self.capabilities.headless:
                raise ProtocolError("Native build lacks true headless mode; rebuild first")
            if synchronous and not self.capabilities.step:
                raise ProtocolError("Native build lacks synchronous step; rebuild first")
            if not render_each_step and not self.capabilities.render_free_steps:
                raise ProtocolError("Native build lacks render-free stepping; rebuild first")
        except BaseException:
            if self._transport is not None:
                self._transport.stop()
            self._state.cleanup()
            raise

    def snapshot(self) -> Snapshot:
        if self._transport is None:
            raise ProtocolError("Game client is closed")
        try:
            return Snapshot.parse(self._transport.call("snapshot"), capabilities=self.capabilities)
        except (ValueError, KeyError) as exc:
            self.close()
            raise ProtocolError(f"Invalid snapshot: {exc}") from exc

    def render(self) -> Snapshot:
        """Display the current state without stepping; display/GL still required."""
        if self._transport is None:
            raise ProtocolError("Game client is closed")
        if not self.capabilities.render:
            raise RemoteError("render requires a synchronous split-render native build")
        try:
            return Snapshot.parse(self._transport.call("render"), capabilities=self.capabilities)
        except (ValueError, KeyError) as exc:
            self.close()
            raise ProtocolError(f"Invalid render response: {exc}") from exc

    def step(self, action: Action, *, ticks: int = 1) -> StepResult:
        """Hold an action for 1..50 full ticks; stop early at single-level end.

        IDLE releases buttons; upstream keyboard accumulation decays, not resets.
        Call reset(seed) for repeatable initialization; reward is caller-defined.
        A terminal episode stays frozen until an explicit reset.
        """
        if not isinstance(action, Action):
            raise ValueError("Use an Action enum member, e.g. Action.RIGHT")
        if type(ticks) is not int or not 1 <= ticks <= 50:
            raise ValueError("ticks must be an integer from 1 to 50")
        if self._transport is None:
            raise ProtocolError("Game client is closed")
        if not self.capabilities.step:
            raise RemoteError("step requires GameClient(synchronous=True)")
        try:
            result = StepResult.parse(self._transport.call("step", action=int(action), ticks=ticks),
                                      capabilities=self.capabilities)
            if result.actual_ticks > ticks or (result.actual_ticks < ticks and not result.terminated):
                raise ValueError("Returned tick count does not match request")
            return result
        except (ValueError, KeyError) as exc:
            self.close()
            raise ProtocolError(f"Invalid step result: {exc}") from exc

    def reset(self, seed: int) -> Snapshot:
        """Rebuild a first-level episode in the same process using a uint32 seed.

        Repeatability is scoped to the same native build/configuration/platform.
        """
        if type(seed) is not int or not 0 <= seed <= 4294967295:
            raise ValueError("seed must be an integer from 0 to 4294967295")
        if self._transport is None:
            raise ProtocolError("Game client is closed")
        if not self.capabilities.reset:
            raise RemoteError("This native runtime does not support synchronous reset")
        try:
            return Snapshot.parse(self._transport.call("reset", seed=seed), capabilities=self.capabilities)
        except (ValueError, KeyError) as exc:
            self.close()
            raise ProtocolError(f"Invalid reset snapshot: {exc}") from exc

    def close(self) -> None:
        transport, self._transport = self._transport, None
        if transport is not None:
            try:
                transport.call("close")
            except (ProtocolError, RemoteError):
                pass
            finally:
                transport.stop()
                self._state.cleanup()

    def __enter__(self) -> GameClient:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None,
                 traceback: TracebackType | None) -> None:
        self.close()
