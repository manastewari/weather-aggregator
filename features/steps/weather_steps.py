from behave import given, when, then

from tests.support import stub_weather


@given('current weather is available for "{city}"')
def available(context, city):
    stub_weather(context.stub, city)


@given('the city "{city}" does not exist')
def missing(context, city):
    stub_weather(context.stub, city, mode="missing")


@given('the weather provider is unavailable for "{city}"')
def unavailable(context, city):
    stub_weather(context.stub, city, mode="failure")


@when('I fetch weather for "{city}"')
def fetch(context, city):
    context.response = context.client.post("/weather/fetch", params={"city": city})


@then('the response status is {status:d}')
def status(context, status):
    assert context.response.status_code == status, context.response.text


@then('the saved conditions are "{description}" at {temperature:f} degrees')
def conditions(context, description, temperature):
    assert context.response.json()["description"] == description
    assert context.response.json()["temperature"] == temperature


@then('"{city}" has {count:d} stored reading')
@then('"{city}" has {count:d} stored readings')
def history(context, city, count):
    response = context.client.get(f"/weather/{city}")
    assert response.status_code == 200
    assert len(response.json()) == count


@then('the latest reading for "{city}" is the last fetched reading')
def latest(context, city):
    response = context.client.get(f"/weather/{city}/latest")
    assert response.status_code == 200
    assert response.json() == context.response.json()
