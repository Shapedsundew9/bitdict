# bitdict

[![Build Status](https://github.com/Shapedsundew9/bitdict/actions/workflows/python-package.yml/badge.svg)](https://github.com/Shapedsundew9/bitdict/actions/workflows/python-package.yml)
[![codecov](https://codecov.io/gh/Shapedsundew9/bitdict/graph/badge.svg?token=W3H0k3dZ51)](https://codecov.io/gh/Shapedsundew9/bitdict)
[![Known Vulnerabilities](https://snyk.io/test/github/shapedsundew9/bitdict/badge.svg)](https://snyk.io/test/github/shapedsundew9/bitdict)
[![Maintainability](https://api.codeclimate.com/v1/badges/d76bcc73ae04362a2f7f/maintainability)](https://codeclimate.com/github/Shapedsundew9/bitdict/maintainability)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI version](https://badge.fury.io/py/bitdict.svg)](https://pypi.org/project/bitdict/)

BitDict is a Python library for creating custom bit-packed data structures with dynamically defined substructures. It allows you to define and manipulate data structures where individual fields occupy specific bit ranges, similar to a struct in C. This is particularly useful for parsing and generating binary data formats, representing hardware registers, and implementing data structures with specific bit-level packing requirements.

## Installation

```bash
pip install bitdict
```

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
- `description` (str, optional): Arbitary text that is only used in `the generate_markdown_tables` documentation generation function.
- `valid` (dict, optional): A dictionary defining valid values or ranges for the bit field. Cannot be used with 'bitdict' type.
  - `value` (set, optional): A set of valid values for the field. Each value must be an integer or boolean.
  - `range` (list of tuples, optional): A list of valid ranges for the field. Each tuple must contain one, two or 3 integers representing the start (inclusive) and end (exclusive) of the range and the step. Note that both `value` and `range` may be defined and may overlap.

## API

### generate_markdown_tables Function

The `generate_markdown_tables` function converts a bitdict configuration dictionary into a list of markdown tables.

- `generate_markdown_tables(config: dict, include_types: bool = True) -> list[str]`: Converts a bitdict configuration dictionary into a list of markdown tables.
  - `config` (dict): The bitdict configuration dictionary that needs to be converted.
  - `include_types` (bool, optional): A boolean to indicate if data types should be included in the output. Defaults to True.
  - Returns: A list of formatted markdown strings representing the bitdict configuration in table format.

Using the example configuration above:

```python
print(generate_markdown_tables(MyBitDict)[0])
```

returns

```markdown
## BitDict

| Name | Type | Bitfield | Default | Description |
|---|:-:|:-:|:-:|---|
| enabled | bool | 0 | False |  |
| mode | uint | 2:1 | 0 |  |
| value | int | 7:3 | 0 |  |
```

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
    "Reserved": {"start": 4, "width": 2, "type": "uint"},
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

Executing

```python
print('\n\n'.join(generate_markdown_tables(MyBitDict)))
```

Generates the following markdown.

```markdown
## BitDict

| Name | Type | Bitfield | Default | Description |
|---|:-:|:-:|:-:|---|
| SubValue | bitdict | 3:0 | N/A | See 'SubValue' definition table(s). |
| Reserved | uint | 5:4 | 0 |  |
| Mode | bool | 6 | False |  |
| Constant | bool | 7 | False |  |

## SubValue: Mode = 0

| Name | Type | Bitfield | Default | Description |
|---|:-:|:-:|:-:|---|
| PropA | uint | 1:0 | 0 |  |
| PropB | int | 3:2 | -1 |  |

## SubValue: Mode = 1

| Name | Type | Bitfield | Default | Description |
|---|:-:|:-:|:-:|---|
| PropC | uint | 2:0 | 1 |  |
| PropD | bool | 3 | True |  |
```

## FAQ

**Question**: What value does a bitfield have when the selector value is changed?
**Answer**: _When the selector value is changed, the bitfield associated with the selector is reset to its default value._

**Question**: Can you have a bitfield property with the same name as another bitfields property?
**Answer**: _No, you cannot have a bitfield property with the same name as another bitfield's property within the same BitDict configuration. Each property name within a BitDict configuration must be unique to avoid conflicts and ensure that each bitfield can be correctly identified and accessed._

**Question**: What value does an undefined bitfield have i.e. the bits that are between the defined properties?
**Answer**: _Undefined bitfields, or the bits that are between the defined properties, are typically set to 0 by default. This ensures that any gaps between defined bitfields do not contain arbitrary or undefined values. This behavior is consistent with the initialization and reset methods in the `BitDict` class, which set all bits to 0 unless specified otherwise._
