from flask import Flask, request, jsonify, send_file
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# .env load करो
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY .env file में नहीं मिली!")


# -----------------------------
# Unix timestamp को local time में बदलना
# -----------------------------
def format_time(timestamp, timezone_offset=0):

    local_time = datetime.fromtimestamp(
        timestamp,
        timezone.utc
    ) + timedelta(seconds=timezone_offset)

    return local_time.strftime("%I:%M %p")


# -----------------------------
# Wind direction
# -----------------------------
def wind_direction(degree):

    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]

    index = round(degree / 22.5) % 16

    return directions[index]


# -----------------------------
# Home page
# -----------------------------
@app.route("/")
def home():

    return send_file("index.html")


# -----------------------------
# Weather API
# -----------------------------
@app.route("/weather")
def weather():

    city = request.args.get("city", "").strip()

    if not city:

        return jsonify({
            "error": "Please enter a city name."
        }), 400


    # -----------------------------
    # 1. City → Coordinates
    # -----------------------------

    geo_url = "https://api.openweathermap.org/geo/1.0/direct"

    geo_params = {
        "q": city,
        "limit": 1,
        "appid": API_KEY
    }

    geo_response = requests.get(
        geo_url,
        params=geo_params,
        timeout=10
    )


    if geo_response.status_code != 200:

        return jsonify({
            "error": "Unable to find location."
        }), 500


    locations = geo_response.json()


    if not locations:

        return jsonify({
            "error": "City not found."
        }), 404


    location = locations[0]

    lat = location["lat"]
    lon = location["lon"]

    location_name = location.get("name", city)
    state = location.get("state", "")
    country = location.get("country", "")


    # -----------------------------
    # 2. Coordinates → Weather
    # -----------------------------

    weather_url = "https://api.openweathermap.org/data/2.5/weather"

    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
        "lang": "en"
    }


    weather_response = requests.get(
        weather_url,
        params=weather_params,
        timeout=10
    )


    if weather_response.status_code != 200:

        return jsonify({
            "error": "Unable to get weather data."
        }), weather_response.status_code


    data = weather_response.json()


    # -----------------------------
    # Basic weather
    # -----------------------------

    weather = data["weather"][0]

    main = data["main"]

    wind = data.get("wind", {})

    clouds = data.get("clouds", {})

    sys = data.get("sys", {})


    # -----------------------------
    # Rain
    # -----------------------------

    rain = data.get("rain", {})

    rain_1h = rain.get("1h", 0)

    rain_3h = rain.get("3h", 0)


    # -----------------------------
    # Snow
    # -----------------------------

    snow = data.get("snow", {})

    snow_1h = snow.get("1h", 0)

    snow_3h = snow.get("3h", 0)


    # -----------------------------
    # Wind
    # -----------------------------

    wind_speed = wind.get("speed", 0)

    wind_degree = wind.get("deg", 0)

    wind_gust = wind.get("gust", 0)


    # -----------------------------
    # Timezone
    # -----------------------------

    timezone_offset = data.get("timezone", 0)


    # -----------------------------
    # Final data
    # -----------------------------

    result = {

        # Location
        "city": location_name,
        "state": state,
        "country": country,

        "latitude": lat,
        "longitude": lon,

        # Weather
        "condition": weather.get("main", "N/A"),
        "description": weather.get("description", "N/A"),
        "icon": weather.get("icon", ""),

        # Temperature
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "temp_min": main.get("temp_min"),
        "temp_max": main.get("temp_max"),

        # Atmosphere
        "pressure": main.get("pressure"),
        "humidity": main.get("humidity"),
        "sea_level": main.get("sea_level"),
        "ground_level": main.get("grnd_level"),

        # Visibility
        "visibility": data.get("visibility", 0),

        # Clouds
        "cloudiness": clouds.get("all", 0),

        # Wind
        "wind_speed": wind_speed,
        "wind_degree": wind_degree,
        "wind_direction": wind_direction(wind_degree),
        "wind_gust": wind_gust,

        # Rain
        "rain_1h": rain_1h,
        "rain_3h": rain_3h,

        # Snow
        "snow_1h": snow_1h,
        "snow_3h": snow_3h,

        # Time
        "sunrise": format_time(
            sys.get("sunrise", 0),
            timezone_offset
        ) if sys.get("sunrise") else "N/A",

        "sunset": format_time(
            sys.get("sunset", 0),
            timezone_offset
        ) if sys.get("sunset") else "N/A",

        "local_time": format_time(
            data.get("dt", 0),
            timezone_offset
        ) if data.get("dt") else "N/A",

        "timezone": timezone_offset,

        # Weather icon
        "icon_url": (
            f"https://openweathermap.org/img/wn/"
            f"{weather.get('icon', '01d')}@2x.png"
        )
    }


    return jsonify(result)


# -----------------------------
# Start server
# -----------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
        )