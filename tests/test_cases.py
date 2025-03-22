import pytest

from analysis import RelationStructure
from structure import DatabaseStructure
from utils.markdown_test_cases import get_test_cases
from analyze import analyze_sql


@pytest.mark.parametrize("case", list(get_test_cases("tests/straightforward_cases.md")))
def test_straightforward_cases(case):
    with open("tests/test_data/issue_tracker_schema.json") as f:
        structure = DatabaseStructure.model_validate_json(f.read())
    [sql_input, expected_json] = case.parameters
    actual = analyze_sql(structure, sql_input)
    expected = RelationStructure.model_validate_json(expected_json)
    assert actual == expected
