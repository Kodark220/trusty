"""Minimal GenLayer runtime so AgentTrust can run off-chain for e2e."""
from dataclasses import dataclass
from types import SimpleNamespace


class u256(int):
    def __new__(cls, x=0):
        return int.__new__(cls, int(x))


class Address(str):
    def __new__(cls, val):
        return str.__new__(cls, str(val))


class TreeMap(dict):
    def __contains__(self, key):
        return dict.__contains__(self, key)


class DynArray(list):
    pass


def allow_storage(cls):
    return cls


class UserError(Exception):
    def __init__(self, data):
        super().__init__(data)
        self.data = data
        self.message = data if isinstance(data, str) else str(data)


class _Write:
    def __call__(self, fn):
        return fn

    @property
    def payable(self):
        return self


class _Public:
    def view(self, fn):
        return fn

    write = _Write()


class _Eq:
    def prompt_comparative(self, fn, principle):
        return fn()

    def prompt_non_comparative(self, fn, **kwargs):
        return fn()

    def strict_eq(self, fn):
        return fn()


class _Web:
    def render(self, url, mode="text"):
        return f"model card for {url}"


class _Nondet:
    def __init__(self):
        self.web = _Web()
        self._llm = None

    def exec_prompt(self, prompt, response_format=None):
        if self._llm is None:
            raise RuntimeError("no LLM mock queued")
        return self._llm(prompt)


class Contract:
    pass


public = _Public()
eq_principle = _Eq()
nondet = _Nondet()
vm = SimpleNamespace(UserError=UserError)
message = SimpleNamespace(sender_address=Address("0x00"))


class _GL:
    Contract = Contract
    public = public
    eq_principle = eq_principle
    nondet = nondet
    vm = vm
    message = message


gl = _GL()


def boot(cls, owner):
    inst = object.__new__(cls)
    for name, _ann in getattr(cls, "__annotations__", {}).items():
        if name in ("agents", "agents_by_id", "jobs", "disputes", "balances"):
            setattr(inst, name, TreeMap())
        elif name.endswith("_keys"):
            setattr(inst, name, DynArray())
    cls.__init__(inst, owner)
    return inst
