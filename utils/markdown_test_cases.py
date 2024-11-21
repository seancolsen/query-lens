from dataclasses import dataclass, field
from typing import *

import mistune

@dataclass
class TestCase:
    name: str
    parameters: list[str] = field(default_factory=list)


def _get_markdown_elements(file_path: str) -> List[dict]:
    parse_markdown = mistune.create_markdown(renderer=None, escape=False)
    with open(file_path, 'r') as f:
        return parse_markdown(f.read())


def _get_heading_text(element: dict) -> str:
    return element['children'][0]['raw']


def get_test_cases(file_path: str):
    test_case = TestCase(name='')

    for element in _get_markdown_elements(file_path):
        if element['type'] == 'heading':
            if test_case.parameters:
                yield test_case
            test_case = TestCase(name=_get_heading_text(element))
        if element['type'] == 'block_code':
            test_case.parameters.append(element['raw'])

    if test_case.parameters:
        yield test_case
    