Feature: Save and revisit current weather
  Scenario: Fetch and save current conditions
    Given current weather is available for "timisoara"
    When I fetch weather for "timisoara"
    Then the response status is 201
    And the saved conditions are "Overcast" at 22.4 degrees
    And "timisoara" has 1 stored reading

  Scenario: Latest reading is the most recently fetched
    Given current weather is available for "timisoara"
    When I fetch weather for "timisoara"
    And I fetch weather for "timisoara"
    Then "timisoara" has 2 stored readings
    And the latest reading for "timisoara" is the last fetched reading

  Scenario: Unknown city does not create a reading
    Given the city "atlantis" does not exist
    When I fetch weather for "atlantis"
    Then the response status is 404
    And "atlantis" has 0 stored readings

  Scenario: Provider outage does not create a reading
    Given the weather provider is unavailable for "timisoara"
    When I fetch weather for "timisoara"
    Then the response status is 502
    And "timisoara" has 0 stored readings
