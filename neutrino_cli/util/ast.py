import ast
from typing import Union


def get_function_name_from_ast(code: str) -> Union[str, None]:
    """Extract the function name from the given code using AST."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return None


def get_function_param_types_from_ast(code: str) -> dict[str, str]:
    """Extract parameter types from function definition."""
    param_types = {}
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                annotation = arg.annotation
                if annotation:
                    param_types[arg.arg] = annotation.id  # assuming the annotation is simple (e.g., "int", "str")
    return param_types


def get_function_args_from_ast(code: str) -> Union[list[str], None]:
    """
    Extract the arguments of a function from the given code using AST.

    Parameters:
        code (str): The code containing the function definition.

    Returns:
        List[str]: A list of argument names if the function is found, None otherwise.
    """
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return [arg.arg for arg in node.args.args]
    return None


def is_valid_function(code: str) -> bool:
    """Check if the given code contains a valid function."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
    return False


def is_async_function(code: str) -> bool:
    """Check if the given code contains an async function."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return isinstance(node, ast.AsyncFunctionDef)
    return False
