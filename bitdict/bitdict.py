""" A library for creating custom bit-packed data structures. """

from __future__ import annotations
from typing import Any, Generator
from types import MappingProxyType
from copy import deepcopy


def bitdict_factory(config: dict[str, Any], name: str = "BitDict") -> type:
    """
    Factory function to create BitDict classes based on a configuration.

    This factory function dynamically creates a new class (subclass of BitDict)
    based on the provided configuration dictionary. The generated class allows
    you to define and access bit fields within an integer value, similar to
    a struct in C.

    Args:
        config (dict): A dictionary defining the bit field structure.
            The dictionary keys are the names of the bit fields, and the values
            are dictionaries with the following keys:

            * `start` (int): The starting bit position (LSB = 0).
            * `width` (int): The width of the bit field in bits.
            * `type` (str): The data type of the bit field.
              Can be one of: 'bool', 'uint', 'int', 'reserved', 'bitdict'.
            * `default` (optional): The default value for the bit field.
              If not provided, defaults to False for 'bool', 0 for 'uint' and 'int'.
            * `subtype` (list of dict, optional):  Required for 'bitdict' type.
              A list of sub-bitdict configurations to select from based
              on the value of the selector property.
            * `selector` (str, optional): Required for 'bitdict' type.
              The name of the property used to select the active sub-bitdict.

        name (str, optional): The name of the generated class.
            Defaults to "BitDict".

    Returns:
        type: A new class that represents the bit field structure.

    Raises:
        ValueError: If the configuration is invalid (e.g., overlapping
            bit fields, invalid property names, missing required keys).
        TypeError: If the config is not a dictionary.

    Example:
        ```python
        config = {
            'enabled': {'start': 0, 'width': 1, 'type': 'bool'},
            'mode': {'start': 1, 'width': 2, 'type': 'uint'},
            'value': {'start': 3, 'width': 5, 'type': 'int'},
        }
        MyBitDict = bitdict_factory(config, "MyBitDict")

        # Create an instance of the generated class
        bd = MyBitDict()

        # Set and access bit fields
        bd['enabled'] = True
        bd['mode'] = 2
        bd['value'] = -5

        # Get the integer representation
        value = bd.to_int()

        # Create an instance from an integer
        bd2 = MyBitDict(value)
        ```
    """
    if not isinstance(config, dict):
        raise TypeError("config must be a dictionary")

    # Subtype classes are stored in a dictionary for recursive creation.
    subtypes: dict[str, list[type[BitDict] | None]] = {}

    def _calculate_total_width(cfg) -> int:
        """
        Calculates the total bit width based on the configuration.

        This is a helper function that calculates the total number of bits
        required to store all the bit fields defined in the configuration.

        Args:
            cfg (dict): The configuration dictionary.

        Returns:
            int: The total bit width.
        """
        max_bit = 0
        for prop_config in cfg.values():
            end_bit = prop_config["start"] + prop_config["width"]
            max_bit = max(max_bit, end_bit)
        return max_bit

    def _validate_property_config(prop_config_top: dict[str, Any]) -> None:
        """
        Recursively validates the property configuration.

        This helper function checks that the configuration dictionary
        is valid, including the nested configurations for 'bitdict' types.
        It ensures that all required keys are present, that property names
        are valid identifiers, that bit fields do not overlap, and that
        default values are within the allowed range for the data type.

        Args:
            prop_config_top (dict): The top-level configuration dictionary.

        Raises:
            ValueError: If the configuration is invalid.
            TypeError: If the config is not a dictionary.
        """
        for prop_name, prop_config in prop_config_top.items():
            if not isinstance(prop_name, str) or not prop_name.isidentifier():
                raise ValueError(f"Invalid property name: {prop_name}")
            required_keys = {"start", "width", "type"}
            if not isinstance(prop_config, (dict, MappingProxyType)):
                raise TypeError(
                    "Property configuration must be a dictionary or MappingProxyType"
                )
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
                        assert not isinstance(
                            prop_config, MappingProxyType
                        ), "Defaults not defined but config already frozen."
                        prop_config["default"] = False
                    elif prop_config["type"] in ("uint", "int"):
                        assert not isinstance(
                            prop_config, MappingProxyType
                        ), "Defaults not defined but config already frozen."
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

                if len(prop_config["subtype"]) == 0:
                    raise ValueError(
                        f"'bitdict' type for property '{prop_name}' must have at least one subtype"
                    )

                for sub_config in prop_config["subtype"]:
                    # Recursively validate sub-configurations
                    subtypes.setdefault(prop_name, []).append(
                        None if sub_config is None else bitdict_factory(sub_config)
                    )  # We can use the factory recursively

    def _check_overlapping(cfg) -> None:
        """
        Checks for overlapping bit field definitions.

        This helper function ensures that no two bit fields in the
        configuration overlap.

        Args:
            cfg (dict): The configuration dictionary.

        Raises:
            ValueError: If any bit fields overlap.
        """
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
        """
        A dynamic bit-field dictionary for structured data manipulation.

        BitDict provides a flexible way to define and interact with data structures
        where individual fields occupy specific bit ranges. It supports a variety of
        data types including integers (signed and unsigned), booleans, and nested
        BitDict instances, enabling complex data layouts to be easily managed.

        Key Features:
        - **Dynamic Configuration:**  BitDict classes are dynamically created based on a
          provided configuration, defining the structure and properties of the bit field.
        - **Sub-BitDict Support:** Allows nesting of BitDict instances, enabling hierarchical
          data structures with conditional sub-fields based on selector values.
        - **Type Handling:** Enforces type and range checking for property assignments,
          ensuring data integrity.
        - **Data Conversion:** Supports conversion to and from integers, bytes, and
          JSON-compatible dictionaries.
        - **Iteration:** Provides an iterator to traverse properties in LSB to MSB order.

        Use Cases:
        - Parsing and generating binary data formats (e.g., network packets, file formats).
        - Representing hardware registers and memory-mapped I/O.
        - Implementing data structures with specific bit-level packing requirements.

        Example:
        ```python
        config = {
            "enabled": {"type": "bool", "start": 0, "width": 1, "default": False},
            "mode": {"type": "uint", "start": 1, "width": 2, "default": 0},
            "value": {"type": "int", "start": 3, "width": 5, "default": 0},
        }
        MyBitDict = BitDict.create("MyBitDict", config)
        my_dict = MyBitDict()
        my_dict["enabled"] = True
        my_dict["mode"] = 2
        my_dict["value"] = -5
        print(my_dict.to_json())
        ```
        """

        _config: MappingProxyType[str, Any] = MappingProxyType(deepcopy(config))
        _subtypes: dict[str, list[type[BitDict] | None]] = subtypes
        _total_width: int = total_width
        __name__: str = name

        def __init__(
            self, value: int | bytes | bytearray | dict[str, Any] | None = None
        ) -> None:
            """Initializes a BitDict instance with a specified value.
            The initial value can be provided as an integer,
            bytes/bytearray, or a dictionary. If no value is provided,
            the BitDict is initialized to its default state (all bits
            zeroed).

                value (int | bytes | bytearray | dict[str, Any] | None,
                optional): The initial value for the BitDict.
                    - If `int`, the BitDict is set to this integer value.
                      Value must be within the representable range.
                    - If `bytes` or `bytearray`, the BitDict is initialized
                      from the big-endian representation of these bytes. The
                      length of the byte sequence must be appropriate for the
                      BitDict's total width.
                    - If `dict`, the BitDict is initialized using the
                      dictionary's key-value pairs.
                    - If `None`, the BitDict is initialized to its default
                      state. Defaults to None.

                TypeError: If `value` is not one of the supported types
                    (int, bytes, bytearray, dict, None).
                ValueError:
                    - If `value` is an integer that exceeds the maximum or
                      falls below the minimum representable value given the
                      BitDict's total width.
                    - If `value` is a bytes or bytearray object whose length
                      is incompatible with the BitDict's total width.
            """
            self._value = 0
            # Instances of subbitdicts
            self._subbitdicts: dict[str, list[BitDict | None]] = {}

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
            """
            Retrieves the value associated with the given key.
            The key corresponds to a property defined in the BitDict's configuration.
            The type of the returned value depends on the property's type:
            - 'bool': Returns a boolean value.
            - 'int': Returns a signed integer value (two's complement).
            - 'uint': Returns an unsigned integer value.
            - 'bitdict': Returns a sub-BitDict, selected by the value of another property.
            Args:
                key: The name of the property to retrieve.
            Returns:
                The value of the property, with the type depending on the property's configuration.
                Can be a bool, int, or BitDict.
            Raises:
                KeyError: If the key is not a valid property in the configuration.
                ValueError: If attempting to read a 'reserved' property.
                AssertionError: If the selector value for a 'bitdict' type is not an integer,
                        or if an unknown property type is encountered.
            """
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
            """Sets the value of a property within the BitDict.
            Args:
                key (str): The name of the property to set.
                value (bool | int): The value to set the property to.  Must be
                a boolean or integer, depending on the property's type.
            Raises:
                KeyError: If the given key is not a valid property in the BitDict's configuration.
                ValueError: If attempting to set a reserved property, or if the provided value
                is out of the allowed range for the property.
                TypeError: If the provided value is not of the expected type (boolean or integer)
                for the property.
            """
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
            """
            Returns the total width of the bit dictionary, representing the number
            of bits it can store.
            Returns:
                int: The total width (number of bits) of the bit dictionary.
            """

            return self._total_width

        def __contains__(self, key: str) -> bool:
            """Check if a property exists within this BitDict or its nested BitDicts.
            This method checks for the existence of a given key in the BitDict's configuration.
            It considers the current selector state, meaning that if a property exists only within
            a deselected subtype, this method will return False.
            Args:
                key: The property name (key) to check for.
            Returns:
                True if the property exists and is accessible given the current selector state,
                False otherwise.
            """
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

        def __iter__(self) -> Generator[tuple[str, bool | BitDict | int], Any, None]:
            """Iterates over the BitDict, yielding (name, value) pairs for each
            non-reserved field.
            Yields:
                Generator[tuple[Any, bool | Any | BitDict | None], Any, None]:
                A generator that yields tuples of (name, value), where name is the
                field name and value is the corresponding value in the BitDict.
                The values can be of type bool, Any, BitDict, or None.
            """
            sps = sorted(self._config.items(), key=lambda item: item[1]["start"])
            for name, _ in (sp for sp in sps if sp[1]["type"] != "reserved"):
                yield name, self[name]

        def __repr__(self) -> str:
            """
            Return a string representation of the BitDict object.
            The string representation includes the class name and a JSON-like
            representation of the BitDict's contents, obtained via the `to_json()` method.
            Returns:
                str: A string representation of the BitDict.
            """

            return f"{self.__class__.__name__}({self.to_json()})"

        def __str__(self) -> str:
            """
            Returns a string representation of the BitDict object.

            This method converts the BitDict object to its JSON representation
            and then returns the string representation of that JSON object.

            Returns:
                str: A string representation of the BitDict object in JSON format.
            """

            return str(self.to_json())

        def _get_subbitdict(self, key: str, selector_value: int) -> BitDict:
            """Retrieves a sub-BitDict associated with a given key and selector value.
            If the sub-BitDict does not already exist, it is created, initialized,
            and stored for future access.
            Args:
                key: The key associated with the sub-BitDict.  This corresponds to a
                 property defined in the BitDict's configuration.
                selector_value: The selector value used to identify the specific
                        sub-BitDict within the list of possible sub-BitDicts
                        for the given key.  This value is typically derived
                        from another property acting as a selector.
            Returns:
                The sub-BitDict associated with the given key and selector value.
                The returned BitDict is guaranteed to exist.
            Raises:
                AssertionError: If the subtype class has not been created for the
                        given selector value, or if the created sub-BitDict
                        is None.
            """

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
            """Sets the parent BitDict and the key associated with this BitDict in the parent.
            Args:
                parent: The parent BitDict.
                key: The key associated with this BitDict in the parent.
            """

            self._parent = parent
            self._parent_key = key

        def _update_parent(self) -> None:
            """Updates the parent BitField with the current value of this BitField.
            This method assumes that the parent BitField, as well as the key
            associated with this BitField within the parent's configuration,
            are properly set. It calculates a mask based on the width defined
            in the parent's configuration for this BitField, clears the
            corresponding bits in the parent's value, and then sets those bits
            to the current value of this BitField.
            """

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
            """Clears the bit dictionary, setting all bits to 0."""

            self.set(0)

        def reset(self) -> None:
            """Resets the BitDict to its default values.
            Iterates through the properties defined in the configuration.
            If a property is a reserved type, it is skipped.
            If a property is a nested BitDict, its reset method is called recursively.
            Otherwise, the property is set to its default value as specified in the configuration.
            """

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
            """Sets the value of the BitDict.
            The value can be set in two ways:
            1.  As an integer: In this case, the integer value is assigned to the
                underlying integer representation of the BitDict.  A ValueError is
                raised if the integer is outside the allowed range, given the
                configured bit width.
            2.  As a dictionary: In this case, the dictionary is treated as a set
                of property values to be assigned to the BitDict.  The keys of the
                dictionary correspond to the property names defined in the BitDict's
                configuration.  If a property is present in the dictionary, its
                value is assigned to the corresponding sub-BitDict or bit field.
                If a property is not present in the dictionary but has a "default"
                value specified in the configuration, the default value is assigned.
            Args:
                value: The value to set.  Can be an integer or a dictionary of
                property values.
            Raises:
                ValueError: If the integer value is outside the allowed range for
                the configured bit width.
                AssertionError: If the selector value is not an integer when setting
                a sub-BitDict.
            """

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
            """Update the BitDict with values from another dictionary.
            Args:
                data (dict[str, Any]): A dictionary containing the keys and values to update
                in the BitDict.  Keys must be strings and values must be convertible
                to integers within the BitDict's bit_length.
            Raises:
                TypeError: If `data` is not a dictionary.
                ValueError: If a value in `data` cannot be represented within the
                BitDict's bit_length.
            """

            if not isinstance(data, dict):
                raise TypeError("update() requires a dictionary")
            for key, value in data.items():
                self[key] = value  # Use __setitem__ for type/range checking

        def to_json(self) -> dict[str, Any]:
            """
            Converts the BitDict to a JSON-serializable dictionary.
            Iterates through the BitDict in reverse order, creating a dictionary
            where keys are the names of the bitfields and values are their
            corresponding values. If a value is a BitDict itself, its `to_json`
            method is called recursively to convert it to a JSON-serializable
            dictionary as well.
            Returns:
                dict[str, Any]: A dictionary representation of the BitDict suitable
                for JSON serialization.
            """

            result = {}
            for name, _ in list(self)[::-1]:  # Use the iterator
                result[name] = self[name]
                if hasattr(result[name], "to_json"):
                    result[name] = result[
                        name
                    ].to_json()  # Recurse for nested bitdicts.
            return result

        def to_bytes(self) -> bytes:
            """Convert the bit dictionary to a byte string.
            The resulting byte string represents the underlying integer value
            of the bit dictionary in big-endian byte order. The length of the
            byte string is determined by the total width of the bit dictionary,
            rounded up to the nearest whole byte.
            Returns:
                bytes: A byte string representing the bit dictionary's value.
            """

            num_bytes = (self._total_width + 7) // 8  # Round up to nearest byte
            return self._value.to_bytes(num_bytes, "big")

        def to_int(self) -> int:
            """
            Returns the integer representation of the BitDict.
            This method provides a way to access the underlying integer value
            that represents the BitDict's data.
            Returns:
                int: The integer value of the BitDict.
            """

            return self._value

        @classmethod
        def get_config(cls) -> MappingProxyType[str, Any]:
            """Returns the configuration settings for the BitDict class.
            The configuration is stored in a MappingProxyType, which provides
            a read-only view of the underlying dictionary. This prevents
            accidental modification of the configuration after the class
            has been initialized.
            Returns:
                MappingProxyType[str, Any]: A read-only mapping containing the
                configuration settings.
            """

            return cls._config

    # end class BitDict

    # Set the name of the dynamically created class.
    BitDict.__name__ = name
    return BitDict
