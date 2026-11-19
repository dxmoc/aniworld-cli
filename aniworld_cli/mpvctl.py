"""Talk to mpv over its JSON IPC socket, on every OS.

mpv writes newline-delimited JSON on ``--input-ipc-server``: on POSIX that is a
unix socket, on Windows a named pipe. Requests carry a ``request_id`` and are
answered with the same id; ``script-message`` from a Lua script arrives as a
``client-message`` event. That is the whole protocol surface we need, so there
is no HTTP server, no curl and no extra dependency.

All reads happen on one background thread; callers that need an answer block on
a per-request event, so nothing is ever read from two threads at once.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import threading
import time
from typing import Any, Callable


class MpvError(RuntimeError):
    """mpv returned an error, or the connection died."""


def default_socket_path() -> str:
    """A short path for the IPC endpoint.

    AF_UNIX paths are limited to ~104 bytes, so a deeply nested temp dir or a
    long user name can break it; XDG_RUNTIME_DIR is short and already per-user.
    """
    if sys.platform.startswith("win"):
        return "\\\\.\\pipe\\aniworld-cli-mpv-%d" % os.getpid()
    base = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    return os.path.join(base, "aniworld-cli-%d.sock" % os.getpid())


class Mpv:
    """A live connection to one mpv instance."""

    def __init__(self, path: str | None = None) -> None:
        self.path = path or default_socket_path()
        self.on_client_message: Callable[[list[str]], None] | None = None
        self.on_event: dict[str, Callable[[], None]] = {}
        self._sock: socket.socket | None = None
        self._pipe: Any = None
        self._reader: threading.Thread | None = None
        self._buffer = b""
        self._next_id = 1
        self._lock = threading.Lock()
        self._pending: dict[int, tuple[threading.Event, list[Any]]] = {}
        self._closed = threading.Event()

    # -- connection -----------------------------------------------------
    def connect(self, timeout: float = 15.0) -> None:
        """Wait for mpv to create the endpoint, then connect."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self._open()
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise MpvError("could not connect to mpv at %s" % self.path)
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _open(self) -> None:
        if sys.platform.startswith("win"):
            # One duplex handle is enough: opening the same pipe twice races
            # with mpv's own instance handling.
            self._pipe = open(self.path, "r+b", buffering=0)  # noqa: SIM115
        else:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect(self.path)
            except OSError:
                sock.close()
                raise
            self._sock = sock

    def close(self) -> None:
        self._closed.set()
        for obj in (self._sock, self._pipe):
            try:
                if obj is not None:
                    obj.close()
            except OSError:
                pass

    # -- reading --------------------------------------------------------
    def _read_loop(self) -> None:
        while not self._closed.is_set():
            try:
                chunk = self._recv()
            except (OSError, ValueError):
                break
            if not chunk:
                break
            self._buffer += chunk
            while b"\n" in self._buffer:
                line, self._buffer = self._buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    message = json.loads(line)
                except ValueError:
                    continue
                self._dispatch(message)
        self._closed.set()

    def _recv(self) -> bytes:
        if self._sock is not None:
            return self._sock.recv(65536)
        return self._pipe.read(65536)

    def _dispatch(self, message: dict) -> None:
        if "event" in message:
            name = message["event"]
            if name == "client-message" and self.on_client_message:
                self.on_client_message(list(message.get("args") or []))
            handler = self.on_event.get(name)
            if handler:
                handler()
            return
        request_id = message.get("request_id")
        slot = self._pending.pop(request_id, None)
        if slot is not None:
            event, box = slot
            box.append(message)
            event.set()

    # -- writing --------------------------------------------------------
    def _write(self, payload: dict) -> None:
        data = (json.dumps(payload) + "\n").encode("utf-8")
        if self._sock is not None:
            self._sock.sendall(data)
        else:
            self._pipe.write(data)

    def command(self, *args: Any, wait: bool = False, timeout: float = 5.0) -> Any:
        """Send one command. Returns its ``data`` when ``wait`` is set."""
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            slot = (threading.Event(), [])
            if wait:
                self._pending[request_id] = slot
        self._write({"command": list(args), "request_id": request_id})
        if not wait:
            return None
        event, box = slot
        if not event.wait(timeout):
            self._pending.pop(request_id, None)
            raise MpvError("timeout waiting for %r" % (args,))
        reply = box[-1]
        if reply.get("error") not in (None, "success"):
            raise MpvError(str(reply.get("error")))
        return reply.get("data")

    def get(self, prop: str, timeout: float = 3.0) -> Any:
        return self.command("get_property", prop, wait=True, timeout=timeout)

    def set(self, prop: str, value: Any) -> None:
        self.command("set_property", prop, value)

    def loadfile(self, url: str, start: float | None = None, options: str | None = None) -> None:
        """Replace the current file, optionally at ``start`` seconds.

        The index slot (``-1``) is mandatory: without it mpv reads the "start=…"
        string as the playlist index and fails with ``invalid parameter``.
        """
        args: list[Any] = ["loadfile", url, "replace", -1]
        if start is not None:
            opts = "start=%.3f" % start
            args.append(opts if options is None else opts + "," + options)
        elif options is not None:
            args.append(options)
        self.command(*args)

    def script_message(self, script: str, *args: str) -> None:
        self.command("script-message-to", script, *args)
