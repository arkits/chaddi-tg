import traceback

import requests
from loguru import logger
from openai import OpenAI
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.domain import config, dc

app_config = config.get_config()

# Initialize OpenAI client for funny descriptions
openai_client = OpenAI(api_key=app_config.get("OPENAI", "API_KEY"))
OPENAI_MODEL = app_config.get("AI", "OPENAI_MODEL", fallback="gpt-5-nano-2025-08-07")

# OpenWeatherMap API key (will be added to config)
WEATHER_API_KEY = app_config.get("WEATHER", "API_KEY", fallback=None)
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("weather", update)

        # Extract location from message
        location = None

        # Check for text in command args
        if context.args:
            location = " ".join(context.args)

        # Check for reply to message
        if not location and update.message.reply_to_message:
            reply_message = update.message.reply_to_message
            if reply_message.text:
                location = reply_message.text
            elif reply_message.caption:
                location = reply_message.caption

        # Check for caption in current message
        if not location and update.message.caption:
            caption = update.message.caption
            location = (
                caption[8:].strip() if caption.startswith("/weather") else caption
            )

        if not location or location.strip() == "":
            await update.message.reply_text(
                "Please provide a location. Usage: `/weather <location>` or reply to a message with `/weather`.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        location = location.strip()
        logger.info(f"[weather] location={location}")

        if not WEATHER_API_KEY:
            await update.message.reply_text(
                "Weather API key is not configured. Please add WEATHER_API_KEY to your config.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Send initial message
        sent_message = await update.message.reply_text("Fetching weather data...")

        try:
            # Get weather data from OpenWeatherMap API
            params = {
                "q": location,
                "appid": WEATHER_API_KEY,
                "units": "metric",  # Use metric units (Celsius, m/s)
            }

            response = requests.get(WEATHER_API_URL, params=params, timeout=10)
            response.raise_for_status()

            weather_data = response.json()

            # Extract weather information
            description = weather_data["weather"][0]["description"]
            temp = weather_data["main"]["temp"]
            humidity = weather_data["main"]["humidity"]
            wind_speed = weather_data["wind"]["speed"]

            # Get AQI if available (from air_pollution API)
            aqi = None
            try:
                lat = weather_data["coord"]["lat"]
                lon = weather_data["coord"]["lon"]
                aqi_url = "https://api.openweathermap.org/data/2.5/air_pollution"
                aqi_params = {
                    "lat": lat,
                    "lon": lon,
                    "appid": WEATHER_API_KEY,
                }
                aqi_response = requests.get(aqi_url, params=aqi_params, timeout=10)
                if aqi_response.status_code == 200:
                    aqi_data = aqi_response.json()
                    aqi = aqi_data["list"][0]["main"]["aqi"]
            except Exception as e:
                logger.warning(f"[weather] Could not fetch AQI: {e}")

            funny_description = await _generate_funny_description(description)

            # Format the response
            response_text = f"{funny_description}\n"
            response_text += f"🌡️ Temperature: {temp:.1f} °C\n"
            response_text += f"💦 Humidity: {humidity:.1f}%\n"
            response_text += f"💨 Wind: {wind_speed:.1f} m/s"

            if aqi is not None:
                response_text += f"\n🛰 AQI: {aqi}"

            await sent_message.edit_text(response_text)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                await sent_message.edit_text(
                    f"Location '{location}' not found. Please check the location name and try again."
                )
            else:
                logger.error(f"[weather] HTTP error: {e}")
                await sent_message.edit_text(
                    f"Error fetching weather data: {e.response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logger.error(f"[weather] Request error: {e}")
            await sent_message.edit_text(
                "Error connecting to weather service. Please try again later."
            )
        except KeyError as e:
            logger.error(f"[weather] Missing data in API response: {e}")
            await sent_message.edit_text(
                "Error parsing weather data. Please try again later."
            )
        except Exception as e:
            logger.error(
                f"[weather] Error processing weather: {e}\n{traceback.format_exc()}"
            )
            await sent_message.edit_text(f"Error processing weather data: {str(e)}")

    except Exception as e:
        logger.error(
            f"Caught Error in weather.handle - {e} \n {traceback.format_exc()}"
        )
        await update.message.reply_text(
            "Something went wrong while processing your request."
        )


async def _generate_funny_description(weather_description: str) -> str:
    """Generate a funny rude description of the weather using LLM"""
    try:
        prompt = f"""Convert this weather description into a funny, rude, and sarcastic one-liner. Keep it short (1 sentence max) and make it entertaining.

Weather description: "{weather_description}"

Funny rude description:"""

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a sarcastic weather reporter who makes rude and funny comments about the weather. Keep responses to one sentence.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.8,
        )

        funny_desc = response.choices[0].message.content.strip()
        # Remove quotes if present
        funny_desc = funny_desc.strip('"').strip("'")
        return funny_desc

    except Exception as e:
        logger.warning(f"[weather] Failed to generate funny description: {e}")
        # Fallback to original description with a prefix
        return f"Probably {weather_description} or something"
