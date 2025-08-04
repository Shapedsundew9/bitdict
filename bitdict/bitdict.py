"""
bitdict module for creating and manipulating bit field dictionaries.

This module provides a `bitdict_factory` function that dynamically generates
classes for working with bit fields within an integer value.  These classes,
referred to as BitDicts, allow you to define a structure of named bit fields,
each with a specified start position, width, and data type.


- **Dynamic Bitfield Definition:**  Define bitfield layouts at runtime using
    a configuration dictionary.
- **Data Type Support:** Supports boolean, unsigned integer, and signed
    integer bitfields.
- **Nested BitDicts:** Allows defining hierarchical structures with nested
    BitDicts, selected by a selector property.
- **Data Validation:**  Performs validation of property configurations,
    including type checking and range validation.
- **Conversion Methods:** Provides methods for converting BitDicts to and
    from integers, bytes, and JSON-compatible dictionaries.

Usage:

1.  Define a configuration dictionary specifying the bitfield layout.
2.  Call `bitdict_factory` with the configuration to create a BitDict class.
3.  Instantiate the generated class to create a BitDict object.
4.  Access and manipulate bitfields using item access (e.g., `bd["field_name"]`).
"""

from __future__ import annotations

# Import the factory and ABC from the new factory module
from .factory import BitDictABC, bitdict_factory

__all__ = ["BitDictABC", "bitdict_factory"]
