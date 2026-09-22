import pytest


@pytest.fixture(scope="session")
def db_url():
    from tests.support import database_url
    with database_url() as url:
        yield url


@pytest.fixture
def full_app(db_url):
    from tests.support import full_application
    with full_application(db_url) as application:
        yield application
