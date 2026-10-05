from cups.types.base import cupsBaseClass, _lib, _ffi
from cups.utils import _bytes_to_value
from typing import Any, Dict, Optional
from cups.types.ipp import IPPRequest, IPPTag, IPPAttribute

class cupsOption(cupsBaseClass):
    def __init__(self, arg: Any = None, *, name: str = None, value: str = None):
        self._owned = False
        self._transferred = False
        if arg is not None:
            self._name = _bytes_to_value(arg.name)
            self._value = _bytes_to_value(arg.value) if arg.value != _ffi.NULL else None
        else:
            self._name = name
            self._value = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> Optional[Any]:
        return self._value

    ffi_name = "cups_option_t"

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value}

    def toAttribute(self, ipp_req: IPPRequest, group_tag: IPPTag) -> IPPAttribute:
        """Convert this cupsOption into an IPPAttribute.
        Args:
            ipp_req (IPPRequest): The IPPRequest to add the attribute to.
            group_tag (IPPTag): The group tag to use for the attribute.

        Returns:
            IPPAttribute: The created IPPAttribute.
        """
        return IPPAttribute(
            _lib.cupsEncodeOption(
                ipp_req.ffi_value,
                group_tag,
                self.name.encode(),
                self.value.encode() if self.value else b"",
            ),
            parent=ipp_req,
        )

    @classmethod
    def to_cffi_list(cls, opts: "Dict[str, cupsOption]") -> Any:
        count = len(opts)
        c_opts = _ffi.new(f"cups_option_t[{count}]")
        keepalive = []

        for i, opt in enumerate(opts.values()):
            c_name = _ffi.new("char[]", opt.name.encode("utf-8"))
            c_value = _ffi.new("char[]", str(opt.value).encode("utf-8") if opt.value is not None else b"")
            keepalive.extend([c_name, c_value])
            c_opts[i].name = c_name
            c_opts[i].value = c_value

        return c_opts, keepalive

    @classmethod
    def from_cffi_list(cls, opts: Any, count: int) -> "Dict[str, cupsOption]":
        """
        Convert a list of CFFI dest structs to a list of python cupsOption.

        Args:
            dests (Any): The CFFI *cups_option_t pointer.

        Returns:
            List[cupsOption]: The list of cupsDest.
        """
        results: Dict[str, cupsOption] = {}
        for i in range(count):
            new_opt: Any = opts[i]
            results[str(_bytes_to_value(new_opt.name))] = cupsOption(new_opt)
        return results

    def __str__(self):
        return f"{self.name}: {self.value})"
