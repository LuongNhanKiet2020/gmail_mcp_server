# weather.py — Vietnam Weather MCP Server (proper MCP protocol via stdio)
import httpx
from mcp.server.fastmcp import FastMCP

# ─── MCP Server ───────────────────────────────────────────────────────
mcp = FastMCP("Vietnam Weather MCP Server")

# ─── WMO Weather Code Mapping ────────────────────────────────────────
WMO_CODES = {
    0: "Trời quang đãng ☀️",
    1: "Chủ yếu quang đãng 🌤️",
    2: "Có mây một phần ⛅",
    3: "Nhiều mây ☁️",
    45: "Sương mù 🌫️",
    48: "Sương mù đóng băng 🌫️❄️",
    51: "Mưa phùn nhẹ 🌦️",
    53: "Mưa phùn vừa 🌦️",
    55: "Mưa phùn dày 🌧️",
    61: "Mưa nhẹ 🌧️",
    63: "Mưa vừa 🌧️",
    65: "Mưa to 🌧️💧",
    71: "Tuyết nhẹ ❄️",
    73: "Tuyết vừa ❄️",
    75: "Tuyết dày ❄️❄️",
    80: "Mưa rào nhẹ 🌦️",
    81: "Mưa rào vừa 🌧️",
    82: "Mưa rào nặng ⛈️",
    95: "Giông bão ⛈️⚡",
    96: "Giông bão kèm mưa đá nhẹ ⛈️🧊",
    99: "Giông bão kèm mưa đá nặng ⛈️🧊💨",
}


def _get_weather_description(code: int) -> str:
    """Convert WMO weather code to Vietnamese description."""
    return WMO_CODES.get(code, f"Mã thời tiết: {code}")


# ─── MCP Tools ────────────────────────────────────────────────────────

@mcp.tool()
def get_weather(city: str = "Ho Chi Minh City") -> str:
    """
    Get current weather for a city (optimized for Vietnamese cities).
    Returns temperature, humidity, wind speed, and weather condition.
    Examples: "Ha Noi", "Ho Chi Minh City", "Da Nang", "Hue"
    """
    try:
        with httpx.Client(timeout=10) as client:
            # Step 1: Geocode the city name
            geocode_resp = client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "vi"}
            )
            geocode_data = geocode_resp.json()

            if not geocode_data.get("results"):
                return f"❌ Không tìm thấy thành phố: {city}"

            location = geocode_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location.get("name", city)
            country = location.get("country", "")

            # Step 2: Fetch weather data
            weather_resp = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature",
                    "timezone": "Asia/Bangkok",
                }
            )
            weather_data = weather_resp.json()
            current = weather_data["current"]

            temp = current["temperature_2m"]
            feels_like = current["apparent_temperature"]
            humidity = current["relative_humidity_2m"]
            wind_speed = current["wind_speed_10m"]
            weather_code = current["weather_code"]
            condition = _get_weather_description(weather_code)

            return (
                f"🌍 Thời tiết tại {city_name}, {country}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌡️  Nhiệt độ: {temp}°C (cảm giác {feels_like}°C)\n"
                f"💧 Độ ẩm: {humidity}%\n"
                f"💨 Gió: {wind_speed} km/h\n"
                f"🌤️  Trạng thái: {condition}\n"
            )

    except httpx.TimeoutException:
        return "❌ Timeout: API thời tiết không phản hồi. Vui lòng thử lại."
    except Exception as e:
        return f"❌ Lỗi khi lấy thời tiết: {e}"


@mcp.tool()
def get_weather_forecast(city: str = "Ho Chi Minh City", days: int = 3) -> str:
    """
    Get weather forecast for the next N days (max 7).
    Returns daily max/min temperature and weather condition.
    """
    days = min(days, 7)
    try:
        with httpx.Client(timeout=10) as client:
            # Geocode
            geocode_resp = client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "vi"}
            )
            geocode_data = geocode_resp.json()

            if not geocode_data.get("results"):
                return f"❌ Không tìm thấy thành phố: {city}"

            location = geocode_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location.get("name", city)

            # Forecast
            weather_resp = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                    "timezone": "Asia/Bangkok",
                    "forecast_days": days,
                }
            )
            data = weather_resp.json()["daily"]

            lines = [f"📅 Dự báo {days} ngày tại {city_name}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
            for i in range(len(data["time"])):
                date = data["time"][i]
                t_max = data["temperature_2m_max"][i]
                t_min = data["temperature_2m_min"][i]
                code = data["weather_code"][i]
                condition = _get_weather_description(code)
                lines.append(f"  {date}: {t_min}°C – {t_max}°C | {condition}")

            return "\n".join(lines)

    except httpx.TimeoutException:
        return "❌ Timeout: API thời tiết không phản hồi."
    except Exception as e:
        return f"❌ Lỗi khi lấy dự báo: {e}"


# ─── Entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")