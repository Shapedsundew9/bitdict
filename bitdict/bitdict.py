""" A library for creating custom bit-packed data structures. """

from __future__ import annotations
from typing import Any, Generator
from types import MappingProxyType
from copy import deepcopy


def bitdict_factory(config: dict[str, Any], name: str = "BitDict") -> type:
    """
    Factory function to create BitDict classes based on a configuration.

    Args:
        config (dict): The configuration dictionary.  See README.md for details.
        name (str, optional): A name for the generated class. Defaults to "BitDict".

    Returns:
        A custom BitDict class.

    Raises:
        ValueError: If the configuration is invalid.
        TypeError: If the config is not a dictionary.
    """

    if not isinstance(config, dict):
        raise TypeError("config must be a dictionary")

    # Subtype classes are stored in a dictionary for recursive creation.
    subtypes: dict[str, list[type[BitDict] | None]] = {}

    def _calculate_total_width(cfg) -> int:
        """Calculates the total bit width based on the configuration."""
        max_bit = 0
        for prop_config in cfg.values():
            end_bit = prop_config["start"] + prop_config["width"]
            max_bit = max(max_bit, end_bit)
        return max_bit

    def _validate_property_config(prop_config_top: dict[str, Any]) -> None:
        """Recursively validates the property configuration."""
        for prop_name, prop_config in prop_config_top.items():
            if not isinstance(prop_name, str) or not prop_name.isidentifier():
                raise ValueError(f"Invalid property name: {prop_name}")
            required_keys = {"start", "width", "type"}
            if not isinstance(prop_config, dict):
                raise TypeError("Property configuration must be a dictionary")
            if not required_keys.issubset(prop_config):
                raise ValueError(
                    f"Missing required keys in property config: {required_keys - set(prop_config)}"
                )
            if not isinstance(prop_config["start"], int) or prop_config["start"] < 0:
                raise ValueError(f"Invalid start value: {prop_config['start']}")
            if not isinstance(prop_config["width"], int) or prop_config["width"] <= 0:
                raise ValueError(f"Invalid width value: {prop_config['width']}")
            if prop_config["type"] not in (
                "bool",
                "uint",
                "int",
                "reserved",
                "bitdict",
            ):
                raise ValueError(f"Invalid type value: {prop_config['type']}")

            if prop_config["type"] == "bool" and prop_config["width"] != 1:
                raise ValueError("Boolean properties must have width 1")

            if prop_config["type"] in ("reserved", "bitdict"):
                if "default" in prop_config:  # No default allowed for reserved
                    raise ValueError(
                        "'reserved' and 'bitdict' types cannot have a default values."
                    )
            else:
                if "default" in prop_config:
                    if prop_config["type"] == "bool":
                        if not isinstance(prop_config["default"], bool):
                            raise TypeError(
                                f"Invalid default type for property {prop_name}"
                                f" expecting bool: {type(prop_config['default'])}"
                            )
                    elif prop_config["type"] == "uint":
                        if not isinstance(prop_config["default"], int):
                            raise TypeError(
                                f"Invalid default type for property {prop_name}"
                                f" expecting int: {type(prop_config['default'])}"
                            )
                        if (
                            not 0
                            <= prop_config["default"]
                            < (1 << prop_config["width"])
                        ):
                            raise ValueError(
                                f"Invalid default value for property"
                                f" {prop_name}: {prop_config['default']}"
                            )
                    elif prop_config["type"] == "int":
                        if not isinstance(prop_config["default"], int):
                            raise TypeError(
                                f"Invalid default type for property {prop_name}"
                                f" expecting int: {type(prop_config['default'])}"
                            )
                        if (
                            not -(1 << (prop_config["width"] - 1))
                            <= prop_config["default"]
                            < (1 << (prop_config["width"] - 1))
                        ):
                            raise ValueError(
                                f"Invalid default value for property {prop_name}"
                                f": {prop_config['default']}"
                            )
                else:
                    if prop_config["type"] == "bool":
                        prop_config["default"] = False
                    elif prop_config["type"] in ("uint", "int"):
                        prop_config["default"] = 0

            if prop_config["type"] == "bitdict":
                if "subtype" not in prop_config or not isinstance(
                    prop_config["subtype"], list
                ):
                    raise ValueError("'bitdict' type requires a 'subtype' list")
                if "selector" not in prop_config or not isinstance(
                    prop_config["selector"], str
                ):
                    raise ValueError("'bitdict' type requires a 'selector' field")
                selector = prop_config["selector"]
                if selector not in prop_config_top:
                    raise ValueError(f"Invalid selector property: {selector}")
                if prop_config_top[selector]["type"] not in (
                    "bool",
                    "uint",
                ):
                    raise ValueError(
                        "Selector property must be of type 'bool' or 'uint'"
                    )
                if prop_config_top[selector]["width"] > 16:
                    raise ValueError(
                        "Selector property width must be <= 16 (65536 subtypes)"
                    )

                # Reverse linkage
                prop_config_top[selector]["_bitdict"] = prop_name

                for sub_config in prop_config["subtype"]:
                    # Recursively validate sub-configurations
                    subtypes.setdefault(prop_name, []).append(
                        None if sub_config is None else bitdict_factory(sub_config)
                    )  # We can use the factory recursively

    def _check_overlapping(cfg) -> None:
        """Checks for overlapping bit field definitions."""
        used_bits = set()
        for _, prop_config in cfg.items():
            for i in range(
                prop_config["start"], prop_config["start"] + prop_config["width"]
            ):
                if i in used_bits:
                    raise ValueError(
                        f"Overlapping bit definitions: bit {i} is used by multiple properties"
                    )
                used_bits.add(i)

    _validate_property_config(config)  # Initial validation of top level.
    _check_overlapping(config)
    total_width = _calculate_total_width(config)

    class BitDict:
        """Dynamically created class based on the configuration."""

        _config: MappingProxyType[str, Any] = MappingProxyType(deepcopy(config))
        _subbitdicts: dict[str, list[BitDict | None]] = {}
        _subtypes: dict[str, list[type[BitDict] | None]] = subtypes
        _total_width: int = total_width
        __name__: str = name

        def __init__(
            self, value: int | bytes | bytearray | dict[str, Any] | None = None
        ) -> None:
            """
            Initializes a BitDict instance.

            Args:
                value (int, bytes, bytearray, dict, optional):  The initial value.
                    Can be an integer, a bytes/bytearray object, or a dictionary.
                    Defaults to 0.
                parent (BitDict, optional): The parent BitDict object. Defaults to None.
            Raises:
                TypeError: If input value is not an integer, bytes, bytearray or dict
                ValueError: If the integer is too large, or bytes/bytearray are too long
                  or too short
            """
            self._value = 0

            # Identification of this BitDict in a parent BitDict
            # These are set by _parent_config() when this BitDict is a sub-bitdict.
            # They are used in _update_parent() to update the parent BitDict
            # when this BitDict changes.
            self._parent: BitDict | None = None
            self._parent_key: str | None = None

            # Set to defaults
            if value is None:
                self.reset()
            elif isinstance(value, int):
                if value >= (1 << self._total_width):
                    raise ValueError(
                        f"Integer value {value} exceeds maximum"
                        f" value for bit width {self._total_width}"
                    )
                if value < -(1 << (self._total_width - 1)):
                    raise ValueError(
                        f"Integer value {value} exceeds minimum"
                        f"value for bit width {self._total_width}"
                    )
                self.set(value)
            elif isinstance(value, (bytes, bytearray)):
                if len(value) > (self._total_width + 7) // 8:  # +7 to round up
                    raise ValueError(
                        f"Bytes object too long for bit width {self._total_width}"
                    )
                # Convert bytes to integer (big-endian)
                self.set(int.from_bytes(value, "big"))
            elif isinstance(value, dict):
                self.set(value)  # Use update to handle defaults and type checking
            else:
                raise TypeError(
                    "Invalid initialization type: must be None, int, bytes, bytearray, or dict"
                )

        def __getitem__(self, key: str) -> bool | int | BitDict:
            """Gets the value of a property."""
            if key not in self._config:
                raise KeyError(f"Invalid property: {key}")

            prop_config = self._config[key]
            if prop_config["type"] == "reserved":
                raise ValueError(f"Cannot read a reserved property '{key}'")

            if prop_config["type"] == "bitdict":
                selector_value: bool | int | BitDict = self[prop_config["selector"]]
                assert isinstance(selector_value, int), "Selector must be an integer"
                bd: BitDict = self._get_subbitdict(key, selector_value)
                return bd

            start = prop_config["start"]
            width = prop_config["width"]
            mask = (1 << width) - 1
            raw_value = (self._value >> start) & mask

            if prop_config["type"] == "bool":
                return bool(raw_value)

            if prop_config["type"] == "int":
                # Two's complement conversion if the highest bit is set
                return (
                    raw_value - (1 << width)
                    if raw_value & (1 << (width - 1))
                    else raw_value
                )

            if prop_config["type"] == "uint":
                return raw_value

            assert False, f"Unknown property type: {prop_config['type']}"

        def __setitem__(self, key: str, value: bool | int) -> None:
            """Sets the value of a property."""
            if key not in self._config:
                raise KeyError(f"Invalid property: {key}")

            if self._config[key]["type"] == "reserved":
                raise ValueError(f"Cannot set reserved property '{key}'")

            prop_config = self._config[key]
            start = prop_config["start"]
            width = prop_config["width"]
            mask = (1 << width) - 1

            if prop_config["type"] == "bool":
                if not isinstance(value, (bool, int)):
                    raise TypeError(
                        f"Expected boolean or integer value for property '{key}'"
                    )
                value = 1 if value else 0
            elif prop_config["type"] == "int":
                if not isinstance(value, int):
                    raise TypeError(f"Expected integer value for property '{key}'")
                if not -(1 << (width - 1)) <= value < (1 << (width - 1)):
                    raise ValueError(f"Value {value} out of range for property '{key}'")
                # Convert to two's complement representation
                if value < 0:
                    value = (1 << width) + value
            elif prop_config["type"] == "uint":
                if not isinstance(value, int):
                    raise TypeError(f"Expected integer value for property '{key}'")
                if not 0 <= value < (1 << width):
                    raise ValueError(f"Value {value} out of range for property '{key}'")
            elif prop_config["type"] == "reserved":
                # You can't *set* reserved bits.
                raise ValueError(f"Cannot set reserved property '{key}'")
            elif prop_config["type"] == "bitdict":
                # Set the sub-bitdict value.
                selector_value = self[prop_config["selector"]]
                assert isinstance(selector_value, int), "Selector must be an integer"
                bd: BitDict = self._get_subbitdict(key, selector_value)
                bd.set(value)
                value = bd.to_int()

            # If the property is a selector then the sub-bitdict
            # changes and we need to update the value
            # Note that if the newly selected BitDict was previously
            # defined then that value will be used
            # or else it will be the default for the new BitDict.
            # It will not maintain the same numeric value.
            # This is important to call out in the user documentation.
            if "_bitdict" in prop_config:
                bd = self._get_subbitdict(prop_config["_bitdict"], value)
                bdc = self._config[prop_config["_bitdict"]]
                _mask = (1 << bdc["width"]) - 1
                _start = bdc["start"]
                self._value &= ~(_mask << _start)
                self._value |= (bd.to_int() & _mask) << _start

            # Clear the bits for this property, then set the new value
            self._value &= ~(mask << start)
            self._value |= (value & mask) << start

            # If this BitDict is a sub-bitdict then update the parent
            if self._parent is not None:
                self._update_parent()

        def __len__(self) -> int:
            """Returns the total bit width."""
            return self._total_width

        def __contains__(self, key: str) -> bool:
            """Check if a property exists. Note that this check considers
            the value of selectors. If a property does exist in a subtype but
            that subtype is not selected then False is returned."""
            retval: bool = key in self._config
            if not retval:
                for k, bd in self._config.items():
                    if bd["type"] == "bitdict":
                        bdi: bool | int | BitDict = self[k]
                        assert not isinstance(bdi, int), "Expecting BitDict type."
                        retval = retval or key in bdi
                        if retval:
                            break
            return retval

        def __iter__(
            self,
        ) -> Generator[tuple[Any, bool | Any | BitDict | None], Any, None]:
            """Iterates over the properties (name, value) in LSB to MSB order."""
            sps = sorted(self._config.items(), key=lambda item: item[1]["start"])
            for name, _ in (sp for sp in sps if sp[1]["type"] != "reserved"):
                yield name, self[name]

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.to_json()})"

        def __str__(self):
            return str(self.to_json())

        def _get_subbitdict(self, key: str, selector_value: int) -> BitDict:
            """Creates a subtype instance of a sub-bitdict class."""
            prop_config = self._config[key]
            if key not in self._subbitdicts:
                width = self._config[prop_config["selector"]]["width"]
                self._subbitdicts[key] = [None] * 2**width
            sdk: list[BitDict | None] = self._subbitdicts[key]
            if sdk[selector_value] is None:
                bdtype: type[BitDict] | None = self._subtypes[key][selector_value]
                assert bdtype is not None, "Subtype class not created!"
                nbd = bdtype()
                nbd._set_parent(self, key)  # pylint: disable=protected-access
                sdk[selector_value] = nbd
            retval: BitDict | None = sdk[selector_value]
            assert retval is not None, "Subtype class object does not exist!"
            return retval

        def _set_parent(self, parent: BitDict, key: str) -> None:
            """Sets the parent BitDict and key for this sub-bitdict."""
            self._parent = parent
            self._parent_key = key

        def _update_parent(self) -> None:
            """Updates the parent BitDict when this sub-bitdict changes."""
            assert self._parent is not None, "Parent not set"
            assert self._parent_key is not None, "Parent key not set"
            pc = self._parent._config[  # pylint: disable=protected-access
                self._parent_key
            ]
            mask = (1 << pc["width"]) - 1
            start = pc["start"]
            self._parent._value &= ~(mask << start)
            self._parent._value |= (self.to_int() & mask) << start

        def clear(self) -> None:
            """Clears all properties to zero."""
            self.set(0)

        def get(self) -> int:
            """Returns the value as an integer."""
            return self._value

        def reset(self) -> None:
            """Resets all properties to their default values."""
            for prop_name, prop_config in self._config.items():
                if prop_config["type"] == "reserved":
                    continue
                if prop_config["type"] == "bitdict":
                    selector_value = self[prop_config["selector"]]
                    assert isinstance(
                        selector_value, int
                    ), "Selector must be an integer"
                    self._get_subbitdict(prop_name, selector_value).reset()
                else:
                    self[prop_name] = prop_config["default"]

        def set(self, value: int | dict[str, Any]) -> None:
            """Sets the value from an integer or updates properties from a dictionary."""
            if isinstance(value, dict):
                for prop_name, prop_config in self._config.items():
                    if prop_name in value:
                        self[prop_name] = value[prop_name]
                    elif "default" in prop_config:
                        self[prop_name] = prop_config["default"]
            else:
                if value >= (1 << self._total_width):
                    raise ValueError(
                        f"Integer value {value} exceeds maximum"
                        f" value for bit width {self._total_width}"
                    )
                if value < -(1 << (self._total_width - 1)):
                    raise ValueError(
                        f"Integer value {value} exceeds minimum"
                        f"value for bit width {self._total_width}"
                    )
                self._value: int = value

                # Must set sub-bitdicts after setting the main value.
                for prop_name, prop_config in self._config.items():
                    if prop_config["type"] == "bitdict":
                        selector_value = self[prop_config["selector"]]
                        assert isinstance(
                            selector_value, int
                        ), "Selector must be an integer"
                        bd_value = (value >> prop_config["start"]) & (
                            (1 << prop_config["width"]) - 1
                        )
                        self._get_subbitdict(prop_name, selector_value).set(bd_value)

        def update(self, data: dict[str, Any]) -> None:
            """Updates multiple properties from a dictionary."""
            if not isinstance(data, dict):
                raise TypeError("update() requires a dictionary")
            for key, value in data.items():
                self[key] = value  # Use __setitem__ for type/range checking

        def to_json(self) -> dict[str, Any]:
            """Returns a JSON-compatible dictionary representation."""
            result = {}
            for name, _ in list(self)[::-1]:  # Use the iterator
                result[name] = self[name]
                if hasattr(result[name], "to_json"):
                    result[name] = result[
                        name
                    ].to_json()  # Recurse for nested bitdicts.
            return result

        def to_bytes(self) -> bytes:
            """Returns the value as a bytes object (big-endian)."""
            num_bytes = (self._total_width + 7) // 8  # Round up to nearest byte
            return self._value.to_bytes(num_bytes, "big")

        def to_int(self) -> int:
            """Returns the value as an integer."""
            return self._value

        @classmethod
        def get_config(cls) -> MappingProxyType[str, Any]:
            """Returns the configuration dictionary (read-only)."""
            return cls._config

    # end class BitDict

    # Set the name of the dynamically created class.
    BitDict.__name__ = name
    return BitDict
