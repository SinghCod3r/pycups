from abc import ABC
from functools import singledispatchmethod
from typing import Any
import sys

from cups import _cups

_ffi = _cups.ffi
_lib = _cups.lib


class cupsBaseClass(ABC):
    ffi_name: str
    ffi_free: str
    ffi_value: Any

    @singledispatchmethod
    def __init__(self, arg: Any = None) -> "cupsBaseClass":
        self._owned = True
        self._transferred = False
        if arg is None:
            self.ffi_value = _ffi.new(f"{self.ffi_name} *")
        else:
            raise NotImplementedError

    @__init__.register
    def _(self, arg: str):
        self._owned = True
        self._transferred = False
        self.ffi_value = _ffi.new(f"{self.ffi_name} {arg}")

    @__init__.register(_ffi.CData)
    def _(self, arg: Any):
        self._owned = False
        self._transferred = False
        if arg and self._is_valid_ctype(arg):
            self.ffi_value = arg
        else:
            raise TypeError(
                f"Invalid CFFI type for {self.__class__.__name__}: {type(arg)}"
            )

    @classmethod
    def from_owned_cdata(cls, c_data: Any):
        obj = cls.__new__(cls)
        obj._owned = True
        obj._transferred = False
        obj.ffi_value = c_data
        return obj

    def _transfer_ownership(self):
        """Mark object as transferred (e.g. to a C function that consumes it).
        Prevents __del__ from freeing it."""
        self._owned = False
        self._transferred = True

    def __del__(self):
        # We must not raise exceptions here during shutdown.
        try:
            if not getattr(self, "_owned", False):
                return
            if getattr(self, "_transferred", False):
                return

            # Avoid accessing globals/modules that might be None during shutdown
            _ffi_local = sys.modules.get("cups")._cups.ffi if "cups" in sys.modules else None
            _lib_local = sys.modules.get("cups")._cups.lib if "cups" in sys.modules else None

            if _ffi_local is None or _lib_local is None:
                return

            if getattr(self, "ffi_value", _ffi_local.NULL) == _ffi_local.NULL:
                return

            ffi_free = getattr(self, "ffi_free", None)
            if not ffi_free:
                return

            cffi_free = getattr(_lib_local, ffi_free, None)
            if cffi_free is None:
                return

            cffi_free(self.ffi_value)

            # Prevent double-free
            self.ffi_value = _ffi_local.NULL
            self._owned = False
        except Exception:
            pass

    @property
    def valid(self):
        return self._is_valid_ctype(self.ffi_value)

    @classmethod
    def _is_valid_c_list(cls, ffi_value: Any) -> bool:
        try:
            ctype = _ffi.typeof(ffi_value)
            return ctype.item.kind == "pointer"
        except:
            return False

    @classmethod
    def _is_valid_ctype(cls, ffi_value: Any) -> bool:
        try:
            ctype = _ffi.typeof(ffi_value)
            ctype_name = _ffi.getctype(cls.ffi_name)

            if ctype.kind == "pointer":
                return ctype.item.cname == ctype_name
            return ctype.cname == _ffi.getctype(cls.ffi_name)
        except:
            return False

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.__class__.__name__}(ffi_value={self.ffi_value})"
