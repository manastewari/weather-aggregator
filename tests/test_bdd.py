from behave.__main__ import main
import pytest

pytestmark = pytest.mark.bdd


def test_behave_scenarios(db_url):
    assert main(["features", "--no-capture", "--define", f"database_url={db_url}"]) == 0
