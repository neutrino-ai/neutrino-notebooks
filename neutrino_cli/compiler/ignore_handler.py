import os
from fnmatch import fnmatchcase


def read_ignore_list(ignore_file_path: str = '.neutrinoignore') -> list[str]:
    """Read the ignore list from a given file.
    Parameters:
        ignore_file_path (str): Path to the ignore file. Defaults to '.neutrinoignore'.
    """
    if not os.path.exists(ignore_file_path):
        return []

    with open(ignore_file_path, 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def should_ignore_file(file_path: str, ignore_list: list[str]) -> bool:
    """Check if a file should be ignored based on the ignore list.

    Parameters:
        file_path (str): Path to the file.
        ignore_list (list): List of patterns to ignore.

    Returns:
        bool: True if the file should be ignored, False otherwise.
    """

    # Remove comment lines from the ignore list
    filtered_ignore_list = [pattern for pattern in ignore_list if not pattern.startswith("#")]

    # Process negated patterns (those starting with "!")
    negated_patterns = [pattern[1:] for pattern in filtered_ignore_list if pattern.startswith("!")]
    filtered_ignore_list = [pattern for pattern in filtered_ignore_list if not pattern.startswith("!")]

    for pattern in negated_patterns:
        if fnmatchcase(file_path, pattern):
            return False

    for pattern in filtered_ignore_list:
        # Remove trailing slashes for directory matching
        normalized_pattern = pattern.rstrip('/')
        normalized_file_path = file_path.rstrip('/')

        if fnmatchcase(normalized_file_path, normalized_pattern) or fnmatchcase(file_path, pattern):
            return True

    return False
