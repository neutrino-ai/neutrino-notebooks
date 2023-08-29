import re


def snake_to_pascal(snake_str: str) -> str:
    """
    Converts a snake_case string to PascalCase.

    Args:
        snake_str (str): The snake_case string to convert.

    Returns:
        str: The converted PascalCase string.
    """
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)


def to_snake_case(string: str) -> str:
    """
    Converts a string to snake_case

    Args:
        string (str): The string to convert.

    Returns:
        str: The converted snake_case string.
    """
    string = re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()
    string = re.sub(r'[\s-]', '_', string).lower()
    return string
