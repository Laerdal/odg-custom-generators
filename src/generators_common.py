import re
from collections import UserDict
from dataclasses import dataclass
from typing import Any

from objdictgen.typing import TODValue, NodeProtocol


RE_WORD = re.compile(r'([a-zA-Z_0-9]*)')
RE_TYPE = re.compile(r'([\_A-Z]*)([0-9]*)')
RE_RANGE = re.compile(r'([\_A-Z]*)([0-9]*)\[([\-0-9]*)-([\-0-9]*)\]')
RE_STARTS_WITH_DIGIT = re.compile(r'^(\d.*)')
RE_NOTW = re.compile(r"[^\w]")

CATEGORIES: list[tuple[str, int, int]] = [
    ("SDO_SVR", 0x1200, 0x127F), ("SDO_CLT", 0x1280, 0x12FF),
    ("PDO_RCV", 0x1400, 0x15FF), ("PDO_RCV_MAP", 0x1600, 0x17FF),
    ("PDO_TRS", 0x1800, 0x19FF), ("PDO_TRS_MAP", 0x1A00, 0x1BFF)
]
INDEX_CATEGORIES = ["firstIndex", "lastIndex"]

@dataclass
class TypeInfos:
    """Type infos for a type."""
    type: str
    size: int|None
    ctype: str
    is_unsigned: bool

class CFileContext:
    pass

class Text:
    pass

class Text:
    """Helper class for formatting text. The class store a string and supports
    concatenation and formatting. Operators '+' and '+=' can be used to add
    strings without formatting and '%=' can be used to add strings with
    formatting. The string is formatted with varaibled from the context 
    dictionary.

    This exists as a workaround until the strings have been converted to
    proper f-strings.
    """

    # FIXME: Remove all %= entries, use f-strings instead, and delete this class

    def __init__(self, context: CFileContext, text: str):
        self.text: str = text
        self.context: CFileContext = context

    def __iadd__(self, other: str|Text) -> Text:
        """Add a string to the text without formatting."""
        self.text += str(other)
        return self

    def __add__(self, other: str|Text) -> Text:
        """Add a string to the text without formatting."""
        return Text(self.context, self.text + str(other))

    def __imod__(self, other: str) -> Text:
        """Add a string to the text with formatting."""
        self.text += other.format(**self.context)
        return self

    def __str__(self) -> str:
        """Return the text."""
        return self.text
    
class CFileContext(UserDict):
    """Context for generating C file. It serves as a dictionary to store data
    and as a helper for formatting text.
    """
    internal_types: dict[str, TypeInfos]
    default_string_size: int = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.internal_types = {}

    def __getattr__(self, name: str) -> Any:
        """Look up unknown attributes in the data dictionary."""
        return self.data[name]
    
    def __copy__(self):
        newInstance = CFileContext(self.data.copy())
        newInstance.internal_types = self.internal_types.copy()
        return newInstance

    # FIXME: Delete this method when everything is converted to f-strings
    def text(self, s: str = "") -> Text:
        """Start a new text object"""
        return Text(self, s)

    # FIXME: Delete this method when everything is converted to f-strings
    def ftext(self, s: str) -> Text:
        """Format a text string."""
        return Text(self, "").__imod__(s)  # pylint: disable=unnecessary-dunder-call

    def get_valid_type_infos(self, typename: str, items=None) -> TypeInfos:
        """Get valid type infos from a typename.
        """

        # Return cached typeinfos
        if typename in self.internal_types:
            return self.internal_types[typename]

        items = items or []
        result = RE_TYPE.match(typename)
        if not result:
            # FIXME: The !!! is for special UI handling
            raise ValueError(f"!!! '{typename}' isn't a valid type for CanFestival.")

        if result[1] == "UNSIGNED" and int(result[2]) in [i * 8 for i in range(1, 9)]:
            typeinfos = TypeInfos(f"UNS{result[2]}", None, f"uint{result[2]}", True)
        elif result[1] == "INTEGER" and int(result[2]) in [i * 8 for i in range(1, 9)]:
            typeinfos = TypeInfos(f"INTEGER{result[2]}", None, f"int{result[2]}", False)
        elif result[1] == "REAL" and int(result[2]) in (32, 64):
            typeinfos = TypeInfos(f"{result[1]}{result[2]}", None, f"real{result[2]}", False)
        elif result[1] in ["VISIBLE_STRING", "OCTET_STRING"]:
            size = self.default_string_size
            for item in items:
                size = max(size, len(item))
            if result[2]:
                size = max(size, int(result[2]))
            typeinfos = TypeInfos("UNS8", size, "visible_string", False)
        elif result[1] == "DOMAIN":
            size = 0
            for item in items:
                size = max(size, len(item))
            typeinfos = TypeInfos("UNS8", size, "domain", False)
        elif result[1] == "BOOLEAN":
            typeinfos = TypeInfos("UNS8", None, "boolean", False)
        else:
            # FIXME: The !!! is for special UI handling
            raise ValueError(f"!!! '{typename}' isn't a valid type for CanFestival.")

        # Cache the typeinfos
        if typeinfos.ctype not in ["visible_string", "domain"]:
            self.internal_types[typename] = typeinfos
        return typeinfos
    
def format_name(name: str) -> str:
    """Format a string for making a C++ variable."""
    wordlist = [word for word in RE_WORD.findall(name) if word]
    return "_".join(wordlist)


def compute_value(value: TODValue, ctype: str) -> tuple[str, str]:
    """Compute value for C file."""
    if ctype == "visible_string":
        return f'"{value}"', ""
    if ctype == "domain":
        # FIXME: This ctype assumes the value type
        assert isinstance(value, str)
        tp = ''.join([f"\\x{ord(char):02x}" for char in value])
        return f'"{tp}"', ""
    if ctype.startswith("real"):
        return str(value), ""
    # FIXME: Assume value is an integer
    assert not isinstance(value, str)
    # Make sure to handle negative numbers correctly
    if value < 0:
        return f"-0x{-value:X}", f"\t/* {value} */"
    return f"0x{value:X}", f"\t/* {value} */"

def convert_from_canopen_to_c_type(type):
    # Used to convert types when ctype is an illegal non-int value (e.g. valueRange_X)
    illegal_int_values = ["int40", "int48", "int56", "uint40", "uint48", "uint56"]
    type_map = {}
    type_map["boolean"] = "bool"
    type_map["int8"] = "int8_t"
    type_map["int16"] = "int16_t"
    type_map["int32"] = "int32_t"
    type_map["int40"] = "int64_t"
    type_map["int48"] = "int64_t"
    type_map["int56"] = "int64_t"
    type_map["int64"] = "int64_t"
    type_map["uint8"] = "uint8_t"
    type_map["uint16"] = "uint16_t"
    type_map["uint32"] = "uint32_t"
    type_map["uint40"] = "uint64_t"
    type_map["uint48"] = "uint64_t"
    type_map["uint56"] = "uint64_t"
    type_map["uint64"] = "uint64_t"
    type_map["real32"] = "float"
    type_map["real64"] = "double"
    #if type in illegal_int_values:
    #    raise TypeError("referencing illegal type in:", illegal_int_values, "aborting")
    return type_map.get(type, "dummy")

def setup_c_file_context(node: NodeProtocol):
    # Setup the main context to store the data
    # Setup the main context to store the data
    ctx = CFileContext()

    ctx["maxPDOtransmit"] = 0
    ctx["NodeName"] = node.Name
    ctx["NodeID"] = node.ID
    ctx["NodeType"] = node.Type
    ctx["Description"] = node.Description or ""
    ctx["iam_a_slave"] = 1 if node.Type == "slave" else 0

    ctx.default_string_size = node.DefaultStringSize

    # Compiling lists of indexes
    rangelist = [idx for idx in node.GetIndexes() if 0 <= idx <= 0x260]
    listindex = [idx for idx in node.GetIndexes() if 0x1000 <= idx <= 0xFFFF]
    communicationlist = [idx for idx in node.GetIndexes() if 0x1000 <= idx <= 0x11FF]
    variablelist = [idx for idx in node.GetIndexes() if 0x2000 <= idx <= 0xBFFF]

    # --------------------------------------------------------------------------
    #                   Declaration of the value range types
    # --------------------------------------------------------------------------

    valueRangeContent = ctx.text()
    strDefine = ctx.text(
        "\n#define valueRange_EMC 0x9F "
        "/* Type for index 0x1003 subindex 0x00 (only set of value 0 is possible) */"
    )
    strSwitch = ctx.text("""    case valueRange_EMC:
      if (*(UNS8*)value != (UNS8)0) return OD_VALUE_RANGE_EXCEEDED;
      break;
""")
    ctx.internal_types["valueRange_EMC"] = TypeInfos("UNS8", 0, "valueRange_EMC", True)
    num = 0
    for index in rangelist:
        rangename = node.GetEntryName(index)
        result = RE_RANGE.match(rangename)
        if result:
            num += 1
            typeindex = node.GetEntry(index, 1)
            # FIXME: It is assumed that rangelist contains propery formatted entries
            #        where index 1 is the object type as int
            assert isinstance(typeindex, int)
            typename = node.GetTypeName(typeindex)
            typeinfos = ctx.get_valid_type_infos(typename)
            ctx.internal_types[rangename] = TypeInfos(
                typeinfos.type, typeinfos.size, f"valueRange_{num}", typeinfos.is_unsigned
            )
            minvalue = node.GetEntry(index, 2)
            maxvalue = node.GetEntry(index, 3)
            # FIXME: It assumed the data is properly formatted
            assert isinstance(minvalue, int)
            assert isinstance(maxvalue, int)
            strDefine += (
                f"\n#define valueRange_{num} 0x{index:02X} "
                f"/* Type {typeinfos.type}, {minvalue} < value < {maxvalue} */"
            )
            strSwitch += f"    case valueRange_{num}:\n"
            if typeinfos.is_unsigned and minvalue <= 0:
                strSwitch += "      /* Negative or null low limit ignored because of unsigned type */;\n"
            else:
                strSwitch += (
                    f"      if (*({typeinfos.type}*)value < ({typeinfos.type}){minvalue}) return OD_VALUE_TOO_LOW;\n"
                )
            strSwitch += (
                f"      if (*({typeinfos.type}*)value > ({typeinfos.type}){maxvalue}) return OD_VALUE_TOO_HIGH;\n"
            )
            strSwitch += "    break;\n"

    valueRangeContent += strDefine
    valueRangeContent %= "\nUNS32 {NodeName}_valueRangeTest (UNS8 typeValue, void * value)\n{{"
    valueRangeContent += "\n  switch (typeValue) {\n"
    valueRangeContent += strSwitch
    valueRangeContent += "  }\n  return 0;\n}\n"

    return ctx, listindex, variablelist, communicationlist, valueRangeContent