"""
The module provides a helper function to convert a bitdict configuration dictionary into a
a series of markdown tables.

This function takes the configuration dictionary as input and outputs list of 
markdown strings representing the data in table form. It can be useful for generating 
documentation or for displaying configuration settings in a readable format.

The function is called `config_to_markdown` and takes the following arguments:
    
- `config`: The bitdict configuration dictionary that needs to be converted.
- `include_types`: A boolean to indicate if data types should be included in the output.

Each bitdict in the configuration (there may be nested bitdicts) is represented as a table.
Each table is a table of bitdict properties with the following columns:
- `Name`: The name of the property.
- `Type`: The data type of the property.
- `Bitfield`: The bitrange of the property i.e. f"{start+width-1}:{start}"
    or f"{start}" if width == 1
- `Default`: The default value of the property.
- `Description`: A description of the property.

If the property has a "valid" key in the bitdict, the valid values are listed in the description.
If the property is a "bitdict" then the default values is "N/A" and the description is
f"See {config['name']} definition table.".
If the properties do not define a contiguous range of bits, the undefined bitranges are listed
in the table with the name "Undefined" and all other columns "N/A".

Returns:
A list of formatted markdown strings representing the bitdict configuration in table format.
"""


def _format_undefined_row(current_bit: int, start: int, include_types: bool) -> str:
    """Formats a row for undefined bits in the table."""
    undefined_name = "Undefined"
    undefined_bitfield = (
        f"{current_bit}-{start - 1}" if start - current_bit > 1 else f"{current_bit}"
    )
    if include_types:
        return f"| {undefined_name} | N/A | {undefined_bitfield} | N/A | N/A |"
    return f"| {undefined_name} | {undefined_bitfield} | N/A | N/A |"


def _get_description(prop_config: dict) -> str:
    """Extracts and formats the description from the property configuration."""
    description = ""
    if "valid" in prop_config:
        valid_values = prop_config["valid"].get("value")
        valid_range = prop_config["valid"].get("range")
        if valid_values:
            description += f"Valid values: {valid_values}. "
        if valid_range:
            description += f"Valid ranges: {valid_range}. "
    return description + prop_config.get("description", "")


def _format_row(name: str, prop_config: dict, **kwargs) -> str:
    """Formats a standard data row for the table."""
    bitfield = kwargs.get("bitfield", "N/A")
    default = kwargs.get("default", "N/A")
    description = kwargs.get("description", "")
    include_types = kwargs.get("include_types", True)

    if include_types:
        return f"| {name} | {prop_config['type']} | {bitfield} | {default} | {description} |"
    return f"| {name} | {bitfield} | {default} | {description} |"


def _process_property(
    name: str, prop_config: dict, current_bit: int, include_types: bool
) -> tuple[list[str], int]:
    """Processes a single property and returns the row and the updated current bit."""
    rows = []
    start = prop_config["start"]
    width = prop_config["width"]
    end = start + width - 1

    if start > current_bit:
        undefined_row = _format_undefined_row(current_bit, start, include_types)
        rows.append(undefined_row)

    bitfield = f"{end}:{start}" if width > 1 else f"{start}"
    default = prop_config.get("default", "N/A")
    description = _get_description(prop_config)

    if prop_config["type"] == "bitdict":
        default = "N/A"
        description = f"See '{name}' definition table(s)."

    row = _format_row(
        name,
        prop_config,
        bitfield=bitfield,
        default=default,
        description=description,
        include_types=include_types,
    )
    rows.append(row)
    current_bit = end + 1
    return rows, current_bit


def generate_markdown_tables(bitdict_t: type, include_types: bool = True) -> list[str]:
    """
    Converts a bitdict configuration dictionary into a list of markdown tables.

    Args:
        bitdict_t: The bitdict class returned from bitdict_factory().
        include_types: A boolean to indicate if data types should be included in the output.

    Returns:
        A list of formatted markdown strings representing the bitdict configuration in table format.
    """
    _config = bitdict_t.get_config()
    markdown_tables = []
    table_header: str = f"## {bitdict_t.title}\n\n"
    table_header += (
        "| Name | Type | Bitfield | Default | Description |\n"
        if include_types
        else "| Name | Bitfield | Default | Description |\n"
    )
    table_header += (
        "|---|:-:|:-:|:-:|---|\n" if include_types else "|---|:-:|:-:|---|\n"
    )

    rows = []
    current_bit = 0
    sorted_properties = sorted(_config.items(), key=lambda item: item[1]["start"])

    for name, prop_config in sorted_properties:
        new_rows, current_bit = _process_property(
            name, prop_config, current_bit, include_types
        )
        rows.extend(new_rows)

    table = table_header + "\n".join(rows)
    markdown_tables.append(table)

    # Recursively process nested bitdicts
    for subtypes in bitdict_t.subtypes.values():
        for subtype in subtypes:
            markdown_tables.extend(generate_markdown_tables(subtype, include_types))

    return markdown_tables
