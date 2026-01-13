import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from src.services.weather_service import WeatherService, weather_service
from src.models.Weather import WeatherResponse, ForecastResponse
import httpx


@pytest.fixture
def service():
    """Fixture pour créer une instance du service météo"""
    return WeatherService()


@pytest.fixture
def mock_geocoding_response():
    """Mock de réponse API de géocodage"""
    return {
        "results": [
            {
                "latitude": 43.2964,
                "longitude": -0.3701,
                "name": "Pau",
                "country_code": "FR"
            }
        ]
    }


@pytest.fixture
def mock_current_weather_response():
    """Mock de réponse API météo actuelle"""
    return {
        "current": {
            "time": "2026-01-13T10:00:00",
            "temperature_2m": 15.5,
            "apparent_temperature": 14.2,
            "relative_humidity_2m": 75,
            "pressure_msl": 1013.2,
            "wind_speed_10m": 12.5,
            "weather_code": 2
        }
    }


@pytest.fixture
def mock_forecast_response():
    """Mock de réponse API prévisions"""
    return {
        "daily": {
            "time": ["2026-01-13", "2026-01-14", "2026-01-15"],
            "weather_code": [0, 61, 95],
            "temperature_2m_max": [18.0, 16.5, 14.2],
            "temperature_2m_min": [8.0, 10.2, 9.5],
            "apparent_temperature_max": [17.0, 15.5, 13.0],
            "apparent_temperature_min": [7.0, 9.0, 8.5],
            "precipitation_probability_max": [10, 80, 95],
            "wind_speed_10m_max": [15.0, 20.5, 25.0]
        }
    }


class TestWeatherServiceInit:
    """Tests pour l'initialisation du service"""

    def test_service_initialization(self, service):
        """Test que le service s'initialise correctement"""
        assert service.geocoding_url == "https://geocoding-api.open-meteo.com/v1/search"
        assert service.weather_url == "https://api.open-meteo.com/v1/forecast"
        assert isinstance(service.wmo_codes, dict)
        assert len(service.wmo_codes) > 0

    def test_singleton_instance(self):
        """Test que l'instance singleton existe"""
        assert weather_service is not None
        assert isinstance(weather_service, WeatherService)


class TestWMOCodeMapping:
    """Tests pour le mapping des codes WMO"""

    def test_get_weather_description_clear_sky(self, service):
        """Test description pour ciel dégagé"""
        assert service._get_weather_description(0) == "Ciel dégagé"

    def test_get_weather_description_rain(self, service):
        """Test description pour pluie"""
        assert service._get_weather_description(61) == "Pluie légère"
        assert service._get_weather_description(63) == "Pluie modérée"

    def test_get_weather_description_thunderstorm(self, service):
        """Test description pour orage"""
        assert service._get_weather_description(95) == "Orage"

    def test_get_weather_description_unknown(self, service):
        """Test description pour code inconnu"""
        assert service._get_weather_description(999) == "Conditions inconnues"

    def test_wmo_to_icon_mapping(self, service):
        """Test conversion code WMO vers icône"""
        assert service._wmo_to_icon(0) == "01d"
        assert service._wmo_to_icon(61) == "10d"
        assert service._wmo_to_icon(95) == "11d"
        assert service._wmo_to_icon(999) == "01d"  # Default


class TestGetCoordinates:
    """Tests pour la récupération des coordonnées"""

    @pytest.mark.asyncio
    async def test_get_coordinates_success(self, service, mock_geocoding_response):
        """Test récupération des coordonnées avec succès"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_geocoding_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            lat, lon, city, country = await service._get_coordinates("Pau")

            assert lat == 43.2964
            assert lon == -0.3701
            assert city == "Pau"
            assert country == "FR"

    @pytest.mark.asyncio
    async def test_get_coordinates_city_not_found(self, service):
        """Test quand la ville n'est pas trouvée"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"results": []}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="Ville .* non trouvée"):
                await service._get_coordinates("VilleInexistante")

    @pytest.mark.asyncio
    async def test_get_coordinates_api_error(self, service):
        """Test gestion erreur API"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.HTTPError("API Error")

            with pytest.raises(httpx.HTTPError):
                await service._get_coordinates("Paris")


class TestGetCurrentWeather:
    """Tests pour récupérer la météo actuelle"""

    @pytest.mark.asyncio
    async def test_get_current_weather_success(
        self, service, mock_geocoding_response, mock_current_weather_response
    ):
        """Test récupération météo actuelle avec succès"""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Premier appel : géocodage
            mock_geo_response = MagicMock()
            mock_geo_response.json.return_value = mock_geocoding_response
            mock_geo_response.raise_for_status = MagicMock()

            # Deuxième appel : météo
            mock_weather_response = MagicMock()
            mock_weather_response.json.return_value = mock_current_weather_response
            mock_weather_response.raise_for_status = MagicMock()

            mock_get.side_effect = [mock_geo_response, mock_weather_response]

            result = await service.get_current_weather("Pau")

            assert isinstance(result, WeatherResponse)
            assert result.city == "Pau"
            assert result.country == "FR"
            assert result.weather.temperature == 15.5
            assert result.weather.humidity == 75
            assert result.weather.description == "Partiellement nuageux"

    @pytest.mark.asyncio
    async def test_get_current_weather_with_country_code(
        self, service, mock_geocoding_response, mock_current_weather_response
    ):
        """Test récupération météo avec code pays"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_geo_response = MagicMock()
            mock_geo_response.json.return_value = mock_geocoding_response
            mock_geo_response.raise_for_status = MagicMock()

            mock_weather_response = MagicMock()
            mock_weather_response.json.return_value = mock_current_weather_response
            mock_weather_response.raise_for_status = MagicMock()

            mock_get.side_effect = [mock_geo_response, mock_weather_response]

            result = await service.get_current_weather("Pau", "FR")

            assert result.city == "Pau"
            assert result.country == "FR"


class TestGetForecast:
    """Tests pour récupérer les prévisions météo"""

    @pytest.mark.asyncio
    async def test_get_forecast_success(
        self, service, mock_geocoding_response, mock_forecast_response
    ):
        """Test récupération prévisions avec succès"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_geo_response = MagicMock()
            mock_geo_response.json.return_value = mock_geocoding_response
            mock_geo_response.raise_for_status = MagicMock()

            mock_weather_response = MagicMock()
            mock_weather_response.json.return_value = mock_forecast_response
            mock_weather_response.raise_for_status = MagicMock()

            mock_get.side_effect = [mock_geo_response, mock_weather_response]

            result = await service.get_forecast("Pau")

            assert isinstance(result, ForecastResponse)
            assert result.city == "Pau"
            assert result.country == "FR"
            assert len(result.forecast) == 3
            assert result.forecast[0].date == "2026-01-13"
            assert result.forecast[0].temp_max == 18.0
            assert result.forecast[0].temp_min == 8.0
            assert result.forecast[0].precipitation_probability == 10

    @pytest.mark.asyncio
    async def test_get_forecast_temperature_calculations(
        self, service, mock_geocoding_response, mock_forecast_response
    ):
        """Test calcul des températures jour/nuit"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_geo_response = MagicMock()
            mock_geo_response.json.return_value = mock_geocoding_response
            mock_geo_response.raise_for_status = MagicMock()

            mock_weather_response = MagicMock()
            mock_weather_response.json.return_value = mock_forecast_response
            mock_weather_response.raise_for_status = MagicMock()

            mock_get.side_effect = [mock_geo_response, mock_weather_response]

            result = await service.get_forecast("Pau")

            # Vérifier que temp_day > temp_night
            assert result.forecast[0].temp_day > result.forecast[0].temp_night
            # Vérifier que les températures sont dans un intervalle raisonnable
            assert result.forecast[0].temp_min < result.forecast[0].temp_day < result.forecast[0].temp_max