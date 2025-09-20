# BitDict Library

BitDict is a Python library for creating custom bit-packed data structures with dynamically defined substructures. It allows you to define and manipulate data structures where individual fields occupy specific bit ranges, similar to C structs with bitfields.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Dependencies
- Install Python development dependencies:
  - `python3 -m pip install --upgrade pip`
  - `python3 -m pip install pylint` (for linting)
  - `python3 -m pip install coverage` (for coverage testing)
- The library has NO external runtime dependencies - it's pure Python
- Requires Python 3.10 or higher

### Build and Test
- Run unit tests: `python3 -m unittest discover -v` -- takes ~0.08 seconds
- Run linting: `pylint --max-line-length=100 --ignore=tests .` -- takes ~1 second
- Run with coverage: `coverage run --omit="tests/*" -m unittest discover && coverage report` -- takes ~0.13 seconds
- No build step required - this is a pure Python library with no compilation

### Development Workflow
- All tests: 98 tests with 100% code coverage on library code
- Code quality: Maintains 10.00/10 pylint rating
- Test framework: Python's built-in unittest
- Fast operations: All commands complete in under 5 seconds

## Validation

### Essential Validation Steps
After making any changes, always run these validation commands:
1. `python3 -m unittest discover -v` - verify all tests pass
2. `pylint --max-line-length=100 --ignore=tests .` - ensure code quality remains 10.00/10
3. Test basic functionality with the validation script below

### Manual Validation Scenarios
Always test these core scenarios after making changes:

```python
# Basic BitDict functionality test
from bitdict import bitdict_factory, generate_markdown_tables

# Test 1: Basic bitdict creation and manipulation
config = {
    'field1': {'start': 0, 'width': 4, 'type': 'uint'},
    'field2': {'start': 4, 'width': 1, 'type': 'bool'},
    'field3': {'start': 5, 'width': 3, 'type': 'int'}
}

MyBitDict = bitdict_factory(config, 'TestBitDict')
bd = MyBitDict()
bd['field1'] = 5
bd['field2'] = True  
bd['field3'] = -2

# Verify: Values should be set correctly
assert bd['field1'] == 5
assert bd['field2'] == True
assert bd['field3'] == -2

# Test 2: Conversion methods
json_data = bd.to_json()  # Should return dict
bytes_data = bd.to_bytes()  # Should return bytes
int_data = bd.to_int()  # Should return integer

# Test 3: Markdown generation
tables = generate_markdown_tables(MyBitDict)
assert len(tables) >= 1
assert "| Name | Type | Bitfield | Default | Description |" in tables[0]
```

### Library Usage Patterns
- Create bitdict classes: `MyClass = bitdict_factory(config, name, title)`
- Instance creation: `obj = MyClass()` or `MyClass(initial_value)`
- Field access: `obj['field_name'] = value` and `value = obj['field_name']`
- Conversions: `obj.to_json()`, `obj.to_bytes()`, `obj.to_int()`
- Validation: `obj.valid()` returns bool
- Documentation: `generate_markdown_tables(MyClass)`

## Common Tasks

### Repository Structure
```
bitdict/
├── .github/workflows/          # CI/CD pipelines
├── bitdict/                    # Main library code
│   ├── __init__.py            # Package exports
│   ├── bitdict.py             # Core BitDict implementation
│   └── markdown.py            # Markdown table generation
├── tests/                      # Test suite (98 tests)
│   ├── __init__.py
│   ├── test_bitdict.py        # Main functionality tests
│   └── test_markdown.py       # Markdown generation tests
├── pyproject.toml             # Project configuration
└── README.md                  # Documentation
```

### Key Development Files
- **bitdict/bitdict.py**: Core implementation with bitdict_factory() function
- **bitdict/markdown.py**: Markdown table generation with generate_markdown_tables()
- **tests/**: Comprehensive test suite covering all functionality
- **pyproject.toml**: Project metadata and configuration
- **.github/workflows/python-package.yml**: CI pipeline that runs tests and linting

### Performance Characteristics
Based on the test suite performance benchmarks:
- Instance creation: ~37µs per operation
- Property access: ~1.7µs per operation  
- JSON conversion: ~42µs per operation
- Bytes conversion: ~0.85µs per operation

### CI/CD Requirements
The GitHub Actions CI requires:
- All 98 tests to pass on Python 3.10-3.13
- Pylint score of 10.00/10 with no issues
- Uses `pylint --max-line-length=100 --ignore=tests .`
- Coverage reporting to Codecov (100% library coverage expected)

## Troubleshooting

### Common Issues
- **Import errors**: Ensure you're in the repository root directory
- **Test failures**: Run `python3 -m unittest discover -v` to see detailed failure information
- **Linting issues**: Run `pylint --max-line-length=100 --ignore=tests .` and fix reported issues
- **Coverage drops**: Add tests for any new code - the library maintains 100% coverage

### Development Tips
- The library supports complex nested bitdicts with selectors
- Validation rules can be specified with 'valid' keys in field configurations  
- Default values are automatically set if not specified (False for bool, 0 for int/uint)
- Field names must be valid Python identifiers
- Bitfields cannot overlap and must fit within the total bit width

Always run the complete validation workflow before submitting changes to ensure compatibility with the existing codebase and CI requirements.