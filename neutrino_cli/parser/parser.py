import re
from typing import Union

import autopep8
import nbformat
import yaml
from termcolor import colored

from neutrino_cli.parser.cells.scheduled_cell import ScheduledCell
from neutrino_cli.parser.cells.websocket_cell import WebSocketCell
from .cells import Cell, CodeCell, HttpCell



def clean_source(lines: list[str]) -> tuple[list[str], list[str]]:
    """
    Remove empty lines and split the cell into declaration lines and source lines.
    Only the first 'chunk' of comments or first multi-line comment is considered as declaration.
    """
    declaration_lines = []
    source_lines = []
    inside_multi_line = False
    first_chunk_collected = False

    for line in lines:
        stripped_line = line.strip()

        if not first_chunk_collected:
            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                inside_multi_line = not inside_multi_line
                if not inside_multi_line:
                    first_chunk_collected = True
                continue

            if inside_multi_line or stripped_line.startswith("#"):
                declaration_lines.append(stripped_line.lstrip('#').strip())
            else:
                first_chunk_collected = True
                source_lines.append(line)  # Keep original indentation in source lines
        else:
            source_lines.append(line)  # Keep original indentation in source lines

    return declaration_lines, source_lines


def parse_cell(cell_content: dict, filepath: str) -> Union[Cell, None]:
    """
    Parses a Jupyter notebook cell to determine its type and content.

    Parameters:
    - cell_content (dict): A dictionary containing the cell content. Expects 'source' to be a key in the dict.
    - filepath (str): The path of the file containing the cell, used for error reporting.

    Returns:
    - Union[Cell, None]: Returns an object of type HttpCell, WebSocketCell, ScheduledCell, or CodeCell based on the
                   cell content. Returns None if the cell is not one of these types.
    """
    source = cell_content['source']
    lines = source.split("\n")
    cleaned_declaration_lines, source_lines = clean_source(lines)

    if not cleaned_declaration_lines and not source_lines:
        return None

    first_line = cleaned_declaration_lines[0] if cleaned_declaration_lines else None

    if first_line and re.match(r'@HTTP', first_line):
        if first_line.strip() == '@HTTP':
            cleaned_declaration_lines.pop(0)  # Remove the line entirely if it only contains @HTTP
        else:
            cleaned_declaration_lines[0] = first_line.replace('@HTTP ', '')  # Remove @HTTP but keep the rest
        return parse_http_cell(cleaned_declaration_lines, source_lines, filepath=filepath)

    elif first_line and re.match(r'@WS', first_line):
        return parse_websocket_cell(cleaned_declaration_lines, source_lines, filepath=filepath)

    elif first_line and re.match(r'@SCHEDULE', first_line):
        return parse_scheduled_cell(cleaned_declaration_lines, source_lines, filepath=filepath)

    else:
        return CodeCell(source=source)


def split_types(s: str) -> list[str]:
    """
    Split a string of types into a list of types.
    Example: "int, str, list[int]" -> ["int", "str", "list[int]"]
    :param s:
    :return:
    """
    stack = []
    start = 0
    result = []
    for i, c in enumerate(s):
        if c in ['[', '{']:
            stack.append(c)
        elif c in [']', '}']:
            stack.pop()
        elif c == ',':
            if not stack:
                result.append(s[start:i].strip())
                start = i + 1
    result.append(s[start:].strip())
    return result


def parse_http_cell(declaration_lines: list[str], source_lines: list[str], filepath: str) -> Union['HttpCell', None]:
    http_verb, endpoint = None, None
    cell_dict = {}

    first_line = declaration_lines[0]
    for x in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
        if x in first_line:
            http_verb = x
            endpoint = first_line.replace(x, '').strip()
            declaration_lines.pop(0)
            break

    try:
        parsed_yaml = yaml.safe_load("\n".join(declaration_lines))
        if parsed_yaml:
            cell_dict.update(parsed_yaml)
    except yaml.YAMLError as e:
        print(colored(f"Error in {filepath}:\nFailed to parse YAML: {e}", "red"))
        return None

    for key in ['body', 'resp']:
        if key in cell_dict:
            if isinstance(cell_dict[key], str):
                cell_dict[key] = split_types(cell_dict[key])

    func_body = "\n".join(source_lines).strip()

    if func_body and (http_verb and endpoint):
        try:
            return HttpCell(
                http=http_verb,
                body=cell_dict.get('body'),
                resp=cell_dict.get('resp'),
                query=cell_dict.get('query'),
                headers=cell_dict.get('headers'),
                endpoint=endpoint,
                func_body=func_body
            )
        except Exception as e:
            print(colored(f"Error parsing cell in {filepath}:\n{e}", "red"))
            return None


def parse_websocket_cell(declaration_lines: list[str], source_lines: list[str], filepath: str) -> Union[WebSocketCell, None]:
    endpoint = None
    cell_dict = {}

    first_line = declaration_lines[0]
    if "@WS" in first_line:
        endpoint = first_line.replace("@WS", '').strip()
        declaration_lines.pop(0)

    try:
        parsed_yaml = yaml.safe_load("\n".join(declaration_lines))
        if parsed_yaml:
            cell_dict.update(parsed_yaml)
    except yaml.YAMLError as e:
        print(f"Error in {filepath}:\nFailed to parse YAML: {e}")
        return None

    for key in ['query', 'headers', 'message']:
        if key in cell_dict:
            if isinstance(cell_dict[key], str):
                cell_dict[key] = split_types(cell_dict[key])

    validate_flag = cell_dict.get('validate', False)

    func_body = "\n".join(source_lines).strip()

    if func_body and endpoint:
        try:
            return WebSocketCell(
                endpoint=endpoint,
                func_body=func_body,
                ws_type=cell_dict.get('type', 'event'),
                message_schema=cell_dict.get('message'),
                query=cell_dict.get('query'),
                headers=cell_dict.get('headers'),
                validate_message_schema=validate_flag,
            )
        except Exception as e:
            print(f"Error parsing cell in {filepath}:\n{e}")
            return None


def parse_scheduled_cell(declaration_lines: list[str], source_lines: list[str], filepath: str) -> Union[ScheduledCell, None]:
    cron = None
    interval = None

    # Remove the first line as it is "@SCHEDULE"
    if declaration_lines[0].strip() == "@SCHEDULE":
        declaration_lines.pop(0)

    for line in declaration_lines:
        if ':' in line:
            key, value = map(str.strip, line.split(':', 1))
            if key == 'cron':
                cron = value
            elif key == 'interval':
                interval = value
        else:
            print(colored(f"Warning in {filepath}:\nInvalid line in schedule declaration: {line}", "red"))

    func_body = "\n".join(source_lines).strip()

    if func_body and (cron or interval):
        try:
            return ScheduledCell(
                func_body=func_body,
                cron=cron,
                interval=interval
            )
        except Exception as e:
            print(colored(f"Error parsing cell in {filepath}:\n{e}", "red"))
            return None


def parse_notebook_cells(filepath: str) -> list[str]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
    except FileNotFoundError:
        print(colored(f"Error: Notebook file not found: {filepath}", 'red'))
        return []
    except nbformat.reader.NotJSONError:
        print(colored(f"Error: Notebook file is not a valid JSON file: {filepath}", 'red'))
        return []

    parsed_cells = []
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            parsed_cell = parse_cell(cell, filepath=filepath)
            if parsed_cell:
                parsed_cells.append(parsed_cell)

    # Sort so HttpCells appear last
    sorted_cells = sorted(parsed_cells, key=lambda x: isinstance(x, HttpCell))

    return [str(cell) for cell in sorted_cells]


def compile_notebook_to_py(filepath: str) -> str:
    """Compile the notebook to Python code."""
    cells = parse_notebook_cells(filepath)

    output_lines = [
        'from fastapi import APIRouter, HTTPException, WebSocket',
        'from pydantic import BaseModel, ValidationError',
        'from scheduler import scheduler',
        'from typing import List, Dict, Optional, Union, Any, AsyncGenerator, Callable',
        'import uuid',
        'import json\n',
        'from websocket_manager import manager\n\n\n'
        'router = APIRouter()\n',
    ]
    for cell in cells:
        output_lines.append(str(cell))
        output_lines.append('\n')

    return autopep8.fix_code('\n'.join(output_lines))


if __name__ == "__main__":
    code = compile_notebook_to_py('notebook.ipynb')
    print(code)
