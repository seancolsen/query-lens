import pytest

from analysis import Analysis
from structure import DatabaseStructure
from utils.markdown_test_cases import get_test_cases
from analyze import analyze_sql


@pytest.mark.parametrize("case", list(get_test_cases("tests/straightforward_cases.md")))
def test_straightforward_cases(case):
    with open("tests/test_data/issue_tracker_schema.json") as f:
        structure = DatabaseStructure.model_validate_json(f.read())
    [sql_input, expected_analysis_json] = case.parameters
    actual_analysis = analyze_sql(structure, sql_input)
    expected_analysis = Analysis.model_validate_json(expected_analysis_json)
    assert actual_analysis == expected_analysis
