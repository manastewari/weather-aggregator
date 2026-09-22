from contextlib import ExitStack

from tests.support import database_url, full_application


def before_all(context):
    context.infrastructure = ExitStack()
    context.add_cleanup(context.infrastructure.close)
    # Pytest passes its existing Testcontainers URL; standalone Behave uses the same factory.
    context.db_url = context.config.userdata.get("database_url")
    if not context.db_url:
        context.db_url = context.infrastructure.enter_context(database_url())


def before_scenario(context, scenario):
    stack = ExitStack()
    context.add_cleanup(stack.close)
    context.client, context.stub = stack.enter_context(full_application(context.db_url))
