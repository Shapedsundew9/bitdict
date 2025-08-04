"""
BitDict configuration validation module.

This module provides validation classes for BitDict configurations,
implementing a clean separation of validation concerns from the core
BitDict functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import Any, Protocol


class PropertyValidator(Protocol):
    """Protocol defining the interface for property validators."""

    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validate a property configuration.

        Args:
            prop_name: The name of the property being validated
            prop_config: The property configuration dictionary

        Raises:
            ValueError: If the property configuration is invalid
            TypeError: If the property configuration has wrong types
        """
        ...


class BasePropertyValidator(ABC):
    """Base class for property validators."""

    @abstractmethod
    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validate a property configuration."""
        pass


class PropertyNameValidator(BasePropertyValidator):
    """Validates property names."""

    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validates that the property name is a valid identifier."""
        if not isinstance(prop_name, str) or not prop_name.isidentifier():  # type: ignore[misc]
            raise ValueError(f"Invalid property name: {prop_name}")


class ConfigStructureValidator(BasePropertyValidator):
    """Validates the basic structure of property configurations."""

    def validate(
        self, prop_name: str, prop_config: dict[str, Any] | MappingProxyType[str, Any]
    ) -> None:
        """Validates the type and required keys of the property configuration."""
        required_keys = {"start", "width", "type"}
        if not isinstance(prop_config, (dict, MappingProxyType)):  # type: ignore[misc]
            raise TypeError("Property configuration must be a dictionary or MappingProxyType")

        # Reject MappingProxyType objects as per original behavior
        if isinstance(prop_config, MappingProxyType):  # type: ignore[misc]
            raise AssertionError(
                f"Property configuration for '{prop_name}' cannot be a MappingProxyType"
            )

        if not required_keys.issubset(prop_config):
            missing_keys = required_keys - set(prop_config)
            raise ValueError(f"Missing required keys in property config: {missing_keys}")


class StartWidthValidator(BasePropertyValidator):
    """Validates start and width values."""

    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validates the start and width values in the property configuration."""
        if not isinstance(prop_config["start"], int) or prop_config["start"] < 0:
            raise ValueError(f"Invalid start value: {prop_config['start']}")
        if not isinstance(prop_config["width"], int) or prop_config["width"] <= 0:
            raise ValueError(f"Invalid width value: {prop_config['width']}")


class TypeValidator(BasePropertyValidator):
    """Validates property types."""

    VALID_TYPES = {"bool", "uint", "int", "bitdict"}

    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validates the type value in the property configuration."""
        if prop_config["type"] not in self.VALID_TYPES:
            raise ValueError(f"Invalid type value: {prop_config['type']}")
        if prop_config["type"] == "bool" and prop_config["width"] != 1:
            raise ValueError("Boolean properties must have width 1")


class DescriptionValidator(BasePropertyValidator):
    """Validates description fields."""

    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validates the description key in the property configuration."""
        if "description" in prop_config and not isinstance(prop_config["description"], str):
            raise ValueError("Description must be a string")


class DefaultValueValidator(BasePropertyValidator):
    """Validates default values for properties."""

    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validates and sets default values for properties."""
        prop_type = prop_config["type"]

        if prop_type == "bitdict":
            if "default" in prop_config:
                raise ValueError("'bitdict' types cannot have default values.")
            return

        if "default" not in prop_config:
            # Don't try to modify MappingProxyType objects
            if isinstance(prop_config, MappingProxyType):  # type: ignore[misc]
                return
            self._set_missing_defaults(prop_config)
            return

        if "description" not in prop_config:
            # Don't try to modify MappingProxyType objects
            if not isinstance(prop_config, MappingProxyType):  # type: ignore[misc]
                prop_config["description"] = ""

        self._validate_default_value_type(prop_name, prop_config)

    def _set_missing_defaults(self, prop_config: dict[str, Any]) -> None:
        """Sets default values if they are missing in the property configuration."""
        prop_type = prop_config["type"]
        if prop_type == "bool":
            prop_config["default"] = False
        elif prop_type in ("uint", "int"):
            prop_config["default"] = 0

    def _validate_default_value_type(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validates the type and range of the default value."""
        default_value = prop_config["default"]
        prop_type = prop_config["type"]
        width = prop_config["width"]

        if prop_type == "bool":
            if not isinstance(default_value, bool):
                raise TypeError(
                    f"Invalid default type for property {prop_name}"
                    f" expecting bool: {type(default_value)}"
                )
        elif prop_type in ("uint", "int"):
            if not isinstance(default_value, int):
                raise TypeError(
                    f"Invalid default type for property {prop_name}"
                    f" expecting int: {type(default_value)}"
                )
            if prop_type == "uint":
                if not 0 <= default_value < (1 << width):
                    raise ValueError(
                        f"Invalid default value for property" f" {prop_name}: {default_value}"
                    )
            else:  # prop_type == "int"
                if not -(1 << (width - 1)) <= default_value < (1 << (width - 1)):
                    raise ValueError(
                        f"Invalid default value for property {prop_name}" f": {default_value}"
                    )


class ValidKeyValidator(BasePropertyValidator):
    """Validates the 'valid' key in property configurations."""

    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validates the 'valid' key in the property configuration."""
        if prop_config["type"] == "bitdict":
            if "valid" in prop_config:
                raise ValueError(f"'valid' key not allowed for {prop_config['type']} type")
            return

        if "valid" not in prop_config:
            return

        valid_config: dict[str, Any] = prop_config["valid"]
        if not isinstance(valid_config, dict):  # type: ignore[runtime protection]
            raise ValueError(f"'valid' must be a dictionary for property {prop_name}")

        if not valid_config:
            raise ValueError(f"'valid' dictionary cannot be empty for property {prop_name}")

        if "value" not in valid_config and "range" not in valid_config:
            raise ValueError(
                f"'valid' dictionary must contain 'value' or 'range' for property {prop_name}"
            )

        self._validate_valid_value(prop_name, prop_config, valid_config)
        self._validate_valid_range(prop_name, prop_config, valid_config)

    def _validate_valid_value(
        self, prop_name: str, prop_config: dict[str, Any], valid_config: dict[str, Any]
    ) -> None:
        """Validates the 'value' key within the 'valid' configuration."""
        if "value" not in valid_config:
            return

        if not isinstance(valid_config["value"], set):
            raise ValueError(
                f"'value' in 'valid' dictionary must be a set for property {prop_name}"
            )
        if not valid_config["value"]:
            raise ValueError(
                f"'value' set in 'valid' dictionary cannot be empty for property {prop_name}"
            )
        for val in valid_config["value"]:  # type: ignore[runtime safety]
            if not isinstance(val, (int, bool)):
                raise ValueError(
                    f"Invalid value type in 'valid' set for property {prop_name}: {val}"
                )
            if not self._is_value_in_range(val, prop_config):
                raise ValueError(f"Value {val} out of range for property {prop_name}")

    def _validate_valid_range(
        self, prop_name: str, prop_config: dict[str, Any], valid_config: dict[str, Any]
    ) -> None:
        """Validates the 'range' key within the 'valid' configuration."""
        if "range" not in valid_config:
            return

        if not isinstance(valid_config["range"], list):
            raise ValueError(
                f"'range' in 'valid' dictionary must be a list for property {prop_name}"
            )
        if not valid_config["range"]:
            raise ValueError(
                f"'range' list in 'valid' dictionary cannot be empty for property {prop_name}"
            )
        rng: list[tuple[int, ...]] = valid_config["range"]  # type: ignore[runtime safety]
        for r in rng:
            if not isinstance(r, tuple) or not 1 <= len(r) <= 3:  # type: ignore[runtime safety]
                raise ValueError(
                    f"Invalid range tuple in 'valid' list for property {prop_name}: {r}"
                )
            for val in range(*r):
                if not self._is_value_in_range(val, prop_config):
                    raise ValueError(f"Value {val} out of range for property {prop_name}")

    def _is_value_in_range(self, value: int | bool, prop_config: dict[str, Any]) -> bool:
        """Checks if a value is within the allowed range for a property."""
        if prop_config["type"] == "bool":
            return value in (True, False)
        width = prop_config["width"]
        if prop_config["type"] == "uint":
            return 0 <= value < (1 << width)
        assert prop_config["type"] == "int", "Unexpected property type"
        return -(1 << (width - 1)) <= value < (1 << (width - 1))


class BitDictPropertiesValidator(BasePropertyValidator):
    """Validates properties specific to 'bitdict' type configurations."""

    def validate(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validates the properties of a 'bitdict' type configuration."""
        if prop_config["type"] != "bitdict":
            return

        # This will be implemented when needed - for now just validate structure
        if "subtype" not in prop_config or not isinstance(prop_config["subtype"], list):
            raise ValueError("'bitdict' type requires a 'subtype' list")
        if "selector" not in prop_config or not isinstance(prop_config["selector"], str):
            raise ValueError("'bitdict' type requires a 'selector' field")


class ConfigurationValidator:
    """Main validator that coordinates all property validators."""

    def __init__(self):
        """Initialize the validator with all component validators."""
        self._validators: list[PropertyValidator] = [
            PropertyNameValidator(),
            ConfigStructureValidator(),
            StartWidthValidator(),
            TypeValidator(),
            DescriptionValidator(),
            DefaultValueValidator(),
            ValidKeyValidator(),
            BitDictPropertiesValidator(),
        ]

    def validate_property_config(
        self, prop_config_top: dict[str, Any], subtypes: dict[str, list[Any]], factory: Any = None
    ) -> None:
        """
        Validates the entire property configuration.

        Args:
            prop_config_top: The top-level configuration dictionary
            subtypes: Dictionary to store validated subtypes
            factory: Optional factory for creating BitDict classes (to avoid circular imports)

        Raises:
            ValueError: If the configuration is invalid
            TypeError: If the config is not a dictionary
        """
        for prop_name, prop_config in prop_config_top.items():
            self._validate_single_property(prop_name, prop_config)

            # Handle bitdict-specific validation that requires access to top-level config
            if prop_config["type"] == "bitdict":
                self._validate_bitdict_properties(
                    prop_name, prop_config, prop_config_top, subtypes, factory
                )

    def _validate_single_property(self, prop_name: str, prop_config: dict[str, Any]) -> None:
        """Validate a single property using all validators."""
        for validator in self._validators:
            validator.validate(prop_name, prop_config)

    def _validate_bitdict_properties(
        self,
        prop_name: str,
        prop_config: dict[str, Any],
        prop_config_top: dict[str, Any],
        subtypes: dict[str, list[Any]],
        factory: Any = None,
    ) -> None:
        """Validates the properties of a 'bitdict' type configuration."""
        if prop_config["type"] != "bitdict":
            return

        # Check basic requirements
        if "subtype" not in prop_config or not isinstance(prop_config["subtype"], list):
            raise ValueError("'bitdict' type requires a 'subtype' list")
        if "selector" not in prop_config or not isinstance(prop_config["selector"], str):
            raise ValueError("'bitdict' type requires a 'selector' field")

        selector = prop_config["selector"]
        if selector not in prop_config_top:
            raise ValueError(f"Invalid selector property: {selector}")
        if prop_config_top[selector]["type"] not in ("bool", "uint"):
            raise ValueError("Selector property must be of type 'bool' or 'uint'")
        if prop_config_top[selector]["width"] > 16:
            raise ValueError("Selector property width must be <= 16 (65536 subtypes)")

        # Reverse linkage
        prop_config_top[selector]["_bitdict"] = prop_name

        if len(prop_config["subtype"]) == 0:
            raise ValueError(
                f"'bitdict' type for property '{prop_name}' must have at least one subtype"
            )

        # Use factory parameter to avoid circular imports
        # (create_bitdict logic moved inline below)

        pcfg: list[dict[str, Any] | None] = prop_config["subtype"]
        for idx, sub_config in enumerate(pcfg):
            # Recursively validate sub-configurations
            if sub_config is None:
                subtypes.setdefault(prop_name, []).append(None)
            else:
                # Validate the subconfig first to add defaults
                from copy import deepcopy

                validated_sub_config = deepcopy(sub_config)

                # Apply validation to add defaults
                sub_subtypes: dict[str, list[Any]] = {}
                validator = ConfigurationValidator()
                validator.validate_property_config(validated_sub_config, sub_subtypes, factory)

                # Merge nested subtypes back to the parent level
                for sub_key, sub_list in sub_subtypes.items():
                    subtypes[sub_key] = sub_list

                # Update the original config with defaults
                pcfg[idx] = validated_sub_config

                # Now create the BitDict class with the validated config and its subtypes
                if factory is not None:
                    # Use factory method which supports subtypes parameter
                    sub_bitdict_class = factory.create_bitdict_class(
                        validated_sub_config,
                        name=f"{prop_name}{idx}",
                        title=f"{prop_name}: {selector} = {idx}",
                        subtypes=sub_subtypes,
                    )
                else:
                    # Fallback for backward compatibility
                    from .factory import bitdict_factory

                    sub_bitdict_class = bitdict_factory(
                        validated_sub_config,
                        name=f"{prop_name}{idx}",
                        title=f"{prop_name}: {selector} = {idx}",
                    )

                # Store the class
                subtypes.setdefault(prop_name, []).append(sub_bitdict_class)
            if sub_config is None and self._is_valid_value(idx, prop_config_top[selector]):
                raise ValueError(
                    f"Subtype {idx} for property '{prop_name}' "
                    "is a valid selection but no bitdict defined."
                )

    def _is_valid_value(self, value: int | bool, prop_config: dict[str, Any]) -> bool:
        """Checks if a value is valid according to the 'valid'
        key in the property configuration."""
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


class OverlapValidator:
    """Validates that bit field definitions don't overlap."""

    @staticmethod
    def check_overlapping(config: dict[str, Any]) -> None:
        """
        Checks for overlapping bit field definitions.

        Args:
            config: The configuration dictionary

        Raises:
            ValueError: If any bit fields overlap
        """
        used_bits = set()
        for _, prop_config in config.items():
            for i in range(prop_config["start"], prop_config["start"] + prop_config["width"]):
                if i in used_bits:
                    raise ValueError(
                        f"Overlapping bit definitions: bit {i} is used by multiple properties"
                    )
                used_bits.add(i)


# Convenience function for backward compatibility
def validate_property_config(
    prop_config_top: dict[str, Any], subtypes: dict[str, list[Any]], factory: Any = None
) -> None:
    """
    Validates the property configuration using the new validator classes.

    This function maintains backward compatibility with the existing API.

    Args:
        prop_config_top: The top-level configuration dictionary
        subtypes: Dictionary to store validated subtypes
        factory: Optional factory for creating BitDict classes (to avoid circular imports)
    """
    validator = ConfigurationValidator()
    validator.validate_property_config(prop_config_top, subtypes, factory)


def check_overlapping(config: dict[str, Any]) -> None:
    """
    Checks for overlapping bit field definitions.

    This function maintains backward compatibility with the existing API.
    """
    OverlapValidator.check_overlapping(config)
