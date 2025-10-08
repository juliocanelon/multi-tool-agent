from google.adk.agents import Agent
import requests


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city: Name of the city to retrieve weather information for.

    Returns:
        dict: A dictionary containing the weather information with a 'status' key ('success' or 'error') and a 'report' key with the weather details if successful, or an 'error_message' if an error occurred.
    """

    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        payload = response.json()

        current_conditions = payload["current_condition"][0]
        description = current_conditions["weatherDesc"][0]["value"]
        temperature_c = current_conditions["temp_C"]
        temperature_f = current_conditions["temp_F"]
        feels_like_c = current_conditions["FeelsLikeC"]
        humidity = current_conditions["humidity"]

        report = (
            f"The weather in {city} is {description.lower()} with a temperature of "
            f"{temperature_c}°C ({temperature_f}°F). It feels like {feels_like_c}°C with "
            f"a humidity of {humidity}%."
        )

        return {"status": "success", "report": report}
    except requests.RequestException as exc:
        return {
            "status": "error",
            "error_message": f"Unable to retrieve weather information for '{city}'. {exc}"
        }
    except (KeyError, IndexError, ValueError) as exc:
        return {
            "status": "error",
            "error_message": (
                f"Received an unexpected weather response for '{city}'. Please try again later. Details: {exc}"
            ),
        }

def get_current_time(city:str) -> dict:
    """Returns the current time in a specified city.

    Args:
        dict: A dictionary containing the current time for a specified city information with a 'status' key ('success' or 'error') and a 'report' key with the current time details in a city if successful, or an 'error_message' if an error occurred.
    """
    import datetime
    from zoneinfo import ZoneInfo

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {"status": "error",
                "error_message": f"Sorry, I don't have timezone information for {city}."}

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return {"status": "success",
            "report": f"""The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}"""}

root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the time and weather in a city.",
    instruction="I can answer your questions about the time and weather in a city.",
    tools=[get_weather, get_current_time]
)