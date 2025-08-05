"""
BitDict factory module for creating BitDict classes.

This module provides the core factory functionality for creating BitDict classes
from configuration dictionaries. It's separated from the main bitdict module
to avoid circular import issues with validation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from types import MappingProxyType
from typing import Any, Callable, Generator, Protocol


class BitDictFactoryProtocol(Protocol):
    """Protocol defining the interface for BitDict factories."""

    def create_bitdict_class(
        self, config: dict[str, Any], name: str = "BitDict", title: str = "BitDict"
    ) -> type[BitDictABC]:
        """Create a BitDict class from configuration."""
        ...


class BitDictABC(ABC):
    """Abstract base class for BitDict"""

    _config: MappingProxyType[str, Any]
    _total_width: int
    subtypes: dict[str, list[type[BitDictABC] | None]]
    _total_width: int
    title: str

    @abstractmethod
    def __init__(
        self,
        value: int | bytes | bytearray | dict[str, Any] | None = None,
        ignore_unknown: bool = True,
    ) -> None:
        """Initializes a BitDict instance with a specified value."""

    @abstractmethod
    def __getitem__(self, key: str) -> bool | int | BitDictABC:
        """Retrieves the value associated with the given key."""

    @abstractmethod
    def __setitem__(self, key: str, value: bool | int) -> None:
        """Sets the value of a property within the BitDict."""

    @abstractmethod
    def __len__(self) -> int:
        """Returns the total width of the bit dictionary."""

    @abstractmethod
    def __contains__(self, key: str) -> bool:
        """Check if a property exists within this BitDict or its nested BitDict"""

    @abstractmethod
    def __iter__(
        self,
    ) -> Generator[tuple[str, bool | int | BitDictABC], Any, None]:
        """BitDict iterator to traverse properties in LSB to MSB order"""

    @abstractmethod
    def __repr__(self) -> str:
        """Returns a string representation of the BitDict"""

    @abstractmethod
    def __str__(self) -> str:
        """Returns a string representation of the BitDict"""

    @abstractmethod
    def _get_value(self) -> int:
        """Returns the value of the BitDict"""

    @abstractmethod
    def _set_parent(self, parent: BitDictABC, key: str) -> None:
        """Sets the parent BitDict and key for this BitDict"""

    @abstractmethod
    def _set_value(self, value: int) -> None:
        """Sets the value of the BitDict"""

    @classmethod
    @abstractmethod
    def assign_verification_function(
        cls, verification_function: Callable[[BitDictABC], bool]
    ) -> None:
        """Assigns a verification function to the BitDict"""

    @abstractmethod
    def clear(self) -> None:
        """Clears all bit fields to their default values."""

    @classmethod
    @abstractmethod
    def get_config(cls) -> MappingProxyType[str, Any]:
        """Returns the configuration dictionary for the BitDict."""

    @abstractmethod
    def inspect(self) -> dict[str, Any]:
        """Inspects the current state of the BitDict and returns a dictionary."""

    @abstractmethod
    def reset(self) -> None:
        """Resets all bit fields to their default values."""

    @abstractmethod
    def set(self, value: int | dict[str, Any], ignore_unknown: bool = True) -> None:
        """Sets the BitDict to the provided integer value
        or a dictionary for multi-field updates."""

    @abstractmethod
    def update(self, data: dict[str, Any]) -> None:
        """Updates the BitDict with the provided data."""

    @abstractmethod
    def to_bytes(self) -> bytes:
        """Converts the BitDict to a byte representation."""

    @abstractmethod
    def to_int(self) -> int:
        """Converts the BitDict to an integer representation."""

    @abstractmethod
    def to_json(self) -> dict[str, Any]:
        """Converts the BitDict to a JSON-compatible dictionary."""

    @abstractmethod
    def valid(self) -> bool:
        """Checks if the bit dictionary is valid."""

    @abstractmethod
    def verify(self) -> bool:
        """Verifies the integrity of the bit dictionary."""


def _calculate_total_width(cfg: dict[str, Any]) -> int:
    """
    Calculates the total bit width based on the configuration.

    This is a helper function that calculates the total number of bits
    required to store all the bit fields defined in the configuration.

    Args:
        cfg: The configuration dictionary.

    Returns:
        int: The total bit width.
    """
    max_bit = 0
    for prop_config in cfg.values():
        end_bit = prop_config["start"] + prop_config["width"]
        max_bit = max(max_bit, end_bit)
    return max_bit


def _is_valid_value(value: int | bool, prop_config: dict[str, Any]) -> bool:
    """Checks if a value is valid according to the 'valid'
    key in the property configuration."""
    # pylint: disable=duplicate-code
    if "valid" not in prop_config:
        return True

    valid_config = prop_config["valid"]
    if "value" in valid_config and value in valid_config["value"]:
        return True

    if "range" in valid_config:
        for r in valid_config["range"]:
            if value in range(*r):
                return True

    return False


class BitDictFactory:
    """Factory class for creating BitDict classes with dependency injection support."""

    def create_bitdict_class(
        self,
        config: dict[str, Any],
        name: str = "BitDict",
        title: str = "BitDict",
        subtypes: dict[str, list[type[BitDictABC] | None]] | None = None,
    ) -> type[BitDictABC]:
        # pylint: disable=too-many-statements
        """
        Creates a BitDict class based on the provided configuration.

        This method is used internally by validation to create nested BitDict classes
        without causing circular imports.

        Args:
            config: The configuration dictionary
            name: The name of the class
            title: The title for documentation
            subtypes: Pre-populated subtypes dictionary (used in validation)

        Returns:
            type[BitDictABC]: The created BitDict class
        """
        if not isinstance(config, dict):  # type: ignore[runtime safety]
            raise TypeError("config must be a dictionary")
        if not name.isidentifier():
            raise ValueError("Invalid class name")

        # Use provided subtypes or create new one
        subtype_lists: dict[str, list[type[BitDictABC] | None]] = subtypes or {}
        total_width = _calculate_total_width(config)
        _title = title  # Capture title in local variable

        class BitDict(BitDictABC):
            """
            A dynamic bit-field dictionary for structured data manipulation.

            BitDict provides a flexible way to define and interact with data structures
            where individual fields occupy specific bit ranges. It supports a variety of
            data types including integers (signed and unsigned), booleans, and nested
            BitDict instances, enabling complex data layouts to be easily managed.
            """

            _config: MappingProxyType[str, Any] = MappingProxyType(config)
            subtypes: dict[str, list[type[BitDictABC] | None]] = subtype_lists
            _total_width: int = total_width
            title: str = _title
            __name__: str = name
            # pylint: disable=line-too-long
            verification_function: Callable[[BitDictABC], bool] = staticmethod(  # type: ignore[misc]
                lambda _: True  # type: ignore[misc]
            )
            __slots__: tuple[str, ...] = (
                "_value",
                "_subbitdicts",
                "_parent",
                "_parent_key",
            )

            def __init__(
                self,
                value: int | bytes | bytearray | dict[str, Any] | None = None,
                ignore_unknown: bool = True,
            ) -> None:
                """Initializes a BitDict instance with a specified value."""
                self._value = 0
                # Instances of subbitdicts
                self._subbitdicts: dict[str, list[BitDictABC | None]] = {}

                # Identification of this BitDict in a parent BitDict
                self._parent: BitDictABC | None = None
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
                        raise ValueError(f"Bytes object too long for bit width {self._total_width}")
                    # Convert bytes to integer (big-endian)
                    self.set(int.from_bytes(value, "big"))
                elif isinstance(value, dict):  # type: ignore[misc]
                    self.set(value, ignore_unknown)
                else:
                    raise TypeError(
                        "Invalid initialization type: must be None, int, bytes, bytearray, or dict"
                    )

            def __getitem__(self, key: str) -> bool | int | BitDictABC:
                """Retrieves the value associated with the given key."""
                if key not in self._config:
                    raise KeyError(f"Invalid property: {key}")

                prop_config = self._config[key]
                start = prop_config["start"]
                width = prop_config["width"]
                mask = (1 << width) - 1
                raw_value = (self._value >> start) & mask

                if prop_config["type"] == "bool":
                    return bool(raw_value)

                if prop_config["type"] == "uint":
                    return raw_value

                if prop_config["type"] == "int":
                    # Two's complement conversion if the highest bit is set
                    return raw_value - (1 << width) if raw_value & (1 << (width - 1)) else raw_value

                if prop_config["type"] == "bitdict":
                    selector_value: bool | int | BitDictABC = self[prop_config["selector"]]
                    assert isinstance(selector_value, int), "Selector must be an integer"
                    bd: BitDictABC = self._get_subbitdict(key, selector_value)
                    return bd

                assert False, f"Unknown property type: {prop_config['type']}"

            def __setitem__(self, key: str, value: bool | int) -> None:
                """Sets the value of a property within the BitDict."""
                if key not in self._config:
                    raise KeyError(f"Invalid property: {key}")

                prop_config = self._config[key]
                start = prop_config["start"]
                width = prop_config["width"]
                mask = (1 << width) - 1

                match prop_config["type"]:
                    case "bool":
                        if not isinstance(value, (bool, int)):  # type: ignore[misc]
                            raise TypeError(
                                f"Expected boolean or integer value for property '{key}'"
                            )
                        value = 1 if value else 0
                    case "uint":
                        if not isinstance(value, int):  # type: ignore[misc]
                            raise TypeError(f"Expected integer value for property '{key}'")
                        if not 0 <= value < (1 << width):
                            raise ValueError(f"Value {value} out of range for property '{key}'")
                    case "int":
                        if not isinstance(value, int):  # type: ignore[misc]
                            raise TypeError(f"Expected integer value for property '{key}'")
                        if not -(1 << (width - 1)) <= value < (1 << (width - 1)):
                            raise ValueError(f"Value {value} out of range for property '{key}'")
                        # Convert to two's complement representation
                        if value < 0:
                            value = (1 << width) + value
                    case "bitdict":
                        # Set the sub-bitdict value.
                        selector_value = self[prop_config["selector"]]
                        assert isinstance(selector_value, int), "Selector must be an integer"
                        bd: BitDictABC = self._get_subbitdict(key, selector_value)
                        bd.set(value)
                        value = bd.to_int()
                    case _:
                        assert False, f"Unknown property type: {prop_config['type']}"

                # If the property is a selector then the sub-bitdict changes
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
                """Returns the total width of the bit dictionary."""
                return self._total_width

            def __contains__(self, key: str) -> bool:
                """Check if a property exists within this BitDict or its nested BitDicts."""
                retval: bool = key in self._config
                if not retval:
                    for k, bd in self._config.items():
                        if bd["type"] == "bitdict":
                            bdi: bool | int | BitDictABC = self[k]
                            assert not isinstance(bdi, int), "Expecting BitDict type."
                            retval = retval or key in bdi
                            if retval:
                                break
                return retval

            def __iter__(self) -> Generator[tuple[str, bool | BitDictABC | int], Any, None]:
                """Iterates over the BitDict, yielding (name, value) pairs."""
                sps = sorted(self._config.items(), key=lambda item: item[1]["start"])
                for name, _ in sps:
                    yield name, self[name]

            def __repr__(self) -> str:
                """Return a string representation of the BitDict object."""
                return f"{self.__class__.__name__}({self.to_json()})"

            def __str__(self) -> str:
                """Returns a string representation of the BitDict object."""
                return str(self.to_json())

            def _get_subbitdict(self, key: str, selector_value: int) -> BitDictABC:
                """Retrieves a sub-BitDict associated with a given key and selector value."""
                prop_config = self._config[key]
                if key not in self._subbitdicts:
                    width = self._config[prop_config["selector"]]["width"]
                    self._subbitdicts[key] = [None] * 2**width
                sdk: list[BitDictABC | None] = self._subbitdicts[key]
                if sdk[selector_value] is None:
                    if selector_value >= len(self.subtypes[key]):
                        raise IndexError(
                            "Subtype class not created for selector"
                            f" {prop_config['selector']} at index {selector_value}"
                        )
                    bdtype: type[BitDictABC] | None = self.subtypes[key][selector_value]
                    assert bdtype is not None, "Subtype class not created!"
                    nbd = bdtype()
                    nbd._set_parent(self, key)  # pylint: disable=protected-access
                    sdk[selector_value] = nbd
                retval: BitDictABC | None = sdk[selector_value]
                assert retval is not None, "Subtype class not created!"
                return retval

            def _get_value(self) -> int:
                """Returns the integer value representing the BitDict."""
                return self._value

            def _set_parent(self, parent: BitDictABC, key: str) -> None:
                """Sets the parent BitDict and the key associated with this BitDict
                in the parent."""
                self._parent = parent
                self._parent_key = key

            def _set_value(self, value: int) -> None:
                """Sets the integer value representing the BitDict."""
                self._value = value

            def _update_parent(self) -> None:
                """Updates the parent BitField with the current value of this BitField."""
                assert self._parent is not None, "Parent not set"
                assert self._parent_key is not None, "Parent key not set"
                pc = self._parent._config[self._parent_key]  # pylint: disable=protected-access
                mask = (1 << pc["width"]) - 1
                start = pc["start"]
                _value = self._parent._get_value()  # pylint: disable=protected-access
                _value &= ~(mask << start)
                _value |= (self.to_int() & mask) << start
                self._parent._set_value(_value)  # pylint: disable=protected-access

            @classmethod
            def assign_verification_function(
                cls, verification_function: Callable[[BitDictABC], bool]
            ) -> None:
                """Assigns a verification function to the BitDict."""
                cls.verification_function = verification_function

            def clear(self) -> None:
                """Clears the bit dictionary, setting all bits to 0."""
                self.set(0)

            @classmethod
            def get_config(cls) -> MappingProxyType[str, Any]:
                """Returns the configuration settings for the BitDict class."""
                return cls._config

            def inspect(self) -> dict[str, Any]:
                """Inspects the BitDict and returns a dictionary of properties
                with invalid values."""
                invalid_props: dict[str, Any] = {}
                for prop_name, prop_config in self._config.items():
                    if prop_config["type"] == "bitdict":
                        selector_value = self[prop_config["selector"]]
                        assert isinstance(selector_value, int), "Selector must be an integer"
                        if not _is_valid_value(
                            selector_value, self._config[prop_config["selector"]]
                        ):
                            invalid_props[prop_config["selector"]] = selector_value
                        else:
                            sub_bitdict = self._get_subbitdict(prop_name, selector_value)
                            sub_invalid_props = sub_bitdict.inspect()
                            if sub_invalid_props:
                                invalid_props[prop_name] = sub_invalid_props
                    else:
                        value = self[prop_name]
                        assert isinstance(value, (int, bool)), "Value must be an integer or boolean"
                        if not _is_valid_value(value, prop_config):
                            invalid_props[prop_name] = self[prop_name]
                return invalid_props

            def reset(self) -> None:
                """Resets the BitDict to its default values."""
                for prop_name, prop_config in self._config.items():
                    if prop_config["type"] == "bitdict":
                        selector_value = self[prop_config["selector"]]
                        assert isinstance(selector_value, int), "Selector must be an integer"
                        self._get_subbitdict(prop_name, selector_value).reset()
                    else:
                        self[prop_name] = prop_config["default"]

            def set(self, value: int | dict[str, Any], ignore_unknown: bool = True) -> None:
                # pylint: disable=too-many-branches
                """Sets the value of the BitDict."""
                if isinstance(value, dict):
                    if ignore_unknown:
                        for prop_name, prop_config in self._config.items():
                            if prop_name in value:
                                self[prop_name] = value[prop_name]
                            elif "default" in prop_config:
                                self[prop_name] = prop_config["default"]
                    else:
                        defaults = set(self._config.keys())
                        for v_name in value:
                            if v_name not in self._config:
                                raise KeyError(f"Unknown property: {v_name}")
                            self[v_name] = value[v_name]
                            defaults.discard(v_name)
                        for prop_name in defaults:
                            prop_config = self._config[prop_name]
                            if "default" in prop_config:
                                self[prop_name] = prop_config["default"]
                else:
                    if value >= (1 << self._total_width):
                        raise ValueError(
                            f"Integer value {value} exceeds maximum"
                            f" value for bit width {self._total_width}"
                        )
                    if value < 0:
                        raise ValueError(f"Integer must be non-negative, got {value}")
                    self._value: int = value

                    # Must set sub-bitdicts after setting the main value.
                    for prop_name, prop_config in self._config.items():
                        if prop_config["type"] == "bitdict":
                            selector_value = self[prop_config["selector"]]
                            assert isinstance(selector_value, int), "Selector must be an integer"
                            bd_value = (value >> prop_config["start"]) & (
                                (1 << prop_config["width"]) - 1
                            )
                            self._get_subbitdict(prop_name, selector_value).set(bd_value)

            def update(self, data: dict[str, Any]) -> None:
                """Update the BitDict with values from another dictionary."""
                if not isinstance(data, dict):  # type: ignore[misc]
                    raise TypeError("update() requires a dictionary")
                for key, value in data.items():
                    self[key] = value

            def to_bytes(self) -> bytes:
                """Convert the bit dictionary to a byte string."""
                num_bytes = (self._total_width + 7) // 8  # Round up to nearest byte
                return self._value.to_bytes(num_bytes, "big")

            def to_int(self) -> int:
                """Returns the integer representation of the BitDict."""
                return self._value

            def to_json(self) -> dict[str, Any]:
                """Converts the BitDict to a JSON-serializable dictionary."""
                result: dict[str, Any] = {}
                for name, _ in list(self)[::-1]:  # Use the iterator
                    result[name] = self[name]
                    if hasattr(result[name], "to_json"):
                        result[name] = result[name].to_json()  # Recurse for nested bitdicts.
                return result

            def valid(self) -> bool:
                """Checks if all properties have valid values."""
                for prop_name, prop_config in self._config.items():
                    if prop_config["type"] == "bitdict":
                        selector_value = self[prop_config["selector"]]
                        assert isinstance(selector_value, int), "Selector must be an integer"
                        if not _is_valid_value(
                            selector_value, self._config[prop_config["selector"]]
                        ):
                            return False
                        sub_bitdict = self._get_subbitdict(prop_name, selector_value)
                        if not sub_bitdict.valid():
                            return False
                    else:
                        value = self[prop_name]
                        assert isinstance(value, (int, bool)), "Value must be an integer or boolean"
                        if not _is_valid_value(value, prop_config):
                            return False
                return True

            def verify(self) -> bool:
                """Verifies the BitDict against a verification function."""
                return self.__class__.verification_function(self)

        # Set the name of the dynamically created class.
        BitDict.__name__ = name
        return BitDict


# Global factory instance
_default_factory = BitDictFactory()


def bitdict_factory(
    config: dict[str, Any], name: str = "BitDict", title: str = "BitDict"
) -> type[BitDictABC]:
    """
    Factory function to create BitDict classes based on a configuration.

    This is the main public API that maintains backward compatibility while
    using the new factory architecture internally.
    """
    # Import validation here to avoid circular imports
    from .validation import (  # pylint: disable=import-outside-toplevel
        check_overlapping,
        validate_property_config,
    )

    if not isinstance(config, dict):  # type: ignore[runtime safety]
        raise TypeError("config must be a dictionary")
    if not name.isidentifier():
        raise ValueError("Invalid class name")

    # Try to make a deep copy to avoid modifying the original
    # If deepcopy fails (e.g., with MappingProxyType), let validation handle the error
    try:
        config_copy = deepcopy(config)
    except (TypeError, AttributeError):
        # If deepcopy fails, use the original config and let validation catch issues
        config_copy = config

    # Subtype classes are stored in a dictionary for recursive creation.
    subtype_lists: dict[str, list[type[BitDictABC] | None]] = {}

    validate_property_config(config_copy, subtype_lists, _default_factory)  # Initial validation
    check_overlapping(config_copy)

    return _default_factory.create_bitdict_class(config_copy, name, title, subtype_lists)
