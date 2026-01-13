from datetime import datetime

import httpx

from src.models.Weather import (
    CurrentWeatherData,
    DailyForecastData,
    ForecastResponse,
    WeatherResponse,
)


class WeatherService:
    """Service pour récupérer les données météo depuis Open-Meteo (API gratuite)"""

    def __init__(self):
        # Open-Meteo est gratuit et ne nécessite pas de clé API
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

        # Mapping des codes WMO vers des descriptions en français
        self.wmo_codes = {
            0: "Ciel dégagé",
            1: "Principalement dégagé",
            2: "Partiellement nuageux",
            3: "Couvert",
            45: "Brouillard",
            48: "Brouillard givrant",
            51: "Bruine légère",
            53: "Bruine modérée",
            55: "Bruine dense",
            61: "Pluie légère",
            63: "Pluie modérée",
            65: "Pluie forte",
            71: "Neige légère",
            73: "Neige modérée",
            75: "Neige forte",
            77: "Grains de neige",
            80: "Averses légères",
            81: "Averses modérées",
            82: "Averses violentes",
            85: "Averses de neige légères",
            86: "Averses de neige fortes",
            95: "Orage",
            96: "Orage avec grêle légère",
            99: "Orage avec grêle forte",
        }

    async def _get_coordinates(
        self, city: str, country_code: str | None = None
    ) -> tuple[float, float, str, str]:
        """
        Récupère les coordonnées géographiques d'une ville via l'API de géocodage Open-Meteo

        Returns:
            tuple: (latitude, longitude, city_name, country_code)
        """
        params = {"name": city, "count": 1, "language": "fr", "format": "json"}

        async with httpx.AsyncClient() as client:
            response = await client.get(self.geocoding_url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("results"):
                raise ValueError(f"Ville '{city}' non trouvée")

            result = data["results"][0]
            return (
                result["latitude"],
                result["longitude"],
                result["name"],
                result.get("country_code", ""),
            )

    def _get_weather_description(self, wmo_code: int) -> str:
        """Convertit un code WMO en description textuelle"""
        return self.wmo_codes.get(wmo_code, "Conditions inconnues")

    def _wmo_to_icon(self, wmo_code: int) -> str:
        """Convertit un code WMO en code d'icône (format OpenWeather pour compatibilité)"""
        icon_map = {
            0: "01d",
            1: "02d",
            2: "03d",
            3: "04d",
            45: "50d",
            48: "50d",
            51: "09d",
            53: "09d",
            55: "09d",
            61: "10d",
            63: "10d",
            65: "10d",
            71: "13d",
            73: "13d",
            75: "13d",
            77: "13d",
            80: "09d",
            81: "09d",
            82: "09d",
            85: "13d",
            86: "13d",
            95: "11d",
            96: "11d",
            99: "11d",
        }
        return icon_map.get(wmo_code, "01d")

    async def get_current_weather(
        self, city: str, country_code: str | None = None
    ) -> WeatherResponse:
        """
        Récupère la météo actuelle pour une ville donnée

        Args:
            city: Nom de la ville
            country_code: Code pays ISO optionnel (ex: FR, US)

        Returns:
            WeatherResponse: Données météo actuelles

        Raises:
            httpx.HTTPError: En cas d'erreur lors de l'appel API
        """
        # Récupération des coordonnées
        lat, lon, city_name, country = await self._get_coordinates(city, country_code)

        # Paramètres pour Open-Meteo
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "pressure_msl",
                "wind_speed_10m",
                "weather_code",
            ],
            "timezone": "auto",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.weather_url, params=params)
            response.raise_for_status()
            data = response.json()

        current = data["current"]
        wmo_code = current["weather_code"]

        # Transformation des données en DTO
        weather_data = CurrentWeatherData(
            temperature=current["temperature_2m"],
            feels_like=current["apparent_temperature"],
            humidity=current["relative_humidity_2m"],
            pressure=current["pressure_msl"],
            wind_speed=current["wind_speed_10m"],
            description=self._get_weather_description(wmo_code),
            icon=self._wmo_to_icon(wmo_code),
        )

        return WeatherResponse(
            city=city_name,
            country=country,
            timestamp=datetime.fromisoformat(current["time"]),
            weather=weather_data,
        )

    async def get_forecast(self, city: str, country_code: str | None = None) -> ForecastResponse:
        """
        Récupère les prévisions météo sur 7 jours pour une ville donnée

        Args:
            city: Nom de la ville
            country_code: Code pays ISO optionnel (ex: FR, US)

        Returns:
            ForecastResponse: Prévisions sur 7 jours

        Raises:
            httpx.HTTPError: En cas d'erreur lors de l'appel API
        """
        # Récupération des coordonnées
        lat, lon, city_name, country = await self._get_coordinates(city, country_code)

        # Paramètres pour Open-Meteo
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_probability_max",
                "wind_speed_10m_max",
            ],
            "timezone": "auto",
            "forecast_days": 7,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.weather_url, params=params)
            response.raise_for_status()
            data = response.json()

        daily = data["daily"]

        # Transformation des données en DTO
        forecast_list = []
        for i in range(len(daily["time"])):
            wmo_code = daily["weather_code"][i]

            # Calcul des températures jour/nuit (approximation)
            temp_max = daily["temperature_2m_max"][i]
            temp_min = daily["temperature_2m_min"][i]
            temp_day = (temp_max + temp_min) / 2 + 2  # Approximation jour
            temp_night = (temp_max + temp_min) / 2 - 2  # Approximation nuit

            forecast = DailyForecastData(
                date=daily["time"][i],
                temp_min=temp_min,
                temp_max=temp_max,
                temp_day=temp_day,
                temp_night=temp_night,
                humidity=50,  # Open-Meteo ne fournit pas l'humidité quotidienne moyenne dans l'API gratuite
                wind_speed=daily["wind_speed_10m_max"][i],
                description=self._get_weather_description(wmo_code),
                icon=self._wmo_to_icon(wmo_code),
                precipitation_probability=daily["precipitation_probability_max"][i],
            )
            forecast_list.append(forecast)

        return ForecastResponse(
            city=city_name,
            country=country,
            forecast=forecast_list,
        )


# Instance singleton du service
weather_service = WeatherService()
