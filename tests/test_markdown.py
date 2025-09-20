"""
Unit tests for the markdown module.
"""

import unittest
from bitdict import generate_markdown_tables, bitdict_factory


class TestMarkdown(unittest.TestCase):
    """
    Unit tests for the config_to_markdown function.
    """

    def test_config_to_markdown_simple(self):
        """
        Test config_to_markdown with a simple configuration.
        """
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        markdown_tables = generate_markdown_tables(bitdict_factory(config))
        self.assertEqual(len(markdown_tables), 1)
        self.assertTrue(
            "| Name | Type | Bitfield | Default | Description |" in markdown_tables[0]
        )
        self.assertTrue("| field1 | uint | 3:0 | 0 |  |" in markdown_tables[0])
        self.assertTrue("| field2 | bool | 4 | False |  |" in markdown_tables[0])

    def test_config_to_markdown_with_defaults(self):
        """
        Test config_to_markdown with default values.
        """
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint", "default": 5},
            "field2": {"start": 4, "width": 1, "type": "bool", "default": True},
        }
        markdown_tables = generate_markdown_tables(bitdict_factory(config))
        self.assertEqual(len(markdown_tables), 1)
        self.assertTrue("| field1 | uint | 3:0 | 5 |  |" in markdown_tables[0])
        self.assertTrue("| field2 | bool | 4 | True |  |" in markdown_tables[0])

    def test_config_to_markdown_with_valid(self):
        """
        Test config_to_markdown with valid values.
        """
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"value": {1, 2, 3}},
            },
            "field2": {
                "start": 4,
                "width": 1,
                "type": "bool",
                "valid": {"value": {True}},
            },
        }
        markdown_tables = generate_markdown_tables(bitdict_factory(config))
        self.assertEqual(len(markdown_tables), 1)
        self.assertTrue(
            "| field1 | uint | 3:0 | 0 | Valid values: {1, 2, 3}.  |"
            in markdown_tables[0]
        )
        self.assertTrue(
            "| field2 | bool | 4 | False | Valid values: {True}.  |"
            in markdown_tables[0]
        )

    def test_config_to_markdown_with_bitdict(self):
        """
        Test config_to_markdown with a bitdict.
        """
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {
                "start": 4,
                "width": 4,
                "type": "bitdict",
                "subtype": [{"nested": {"start": 0, "width": 2, "type": "uint"}}],
                "selector": "field1",
            },
        }
        markdown_tables = generate_markdown_tables(bitdict_factory(config))
        self.assertEqual(len(markdown_tables), 2)
        self.assertTrue(
            "| field2 | bitdict | 7:4 | N/A | See 'field2' definition table(s). |"
            in markdown_tables[0]
        )

    def test_config_to_markdown_without_types(self):
        """
        Test config_to_markdown without types.
        """
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        markdown_tables = generate_markdown_tables(
            bitdict_factory(config), include_types=False
        )
        self.assertEqual(len(markdown_tables), 1)
        self.assertTrue(
            "| Name | Bitfield | Default | Description |" in markdown_tables[0]
        )
        self.assertTrue("| field1 | 3:0 | 0 |  |" in markdown_tables[0])
        self.assertTrue("| field2 | 4 | False |  |" in markdown_tables[0])

    def test_config_to_markdown_undefined_bits(self):
        """
        Test config_to_markdown with undefined bits.
        """
        config = {
            "field1": {"start": 2, "width": 4, "type": "uint"},
            "field2": {"start": 7, "width": 1, "type": "bool"},
        }
        markdown_tables = generate_markdown_tables(bitdict_factory(config))
        self.assertEqual(len(markdown_tables), 1)
        self.assertTrue("| Undefined | N/A | 0-1 | N/A | N/A |" in markdown_tables[0])
        self.assertTrue("| field1 | uint | 5:2 | 0 |  |" in markdown_tables[0])
        self.assertTrue("| field2 | bool | 7 | False |  |" in markdown_tables[0])

    def test_config_to_markdown_undefined_bits_no_types(self):
        """
        Test config_to_markdown with undefined bits.
        """
        config = {
            "field1": {"start": 2, "width": 4, "type": "uint"},
            "field2": {"start": 7, "width": 1, "type": "bool"},
        }
        markdown_tables = generate_markdown_tables(
            bitdict_factory(config), include_types=False
        )
        self.assertEqual(len(markdown_tables), 1)
        self.assertTrue("| Undefined | 0-1 | N/A | N/A |" in markdown_tables[0])
        self.assertTrue("| field1 | 5:2 | 0 |  |" in markdown_tables[0])
        self.assertTrue("| field2 | 7 | False |  |" in markdown_tables[0])

    def test_config_to_markdown_valid_range(self):
        """
        Test config_to_markdown with valid range.
        """
        config = {
            "field1": {
                "start": 0,
                "width": 4,
                "type": "uint",
                "valid": {"range": [(0, 5), (7, 8)]},
            },
        }
        markdown_tables = generate_markdown_tables(bitdict_factory(config))
        self.assertEqual(len(markdown_tables), 1)
        self.assertTrue(
            "| field1 | uint | 3:0 | 0 | Valid ranges: [(0, 5), (7, 8)].  |"
            in markdown_tables[0]
        )

    def test_config_to_markdown_complex(self):
        """Test config_to_markdown with a complex configuration including nested bitdicts,
        selectors, valid ranges, and default values.
        """
        config = {
            "Selector1": {"start": 0, "width": 1, "type": "bool", "default": False},
            "BitDict1": {
                "start": 1,
                "width": 3,
                "type": "bitdict",
                "selector": "Selector1",
                "subtype": [
                    {
                        "Selector2": {
                            "start": 0,
                            "width": 1,
                            "type": "bool",
                            "default": True,
                        },
                        "BitDict2": {
                            "start": 1,
                            "width": 2,
                            "type": "bitdict",
                            "selector": "Selector2",
                            "subtype": [
                                {
                                    "fieldA": {
                                        "start": 0,
                                        "width": 1,
                                        "type": "uint",
                                        "valid": {"range": [(0, 1)]},
                                        "default": 0,
                                    }
                                },
                                {
                                    "fieldB": {
                                        "start": 0,
                                        "width": 1,
                                        "type": "uint",
                                        "valid": {"value": {1}},
                                        "default": 1,
                                    }
                                },
                            ],
                        },
                    },
                    {
                        "Selector2": {
                            "start": 0,
                            "width": 1,
                            "type": "bool",
                            "default": False,
                        },
                        "BitDict2": {
                            "start": 1,
                            "width": 2,
                            "type": "bitdict",
                            "selector": "Selector2",
                            "subtype": [
                                {
                                    "fieldC": {
                                        "start": 0,
                                        "width": 1,
                                        "type": "uint",
                                        "valid": {"range": [(0, 1)]},
                                        "default": 0,
                                    }
                                },
                                {
                                    "fieldD": {
                                        "start": 0,
                                        "width": 1,
                                        "type": "uint",
                                        "valid": {"value": {1}},
                                        "default": 1,
                                    }
                                },
                            ],
                        },
                    },
                ],
            },
        }
        markdown_tables = generate_markdown_tables(bitdict_factory(config))
        self.assertEqual(len(markdown_tables), 7)
        self.assertTrue("| Selector1 | bool | 0 | False |  |" in markdown_tables[0])
        self.assertTrue(
            "| BitDict1 | bitdict | 3:1 | N/A | See 'BitDict1' definition table(s). |"
            in markdown_tables[0]
        )

    def test_config_to_markdown_with_groups(self):
        """
        Test config_to_markdown with groups.
        """
        config = {
            "enabled": {"start": 0, "width": 1, "type": "bool", "description": "Enable flag"},
            "mode": {"start": 1, "width": 2, "type": "uint", "description": "Mode setting"},
            "value": {"start": 3, "width": 5, "type": "int", "description": "Value field"},
            "groups": [
                {
                    "name": "Control",
                    "description": "Fields that control basic operations",
                    "fields": ["enabled", "mode"],
                    "contiguous": True
                },
                {
                    "name": "Data",
                    "description": "Data storage field", 
                    "fields": ["value"]
                }
            ]
        }
        
        markdown_tables = generate_markdown_tables(bitdict_factory(config, "TestBitDict"))
        self.assertEqual(len(markdown_tables), 1)
        
        markdown = markdown_tables[0]
        
        # Check that group section is included
        self.assertIn("### Field Groups", markdown)
        self.assertIn("**Control** (contiguous): Fields that control basic operations", markdown)
        self.assertIn("- Fields: `enabled`, `mode`", markdown)
        self.assertIn("**Data**: Data storage field", markdown)
        self.assertIn("- Fields: `value`", markdown)
        
        # Check that regular table is still there
        self.assertIn("| Name | Type | Bitfield | Default | Description |", markdown)
        self.assertIn("| enabled | bool | 0 | False | Enable flag |", markdown)
        self.assertIn("| mode | uint | 2:1 | 0 | Mode setting |", markdown)
        self.assertIn("| value | int | 7:3 | 0 | Value field |", markdown)

    def test_config_to_markdown_without_groups(self):
        """
        Test that config_to_markdown works without groups (no group section).
        """
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        
        markdown_tables = generate_markdown_tables(bitdict_factory(config))
        self.assertEqual(len(markdown_tables), 1)
        
        # Should not contain group section
        self.assertNotIn("### Field Groups", markdown_tables[0])
        
        # Should still contain regular table
        self.assertIn("| Name | Type | Bitfield | Default | Description |", markdown_tables[0])
