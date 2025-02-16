
# BitDict

BitDict is a Python library for creating custom bit-packed data structures. It allows you to define and manipulate data structures where individual fields occupy specific bit ranges, similar to a struct in C. This is particularly useful for parsing and generating binary data formats, representing hardware registers, and implementing data structures with specific bit-level packing requirements.

## Concept and Use Case

BitDict provides a flexible way to define and interact with data structures where individual fields occupy specific bit ranges. It supports various data types, including integers (signed and unsigned), booleans, and nested BitDict instances, enabling complex data layouts to be easily managed.

### Example Use Case

Consider a scenario where you need to parse a binary data format with specific bit-level packing requirements. BitDict allows you to define the structure of this data format and provides methods to access and manipulate individual fields within the structure.

## Simple Configuration and Usage Example

Here's a simple example of how to define and use a BitDict:

```python
from bitdict import bitdict_factory

# Define the configuration for the BitDict
config = {
    "enabled": {"start": 0, "width": 1, "type": "bool"},
    "mode": {"start": 1, "width": 2, "type": "uint"},
    "value": {"start": 3, "width": 5, "type": "int"},
}

# Create a BitDict class using the factory function
MyBitDict = bitdict_factory(config, "MyBitDict")

# Create an instance of the BitDict
bd = MyBitDict()

# Set and access bit fields
bd["enabled"] = True
bd["mode"] = 2
bd["value"] = -5

# Get the integer representation
value = bd.to_int()
print(value)  # Output: 221

# Create an instance from an integer
bd2 = MyBitDict(value)
print(bd2.to_json())  # Output: {'value': -5, 'mode': 2, 'enabled': True}
```

## Configuration

The configuration for a BitDict is a dictionary that defines the structure of the bit fields. Each key in the dictionary represents a field name, and the value is another dictionary with the following keys:

- `start` (int): The starting bit position (LSB = 0).
- `width` (int): The width of the bit field in bits.
- `type` (str): The data type of the bit field. Can be one of: 'bool', 'uint', 'int', 'reserved', 'bitdict'.
- `default` (optional): The default value for the bit field. If not provided, defaults to False for 'bool', 0 for 'uint' and 'int'.
- `subtype` (list of dict, optional): Required for 'bitdict' type. Ignored for other types. A list of sub-bitdict configurations to select from based on the value of the selector property.
- `selector` (str, optional): Required for 'bitdict' type. Ignored for other types. The name of the property used to select the active sub-bitdict. This property must be of type 'bool' or 'uint' and have a width <= 16.

## API

### BitDict Class

The BitDict class provides methods to interact with the bit-packed data structure. Here are some of the key methods:

- `__getitem__(self, key: str) -> bool | int | BitDict`: Retrieves the value associated with the given key.
- `__setitem__(self, key: str, value: bool | int) -> None`: Sets the value of a property within the BitDict.
- `__len__(self) -> int`: Returns the total width of the bit dictionary, representing the number of bits it can store.
- `__contains__(self, key: str) -> bool`: Checks if a property exists within this BitDict or its selected nested BitDicts.
- `__iter__(self) -> Generator[tuple[str, bool | BitDict | int], Any, None]`: Iterates over the BitDict, yielding (name, value) pairs for each non-reserved field.
- `clear(self) -> None`: Clears the bit dictionary, setting all bits to 0.
- `reset(self) -> None`: Resets the BitDict to its default values.
- `set(self, value: int | dict[str, Any]) -> None`: Sets the value of the BitDict.
- `update(self, data: dict[str, Any]) -> None`: Updates the BitDict with values from another dictionary.
- `to_json(self) -> dict[str, Any]`: Converts the BitDict to a JSON-serializable dictionary.
- `to_bytes(self) -> bytes`: Converts the bit dictionary to a byte string.
- `to_int(self) -> int`: Returns the integer representation of the BitDict.
- `get_config(cls) -> MappingProxyType[str, Any]`: Returns the configuration settings for the BitDict class.

## Detailed Example

Here's a more detailed example that demonstrates the use of nested BitDicts and selectors:

```python
from bitdict import bitdict_factory

# Define the configuration for the BitDict
config = {
    "Constant": {"start": 7, "width": 1, "type": "bool"},
    "Mode": {"start": 6, "width": 1, "type": "bool"},
    "Reserved": {"start": 4, "width": 2, "type": "reserved"},
    "SubValue": {
        "start": 0,
        "width": 4,
        "type": "bitdict",
        "selector": "Mode",
        "subtype": [
            {
                "PropA": {"start": 0, "width": 2, "type": "uint", "default": 0},
                "PropB": {"start": 2, "width": 2, "type": "int", "default": -1},
            },
            {
                "PropC": {"start": 0, "width": 3, "type": "uint", "default": 1},
                "PropD": {"start": 3, "width": 1, "type": "bool", "default": True},
            },
        ],
    },
}

# Create a BitDict class using the factory function
MyBitDict = bitdict_factory(config, "MyBitDict")

# Create an instance of the BitDict
bd = MyBitDict()

# Set and access bit fields
bd["Constant"] = True
bd["Mode"] = False
bd["SubValue"]["PropA"] = 2
bd["SubValue"]["PropB"] = -1

# Get the integer representation
value = bd.to_int()
print(value)  # Output: 142

# Create an instance from an integer
bd2 = MyBitDict(value)
print(
    bd2.to_json()
)  # Output: {'Constant': True, 'Mode': False, 'SubValue': {'PropB': -1, 'PropA': 2}}

# Change the mode and access the new sub-bitdict
bd["Mode"] = True
bd["SubValue"]["PropC"] = 5
bd["SubValue"]["PropD"] = False

# Get the updated integer representation
value = bd.to_int()
print(value)  # Output: 197

# Create an instance from the updated integer
bd3 = MyBitDict(value)
print(
    bd3.to_json()
)  # Output: {'Constant': True, 'Mode': True, 'SubValue': {'PropD': False, 'PropC': 5}}
```

This example demonstrates how to define a BitDict with nested sub-bitdicts and selectors, set and access bit fields, and convert the BitDict to and from its integer representation.
