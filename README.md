# `symbolpilot`

An interactive, human-in-the-loop object file symbol resolver.

## Motivation

Traditional symbol resolvers (e.g., linkers such as `ld`, `lld`, or `gold`) operate as black boxes: they resolve symbols
and dependencies in a fully automatic fashion, either silently resolve or entirely fail on complex symbol situations
such as One Definition Rule (ODR) violations, giving little visibility and virtually no control to developers during the
process.

**This tool offers a new, interactive, and transparent approach to symbol resolution and object file dependency
analysis.** It is designed for *human-in-the-loop* workflows, where developers can step through symbol closures,
explicitly see (and resolve) ambiguities, and gain detailed insight into which object files provide which symbols. All
symbol names are handled verbatim, with no demangling or reinterpretation.

This approach is, to our knowledge, novel - no other tool provides this level of programmably accessible, step-wise, and
ambiguity-exposing symbol resolution. It **fills a gap left by traditional development toolchains**, serving as both an
educational resource and a practical utility. It is especially useful for:

- Teaching or researching real-world linking and symbol resolution
- Exploring and debugging complex or non-standard builds
- Diagnosing ODR violations and dependency tangling in large or legacy codebases
- Manually assembling symbol closure for small systems or embedded targets

## Key Features & Characteristics

- **Interactive, human-in-the-loop:** The tool is intended for iterative and supervised symbol resolution, not
  automated, "black-box" full program linking.
- **No name demangling:** All symbols are handled *as is*, exactly as reported by `nm`; C++ or Fortran mangled names are
  not demangled at any stage.
- **Strict ODR handling:** If multiple object files provide the same symbol (One Definition Rule violation), the tool
  cannot resolve the repeated symbol and will treat it as unresolvable.

## Usage Example

Suppose you have a directory of object files: `lib/*.o`, and you want to analyze and resolve symbols in `main.o`:

```python
from glob import glob
from symbolpilot import construct_o_file_database, resolve_symbols, get_symbols_in_o_file

# Step 1: Build databases and dependency graph
(
    o_file_paths_to_symbol_types_to_symbol_names,
    symbol_types_to_symbol_names_to_o_file_paths,
) = construct_o_file_database(glob('lib/*.o'), nm_command=('nm',))

# Step 2: Prepare lists of symbols to resolve
# Here, for demonstration, we aggregate all undefined ('U') and defined ('T') symbols found
symbols_in_main_o = get_symbols_in_o_file(
    'main.o',
    nm_command=('nm',)
)
u_symbols = symbols_in_main_o.get('U', [])
t_symbols = symbols_in_main_o.get('T', [])

# Step 3: Attempt to resolve undefined symbols to object files
resolved, ambiguous, unresolved = resolve_symbols(
    u_symbols,
    t_symbols,
    o_file_paths_to_symbol_types_to_symbol_names,
    symbol_types_to_symbol_names_to_o_file_paths
)

print("Resolved symbols and their providing object files:")
for symbol, objfile in resolved.items():
    print(f"  {symbol} -> {objfile}")

print("Ambiguous symbols and their providing object files:")
for symbol, objfiles in ambiguous.items():
    print(f"  {symbol} -> {objfiles}")

print("Symbols that could not be resolved:")
for symbol in unresolved:
    print(f"  {symbol}")
```

## Output Serialization

All outputs produced by this tool are standard Python lists and dicts, making them **very easy to serialize and
deserialize using JSON**. This allows seamless integration with other development tools and scripting environments.

For example, you can save your data structures with:

```python
import json

with open('symbol_index.json', 'w') as f:
    json.dump(o_file_paths_to_symbol_types_to_symbol_names, f, indent=2)

with open('inverse_symbol_index.json', 'w') as f:
    json.dump(symbol_types_to_symbol_names_to_o_file_paths, f, indent=2)
```

And restore them in another session with:

```python
import json

with open('symbol_index.json', 'r') as f:
    o_file_paths_to_symbol_types_to_symbol_names = json.load(f)

with open('inverse_symbol_index.json', 'r') as f:
    symbol_types_to_symbol_names_to_o_file_paths = json.load(f)
```

This makes it simple to:

- Export and share symbol databases and dependency graphs,
- Store analysis results,
- Pipe data between tools,
- Or use your own post-processing scripts.

**No custom classes or obscure data structures are used, ensuring maximal portability and ease of use with common JSON
tools.**

## Installation

```commandline
pip install symbolpilot
```

## Requirements

- Unix system with `nm` or compatible command

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
