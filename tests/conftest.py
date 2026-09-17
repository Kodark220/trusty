"""Compatibility glue for gltest with the current GenLayer Python SDK."""

import os
import tempfile

import gltest.direct.loader as loader
from gltest.direct.sdk_compat import import_address, import_calldata
from gltest.direct.vm import VMContext


def _inject_message(vm: VMContext) -> None:
	try:
		calldata = import_calldata()
	except ImportError:
		from genlayer.py import calldata
	try:
		Address = import_address()
	except ImportError:
		from genlayer.py.types import Address

	def normalize(value):
		return Address(value) if isinstance(value, bytes) else value

	data = {
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
	fd, path = tempfile.mkstemp()
	os.write(fd, calldata.encode(data))
	os.lseek(fd, 0, os.SEEK_SET)
	vm._original_stdin_fd = os.dup(0)
	os.dup2(fd, 0)
	os.close(fd)
	vm._direct_stdin_path = path


def _allocate_contract(contract_cls, vm, *args, **kwargs):
	from genlayer.storage import ROOT_SLOT_ID
	try:
		from genlayer.storage._internal.generate import ORIGINAL_INIT_ATTR, _storage_build, _BuilderCtx
		ctx = _BuilderCtx({}, None)
		descriptor = _storage_build(ctx, contract_cls)
	except Exception:
		from genlayer.storage._internal.generate import ORIGINAL_INIT_ATTR, _storage_build
		descriptor = _storage_build(contract_cls, {})

	instance = descriptor.get(vm._storage.get_store_slot(ROOT_SLOT_ID), 0)
	init = getattr(descriptor.cls, "__init__", None)
	if init and hasattr(init, ORIGINAL_INIT_ATTR):
		init = getattr(init, ORIGINAL_INIT_ATTR)
	if init:
		init(instance, *args, **kwargs)
	return instance


def _cleanup(self: VMContext) -> None:
	path = getattr(self, "_direct_stdin_path", None)
	original = getattr(self, "_original_stdin_fd", None)
	if original is not None:
		os.dup2(original, 0)
		os.close(original)
		self._original_stdin_fd = None
	if path:
		try:
			os.unlink(path)
		except FileNotFoundError:
			pass
		self._direct_stdin_path = None


loader._inject_message_to_fd0 = _inject_message
loader._allocate_contract = _allocate_contract
VMContext._cleanup_after_deactivate = _cleanup

_load_module = loader._load_module


def _load_contract_module(contract_path):
	try:
		import genlayer.contract as genlayer_contract
		genlayer_contract.__known_contract__ = None
	except Exception:
		pass
	try:
		import genlayer.gl.genvm_contracts as genvm_contracts
		genvm_contracts.__known_contract__ = None
	except Exception:
		pass
	return _load_module(contract_path)


loader._load_module = _load_contract_module