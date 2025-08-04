"""
Test cases for the bitdict_factory function.

This class contains various unit tests to validate the behavior of the
bitdict_factory function, ensuring it correctly handles valid and invalid
configurations, including edge cases and error conditions.
"""

import timeit
import unittest
from types import MappingProxyType

from bitdict import BitDictABC, bitdict_factory

# Lots of duplicate looking test data & protected access in the test cases
# pylint: disable=duplicate-code
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-lines


class TestBitDictFactory(unittest.TestCase):
    """
    Unit tests for the bitdict_factory function.
    This test suite covers various scenarios for validating the configuration
    passed to the bitdict_factory function, including:
    - Valid configurations with different field types (uint, bool).
    - Invalid configurations with incorrect types, missing keys,
        invalid values for start, width, and type.
    - Mismatches between boolean field widths and specified widths.
    - Usage of reserved keywords like 'default' with reserved types.
    - Invalid default values for uint, int, and bool types.
    - Missing or invalid subtype and selector configurations for bitdict types.
    - Overlapping bit fields.
    - Nested configuration validation for bitdict subtypes.
    - Invalid selector properties (non-bool/uint selectors, or selectors with too large width).
    """

    def test_factory_valid_config(self) -> None:
        """
        Tests the bitdict_factory function with a valid configuration.
        This test verifies that the factory function:
            - Creates a class.
            - Stores the configuration correctly.
            - Calculates the total width correctly.
            - Allows instantiation of the created class.
        """

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        MyBitDict = bitdict_factory(config)
        self.assertTrue(issubclass(MyBitDict, object))  # Check it's a class
        self.assertEqual(MyBitDict.get_config(), config)  # Check config stored
        self.assertEqual(MyBitDict._total_width, 5)  # type: ignore[protected-access]
        _ = MyBitDict()  # Check we can instantiate.

    def test_factory_invalid_config_type(self) -> None:
        """
        Test that the bitdict_factory raises a TypeError when passed an invalid config type.
        """

        with self.assertRaises(TypeError):
            bitdict_factory("not a dict")  # type: ignore

    def test_factory_invalid_property_name(self):
        """
        Test that the bitdict_factory raises a ValueError when an invalid property name is provided.

        An invalid property name is one that cannot be used as a valid Python identifier.
        In this case, the property name "1badname" starts with a digit, which is not allowed.
        """
        with self.assertRaises(ValueError):
            bitdict_factory({"1badname": {"start": 0, "width": 1, "type": "bool"}})

    def test_factory_missing_required_keys(self):
        """
        Test that the bitdict_factory function raises a ValueError when required
        keys are missing from the field definitions.
        Specifically, it checks for missing 'width', 'start', and 'type' keys.
        """
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "type": "uint"}})  # Missing width
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"width": 4, "type": "uint"}})  # Missing start
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": 4}})  # Missing type

    def test_factory_invalid_start_value(self):
        """
        Test that the bitdict_factory raises a ValueError when an invalid start value is provided.

        Specifically, it checks for the following invalid start values:
        - A negative integer (-1).
        - A string ("0").
        """
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": -1, "width": 4, "type": "uint"}})
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": "0", "width": 4, "type": "uint"}})

    def test_factory_invalid_width_value(self):
        """Tests that the bitdict_factory raises a ValueError when an invalid
        width value is provided in the field definition.

        Specifically, it checks for the following invalid width values:
            - 0
            - Negative values (e.g., -1)
            - Non-integer values (e.g., "4")
        """
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": 0, "type": "uint"}})
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": -1, "type": "uint"}})
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": "4", "type": "uint"}})

    def test_factory_invalid_type_value(self):
        """
        Test that bitdict_factory raises a ValueError when an invalid type is
        specified in the field definition.
        """
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": 4, "type": "invalid"}})

    def test_factory_bool_width_mismatch(self):
        """
        Test that a ValueError is raised when a bitdict factory is created with a boolean field
        that has a width other than 1.
        """
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": 2, "type": "bool"}})

    def test_factory_invalid_uint_default(self):
        """
        Test that the bitdict_factory raises a ValueError when a uint
        field has a negative default value.
        """
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "uint", "default": -3}}
            )

    def test_factory_invalid_int_default(self):
        """
        Test that bitdict_factory raises a ValueError when an invalid default value
        is provided for an integer field.  Specifically, the default value is
        out of range for the specified width.
        """
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "int", "default": 17}}
            )

    def test_factory_invalid_bool_default(self):
        """
        Test that the bitdict_factory raises a TypeError when a bool field
        has an invalid default value.
        """
        with self.assertRaises(TypeError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 1, "type": "bool", "default": 2}}
            )

    def test_factory_bitdict_missing_subtype(self):
        """
        Test that the bitdict_factory raises a ValueError when the subtype is missing or invalid.

        Specifically, it checks for the following cases:
        - When the 'type' is 'bitdict' but the 'subtype' key is missing.
        - When the 'subtype' key is present but its value is not a list.
        """
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "bitdict"}}
            )  # No subtype
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "bitdict", "subtype": {}}}
            )  # Not a list

    def test_factory_bitdict_missing_selector(self):
        """Test that bitdict_factory raises ValueError when the selector is missing or invalid.

        This test checks two cases:
        1. When the 'selector' key is completely missing from the field definition.
        2. When the 'selector' key is present but its value is an empty dictionary.
        """
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "bitdict", "subtype": []}}
            )  # No selector
        with self.assertRaises(ValueError):
            bitdict_factory(
                {
                    "field1": {
                        "start": 0,
                        "width": 4,
                        "type": "bitdict",
                        "subtype": [],
                        "selector": {},
                    }
                }
            )  # Selector is not string

    def test_factory_overlapping_bits(self):
        """
        Test that the bitdict_factory raises a ValueError when the bitfields overlap.
        """
        with self.assertRaises(ValueError):
            bitdict_factory(
                {
                    "field1": {"start": 0, "width": 4, "type": "uint"},
                    "field2": {"start": 2, "width": 4, "type": "uint"},
                }
            )

    def test_factory_nested_validation(self):
        """
        Test that the bitdict_factory raises a ValueError when an invalid type
        is specified within a nested bitdict configuration. Specifically, this
        test checks if the factory correctly identifies an invalid 'type'
        definition ('invalid' in this case) within the 'subtype' configuration
        of a nested bitdict.
        """
        config = {
            "Mode": {"start": 0, "width": 1, "type": "bool", "selector": "Mode"},
            "SubValue": {
                "start": 1,
                "width": 4,
                "type": "bitdict",
                "subtype": [
                    {"PropA": {"start": 0, "width": 2, "type": "uint"}},
                    {
                        "PropB": {"start": 0, "width": 2, "type": "invalid"}
                    },  # Invalid type in nested config
                ],
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_selector_property(self):
        """
        Tests the bitdict_factory function with invalid selector properties.
        Specifically, it checks for two cases:
        1. When the selector field is not of type 'bool' or 'uint'.
        2. When the selector field's width is greater than 16 bits.
        In both cases, a ValueError should be raised by the bitdict_factory.
        """

        with self.assertRaises(ValueError):
            bitdict_factory(
                {
                    "field1": {
                        "start": 0,
                        "width": 4,
                        "type": "bitdict",
                        "subtype": [],
                        "selector": "field2",
                    },
                    "field2": {
                        "start": 4,
                        "width": 4,
                        "type": "int",
                    },  # Selector is not bool or uint
                }
            )
        with self.assertRaises(ValueError):
            bitdict_factory(
                {
                    "field1": {
                        "start": 0,
                        "width": 4,
                        "type": "bitdict",
                        "subtype": [],
                        "selector": "field2",
                    },
                    "field2": {
                        "start": 4,
                        "width": 17,
                        "type": "uint",
                    },  # Selector width is too large
                }
            )

    def test_factory_valid_config_with_valid_key(self):
        """Test that bitdict_factory correctly handles configurations with the 'valid' key."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"value": {0, 1, 2}},
            },
            "field2": {
                "start": 4,
                "width": 1,
                "type": "bool",
                "valid": {"value": {True}},
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict(0x12)
        self.assertTrue(bd.valid())
        bd["field1"] = 1
        self.assertTrue(bd.valid())
        bd["field1"] = 3
        self.assertFalse(bd.valid())

    def test_factory_invalid_valid_key(self):
        """Test that bitdict_factory raises a ValueError for invalid 'valid' key configurations."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint", "valid": {}},
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint", "valid": {"value": []}},
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"value": set()},
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint", "valid": {"range": []}},
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_valid_config_with_invalid_values(self):
        """Test that bitdict_factory raises a ValueError for invalid values in the 'valid' key."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"value": {16}},
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_valid_method(self):
        """Test the valid method of the BitDict class."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"value": {0, 1, 2}},
            },
            "field2": {
                "start": 4,
                "width": 1,
                "type": "bool",
                "valid": {"value": {True}},
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict(0x12)
        self.assertTrue(bd.valid())
        bd["field1"] = 3
        self.assertFalse(bd.valid())

    def test_inspect_method(self):
        """Test the inspect method of the BitDict class."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"value": {0, 1, 2}},
            },
            "field2": {
                "start": 4,
                "width": 1,
                "type": "bool",
                "valid": {"value": {True}},
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict(0x12)
        self.assertEqual(bd.inspect(), {})
        bd["field1"] = 3
        self.assertEqual(bd.inspect(), {"field1": 3})


class TestBitDict(unittest.TestCase):
    """
    Test suite for the BitDict class, covering various functionalities
    including instance creation, value access, manipulation, and conversion
    to different formats.

    This test suite utilizes a pre-defined configuration to create BitDict
    instances and validate their behavior against expected outcomes. It
    includes tests for:

    - Instance creation with integers, bytes, and dictionaries.
    - Getting and setting boolean, unsigned integer, and integer values.
    - Handling reserved fields.
    - Working with nested BitDicts and selectors.
    - Determining the length (bit width) of a BitDict.
    - Checking for the presence of fields using the 'in' operator.
    - Iterating through fields and their values.
    - Representing BitDicts as strings and dictionaries.
    - Updating BitDicts with dictionary values.
    - Converting BitDicts to JSON, bytes, and integers.
    - Retrieving the configuration of a BitDict.
    - Handling large bit widths and extreme integer values.
    - Error handling for invalid input values.
    - Performance testing of common operations.
    - Testing edge cases and various configurations to ensure robustness.
    """

    def setUp(self):
        """Set up the test environment.

        This method initializes the configuration dictionary and creates an instance
        of the MyBitDict class using the bitdict_factory. The configuration defines
        the structure of the bitfield, including fields like 'Constant', 'Mode', 'Reserved'
        and 'SubValue'. 'SubValue' is a nested bitdict that depends on the value of the
        'Mode' field.  Each field specifies its starting bit, width, and data type.
        Default values are also provided for some fields.
        """
        self.config = {
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
                        "PropD": {
                            "start": 3,
                            "width": 1,
                            "type": "bool",
                            "default": True,
                        },
                    },
                ],
            },
        }
        self.my_bitdict = bitdict_factory(self.config, name="MyBitDict")

    def test_create_instance_int(self):
        """Test that a BitDict instance can be created from an integer.

        Checks that the BitDict instance is correctly initialized with the given integer value.
        Also checks that ValueErrors are raised when the integer is out of the allowed range
        (0-255).
        """
        bd = self.my_bitdict(0x8C)
        self.assertEqual(bd.to_int(), 0x8C)
        with self.assertRaises(ValueError):
            self.my_bitdict(256)  # Too large
        with self.assertRaises(ValueError):
            self.my_bitdict(-256)  # Too small

    def test_create_instance_bytes(self):
        """Test creating an instance of MyBitDict from bytes or bytearray.

        Checks that the instance is correctly initialized with the given byte value.
        Also tests that a ValueError is raised when the input bytes object is too long
        (more than one byte). Finally, it tests that padding works as expected when
        the input byte has leading zero bits.
        """
        bd = self.my_bitdict(bytes([0x8C]))
        self.assertEqual(bd.to_int(), 0x8C)
        bd2 = self.my_bitdict(bytearray([0x8C]))  # Test bytearray too
        self.assertEqual(bd2.to_int(), 0x8C)
        with self.assertRaises(ValueError):
            self.my_bitdict(bytes([0x01, 0x02]))  # Too long
        # Test padding:
        bd3 = self.my_bitdict(bytes([0xC]))
        self.assertEqual(bd3.to_int(), 0xC)

    def test_create_instance_dict(self):
        """Test the creation of MyBitDict instances with a dictionary.

        This test verifies that MyBitDict instances can be created using a dictionary
        to initialize their values. It checks if the values are correctly assigned
        and if the `to_int()` method returns the expected integer representation.
        It also tests the behavior when values are missing in the input dictionary,
        ensuring that default values are used in such cases.
        """
        bd = self.my_bitdict(
            {"Constant": True, "Mode": False, "SubValue": {"PropA": 2, "PropB": -1}}
        )
        self.assertEqual(bd.to_int(), 0b10001110)  # Check against expected value.
        self.assertEqual(bd["Constant"], True)
        self.assertEqual(bd["Mode"], False)
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)
        self.assertEqual(sub_value["PropA"], 2)
        self.assertEqual(sub_value["PropB"], -1)

        # Test with missing values (should use defaults)
        bd2 = self.my_bitdict({"Constant": True})
        self.assertEqual(bd2["Constant"], True)
        self.assertEqual(bd2["Mode"], False)  # Default for bool

    def test_create_instance_invalid_type(self):
        """
        Test that creating an instance of MyBitDict with an invalid type raises a TypeError.
        """
        with self.assertRaises(TypeError):
            self.my_bitdict("string")  # type: ignore

    def test_get_set_bool(self):
        """Test that boolean values can be set and retrieved correctly,
        and that setting a value of the wrong type raises a TypeError.
        """
        bd = self.my_bitdict()
        bd["Constant"] = True
        self.assertEqual(bd["Constant"], True)
        bd["Constant"] = False
        self.assertEqual(bd["Constant"], False)
        with self.assertRaises(TypeError):
            bd["Constant"] = "Frank"  # type: ignore

    def test_get_set_uint(self):
        """Test getting and setting unsigned integer values in the BitDict.

        This test verifies that unsigned integer values can be correctly set and retrieved
        from the BitDict. It also checks that values outside the allowed range raise a
        ValueError, and that assigning values of incorrect types raise a TypeError.
        """
        bd = self.my_bitdict()
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)

        sub_value["PropA"] = 3
        self.assertEqual(sub_value["PropA"], 3)
        with self.assertRaises(ValueError):
            sub_value["PropA"] = 5  # Out of range
        sub_value["PropA"] = True  # Is an int type
        with self.assertRaises(TypeError):
            sub_value["PropA"] = "Harry"  # type: ignore

    def test_get_set_int(self):
        """Test getting and setting integer values within the BitDict.

        This test verifies that integer values can be correctly set and retrieved
        from the BitDict, including negative values within the allowed range.
        It also checks that attempts to set values outside the allowed range
        raise a ValueError, and that attempts to set values of incorrect types
        raise a TypeError.
        """
        bd = self.my_bitdict()
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)

        sub_value["PropB"] = -2
        self.assertEqual(sub_value["PropB"], -2)
        sub_value["PropB"] = 1
        self.assertEqual(sub_value["PropB"], 1)
        with self.assertRaises(ValueError):
            sub_value["PropB"] = -3  # Out of range
        with self.assertRaises(TypeError):
            sub_value["PropB"] = "string"  # type: ignore

    def test_nested_bitdict(self):
        """Test nested BitDict functionality.

        This test verifies that nested BitDicts can be accessed and modified correctly.
        It checks the following:
            - Initial values of nested properties.
            - Setting the parent property resets the nested BitDict to its default value.
            - Individual properties within the nested BitDict can be modified.
            - Accessing the nested BitDict through a variable still works.
            - Attempting to assign an incorrect type to the nested BitDict raises a TypeError.
            - Assigning an integer value to the nested BitDict updates its properties accordingly.
        """
        bd = self.my_bitdict(0x8C)
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)

        self.assertEqual(bd["Mode"], False)
        self.assertEqual(sub_value["PropA"], 0)
        self.assertEqual(sub_value["PropB"], -1)

        bd["Mode"] = True  # Resets Subvalue to bitdict[1] default
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)
        self.assertEqual(sub_value["PropC"], 1)
        self.assertEqual(sub_value["PropD"], True)
        self.assertEqual(sub_value.to_int(), 9)

        sub_value["PropC"] = 5
        self.assertEqual(sub_value["PropC"], 5)
        nested = bd["SubValue"]
        assert isinstance(nested, BitDictABC)
        self.assertEqual(nested["PropC"], 5)
        with self.assertRaises(TypeError):
            bd["SubValue"] = "string"  # type: ignore
        bd["SubValue"] = 3  # Value set
        self.assertEqual(sub_value["PropC"], 3)
        self.assertEqual(sub_value["PropD"], False)

    def test_len(self):
        """Test the __len__ method of the BitDict class.

        It should return the total number of bits the BitDict can hold,
        which is determined by the sum of the bit widths of all fields.
        """
        bd = self.my_bitdict()
        self.assertEqual(len(bd), 8)  # Total bit width

    def test_contains(self):
        """Test the __contains__ method of the BitDict class.

        This method checks if the BitDict instance correctly identifies
        the presence or absence of specific keys. It verifies that
        keys defined in the BitDict are recognized as present, while
        keys not defined are recognized as absent.
        """
        bd = self.my_bitdict()
        self.assertTrue("Constant" in bd)
        self.assertTrue("PropA" in bd)
        self.assertFalse("PropC" in bd)  # Not selected

    def test_iteration(self):
        """Test the iteration functionality of the BitDict.

        This test verifies that the BitDict iterates through its fields in the correct order
        (LSB to MSB)
        and that the values returned during iteration match the expected values based on the
        BitDict's configuration.
        It also checks that sub-properties within fields are accessed correctly during iteration.
        """
        bd = self.my_bitdict(0x8C)
        expected_order = [
            "SubValue",
            "Reserved",
            "Mode",
            "Constant",
        ]  # LSB to MSB order
        actual_order = [name for name, _ in bd]
        self.assertEqual(actual_order, expected_order)

        expected_values = [(True, False, 0, -1, 0), (True, True, 0, True, 1)]
        mode = 0
        for constant, mode_val, reserved, sub_prop_b, sub_prop_a in [
            expected_values[0]
        ]:
            bd = self.my_bitdict({"Constant": constant, "Mode": mode_val})
            for name, value in bd:
                if name == "Constant":
                    self.assertEqual(value, constant)
                elif name == "Mode":
                    self.assertEqual(value, mode_val)
                elif name == "Reserved":
                    self.assertEqual(value, reserved)
                elif name == "SubValue":
                    assert isinstance(value, BitDictABC)
                    if not mode_val:
                        self.assertEqual(value["PropA"], sub_prop_a)
                        self.assertEqual(value["PropB"], sub_prop_b)
                    else:
                        self.assertEqual(value["PropC"], sub_prop_a)
                        self.assertEqual(value["PropD"], sub_prop_b)
            mode = mode + 1

    def test_repr(self):
        """Test the string representation of the BitDict."""
        bd = self.my_bitdict(0x8C)
        self.assertEqual(
            repr(bd),
            "MyBitDict({'Constant': True, 'Mode': False, "
            "'Reserved': 0, 'SubValue': {'PropB': -1, 'PropA': 0}})",
        )

    def test_str(self):
        """Test the string representation of the BitDict."""
        bd = self.my_bitdict(0x8C)
        self.assertEqual(
            str(bd),
            "{'Constant': True, 'Mode': False, 'Reserved': 0,"
            " 'SubValue': {'PropB': -1, 'PropA': 0}}",
        )

    def test_update(self):
        """Test the update method of the BitDict class.

        This method tests that the update method correctly updates the BitDict
        with values from a dictionary, including nested dictionaries.
        It also tests that the update method raises a TypeError if the input
        is not a dictionary and a KeyError if the input dictionary contains
        invalid keys.
        """
        bd = self.my_bitdict()
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)
        bd.update({"Constant": True, "SubValue": {"PropA": 1}})
        self.assertEqual(bd["Constant"], True)
        self.assertEqual(sub_value["PropA"], 1)
        with self.assertRaises(TypeError):
            bd.update("not a dict")  # type: ignore
        with self.assertRaises(KeyError):
            bd.update({"InvalidKey": 1})

    def test_to_json(self):
        """Test the to_json method of the BitDict class.

        This method tests the conversion of a BitDict object to a JSON-compatible
        dictionary. It checks both the base case and a case with nested BitDicts
        and different configurations.
        """
        bd = self.my_bitdict(0x8C)
        expected_json = {
            "Constant": True,
            "Mode": False,
            "Reserved": 0,
            "SubValue": {"PropA": 0, "PropB": -1},
        }
        self.assertEqual(bd.to_json(), expected_json)
        # Test nested to_json
        bd["Mode"] = True
        expected_json = {
            "Constant": True,
            "Mode": True,
            "Reserved": 0,
            "SubValue": {"PropC": 1, "PropD": True},
        }
        self.assertEqual(bd.to_json(), expected_json)

    def test_to_bytes(self):
        """Test that the bitdict can be converted to bytes."""
        bd = self.my_bitdict(0x8C)
        self.assertEqual(bd.to_bytes(), bytes([0x8C]))

    def test_to_int(self):
        """Test that the to_int() method returns the correct integer representation
        of the BitDict."""
        bd = self.my_bitdict(0x8C)
        self.assertEqual(bd.to_int(), 0x8C)

    def test_get_config(self):
        """
        Test that the get_config method returns the correct configuration and that the returned
        configuration is read-only (immutable).
        """
        retrieved_config = self.my_bitdict.get_config()
        self.assertEqual(retrieved_config, self.config)
        # Ensure it's read-only (check for immutability)
        with self.assertRaises(TypeError):
            retrieved_config["Constant"] = "something else"  # type: ignore

    def test_large_bit_width(self):
        """Test that bitdict works with large bit widths.
        This test creates a bitdict with a single field that has a width of 1024 bits.
        It then sets the value of the field to the maximum possible value and asserts
        that the value is correctly retrieved.
        """

        config = {
            "field1": {"start": 0, "width": 1024, "type": "uint"},
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict(2**1024 - 1)
        self.assertEqual(bd["field1"], 2**1024 - 1)

    def test_extreme_values(self):
        """Test the handling of extreme values for uint and int fields.
        This test checks if the bitdict correctly stores and retrieves the maximum
        and minimum possible values for a 32-bit unsigned integer field ('field1')
        and a 32-bit signed integer field ('field2'). It verifies that no overflow
        or underflow occurs when assigning these extreme values to the bitdict
        fields.
        """

        config = {
            "field1": {"start": 0, "width": 32, "type": "uint"},
            "field2": {"start": 32, "width": 32, "type": "int"},
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        bd["field1"] = 2**32 - 1
        bd["field2"] = 2**31 - 1
        self.assertEqual(bd["field1"], 2**32 - 1)
        self.assertEqual(bd["field2"], 2**31 - 1)
        bd["field2"] = -(2**31)
        self.assertEqual(bd["field2"], -(2**31))

    def test_error_handling(self):
        """
        Test the error handling of the BitDict class.
        This method checks if the BitDict class raises the correct exceptions
        when attempting to assign invalid types or values to its fields.
        It specifically tests for:
        - TypeError when assigning a non-boolean value to a boolean field.
        - ValueError when assigning an out-of-range value to a uint field.
        - ValueError when assigning an out-of-range value to an int field.
        """

        bd = self.my_bitdict()
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)
        with self.assertRaises(TypeError):
            bd["Constant"] = "string"  # type: ignore
        with self.assertRaises(ValueError):
            sub_value["PropA"] = -1  # Out of range for uint
        with self.assertRaises(ValueError):
            sub_value["PropB"] = 3  # Invalid value for int

    def test_performance(self):
        """Test the performance of MyBitDict in terms of instance creation,
        property access, JSON conversion, and bytes conversion.
        This test uses the `timeit` module to measure the execution time of
        various operations performed on `MyBitDict` instances. The results
        are printed to the console, showing the time taken for each operation
        in seconds.
        """

        # Time instance creation
        creation_time = timeit.timeit(self.my_bitdict, number=1000)
        print(f"Instance creation time: {creation_time:.6f} seconds")

        # Time property access
        bd = self.my_bitdict()
        access_time = timeit.timeit(lambda: bd["Constant"], number=1000)
        print(f"Property access time: {access_time:.6f} seconds")

        # Time conversion to JSON
        json_time = timeit.timeit(bd.to_json, number=1000)
        print(f"JSON conversion time: {json_time:.6f} seconds")

        # Time conversion to bytes
        bytes_time = timeit.timeit(bd.to_bytes, number=1000)
        print(f"Bytes conversion time: {bytes_time:.6f} seconds")

    def test_len_with_various_configs(self) -> None:
        """Test __len__ with different configurations.

        This test case checks the __len__ method of the BitDict class
        when initialized with various configurations of fields,
        including different data types (uint, bool, int, bitdict) and widths.
        It asserts that the length of the BitDict instance, which represents
        the total number of bits it manages, is calculated correctly based
        on the provided configuration.
        """

        # Test with different combinations of property types and widths
        config1 = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        MyBitDict1 = bitdict_factory(config1)
        bd1 = MyBitDict1()
        self.assertEqual(len(bd1), 5)

        config2 = {
            "field1": {"start": 0, "width": 32, "type": "int"},
            "field2": {
                "start": 32,
                "width": 16,
                "type": "bitdict",
                "subtype": [
                    {"int": {"start": 0, "width": 16, "type": "uint"}},
                    {"uint": {"start": 16, "width": 16, "type": "uint"}},
                ],
                "selector": "field3",
            },
            "field3": {"start": 48, "width": 1, "type": "bool"},
        }
        MyBitDict2 = bitdict_factory(config2)
        bd2 = MyBitDict2()
        self.assertEqual(len(bd2), 49)

    def test_contains_with_selectors(self):
        """Test the __contains__ method with selectors.
        This test verifies that the __contains__ method of the BitDict class
        correctly identifies the presence of keys based on selector conditions.
        It checks scenarios where keys are initially absent due to selector
        conditions, then become present when the conditions are met, and
        vice versa.
        """

        bd = self.my_bitdict()
        self.assertTrue("Constant" in bd)
        self.assertTrue("PropA" in bd)
        self.assertFalse("PropC" in bd)  # Not selected
        bd["Mode"] = True
        self.assertTrue("PropC" in bd)  # Now selected
        self.assertFalse("PropA" in bd)  # No longer selected

    def test_iter_with_various_configs(self):
        """Test the iteration order of a BitDict with various configurations.
        This test defines two different BitDict configurations with varying
        field types (uint, int, bool, bitdict) and widths. It then checks
        if the iteration order of the BitDict matches the expected order
        based on the field definitions in the configuration.
        """

        # Test with different combinations of property types and widths
        config1 = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        MyBitDict1 = bitdict_factory(config1)
        bd1 = MyBitDict1()
        expected_order1 = ["field1", "field2"]
        actual_order1 = [name for name, _ in bd1]
        self.assertEqual(actual_order1, expected_order1)

        config2 = {
            "field1": {"start": 0, "width": 32, "type": "int"},
            "field2": {
                "start": 32,
                "width": 16,
                "type": "bitdict",
                "subtype": [
                    {"int": {"start": 0, "width": 16, "type": "uint"}},
                    {"uint": {"start": 16, "width": 16, "type": "uint"}},
                ],
                "selector": "field3",
            },
            "field3": {"start": 48, "width": 1, "type": "bool"},
        }
        MyBitDict2 = bitdict_factory(config2)
        bd2 = MyBitDict2()
        expected_order2 = ["field1", "field2", "field3"]
        actual_order2 = [name for name, _ in bd2]
        self.assertEqual(actual_order2, expected_order2)

    def test_to_json_with_nested_bitdicts(self):
        """
        Test the to_json method with nested BitDicts to ensure correct JSON serialization.
        This test creates a BitDict with a nested BitDict as a property. It then checks
        if the to_json method correctly serializes the BitDict, including the nested
        BitDict, into a JSON-compatible dictionary. The expected JSON structure includes
        the boolean values of the BitDict's properties and the values of the nested
        BitDict's properties.
        """

        bd = self.my_bitdict(0x8C)
        bd["Mode"] = True
        expected_json = {
            "Constant": True,
            "Mode": True,
            "Reserved": 0,
            "SubValue": {"PropC": 1, "PropD": True},
        }
        self.assertEqual(bd.to_json(), expected_json)

    def test_to_bytes_with_various_bit_widths(self):
        """Test the to_bytes method with various bit widths and configurations.
        This test covers cases where the BitDict is configured with different
        field widths and types (uint, bool, int) to ensure that the to_bytes
        method correctly serializes the data into bytes. It checks if the
        resulting bytes match the expected byte representation for the given
        BitDict configuration and value.
        """

        config1 = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        MyBitDict1 = bitdict_factory(config1)
        bd1 = MyBitDict1(0b11111)
        self.assertEqual(bd1.to_bytes(), bytes([0b11111]))

        config2 = {
            "field1": {"start": 0, "width": 32, "type": "int"},
        }
        MyBitDict2 = bitdict_factory(config2)
        bd2 = MyBitDict2(0xFFFFFFFF)
        self.assertEqual(bd2.to_bytes(), bytes([0xFF, 0xFF, 0xFF, 0xFF]))

    def test_factory_invalid_config_mappingproxy(self):
        """
        Test that the bitdict_factory raises a TypeError when passed a
        config where a property is a MappingProxyType.
        """

        config = {"field1": MappingProxyType({"start": 0, "width": 4, "type": "uint"})}
        with self.assertRaises(AssertionError):
            bitdict_factory(config)

    def test_factory_invalid_config_mappingproxy_property(self):
        """
        Test that the bitdict_factory raises a TypeError when passed a
        config where a property config is a MappingProxyType.
        """

        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
            }
        }
        config["field1"] = MappingProxyType(config["field1"])  # type: ignore
        with self.assertRaises(AssertionError):
            bitdict_factory(config)

    def test_factory_missing_default_value(self):
        """
        Test that the bitdict_factory function correctly assigns default values
        to fields when the 'default' key is missing in the configuration.

        It checks if the default value for uint fields is set to 0,
        for boolean fields is set to False, and for int fields is set to 0.
        """

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
            "field3": {"start": 5, "width": 4, "type": "int"},
        }
        MyBitDict = bitdict_factory(config)
        self.assertEqual(MyBitDict.get_config()["field1"]["default"], 0)
        self.assertEqual(MyBitDict.get_config()["field2"]["default"], False)
        self.assertEqual(MyBitDict.get_config()["field3"]["default"], 0)

    def test_factory_missing_default_value_nested(self):
        """Test that the bitdict_factory correctly assigns default values to nested fields
        when no default value is explicitly provided in the configuration. Specifically,
        this test checks that uint fields are assigned a default value of 0 and bool
        fields are assigned a default value of False within a nested bitdict structure.
        """

        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "bitdict",
                "subtype": [
                    {
                        "nested_field1": {"start": 0, "width": 2, "type": "uint"},
                        "nested_field2": {"start": 2, "width": 1, "type": "bool"},
                    }
                ],
                "selector": "field2",
            },
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        MyBitDict = bitdict_factory(config)
        self.assertEqual(
            MyBitDict.get_config()["field1"]["subtype"][0]["nested_field1"]["default"],
            0,
        )
        self.assertEqual(
            MyBitDict.get_config()["field1"]["subtype"][0]["nested_field2"]["default"],
            False,
        )

    def test_factory_valid_config_no_default(self):
        """
        Test that the bitdict_factory creates a class that initializes fields to zero/False
        when a valid configuration is provided and no default values are specified.
        """

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
            "field3": {"start": 5, "width": 4, "type": "int"},
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        self.assertEqual(bd["field1"], 0)
        self.assertEqual(bd["field2"], False)
        self.assertEqual(bd["field3"], 0)

    def test_factory_valid_config_invalid_default_uint_type(self):
        """
        Test that bitdict_factory raises a TypeError when a valid configuration
        is provided, but the default value for a uint field is of an invalid type
        (i.e., not an integer or convertible to an integer).
        """

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint", "default": "invalid"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
            "field3": {"start": 5, "width": 4, "type": "int"},
        }
        with self.assertRaises(TypeError):
            _ = bitdict_factory(config)

    def test_factory_valid_config_invalid_default_bool_type(self):
        """
        Test that bitdict_factory raises a TypeError when a valid configuration
        is provided, but the default value for a boolean field is of an invalid type
        (i.e., not a boolean).
        """

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool", "default": "invalid"},
            "field3": {"start": 5, "width": 4, "type": "int"},
        }
        with self.assertRaises(TypeError):
            _ = bitdict_factory(config)

    def test_factory_valid_config_invalid_default_int_type(self):
        """
        Test that bitdict_factory raises a TypeError when a valid configuration
        is provided, but the default value for an integer field is of an invalid type (string).
        """

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
            "field3": {"start": 5, "width": 4, "type": "int", "default": "invalid"},
        }
        with self.assertRaises(TypeError):
            _ = bitdict_factory(config)

    def test_factory_valid_config_invalid_type(self):
        """
        Test that bitdict_factory raises a TypeError when a valid configuration
        dictionary is provided, but one of the fields has an invalid default value
        that cannot be cast to the specified type.
        """

        config = {
            "field1": [0, 1],
            "field2": {"start": 4, "width": 1, "type": "bool"},
            "field3": {"start": 5, "width": 4, "type": "int", "default": "invalid"},
        }
        with self.assertRaises(TypeError):
            _ = bitdict_factory(config)

    def test_factory_valid_config_invalid_selector(self):
        """
        Test that a ValueError is raised when the selector field in a bitdict subtype
        configuration is invalid. This test uses a valid configuration for the
        top-level bitdict but provides an invalid selector name ('Invalid') for
        a nested bitdict, which should trigger the ValueError during bitdict factory
        creation.
        """

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
            "field3": {
                "start": 5,
                "width": 4,
                "type": "bitdict",
                "selector": "Invalid",
                "subtype": [{"field1": {"start": 0, "width": 4, "type": "uint"}}],
            },
        }
        with self.assertRaises(ValueError):
            _ = bitdict_factory(config)

    def test_factory_valid_config_no_subtypes(self):
        """
        Test that the bitdict_factory raises a ValueError when a valid configuration
        with a bitdict type field is provided, but the subtype list is empty.
        """

        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
            "field3": {
                "start": 5,
                "width": 4,
                "type": "bitdict",
                "selector": "field1",
                "subtype": [],
            },
        }
        with self.assertRaises(ValueError):
            _ = bitdict_factory(config)

    def test_getitem_invalid_key(self):
        """Test that __getitem__ raises a KeyError for an invalid key."""
        bd = self.my_bitdict()
        with self.assertRaises(KeyError):
            _ = bd["InvalidKey"]

    def test_getitem_unknown_property_type(self):
        """Test that __getitem__ raises an AssertionError for an unknown property type."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        bd._config["field1"]["type"] = "unknown"  # type: ignore[protected-access]
        with self.assertRaises(AssertionError):
            _ = bd["field1"]

    def test_clear(self):
        """Test the clear method of the BitDict class.

        This test verifies that the clear method correctly resets all bits in the BitDict to 0,
        effectively setting all properties to their default values (if defaults are defined) or
        to 0/False if no defaults are specified.
        """
        bd = self.my_bitdict(0xFF)  # Initialize with all bits set
        bd.clear()
        self.assertEqual(bd.to_int(), 0)  # All bits should be cleared

    def test_int_width_1(self):
        """Test that an 'int' type property with a width of 1 works correctly."""
        config = {
            "field1": {"start": 0, "width": 1, "type": "int"},
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        bd["field1"] = 0
        self.assertEqual(bd["field1"], 0)
        bd["field1"] = -1
        self.assertEqual(bd["field1"], -1)
        with self.assertRaises(ValueError):
            bd["field1"] = 1
        with self.assertRaises(ValueError):
            bd["field1"] = -2

    def test_uint_width_1(self):
        """Test that a uint field with width 1 can be set and retrieved correctly.

        This test defines a bitdict with a single uint field of width 1.
        It then checks that the field can be set to 0 and 1, and that
        attempting to set it to a value outside this range raises a ValueError.
        """

        config = {
            "field1": {"start": 0, "width": 1, "type": "uint"},
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        bd["field1"] = 0
        self.assertEqual(bd["field1"], 0)
        bd["field1"] = 1
        self.assertEqual(bd["field1"], 1)
        with self.assertRaises(ValueError):
            bd["field1"] = -1
        with self.assertRaises(ValueError):
            bd["field1"] = 2

    def test_two_bitdicts_same_selector(self):
        """Test that two bitdicts can use the same selector field without interfering
        with each other.

        This test defines a bitdict configuration with two sub-bitdicts, BitDict1 and BitDict2,
        both controlled by the same selector field, Selector.  It verifies that setting values
        in one sub-bitdict does not affect the other, based on the selector value.
        """

        config = {
            "Selector": {"start": 0, "width": 1, "type": "bool"},
            "BitDict1": {
                "start": 1,
                "width": 2,
                "type": "bitdict",
                "selector": "Selector",
                "subtype": [
                    {"fieldA": {"start": 0, "width": 2, "type": "uint"}},
                    {"fieldB": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
            "BitDict2": {
                "start": 3,
                "width": 2,
                "type": "bitdict",
                "selector": "Selector",
                "subtype": [
                    {"fieldC": {"start": 0, "width": 2, "type": "uint"}},
                    {"fieldD": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()

        # Set selector to False, check BitDict1.fieldA and BitDict2.fieldC
        bd["Selector"] = False
        bitdict1 = bd["BitDict1"]
        bitdict2 = bd["BitDict2"]
        assert isinstance(bitdict1, BitDictABC)
        assert isinstance(bitdict2, BitDictABC)
        bitdict1["fieldA"] = 1
        bitdict2["fieldC"] = 2
        self.assertEqual(bitdict1["fieldA"], 1)
        self.assertEqual(bitdict2["fieldC"], 2)

        # Set selector to True, check BitDict1.fieldB and BitDict2.fieldD
        bd["Selector"] = True
        bitdict1 = bd["BitDict1"]
        bitdict2 = bd["BitDict2"]
        assert isinstance(bitdict1, BitDictABC)
        assert isinstance(bitdict2, BitDictABC)
        bitdict1["fieldB"] = 3
        bitdict2["fieldD"] = 0
        self.assertEqual(bitdict1["fieldB"], 3)
        self.assertEqual(bitdict2["fieldD"], 0)

    def test_three_bitdicts_different_selectors(self):
        """Test case to verify the functionality of three BitDicts with different selectors.

        This test defines a configuration with three BitDicts (BitDict1, BitDict2, BitDict3)
        each controlled by different selectors (Selector1, Selector2). It checks if the
        values within these BitDicts can be set and retrieved correctly based on the
        state of their respective selectors. The test covers scenarios where selectors
        are both False and True, ensuring that the correct subtype fields are accessed
        and modified.
        """

        config = {
            "Selector1": {"start": 0, "width": 1, "type": "bool"},
            "Selector2": {"start": 1, "width": 1, "type": "bool"},
            "BitDict1": {
                "start": 2,
                "width": 2,
                "type": "bitdict",
                "selector": "Selector1",
                "subtype": [
                    {"fieldA": {"start": 0, "width": 2, "type": "uint"}},
                    {"fieldB": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
            "BitDict2": {
                "start": 4,
                "width": 2,
                "type": "bitdict",
                "selector": "Selector2",
                "subtype": [
                    {"fieldC": {"start": 0, "width": 2, "type": "uint"}},
                    {"fieldD": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
            "BitDict3": {
                "start": 6,
                "width": 2,
                "type": "bitdict",
                "selector": "Selector1",
                "subtype": [
                    {"fieldE": {"start": 0, "width": 2, "type": "uint"}},
                    {"fieldF": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()

        # Set selectors and check values
        bd["Selector1"] = False
        bd["Selector2"] = True
        bitdict1 = bd["BitDict1"]
        bitdict2 = bd["BitDict2"]
        bitdict3 = bd["BitDict3"]
        assert isinstance(bitdict1, BitDictABC)
        assert isinstance(bitdict2, BitDictABC)
        assert isinstance(bitdict3, BitDictABC)

        bitdict1["fieldA"] = 1
        bitdict2["fieldD"] = 2
        bitdict3["fieldE"] = 3
        self.assertEqual(bitdict1["fieldA"], 1)
        self.assertEqual(bitdict2["fieldD"], 2)
        self.assertEqual(bitdict3["fieldE"], 3)

        bd["Selector1"] = True
        bd["Selector2"] = False
        bitdict1 = bd["BitDict1"]
        bitdict2 = bd["BitDict2"]
        bitdict3 = bd["BitDict3"]
        assert isinstance(bitdict1, BitDictABC)
        assert isinstance(bitdict2, BitDictABC)
        assert isinstance(bitdict3, BitDictABC)
        bitdict1["fieldB"] = 3
        bitdict2["fieldC"] = 1
        bitdict3["fieldF"] = 0
        self.assertEqual(bitdict1["fieldB"], 3)
        self.assertEqual(bitdict2["fieldC"], 1)
        self.assertEqual(bitdict3["fieldF"], 0)

    def test_four_deep_nested_bitdicts(self):
        """
        Test case for four-level deep nested bitdicts.

        This test defines a complex configuration with nested bitdicts up to four levels deep.
        It then creates a bitdict instance using the `bitdict_factory` and verifies that
        values can be set and retrieved correctly at different levels of nesting.

        The test covers the following:
        - Defining a configuration with nested bitdicts and selectors.
        - Creating a bitdict instance from the configuration.
        - Setting values of selectors at different levels to navigate the nested structure.
        - Setting values of fields within the deepest nested bitdicts.
        - Asserting that the values are correctly set and retrieved.
        """

        config = {
            "Selector1": {"start": 0, "width": 1, "type": "bool"},
            "BitDict1": {
                "start": 1,
                "width": 3,
                "type": "bitdict",
                "selector": "Selector1",
                "subtype": [
                    {
                        "Selector2": {"start": 0, "width": 1, "type": "bool"},
                        "BitDict2": {
                            "start": 1,
                            "width": 2,
                            "type": "bitdict",
                            "selector": "Selector2",
                            "subtype": [
                                {
                                    "Selector3": {
                                        "start": 0,
                                        "width": 1,
                                        "type": "bool",
                                    },
                                    "BitDict3": {
                                        "start": 1,
                                        "width": 1,
                                        "type": "bitdict",
                                        "selector": "Selector3",
                                        "subtype": [
                                            {
                                                "fieldA": {
                                                    "start": 0,
                                                    "width": 1,
                                                    "type": "uint",
                                                }
                                            },
                                            {
                                                "fieldB": {
                                                    "start": 0,
                                                    "width": 1,
                                                    "type": "uint",
                                                }
                                            },
                                        ],
                                    },
                                },
                                {
                                    "Selector3": {
                                        "start": 0,
                                        "width": 1,
                                        "type": "bool",
                                    },
                                    "BitDict3": {
                                        "start": 1,
                                        "width": 1,
                                        "type": "bitdict",
                                        "selector": "Selector3",
                                        "subtype": [
                                            {
                                                "fieldC": {
                                                    "start": 0,
                                                    "width": 1,
                                                    "type": "uint",
                                                }
                                            },
                                            {
                                                "fieldD": {
                                                    "start": 0,
                                                    "width": 1,
                                                    "type": "uint",
                                                }
                                            },
                                        ],
                                    },
                                },
                            ],
                        },
                    },
                    {
                        "Selector2": {"start": 0, "width": 1, "type": "bool"},
                        "BitDict2": {
                            "start": 1,
                            "width": 2,
                            "type": "bitdict",
                            "selector": "Selector2",
                            "subtype": [
                                {
                                    "Selector3": {
                                        "start": 0,
                                        "width": 1,
                                        "type": "bool",
                                    },
                                    "BitDict3": {
                                        "start": 1,
                                        "width": 1,
                                        "type": "bitdict",
                                        "selector": "Selector3",
                                        "subtype": [
                                            {
                                                "fieldE": {
                                                    "start": 0,
                                                    "width": 1,
                                                    "type": "uint",
                                                }
                                            },
                                            {
                                                "fieldF": {
                                                    "start": 0,
                                                    "width": 1,
                                                    "type": "uint",
                                                }
                                            },
                                        ],
                                    },
                                },
                                {
                                    "Selector3": {
                                        "start": 0,
                                        "width": 1,
                                        "type": "bool",
                                    },
                                    "BitDict3": {
                                        "start": 1,
                                        "width": 1,
                                        "type": "bitdict",
                                        "selector": "Selector3",
                                        "subtype": [
                                            {
                                                "fieldG": {
                                                    "start": 0,
                                                    "width": 1,
                                                    "type": "uint",
                                                }
                                            },
                                            {
                                                "fieldH": {
                                                    "start": 0,
                                                    "width": 1,
                                                    "type": "uint",
                                                }
                                            },
                                        ],
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()

        # Set selectors and check values
        bd["Selector1"] = False
        bitdict1 = bd["BitDict1"]
        assert isinstance(bitdict1, BitDictABC)

        bitdict1["Selector2"] = True
        bitdict2 = bitdict1["BitDict2"]
        assert isinstance(bitdict2, BitDictABC)

        bitdict2["Selector3"] = False
        bitdict3 = bitdict2["BitDict3"]
        assert isinstance(bitdict3, BitDictABC)

        bitdict3["fieldC"] = 1
        self.assertEqual(bitdict3["fieldC"], 1)

        bd["Selector1"] = True
        bitdict1 = bd["BitDict1"]
        assert isinstance(bitdict1, BitDictABC)
        bitdict1["Selector2"] = False
        bitdict2 = bitdict1["BitDict2"]
        assert isinstance(bitdict2, BitDictABC)
        bitdict2["Selector3"] = True
        bitdict3 = bitdict2["BitDict3"]
        assert isinstance(bitdict3, BitDictABC)
        bitdict3["fieldF"] = 1
        self.assertEqual(bitdict3["fieldF"], 1)

    def test_setitem_reserved_field(self):
        """Test that setting a reserved field raises an AssertionError."""

        bd = self.my_bitdict()
        bd._config["Reserved"]["type"] = "unknown"  # type: ignore[protected-access]
        with self.assertRaises(AssertionError):
            bd["Reserved"] = 1

    def test_setitem_int_overflow(self):
        """Test that setting an item with an integer that overflows the
        bitdict raises a ValueError."""

        bd = self.my_bitdict()
        with self.assertRaises(ValueError):
            bd.set(1 << len(bd))

    def test_setitem_int_underflow(self):
        """Test that setting a negative integer raises a ValueError."""

        bd = self.my_bitdict()
        with self.assertRaises(ValueError):
            bd.set(-1)

    def test_factory_valid_key_bitdict_type(self):
        """Test that bitdict_factory does not allow 'valid' key for 'bitdict' type."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "bitdict",
                "subtype": [{"nested": {"start": 0, "width": 2, "type": "uint"}}],
                "selector": "field2",
                "valid": {"value": {0}},
            },
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_valid_key_not_dict(self):
        """Test that bitdict_factory raises a ValueError when 'valid' key is not a dictionary."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint", "valid": "not a dict"},
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_valid_key_empty_dict(self):
        """Test that bitdict_factory raises a ValueError when 'valid' key is an empty dictionary."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint", "valid": {}},
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_valid_key_missing_range_value(self):
        """Test that bitdict_factory raises a ValueError when neither
        range nor value are present."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"unknown": []},
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_valid_key_range_not_list(self):
        """Test that bitdict_factory raises a ValueError when 'range' in 'valid' is not a list."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"range": "not a list"},
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_valid_key_range_not_tuple(self):
        """Test that bitdict_factory raises a ValueError
        when an element in 'range' is not a tuple."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"range": [1, 2, 3]},
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_valid_config_with_valid_range(self):
        """Test that bitdict_factory correctly handles configurations with the 'range' key."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"range": [(0, 4)]},
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        bd["field1"] = 0
        self.assertTrue(bd.valid())
        bd["field1"] = 3
        self.assertTrue(bd.valid())
        bd["field1"] = 4
        self.assertFalse(bd.valid())

        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"range": [(0, 2), (3, 4)]},
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        bd["field1"] = 0
        self.assertTrue(bd.valid())
        bd["field1"] = 1
        self.assertTrue(bd.valid())
        bd["field1"] = 3
        self.assertTrue(bd.valid())
        bd["field1"] = 2
        self.assertFalse(bd.valid())
        bd["field1"] = 4
        self.assertFalse(bd.valid())

    def test_factory_invalid_valid_key_value_type(self):
        """Test that bitdict_factory raises a ValueError when a
        value in the 'value' set is not an int or bool."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"value": {0, "string"}},
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_valid_key_range_out_of_bounds_uint(self):
        """Test that bitdict_factory raises a ValueError when a range in
        'valid' contains a value out of bounds for a uint."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"range": [(0, 17)]},
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_valid_key_range_out_of_bounds_int(self):
        """Test that bitdict_factory raises a ValueError when a range in
        'valid' contains a value out of bounds for an int."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "int",
                "valid": {"range": [(-8, 9)]},
            },
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_valid_nested_bitdict(self):
        """Test the valid method with a nested BitDict."""
        config = {
            "field1": {
                "start": 0,
                "width": 1,
                "type": "bool",
            },
            "field2": {
                "start": 1,
                "width": 4,
                "type": "bitdict",
                "selector": "field1",
                "subtype": [
                    {
                        "nested_field1": {
                            "start": 0,
                            "width": 2,
                            "type": "uint",
                            "valid": {"value": {0, 1}},
                        }
                    },
                    {
                        "nested_field2": {
                            "start": 0,
                            "width": 2,
                            "type": "uint",
                            "valid": {"value": {2, 3}},
                        }
                    },
                ],
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()

        # Valid case
        bd["field1"] = False
        field2 = bd["field2"]
        assert isinstance(field2, BitDictABC)
        field2["nested_field1"] = 0
        self.assertTrue(bd.valid())

        # Invalid case
        bd["field1"] = False
        field2["nested_field1"] = 2
        self.assertFalse(bd.valid())

        # Valid case
        bd["field1"] = True
        field2 = bd["field2"]
        assert isinstance(field2, BitDictABC)
        field2["nested_field2"] = 2
        self.assertTrue(bd.valid())

        # Invalid case
        bd["field1"] = True
        field2["nested_field2"] = 1
        self.assertFalse(bd.valid())

    def test_factory_valid_config_invalid_selector_value(self):
        """Test that bitdict_factory raises a ValueError when the selector
        for a nested bitdict has an invalid value."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "bitdict",
                "selector": "field2",
                "subtype": [
                    {"nested_field1": {"start": 0, "width": 2, "type": "uint"}},
                    {"nested_field2": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
            "field2": {"start": 4, "width": 2, "type": "uint"},
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        with self.assertRaises(IndexError):
            bd["field2"] = 3

    def test_factory_valid_config_invalid_subconfig(self):
        """Test that bitdict_factory raises a ValueError when the selector
        for a nested bitdict has an invalid value."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "bitdict",
                "selector": "field2",
                "subtype": [
                    {"nested_field1": {"start": 0, "width": 2, "type": "uint"}},
                    None,
                    {"nested_field2": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
            "field2": {"start": 4, "width": 2, "type": "uint"},
        }
        with self.assertRaises(ValueError):
            _ = bitdict_factory(config)

    def test_valid_bitdict_selector_value(self):
        """Test the valid method when the selector value is invalid."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "bitdict",
                "selector": "field2",
                "subtype": [
                    {"nested_field1": {"start": 0, "width": 2, "type": "uint"}},
                    {"nested_field2": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
            "field2": {
                "start": 4,
                "width": 2,
                "type": "uint",
                "valid": {"value": {0, 1}},
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        bd._set_value(0x30)  # type: ignore[protected-access]
        self.assertFalse(bd.valid())

    def test_inspect_nested_bitdict(self):
        """Test the inspect method with a nested BitDict."""
        config = {
            "field1": {
                "start": 0,
                "width": 1,
                "type": "bool",
            },
            "field2": {
                "start": 1,
                "width": 4,
                "type": "bitdict",
                "selector": "field1",
                "subtype": [
                    {
                        "nested_field1": {
                            "start": 0,
                            "width": 2,
                            "type": "uint",
                            "valid": {"value": {0, 1}},
                        }
                    },
                    {
                        "nested_field2": {
                            "start": 0,
                            "width": 2,
                            "type": "uint",
                            "valid": {"value": {2, 3}},
                        }
                    },
                ],
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()

        # Valid case
        bd["field1"] = False
        field2 = bd["field2"]
        assert isinstance(field2, BitDictABC)
        field2["nested_field1"] = 0
        self.assertEqual(bd.inspect(), {})

        # Invalid case
        bd["field1"] = False
        field2["nested_field1"] = 2
        self.assertEqual(bd.inspect(), {"field2": {"nested_field1": 2}})

        # Valid case
        bd["field1"] = True
        field2 = bd["field2"]
        assert isinstance(field2, BitDictABC)
        field2["nested_field2"] = 2
        self.assertEqual(bd.inspect(), {})

        # Invalid case
        bd["field1"] = True
        field2["nested_field2"] = 1
        self.assertEqual(bd.inspect(), {"field2": {"nested_field2": 1}})

    def test_inspect_bitdict_selector_value(self):
        """Test the inspect method when the selector value is invalid."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "bitdict",
                "selector": "field2",
                "subtype": [
                    {"nested_field1": {"start": 0, "width": 2, "type": "uint"}},
                    {"nested_field2": {"start": 0, "width": 2, "type": "uint"}},
                ],
            },
            "field2": {
                "start": 4,
                "width": 2,
                "type": "uint",
                "valid": {"value": {0, 1}},
            },
        }
        MyBitDict = bitdict_factory(config)
        bd = MyBitDict()
        bd._set_value(0x30)  # type: ignore[protected-access]
        self.assertEqual(bd.inspect(), {"field2": 3})

    def test__bitdict_config_with_default(self):
        """Test the inspect method when the selector value is invalid."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "bitdict",
                "selector": "field2",
                "subtype": [
                    {"nested_field1": {"start": 0, "width": 2, "type": "uint"}},
                    {"nested_field2": {"start": 0, "width": 2, "type": "uint"}},
                ],
                "default": 0,
            },
            "field2": {
                "start": 4,
                "width": 2,
                "type": "uint",
                "valid": {"value": {0, 1}},
            },
        }
        with self.assertRaises(ValueError):
            _ = bitdict_factory(config)

    def test_factory_invalid_description_type(self):
        """Test that bitdict_factory raises a ValueError when the description is not a string."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint", "description": 123},
        }
        with self.assertRaises(ValueError):
            bitdict_factory(config)

    def test_factory_invalid_name(self):
        """Test that bitdict_factory raises a ValueError when the name is not a string."""
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "description": "This is a valid description.",
            }
        }
        with self.assertRaises(ValueError):
            _ = bitdict_factory(config, "Invalid Name")

    def test_verify_with_custom_function(self):
        """Test the verify method with a custom verification function.

        This test assigns a custom verification function to the BitDict instance
        and checks if the verify method correctly calls this function and returns
        the expected result.
        """

        def custom_verification_function(bd: BitDictABC) -> bool:
            return bool(bd["Constant"] and bd["Mode"])

        bd = self.my_bitdict()
        bd.assign_verification_function(custom_verification_function)

        # Test with default values (should be False)
        self.assertFalse(bd.verify())

        # Set values to pass the verification function
        bd["Constant"] = True
        bd["Mode"] = True
        self.assertTrue(bd.verify())

        # Set values to fail the verification function
        bd["Mode"] = False
        self.assertFalse(bd.verify())

    def test_set_with_integer(self):
        """Test the set method with an integer value."""
        bd = self.my_bitdict()
        bd.set(0x8C)
        self.assertEqual(bd.to_int(), 0x8C)

        with self.assertRaises(ValueError):
            bd.set(1 << 8)  # Value exceeds the maximum for 8 bits

        with self.assertRaises(ValueError):
            bd.set(-1)  # Negative value not allowed

    def test_set_with_dict_ignore_unknown_true(self):
        """Test the set method with a dictionary when ignore_unknown is True."""
        bd = self.my_bitdict()
        bd.set({"Constant": True, "Mode": False, "SubValue": {"PropA": 2, "PropB": -1}})
        self.assertEqual(bd["Constant"], True)
        self.assertEqual(bd["Mode"], False)
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)
        self.assertEqual(sub_value["PropA"], 2)
        self.assertEqual(sub_value["PropB"], -1)

        # Test with unknown keys (should be ignored)
        bd.set({"UnknownKey": 123}, ignore_unknown=True)
        self.assertNotIn("UnknownKey", bd)

    def test_set_with_dict_ignore_unknown_false_raise(self):
        """Test the set method with a dictionary when ignore_unknown is False."""
        bd = self.my_bitdict()
        bd.set({"Constant": True, "Mode": False, "SubValue": {"PropA": 2, "PropB": -1}})
        self.assertEqual(bd["Constant"], True)
        self.assertEqual(bd["Mode"], False)
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)
        self.assertEqual(sub_value["PropA"], 2)
        self.assertEqual(sub_value["PropB"], -1)

        # Test with unknown keys (should raise KeyError)
        with self.assertRaises(KeyError):
            bd.set({"UnknownKey": 123}, ignore_unknown=False)

    def test_set_with_dict_ignore_unknown_false(self):
        """Test the set method with a dictionary when ignore_unknown is False."""
        bd = self.my_bitdict()
        bd.set({"Constant": True, "Mode": False, "SubValue": {"PropA": 2, "PropB": -1}})
        self.assertEqual(bd["Constant"], True)
        self.assertEqual(bd["Mode"], False)
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)
        self.assertEqual(sub_value["PropA"], 2)
        self.assertEqual(sub_value["PropB"], -1)

        # Test with unknown keys (should raise KeyError)
        bd.set({"Constant": False}, ignore_unknown=False)

    def test_set_with_defaults(self):
        """Test the set method to ensure defaults are applied correctly."""
        bd = self.my_bitdict()
        bd.set({"Constant": True})
        self.assertEqual(bd["Constant"], True)
        self.assertEqual(bd["Mode"], False)  # Default value
        sub_value = bd["SubValue"]
        assert isinstance(sub_value, BitDictABC)
        self.assertEqual(sub_value["PropA"], 0)  # Default value
        self.assertEqual(sub_value["PropB"], -1)  # Default value
