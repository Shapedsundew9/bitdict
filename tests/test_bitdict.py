""""""

import unittest
from bitdict import bitdict_factory


class TestBitDictFactory(unittest.TestCase):

    def test_factory_valid_config(self):
        config = {
            "field1": {"start": 0, "width": 4, "type": "uint"},
            "field2": {"start": 4, "width": 1, "type": "bool"},
        }
        MyBitDict = bitdict_factory(config)
        self.assertTrue(issubclass(MyBitDict, object))  # Check it's a class
        self.assertEqual(MyBitDict.get_config(), config)  # Check config stored
        self.assertEqual(MyBitDict._total_width, 5)  # pylint: disable=protected-access
        _ = MyBitDict()  # Check we can instanciate.

    def test_factory_invalid_config_type(self):
        with self.assertRaises(TypeError):
            bitdict_factory("not a dict")  # type: ignore

    def test_factory_invalid_property_name(self):
        with self.assertRaises(ValueError):
            bitdict_factory({"1badname": {"start": 0, "width": 1, "type": "bool"}})

    def test_factory_missing_required_keys(self):
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "type": "uint"}})  # Missing width
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"width": 4, "type": "uint"}})  # Missing start
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": 4}})  # Missing type

    def test_factory_invalid_start_value(self):
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": -1, "width": 4, "type": "uint"}})
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": "0", "width": 4, "type": "uint"}})

    def test_factory_invalid_width_value(self):
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": 0, "type": "uint"}})
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": -1, "type": "uint"}})
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": "4", "type": "uint"}})

    def test_factory_invalid_type_value(self):
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": 4, "type": "invalid"}})

    def test_factory_bool_width_mismatch(self):
        with self.assertRaises(ValueError):
            bitdict_factory({"field1": {"start": 0, "width": 2, "type": "bool"}})

    def test_factory_reserved_default(self):
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "reserved", "default": 0}}
            )

    def test_factory_invalid_uint_default(self):
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "uint", "default": -3}}
            )

    def test_factory_invalid_int_default(self):
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "int", "default": 17}}
            )

    def test_factory_invalid_bool_default(self):
        with self.assertRaises(TypeError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 1, "type": "bool", "default": 2}}
            )

    def test_factory_bitdict_missing_subtype(self):
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "bitdict"}}
            )  # No subtype
        with self.assertRaises(ValueError):
            bitdict_factory(
                {"field1": {"start": 0, "width": 4, "type": "bitdict", "subtype": {}}}
            )  # Not a list

    def test_factory_bitdict_missing_selector(self):
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
        with self.assertRaises(ValueError):
            bitdict_factory(
                {
                    "field1": {"start": 0, "width": 4, "type": "uint"},
                    "field2": {"start": 2, "width": 4, "type": "uint"},
                }
            )

    def test_factory_nested_validation(self):
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


class TestBitDict(unittest.TestCase):

    def setUp(self):
        self.config = {
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
        self.MyBitDict = bitdict_factory(self.config, name="MyBitDict")

    def test_create_instance_int(self):
        bd = self.MyBitDict(0x8C)
        self.assertEqual(bd.to_int(), 0x8C)
        with self.assertRaises(ValueError):
            self.MyBitDict(256)  # Too large
        with self.assertRaises(ValueError):
            self.MyBitDict(-256)  # Too small

    def test_create_instance_bytes(self):
        bd = self.MyBitDict(bytes([0x8C]))
        self.assertEqual(bd.to_int(), 0x8C)
        bd2 = self.MyBitDict(bytearray([0x8C]))  # Test bytearray too
        self.assertEqual(bd2.to_int(), 0x8C)
        with self.assertRaises(ValueError):
            self.MyBitDict(bytes([0x01, 0x02]))  # Too long
        # Test padding:
        bd3 = self.MyBitDict(bytes([0xC]))
        self.assertEqual(bd3.to_int(), 0xC)

    def test_create_instance_dict(self):
        bd = self.MyBitDict(
            {"Constant": True, "Mode": False, "SubValue": {"PropA": 2, "PropB": -1}}
        )
        self.assertEqual(bd.to_int(), 0b10001110)  # Check against expected value.
        self.assertEqual(bd["Constant"], True)
        self.assertEqual(bd["Mode"], False)
        self.assertEqual(bd["SubValue"]["PropA"], 2)
        self.assertEqual(bd["SubValue"]["PropB"], -1)

        # Test with missing values (should use defaults)
        bd2 = self.MyBitDict({"Constant": True})
        self.assertEqual(bd2["Constant"], True)
        self.assertEqual(bd2["Mode"], False)  # Default for bool

    def test_create_instance_invalid_type(self):
        with self.assertRaises(TypeError):
            self.MyBitDict("string")

    def test_get_set_bool(self):
        bd = self.MyBitDict()
        bd["Constant"] = True
        self.assertEqual(bd["Constant"], True)
        bd["Constant"] = False
        self.assertEqual(bd["Constant"], False)
        with self.assertRaises(TypeError):
            bd["Constant"] = "Frank"  # Wrong type

    def test_get_set_uint(self):
        bd = self.MyBitDict()
        bd["SubValue"]["PropA"] = 3
        self.assertEqual(bd["SubValue"]["PropA"], 3)
        with self.assertRaises(ValueError):
            bd["SubValue"]["PropA"] = 5  # Out of range
        bd["SubValue"]["PropA"] = True  # Is an int type
        with self.assertRaises(TypeError):
            bd["SubValue"]["PropA"] = "Harry"

    def test_get_set_int(self):
        bd = self.MyBitDict()
        bd["SubValue"]["PropB"] = -2
        self.assertEqual(bd["SubValue"]["PropB"], -2)
        bd["SubValue"]["PropB"] = 1
        self.assertEqual(bd["SubValue"]["PropB"], 1)
        with self.assertRaises(ValueError):
            bd["SubValue"]["PropB"] = -3  # Out of range
        with self.assertRaises(TypeError):
            bd["SubValue"]["PropB"] = "string"

    def test_reserved(self):
        bd = self.MyBitDict(0x8C)
        with self.assertRaises(ValueError):
            _ = bd["Reserved"]  # Check cannot read
        with self.assertRaises(ValueError):
            bd["Reserved"] = 1  # Check cannot set

    def test_nested_bitdict(self):
        bd = self.MyBitDict(0x8C)
        self.assertEqual(bd["Mode"], False)
        self.assertEqual(bd["SubValue"]["PropA"], 0)
        self.assertEqual(bd["SubValue"]["PropB"], -1)

        bd["Mode"] = True  # Resets Subvalue to bitdict[1] default
        self.assertEqual(bd["SubValue"]["PropC"], 1)
        self.assertEqual(bd["SubValue"]["PropD"], True)
        self.assertEqual(bd["SubValue"].to_int(), 9)

        bd["SubValue"]["PropC"] = 5
        self.assertEqual(bd["SubValue"]["PropC"], 5)
        nested = bd["SubValue"]
        self.assertEqual(nested["PropC"], 5)
        with self.assertRaises(TypeError):
            bd["SubValue"] = "string"  # Try and set to incorrect type.
        bd["SubValue"] = 3  # Value set
        self.assertEqual(bd["SubValue"]["PropC"], 3)
        self.assertEqual(bd["SubValue"]["PropD"], False)

    def test_len(self):
        bd = self.MyBitDict()
        self.assertEqual(len(bd), 8)  # Total bit width

    def test_contains(self):
        bd = self.MyBitDict()
        self.assertTrue("Constant" in bd)
        self.assertTrue("PropA" in bd)
        self.assertFalse("PropC" in bd)  # Not selected

    def test_iteration(self):
        bd = self.MyBitDict(0x8C)
        expected_order = [
            "SubValue",
            "Mode",
            "Constant",
        ]  # LSB to MSB order
        actual_order = [name for name, _ in bd]
        self.assertEqual(actual_order, expected_order)

        expected_values = [(True, False, None, -1, 0), (True, True, None, True, 1)]
        mode = 0
        for constant, mode_val, reserved, sub_prop_b, sub_prop_a in [
            expected_values[0]
        ]:
            bd = self.MyBitDict({"Constant": constant, "Mode": mode_val})
            for name, value in bd:
                if name == "Constant":
                    self.assertEqual(value, constant)
                elif name == "Mode":
                    self.assertEqual(value, mode_val)
                elif name == "Reserved":
                    self.assertEqual(value, reserved)
                elif name == "SubValue":
                    if not mode_val:
                        self.assertEqual(value["PropA"], sub_prop_a)
                        self.assertEqual(value["PropB"], sub_prop_b)
                    else:
                        self.assertEqual(value["PropC"], sub_prop_a)
                        self.assertEqual(value["PropD"], sub_prop_b)
            mode = mode + 1

    def test_repr(self):
        bd = self.MyBitDict(0x8C)
        self.assertEqual(
            repr(bd),
            "MyBitDict({'Constant': True, 'Mode': False, 'SubValue': {'PropB': -1, 'PropA': 0}})",
        )

    def test_str(self):
        bd = self.MyBitDict(0x8C)
        self.assertEqual(
            str(bd),
            "{'Constant': True, 'Mode': False, 'SubValue': {'PropB': -1, 'PropA': 0}}",
        )

    def test_update(self):
        bd = self.MyBitDict()
        bd.update({"Constant": True, "SubValue": {"PropA": 1}})
        self.assertEqual(bd["Constant"], True)
        self.assertEqual(bd["SubValue"]["PropA"], 1)
        with self.assertRaises(TypeError):
            bd.update("not a dict")
        with self.assertRaises(KeyError):
            bd.update({"InvalidKey": 1})

    def test_to_json(self):
        bd = self.MyBitDict(0x8C)
        expected_json = {
            "Constant": True,
            "Mode": False,
            "SubValue": {"PropA": 0, "PropB": -1},
        }
        self.assertEqual(bd.to_json(), expected_json)
        # Test nested to_json
        bd["Mode"] = True
        expected_json = {
            "Constant": True,
            "Mode": True,
            "SubValue": {"PropC": 1, "PropD": True},
        }
        self.assertEqual(bd.to_json(), expected_json)

    def test_to_bytes(self):
        bd = self.MyBitDict(0x8C)
        self.assertEqual(bd.to_bytes(), bytes([0x8C]))

    def test_to_int(self):
        bd = self.MyBitDict(0x8C)
        self.assertEqual(bd.to_int(), 0x8C)

    def test_get_config(self):
        retrieved_config = self.MyBitDict.get_config()
        self.assertEqual(retrieved_config, self.config)
        # Ensure it's read-only (check for immutability)
        with self.assertRaises(TypeError):
            retrieved_config["Constant"] = "something else"


if __name__ == "__main__":
    unittest.main()
