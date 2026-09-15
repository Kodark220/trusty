"""Local compatibility fixes for the installed GenLayer test runner."""

import os
import tempfile

import gltest.direct.loader as loader
from gltest.direct.sdk_compat import import_address, import_calldata
from gltest.direct.vm import VMContext


def _inject_message_without_early_unlink(vm: VMContext) -> None:
    calldata = import_calldata()
    Address = import_address()

    def normalize(value):
        return Address(value) if isinstance(value, bytes) else value

    message_data = {
        "contract_address": normalize(vm._contract_address),
        "sender_address": normalize(vm.sender),
        "origin_address": normalize(vm.origin),
        "stack": [],
        "value": vm._value,
        "datetime": vm._datetime,
        "is_init": False,
        "chain_id": vm._chain_id,
        "entry_kind": 0,
        "entry_data": b"",
        "entry_stage_data": None,
    }
    encoded = calldata.encode(message_data)
    fd, path = tempfile.mkstemp()
    os.write(fd, encoded)
    os.lseek(fd, 0, os.SEEK_SET)
    vm._original_stdin_fd = os.dup(0)
    os.dup2(fd, 0)
    os.close(fd)
    vm._direct_stdin_path = path


_original_cleanup = VMContext._cleanup_after_deactivate


def _cleanup_with_tempfile(self: VMContext) -> None:
    path = getattr(self, "_direct_stdin_path", None)
    try:
        _original_cleanup(self)
    finally:
        if path:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
            self._direct_stdin_path = None


loader._inject_message_to_fd0 = _inject_message_without_early_unlink
VMContext._cleanup_after_deactivate = _cleanup_with_tempfile