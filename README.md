# bitdict Package Documentation

The `bitdict` package provides a way to define and interact with bitfield-like data structures in Python. It allows you to map named properties to specific bits or ranges of bits within an integer or byte string, and to define nested interpretations based on the values of other properties. Think of it as a declarative way to define binary data layouts.

## Installation

```bash
pip install bitdict  # Assuming you publish it to PyPI
```

Or, since it's a single file, you can simply copy `bitdict.py` into your project. There are no external dependencies.

## Usage

The core of `bitdict` is the `bitdict_factory` function. This factory takes a configuration dictionary and returns a custom BitDict class. You then use this generated class to create instances of your bitfield structure.

### 1. Defining the Configuration

The configuration dictionary defines the structure of your bitfield. It's a dictionary where:

**Keys:** Are strings representing the names of your properties (must be valid Python identifiers).

**Values:** Are dictionaries describing each property, with the following keys:

- `"start"` (int, required): The starting bit position (0-indexed, where 0 is the least significant bit).
- `"width"` (int, required): The number of bits the property occupies (must be greater than 0).
- `"type"` (str, required): The data type of the property. Must be one of:
  - `"bool"`: A single-bit boolean value. `width` must be 1.
  - `"uint"`: An unsigned integer.
  - `"int"`: A signed integer (two's complement).
  - `"reserved"`: Indicates reserved bits. These bits are ignored when setting values and always read as `None` via `to_json()` or 0 as an Integer.
  - `"bitdict"`: Indicates a nested `BitDict` structure. Requires `"subtype"` and `"selector"` keys.
- `"default"` (optional, except for `"reserved"`): The default value for the property. Restrictions:
  - `"bool"`: `True`, `False`, or omitted (defaults to `False`).
  - `"uint"`: 0, 1, or -1 (representing all bits set), or omitted (defaults to 0).
  - `"int"`: 0, 1, or -1, or omitted (defaults to 0).
  - `"reserved"`: Must *not* be present. Reserved bits have no default value.
- `"subtype"` (list, required if `"type"` is `"bitdict"` and `"selector"` is provided): A *list* of configuration dictionaries. Used for nested `BitDict` structures. The `"selector"` key determines which configuration in this list to use.
- `"selector"` (str, optional): The name of another property within the *same* level of the configuration. The *integer* value of this selector property is used as an index into the `"subtype"` list to choose the appropriate nested configuration.

**Important Considerations:**

- **Bit Order:** Bit 0 is the least significant bit (LSB).
- **Endianness:** When initializing from or converting to bytes, big-endian byte order is used.
- **Overlapping:** Properties cannot overlap. The `bitdict_factory` will raise a `ValueError` if overlaps are detected.
- **Total Width:** The bit width of the structure is determined by the largest value of `start + width` in the config.

### 2. Creating the BitDict Class

```python
from bitdict import bitdict_factory

config = {
    "Constant": {"start": 7, "width": 1, "type": "bool"},
    "Mode": {"start": 6, "width": 1, "type": "bool", "selector": "Mode"},
    "Reserved": {"start": 4, "width": 2, "type": "reserved"},
    "SubValue": {
        "start": 0,
        "width": 4,
        "type": "bitdict",
        "subtype": [
            {  # Mode = 0
                "PropA": {"start": 0, "width": 2, "type": "uint", "default": 0},
                "PropB": {"start": 2, "width": 2, "type": "int", "default": -1},
            },
            {  # Mode = 1
                "PropC": {"start": 0, "width": 3, "type": "uint", "default": 1},
                "PropD": {"start": 3, "width": 1, "type": "bool", "default": True},
            }
        ]
    }
}

MyBitDict = bitdict_factory(config, name="MyBitDict")  # Create the class

# You can optionally give the class a custom name
```

### 3. Creating Instances

You can create instances of your BitDict class in several ways:

```python
# From an integer:
instance1 = MyBitDict(0x8C)

# From bytes (big-endian):
instance2 = MyBitDict(bytes([0x8C]))

# From a dictionary:
instance3 = MyBitDict({"Constant": True, "Mode": False, "SubValue": {"PropA": 2, "PropB": -1}})

# With no arguments (defaults are used):
instance4 = MyBitDict()
```

If you provide an integer or bytes object that is *smaller* than the total bit width, it will be zero-padded on the left (most significant bits). If it's *larger*, a `ValueError` will be raised.

### 4. Accessing and Modifying Properties

```python
# Accessing properties:
print(instance1.Constant)  # Access like an attribute
print(instance1["Mode"])   # Access like a dictionary key

# Modifying properties:
instance1.Constant = False
instance1["Mode"] = True

# Accessing nested properties:
print(instance1["SubValue"]["PropC"])  # Access nested properties
instance1["SubValue"]["PropD"] = False
```

### 5. Methods

- `__init__(self, value=0)`: Constructor. See "Creating Instances" above.
- `__getitem__(self, key)`: Gets the value of a property (dictionary-style access).
- `__setitem__(self, key, value)`: Sets the value of a property (dictionary-style access). Raises TypeError or ValueError for invalid types or out-of-range values.
- `__len__(self)`: Returns the total bit width of the BitDict.
- `__contains__(self, key)`: Checks if a property exists and has a non-zero (or True) value.
- `__iter__(self)`: Iterates over the properties in LSB to MSB order, yielding (property_name, value) tuples.
- `__repr__(self)`: Returns a string representation of the BitDict.
- `__str__(self)`: Returns a user-friendly string representation.
- `update(self, data)`: Updates multiple properties from a dictionary. Uses the same type and range checking as `__setitem__`.
- `to_json(self)`: Returns a standard Python dictionary representing the `BitDict`, suitable for serialization with the `json` module. Nested `BitDict` instances are recursively converted to dictionaries. Reserved bits are included with a value of `None`.
- `to_bytes(self)`: Returns the underlying integer value as a `bytes` object (big-endian).
- `to_int(self)`: Returns the underlying integer value.
- `get_config()`: (Class method) Returns the configuration dictionary used to create the `BitDict` class. This is read-only.

### 6. Error Handling

- `ValueError`: Raised for invalid configuration dictionaries, out-of-range values, attempts to set reserved properties, and overlapping bit definitions.
- `TypeError`: Raised for incorrect argument types during initialization or property setting.
- `KeyError`: Raised when trying to access a non-existent property.

### 7. Complete Example

```python
from bitdict import bitdict_factory

# Define a configuration for a hypothetical network packet header
packet_config = {
    "Version": {"start": 28, "width": 4, "type": "uint"},
    "HeaderLength": {"start": 24, "width": 4, "type": "uint"},
    "DSCP": {"start": 18, "width": 6, "type": "uint"},
    "ECN": {"start": 16, "width": 2, "type": "uint"},
    "TotalLength": {"start": 0, "width": 16, "type": "uint"},
}

# Create a class
PacketHeader = bitdict_factory(packet_config, name="PacketHeader")

# Create an instance from bytes
packet_data = bytes([0x45, 0x00, 0x00, 0x73])  # Example packet data
header = PacketHeader(packet_data)

print(f"Version: {header.Version}")
print(f"Header Length: {header.HeaderLength}")
print(f"Total Length: {header.TotalLength}")
print(f"JSON Representation: {header.to_json()}")

# Modify the header
header.TotalLength = 1500
print(f"New Total Length: {header.TotalLength}")
print(f"New Bytes: {header.to_bytes()}")

# Example with nested structures and a selector
config_with_nesting = {
    "Type": {"start": 7, "width": 1, "type": "bool", "selector": "Type"},
    "Payload": {
        "start": 0,
        "width": 7,
        "type": "bitdict",
        "subtype": [
            {  # Type = 0 (Data Packet)
                "SequenceNumber": {"start": 0, "width": 7, "type": "uint"},
            },
            {  # Type = 1 (Control Packet)
                "Command": {"start": 0, "width": 3, "type": "uint"},
                "Flags": {"start": 3, "width": 4, "type": "uint"},
            },
        ],
    },
}

ControlAndData = bitdict_factory(config_with_nesting, name="ControlAndData")
data_packet = ControlAndData({"Type": False, "Payload": {"SequenceNumber": 42}})
control_packet = ControlAndData({"Type": True, "Payload": {"Command": 5, "Flags": 7}})

print(data_packet.to_json())
print(control_packet.to_json())

# Show defaults:
defaults = ControlAndData()
print(defaults.to_json())
```
