# Copyright (c) 2026 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
from collections import OrderedDict
from typing import Sequence, Dict, List, Iterable

from live_tee_and_capture import live_tee_and_capture


def get_symbols_in_o_file(
        o_file_path,  # type: str
        nm_command=('nm',)  # type: Sequence[str]
):
    # type: (...) -> Dict[str, List[str]]
    exit_code, stdout_bytes, stderr_bytes = live_tee_and_capture(
        [*nm_command, o_file_path],
        tee_stdout=False,
        tee_stderr=True
    )

    if exit_code:
        raise OSError('Command failed with exit code %d' % (exit_code,))

    symbol_types_to_symbol_names = OrderedDict()
    for line in stdout_bytes.decode('utf-8').splitlines():
        tokens = line.split()
        symbol_type = tokens[-2]
        symbol_name = tokens[-1]
        symbol_types_to_symbol_names.setdefault(symbol_type, []).append(symbol_name)

    return symbol_types_to_symbol_names


def construct_o_file_database(
        o_file_paths,  # type: Iterable[str]
        nm_command=('nm',)  # type: Sequence[str]
):
    o_file_paths_to_symbol_types_to_symbol_names = OrderedDict()  # type: Dict[str, Dict[str, List[str]]]
    for o_file_path in o_file_paths:
        symbol_types_to_symbol_names = get_symbols_in_o_file(o_file_path, nm_command)
        o_file_paths_to_symbol_types_to_symbol_names[o_file_path] = symbol_types_to_symbol_names

    symbol_types_to_symbol_names_to_o_file_paths = OrderedDict()  # type: Dict[str, Dict[str, List[str]]]
    for o_file_path, symbol_types_to_symbol_names in o_file_paths_to_symbol_types_to_symbol_names.items():
        for symbol_type, symbol_names in symbol_types_to_symbol_names.items():
            for symbol_name in symbol_names:
                symbol_types_to_symbol_names_to_o_file_paths.setdefault(
                    symbol_type,
                    {}
                ).setdefault(
                    symbol_name,
                    []
                ).append(o_file_path)

    return (
        o_file_paths_to_symbol_types_to_symbol_names,
        symbol_types_to_symbol_names_to_o_file_paths,
    )


def resolve_symbols(
        u_symbols,  # type: Iterable[str]
        t_symbols,  # type: Iterable[str]
        o_file_paths_to_symbol_types_to_symbol_names,  # type: Dict[str, Dict[str, List[str]]]
        symbol_types_to_symbol_names_to_o_file_paths,  # type: Dict[str, Dict[str, List[str]]]
):
    unimplemented = set(u_symbols)

    implemented = set(t_symbols)
    resolved_symbols_to_o_files = OrderedDict()
    ambiguous_symbols_to_o_files = OrderedDict()
    unresolvable_symbols = set()

    t_symbols_to_o_files = {}
    for symbol_type, symbol_names_to_o_file_paths in symbol_types_to_symbol_names_to_o_file_paths.items():
        if symbol_type.isupper() and symbol_type != 'U':
            for symbol_name, o_file_paths in symbol_names_to_o_file_paths.items():
                t_symbols_to_o_files.setdefault(symbol_name, set()).update(o_file_paths)

    while unimplemented:
        u_symbol = unimplemented.pop()
        if u_symbol in t_symbols_to_o_files:
            implemented.add(u_symbol)
            o_files = t_symbols_to_o_files[u_symbol]
            if len(o_files) == 1:
                o_file = next(iter(o_files))
                resolved_symbols_to_o_files[u_symbol] = o_file

                u_symbols_in_o_file = set(o_file_paths_to_symbol_types_to_symbol_names.get(o_file, {}).get('U', []))
                unresolved_u_symbols_in_o_file = u_symbols_in_o_file - implemented

                unimplemented.update(unresolved_u_symbols_in_o_file)
            else:
                ambiguous_symbols_to_o_files[u_symbol] = list(o_files)
        else:
            unresolvable_symbols.add(u_symbol)

    return resolved_symbols_to_o_files, ambiguous_symbols_to_o_files, sorted(unresolvable_symbols)
