import re
from typing import Union

import autopep8
import nbformat
import yaml
from termcolor import colored

from parser.cells.scheduled_cell import ScheduledCell
from parser.cells.websocket_cell import WebSocketCell
from .cells import Cell, CodeCell, HttpCell


def split_types(s: str) -> list[str]:
    return [x.strip() for x in re.split(r',\s*(?![^[\]{}]*[\]{}])', s)]


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


def parse_cell(cell_content: dict) -> Cell | None:
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
        return parse_http_cell(cleaned_declaration_lines, source_lines)
    elif first_line and re.match(r'@WS', first_line):  # New condition for WebSocket
        return parse_websocket_cell(cleaned_declaration_lines, source_lines)
    elif first_line and re.match(r'@SCHEDULED', first_line):
        return parse_scheduled_cell(cleaned_declaration_lines, source_lines)
    else:
        return CodeCell(source=source)


def parse_http_cell(declaration_lines: list[str], source_lines: list[str]) -> Union['HttpCell', None]:
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
        print(f"Failed to parse YAML: {e}")
        return None

    for key in ['Body', 'Resp']:
        if key in cell_dict:
            if isinstance(cell_dict[key], str):
                cell_dict[key] = split_types(cell_dict[key])

    func_body = "\n".join(source_lines).strip()

    if func_body and (http_verb and endpoint):
        return HttpCell(
            http=http_verb,
            body=cell_dict.get('body'),
            resp=cell_dict.get('resp'),
            query=cell_dict.get('query'),
            headers=cell_dict.get('headers'),
            endpoint=endpoint,
            func_body=func_body
        )


def parse_websocket_cell(declaration_lines: list[str], source_lines: list[str]) -> WebSocketCell | None:
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
        print(f"Failed to parse YAML: {e}")
        return None

    # Check if Query or Headers is a list, leave it as is. If not, convert it to list.
    for key in ['Query', 'Headers']:
        if key in cell_dict:
            if isinstance(cell_dict[key], str):
                cell_dict[key] = cell_dict[key].split(',')

    func_body = "\n".join(source_lines).strip()

    if func_body and endpoint:
        return WebSocketCell(
            endpoint=endpoint,
            func_body=func_body,
            query=cell_dict.get('query'),
            headers=cell_dict.get('headers')
        )


def parse_scheduled_cell(declaration_lines: list[str], source_lines: list[str]) -> ScheduledCell | None:
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
            print(f"Warning: Invalid line in schedule declaration: {line}")

    func_body = "\n".join(source_lines).strip()

    if func_body and (cron or interval):
        return ScheduledCell(
            func_body=func_body,
            cron=cron,
            interval=interval
        )


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
            parsed_cell = parse_cell(cell)
            if parsed_cell:
                parsed_cells.append(parsed_cell)

    # Sort so HttpCells appear last
    sorted_cells = sorted(parsed_cells, key=lambda x: isinstance(x, HttpCell))

    return [str(cell) for cell in sorted_cells]


def compile_notebook_to_py(filepath: str) -> str:
    """Compile the notebook to Python code."""
    cells = parse_notebook_cells(filepath)

    output_lines = [
        'from fastapi import APIRouter, HTTPException, WebSocket\n',
        'from pydantic import BaseModel\n',
        'from scheduler import scheduler\n',
        'from typing import List, Dict, Optional, Union, Any\n',
        'import json\n',
        'router = APIRouter()\n',
    ]
    for cell in cells:
        output_lines.append(str(cell))
        output_lines.append('\n')

    return autopep8.fix_code('\n'.join(output_lines))


if __name__ == "__main__":
    code = compile_notebook_to_py('notebook.ipynb')
    print(code)
