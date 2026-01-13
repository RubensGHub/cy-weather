from datetime import datetime
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from main import app
from src.models.Weather import (
    CurrentWeatherData,
    DailyForecastData,
    ForecastResponse,
    WeatherResponse,
)

client = TestClient(app)


class TestCurrentWeatherEndpoint:
    """Tests pour l'endpoint /api/weather/current"""

    @patch("src.resources.weather_resource.weather_service.get_current_weather")
    def test_get_current_weather_success(self, mock_get_weather):
        """Test récupération météo actuelle avec succès"""
        mock_get_weather.return_value = WeatherResponse(
            city="Paris",
            country="FR",
            timestamp=datetime.now(),
            weather=CurrentWeatherData(
                temperature=15.5,
                feels_like=14.2,
                humidity=75,
                pressure=1013.2,
                wind_speed=12.5,
                description="Partiellement nuageux",
                icon="02d",
            ),
        )

        response = client.get("/api/weather/current?city=Paris")

        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Paris"
        assert data["country"] == "FR"
        assert data["weather"]["temperature"] == 15.5


class TestForecastEndpoint:
    """Tests pour l'endpoint /api/weather/forecast"""

    @patch("src.resources.weather_resource.weather_service.get_forecast")
    def test_get_forecast_success(self, mock_get_forecast):
        """Test récupération prévisions avec succès"""
        mock_get_forecast.return_value = ForecastResponse(
            city="Lyon",
            country="FR",
            forecast=[
                DailyForecastData(
                    date="2026-01-13",
                    temp_max=18.0,
                    temp_min=8.0,
                    temp_day=15.0,
                    temp_night=10.0,
                    feels_like_day=14.0,
                    feels_like_night=9.0,
                    humidity=65.0,
                    precipitation_probability=20,
                    wind_speed=10.5,
                    description="Ciel dégagé",
                    icon="01d",
                )
            ],
        )

        response = client.get("/api/weather/forecast?city=Lyon")

        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Lyon"
        assert len(data["forecast"]) == 1
        assert data["forecast"][0]["temp_max"] == 18.0

    @patch("src.resources.weather_resource.weather_service.get_forecast")
    def test_get_forecast_multiple_days(self, mock_get_forecast):
        """Test prévisions sur plusieurs jours"""
        mock_get_forecast.return_value = ForecastResponse(
            city="Marseille",
            country="FR",
            forecast=[
                DailyForecastData(
                    date=f"2026-01-{13 + i}",
                    temp_max=18.0 + i,
                    temp_min=8.0 + i,
                    temp_day=15.0,
                    temp_night=10.0,
                    feels_like_day=14.0,
                    feels_like_night=9.0,
                    humidity=65.0,
                    precipitation_probability=20,
                    wind_speed=10.5,
                    description="Ciel dégagé",
                    icon="01d",
                )
                for i in range(7)
            ],
        )

        response = client.get("/api/weather/forecast?city=Marseille")

        assert response.status_code == 200
        data = response.json()
        assert len(data["forecast"]) == 7


class TestPrometheusCounters:
    """Tests pour les compteurs Prometheus"""

    @patch("src.resources.weather_resource.weather_service.get_current_weather")
    def test_pau_counter_increments(self, mock_get_weather):
        """Test que le compteur Pau s'incrémente"""
        from src.resources.weather_resource import pau_search_counter

        mock_get_weather.return_value = WeatherResponse(
            city="Pau",
            country="FR",
            timestamp=datetime.now(),
            weather=CurrentWeatherData(
                temperature=15.5,
                feels_like=14.2,
                humidity=75,
                pressure=1013.2,
                wind_speed=12.5,
                description="Ciel dégagé",
                icon="01d",
            ),
        )

        initial_count = pau_search_counter._value._value
        client.get("/api/weather/current?city=Pau")
        assert pau_search_counter._value._value == initial_count + 1


class TestErrorHandling:
    """Tests pour la gestion d'erreurs"""

    @patch("src.resources.weather_resource.weather_service.get_current_weather")
    def test_city_not_found_404(self, mock_get_weather):
        """Test erreur 404 quand la ville n'existe pas"""

        mock_response = httpx.Response(404, json={})
        mock_get_weather.side_effect = httpx.HTTPStatusError(
            "Not found",
            request=httpx.Request("GET", "http://test"),
            response=mock_response,
        )

        response = client.get("/api/weather/current?city=VilleInexistante")

        assert response.status_code == 404
        assert "non trouvée" in response.json()["detail"]
