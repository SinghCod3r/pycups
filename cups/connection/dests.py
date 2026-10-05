from cups import _cups
from cups.types.cups import cupsDest, cupsDestInfo
from cups.types.media import cupsMedia
from cups.types.ipp import IPPAttribute, IPPRequest, IPPStatus, IPPError
from cups.enums.cups import CUPSDestFlags
from cups.enums.media import CUPSMediaFlags
from cups.enums.ipp import IPPOp, IPPTag
from typing import Any, Dict, Optional, Sequence, Union
from cups.utils import _bytes_to_value

from .base import _Base

_ffi = _cups.ffi
_lib = _cups.lib


class DestsMixin(_Base):
    http: Any

    def addDest(self, name: str, instance: Optional[str] = None) -> Dict[str, cupsDest]:
        c_name = _ffi.new("char[]", name.encode("utf-8"))
        c_instance = (
            _ffi.new("char[]", instance.encode("utf-8")) if instance else _ffi.NULL
        )

        c_dests_ptr = _ffi.new("cups_dest_t **")
        count: int = _lib.cupsGetDests(self.http, c_dests_ptr)
        free_count = count

        try:
            new_count = _lib.cupsAddDest(c_name, c_instance, count, c_dests_ptr)
            if new_count > 0:
                free_count = new_count
            if new_count == 0 or c_dests_ptr[0] == _ffi.NULL:
                return {}
            return cupsDest.from_cffi_list(c_dests_ptr[0], new_count)
        finally:
            if free_count > 0 and c_dests_ptr[0] != _ffi.NULL:
                _lib.cupsFreeDests(free_count, c_dests_ptr[0])

    def findDestDefault(self, dest: cupsDest, dinfo: cupsDestInfo, option: str) -> IPPAttribute:
        c_dest, keepalive = dest.to_cffi()
        return IPPAttribute(
            _lib.cupsFindDestDefault(
                self.http, c_dest, dinfo.ffi_value, option.encode()
            ),
            parent=dinfo,
        )

    def findDestReady(self, dest: cupsDest, dinfo: cupsDestInfo, option: str) -> IPPAttribute:
        c_dest, keepalive = dest.to_cffi()
        return IPPAttribute(
            _lib.cupsFindDestReady(
                self.http, c_dest, dinfo.ffi_value, option.encode()
            ),
            parent=dinfo,
        )

    def findDestSupported(self, dest: cupsDest, dinfo: cupsDestInfo, option: str) -> IPPAttribute:
        c_dest, keepalive = dest.to_cffi()
        return IPPAttribute(
            _lib.cupsFindDestSupported(
                self.http, c_dest, dinfo.ffi_value, option.encode()
            ),
            parent=dinfo,
        )


    def getDefault(self) -> str:
        return _bytes_to_value(_lib.cupsGetDefault(self.http))

    def getDests(self) -> Dict[str, cupsDest]:
        c_dests = _ffi.new("cups_dest_t **")
        count: int = _lib.cupsGetDests(self.http, c_dests)
        try:
            if count == 0 or c_dests[0] == _ffi.NULL:
                return {}
            return cupsDest.from_cffi_list(c_dests[0], count)
        finally:
            if count > 0 and c_dests[0] != _ffi.NULL:
                _lib.cupsFreeDests(count, c_dests[0])

    def setDests(self, dests: Union[Dict[str, cupsDest], Sequence[cupsDest]]) -> bool:
        c_dests, keepalive = cupsDest.to_cffi_list(dests)
        return bool(_lib.cupsSetDests(self.http, len(dests), c_dests))

    def copyDestInfo(
        self, dest: cupsDest, flags: CUPSDestFlags = CUPSDestFlags.NONE
    ) -> cupsDestInfo:
        c_dest, keepalive = dest.to_cffi()
        return cupsDestInfo.from_owned_cdata(
            _lib.cupsCopyDestInfo(self.http, c_dest, flags.value)
        )

    def checkDestSupported(
        self,
        dest: cupsDest,
        dinfo: cupsDestInfo,
        option: str,
        value: Optional[str] = None,
    ) -> bool:
        c_dest, keepalive = dest.to_cffi()
        return bool(
            _bytes_to_value(
                _lib.cupsCheckDestSupported(
                    self.http,
                    c_dest,
                    dinfo.ffi_value,
                    option.encode(),
                    value.encode() if value else _ffi.NULL,
                )
            )
        )
