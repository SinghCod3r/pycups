from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from cups.enums.ipp import IPPOp, IPPTag
from cups.types.base import _ffi, _lib, cupsBaseClass
from cups.types.http import Http
from cups.types.ipp import IPPAttribute, IPPRequest
from cups.utils import _bytes_to_value

from .option import cupsOption


class cupsDest(cupsBaseClass):
    def __init__(self, arg: Any = None, *, name: str = None, instance: Optional[str] = None, is_default: bool = False, options: Dict[str, cupsOption] = None):
        self._owned = False
        self._transferred = False
        if arg is not None:
            self._name = _bytes_to_value(arg.name)
            self._instance = _bytes_to_value(arg.instance) if arg.instance != _ffi.NULL and arg.instance[0] != b'\x00' else None
            self._is_default = arg.is_default
            self._options = cupsOption.from_cffi_list(arg.options, arg.num_options)
        else:
            self._name = name
            self._instance = instance
            self._is_default = is_default
            self._options = options if options is not None else {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def instance(self) -> Optional[str]:
        return self._instance

    @property
    def options(self) -> Dict[str, cupsOption]:
        return self._options

    @property
    def is_default(self) -> bool:
        return self._is_default

    ffi_name = "cups_dest_t"
    ffi_free = "cupsFreeDests"

    @classmethod
    def connectDest(cls, *, dest: "cupsDest", flags, msec: int) -> Mapping[Http, str]:
        c_resource = _ffi.new("char[]", 256)
        c_dest, keepalive = dest.to_cffi()
        http = _lib.cupsConnectDest(
            c_dest,
            flags,
            msec,
            _ffi.NULL,
            c_resource,
            256,
            _ffi.NULL,
            _ffi.NULL,
        )
        return {Http(http): _bytes_to_value(c_resource)}

    @classmethod
    def from_cffi_list(cls, dests_ptr: Any, count: int) -> "Dict[str, cupsDest]":
        """Convert a list of CFFI dest structs to a list of python cupsDest.

        Args:
            dests (Any): The CFFI *cups_dest_t pointer to a pointer.
            count (int): The number of destinations in the list.

        Returns:
            Dict[str, cupsDest]: The list of cupsDest.

        """
        results: Dict[str, cupsDest] = {}
        for i in range(count):
            c_dest = dests_ptr[i]
            results[str(_bytes_to_value(c_dest.name))] = cls(c_dest)
        return results

    @classmethod
    def from_cffi(cls, c_dest: Any) -> "cupsDest":
        """Convert a single CFFI dest struct to a Python cupsDest object.

        Args:
            dest (Any): The CFFI cups_dest_t struct.

        Returns:
            cupsDest: The equivalent Python object.

        """
        return cls(c_dest)

    def to_cffi(self) -> Tuple[Any, List[Any]]:
        c_dest = _ffi.new("cups_dest_t *")
        keepalive = []
        c_name = _ffi.new("char[]", self.name.encode())
        c_instance = _ffi.new("char[]", self.instance.encode() if self.instance else b"")
        c_dest.name = c_name
        c_dest.instance = c_instance
        c_dest.is_default = self.is_default
        c_dest.num_options = len(self.options)

        c_opts, opt_keepalive = cupsOption.to_cffi_list(self.options)
        c_dest.options = c_opts

        keepalive.extend([c_name, c_instance, c_opts] + opt_keepalive)
        return c_dest, keepalive

    @classmethod
    def to_cffi_list(
        cls, dests: Union[Dict[str, "cupsDest"], Sequence["cupsDest"]]
    ) -> Tuple[Any, List[Any]]:
        items = list(dests.values()) if isinstance(dests, dict) else list(dests)
        count = len(items)
        c_dests = _ffi.new(f"cups_dest_t[{count}]")
        keepalive = []

        for i, dest in enumerate(items):
            c_name = _ffi.new("char[]", dest.name.encode())
            c_instance = _ffi.new(
                "char[]", dest.instance.encode() if dest.instance else b""
            )
            c_opts, opt_keepalive = cupsOption.to_cffi_list(dest.options)

            c_dests[i].name = c_name
            c_dests[i].instance = c_instance
            c_dests[i].is_default = dest.is_default
            c_dests[i].num_options = len(dest.options)
            c_dests[i].options = c_opts

            keepalive.extend([c_name, c_instance, c_opts] + opt_keepalive)

        return c_dests, keepalive

    def getPrinterAttributes(self, http: Any) -> dict[str, IPPAttribute]:
        ctype = _ffi.typeof(http)
        if ctype.kind != "pointer" and ctype.cname != "struct _http_s *":
            raise TypeError("http must be of type struct _http_s *")

        req: IPPRequest = IPPRequest(IPPOp.GET_PRINTER_ATTRIBUTES)
        req.addString(
            group=IPPTag.OPERATION,
            value_tag=IPPTag.URI,
            name="printer-uri",
            value=self.options["printer-uri-supported"].value,
        )

        req._transfer_ownership()
        c_ans = _lib.cupsDoRequest(http, req.ffi_value, b"/")
        if c_ans == _ffi.NULL:
            return {}

        res: IPPRequest = IPPRequest.from_owned_cdata(c_ans)
        return {
            attr.name: attr
            for attr in res.attributes
            if isinstance(attr, IPPAttribute)
        }

    def __str__(self):
        return f"{self.name} (Default)" if self.is_default else self.name
