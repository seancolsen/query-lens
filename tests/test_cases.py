import json

import pytest

from utils.markdown_test_cases import get_test_cases
from analyze import analyze_sql


@pytest.mark.parametrize("case", list(get_test_cases("tests/test_cases.md")))
def test_cases(case):
    [sql, analysis_json] = case.parameters
    assert analyze_sql(None, sql) == json.loads(analysis_json)
