"""
Test cases for the validation module.

This module tests the individual validator classes to ensure they work
correctly in isolation, providing the improved testability benefit of
the extracted validation architecture.
"""

import unittest
from types import MappingProxyType

from bitdict.validation import (
    PropertyNameValidator,
    ConfigStructureValidator,
    StartWidthValidator,
    TypeValidator,
    DescriptionValidator,
    DefaultValueValidator,
    ValidKeyValidator,
    BitDictPropertiesValidator,
    ConfigurationValidator,
    OverlapValidator,
)


class TestPropertyNameValidator(unittest.TestCase):
    """Test cases for PropertyNameValidator."""

    def setUp(self):
        self.validator = PropertyNameValidator()

    def test_valid_property_name(self):
        """Test that valid property names pass validation."""
        self.validator.validate("valid_name", {})
        self.validator.validate("field1", {})
        self.validator.validate("_private", {})

    def test_invalid_property_name_not_string(self):
        """Test that non-string property names raise ValueError."""
        with self.assertRaises(ValueError):
            self.validator.validate(123, {})

    def test_invalid_property_name_not_identifier(self):
        """Test that invalid identifiers raise ValueError."""
        with self.assertRaises(ValueError):
            self.validator.validate("123invalid", {})
        with self.assertRaises(ValueError):
            self.validator.validate("invalid-name", {})
        with self.assertRaises(ValueError):
            self.validator.validate("", {})


class TestConfigStructureValidator(unittest.TestCase):
    """Test cases for ConfigStructureValidator."""

    def setUp(self):
        self.validator = ConfigStructureValidator()

    def test_valid_config_structure(self):
        """Test that valid config structures pass validation."""
        config = {"start": 0, "width": 1, "type": "bool"}
        self.validator.validate("test", config)

    def test_invalid_config_not_dict(self):
        """Test that non-dict configs raise TypeError."""
        with self.assertRaises(TypeError):
            self.validator.validate("test", "invalid")
        with self.assertRaises(TypeError):
            self.validator.validate("test", 123)

    def test_invalid_config_mappingproxy(self):
        """Test that MappingProxyType configs raise AssertionError."""
        config = MappingProxyType({"start": 0, "width": 1, "type": "bool"})
        with self.assertRaises(AssertionError):
            self.validator.validate("test", config)

    def test_missing_required_keys(self):
        """Test that missing required keys raise ValueError."""
        with self.assertRaises(ValueError):
            self.validator.validate("test", {"start": 0, "width": 1})  # Missing type
        with self.assertRaises(ValueError):
            self.validator.validate("test", {"width": 1, "type": "bool"})  # Missing start
        with self.assertRaises(ValueError):
            self.validator.validate("test", {"start": 0, "type": "bool"})  # Missing width


class TestStartWidthValidator(unittest.TestCase):
    """Test cases for StartWidthValidator."""

    def setUp(self):
        self.validator = StartWidthValidator()

    def test_valid_start_width(self):
        """Test that valid start and width values pass validation."""
        config = {"start": 0, "width": 1}
        self.validator.validate("test", config)
        config = {"start": 10, "width": 5}
        self.validator.validate("test", config)

    def test_invalid_start_negative(self):
        """Test that negative start values raise ValueError."""
        config = {"start": -1, "width": 1}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_invalid_start_not_int(self):
        """Test that non-integer start values raise ValueError."""
        config = {"start": "0", "width": 1}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_invalid_width_zero(self):
        """Test that zero width raises ValueError."""
        config = {"start": 0, "width": 0}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_invalid_width_negative(self):
        """Test that negative width raises ValueError."""
        config = {"start": 0, "width": -1}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_invalid_width_not_int(self):
        """Test that non-integer width values raise ValueError."""
        config = {"start": 0, "width": "1"}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)


class TestTypeValidator(unittest.TestCase):
    """Test cases for TypeValidator."""

    def setUp(self):
        self.validator = TypeValidator()

    def test_valid_types(self):
        """Test that valid types pass validation."""
        for type_val in ["bool", "uint", "int", "bitdict"]:
            config = {"type": type_val, "width": 1 if type_val == "bool" else 4}
            self.validator.validate("test", config)

    def test_invalid_type(self):
        """Test that invalid types raise ValueError."""
        config = {"type": "invalid", "width": 1}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_bool_invalid_width(self):
        """Test that bool type with width != 1 raises ValueError."""
        config = {"type": "bool", "width": 2}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)


class TestDescriptionValidator(unittest.TestCase):
    """Test cases for DescriptionValidator."""

    def setUp(self):
        self.validator = DescriptionValidator()

    def test_valid_description(self):
        """Test that valid descriptions pass validation."""
        config = {"description": "Valid description"}
        self.validator.validate("test", config)

    def test_missing_description(self):
        """Test that missing description passes validation."""
        config = {}
        self.validator.validate("test", config)

    def test_invalid_description_type(self):
        """Test that non-string descriptions raise ValueError."""
        config = {"description": 123}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)


class TestDefaultValueValidator(unittest.TestCase):
    """Test cases for DefaultValueValidator."""

    def setUp(self):
        self.validator = DefaultValueValidator()

    def test_bool_default_handling(self):
        """Test bool type default value handling."""
        # Test missing default gets set to False
        config = {"type": "bool", "width": 1}
        self.validator.validate("test", config)
        self.assertEqual(config["default"], False)

        # Test valid default
        config = {"type": "bool", "width": 1, "default": True}
        self.validator.validate("test", config)

    def test_uint_default_handling(self):
        """Test uint type default value handling."""
        # Test missing default gets set to 0
        config = {"type": "uint", "width": 4}
        self.validator.validate("test", config)
        self.assertEqual(config["default"], 0)

        # Test valid default
        config = {"type": "uint", "width": 4, "default": 5}
        self.validator.validate("test", config)

    def test_int_default_handling(self):
        """Test int type default value handling."""
        # Test missing default gets set to 0
        config = {"type": "int", "width": 4}
        self.validator.validate("test", config)
        self.assertEqual(config["default"], 0)

        # Test valid default
        config = {"type": "int", "width": 4, "default": -5}
        self.validator.validate("test", config)

    def test_bitdict_no_default(self):
        """Test that bitdict types cannot have defaults."""
        config = {"type": "bitdict", "width": 4, "default": 0}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_invalid_bool_default_type(self):
        """Test that invalid bool default types raise TypeError."""
        config = {"type": "bool", "width": 1, "default": "invalid"}
        with self.assertRaises(TypeError):
            self.validator.validate("test", config)

    def test_invalid_uint_default_range(self):
        """Test that out-of-range uint defaults raise ValueError."""
        config = {"type": "uint", "width": 4, "default": 16}  # Max is 15 for width 4
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_invalid_int_default_range(self):
        """Test that out-of-range int defaults raise ValueError."""
        config = {"type": "int", "width": 4, "default": 8}  # Max is 7 for width 4
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)


class TestValidKeyValidator(unittest.TestCase):
    """Test cases for ValidKeyValidator."""

    def setUp(self):
        self.validator = ValidKeyValidator()

    def test_no_valid_key(self):
        """Test that properties without 'valid' key pass validation."""
        config = {"type": "uint", "width": 4}
        self.validator.validate("test", config)

    def test_bitdict_no_valid_allowed(self):
        """Test that bitdict types cannot have 'valid' key."""
        config = {"type": "bitdict", "width": 4, "valid": {"value": {1, 2}}}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_valid_value_set(self):
        """Test valid 'value' set in 'valid' key."""
        config = {
            "type": "uint",
            "width": 4,
            "valid": {"value": {1, 2, 3}}
        }
        self.validator.validate("test", config)

    def test_valid_range_list(self):
        """Test valid 'range' list in 'valid' key."""
        config = {
            "type": "uint",
            "width": 4,
            "valid": {"range": [(1, 4), (6, 9)]}
        }
        self.validator.validate("test", config)

    def test_invalid_valid_not_dict(self):
        """Test that 'valid' must be a dictionary."""
        config = {"type": "uint", "width": 4, "valid": [1, 2, 3]}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_empty_valid_dict(self):
        """Test that empty 'valid' dict raises ValueError."""
        config = {"type": "uint", "width": 4, "valid": {}}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_missing_value_and_range(self):
        """Test that 'valid' dict must contain 'value' or 'range'."""
        config = {"type": "uint", "width": 4, "valid": {"other": "value"}}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)


class TestBitDictPropertiesValidator(unittest.TestCase):
    """Test cases for BitDictPropertiesValidator."""

    def setUp(self):
        self.validator = BitDictPropertiesValidator()

    def test_non_bitdict_type(self):
        """Test that non-bitdict types pass validation."""
        config = {"type": "uint", "width": 4}
        self.validator.validate("test", config)

    def test_bitdict_with_subtype_and_selector(self):
        """Test that bitdict with required fields passes validation."""
        config = {
            "type": "bitdict",
            "width": 4,
            "subtype": [{"field": {"type": "uint", "width": 2, "start": 0}}],
            "selector": "mode"
        }
        self.validator.validate("test", config)

    def test_bitdict_missing_subtype(self):
        """Test that bitdict missing subtype raises ValueError."""
        config = {"type": "bitdict", "width": 4, "selector": "mode"}
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)

    def test_bitdict_missing_selector(self):
        """Test that bitdict missing selector raises ValueError."""
        config = {
            "type": "bitdict",
            "width": 4,
            "subtype": [{"field": {"type": "uint", "width": 2, "start": 0}}]
        }
        with self.assertRaises(ValueError):
            self.validator.validate("test", config)


class TestOverlapValidator(unittest.TestCase):
    """Test cases for OverlapValidator."""

    def test_no_overlap(self):
        """Test that non-overlapping configurations pass validation."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 2, "type": "uint"},
            "field3": {"start": 6, "width": 1, "type": "bool"}
        }
        OverlapValidator.check_overlapping(config)

    def test_overlap_detected(self):
        """Test that overlapping configurations raise ValueError."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 3, "width": 2, "type": "uint"}  # Overlaps with field1
        }
        with self.assertRaises(ValueError):
            OverlapValidator.check_overlapping(config)

    def test_adjacent_fields_no_overlap(self):
        """Test that adjacent fields don't trigger overlap detection."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 4, "type": "uint"}  # Adjacent, not overlapping
        }
        OverlapValidator.check_overlapping(config)


class TestConfigurationValidator(unittest.TestCase):
    """Test cases for ConfigurationValidator."""

    def setUp(self):
        self.validator = ConfigurationValidator()

    def test_simple_valid_config(self):
        """Test that a simple valid configuration passes validation."""
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"}
        }
        subtypes = {}
        self.validator.validate_property_config(config, subtypes)

    def test_invalid_property_name(self):
        """Test that invalid property names are caught."""
        config = {
            "123invalid": {"start": 0, "width": 4, "type": "uint"}
        }
        subtypes = {}
        with self.assertRaises(ValueError):
            self.validator.validate_property_config(config, subtypes)

    def test_missing_required_keys(self):
        """Test that missing required keys are caught."""
        config = {
            "field1": {"start": 0, "width": 4}  # Missing type
        }
        subtypes = {}
        with self.assertRaises(ValueError):
            self.validator.validate_property_config(config, subtypes)


if __name__ == "__main__":
    unittest.main()