import httpx
from fastapi import APIRouter, HTTPException, Query
from prometheus_client import Counter

from src.models.Weather import ForecastResponse, WeatherResponse
from src.services.weather_service import weather_service

pau_search_counter = Counter(
    "pau_weather_searches_total", "Total number of weather searches for Pau"
)

city_search_counter = Counter(
    "city_weather_searches_total", "Total number of weather searches by city", ["city"]
)

router = APIRouter(prefix="/api/weather", tags=["Weather"])


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    city: str = Query(..., description="Nom de la ville"),
    country_code: str | None = Query(None, description="Code pays (ex: FR, US)"),
):
    """Récupère la météo actuelle pour une ville donnée"""

    if city.lower() == "pau":
        pau_search_counter.inc()

    city_search_counter.labels(city=city.lower()).inc()

    try:
        weather_data = await weather_service.get_current_weather(city, country_code)
        return weather_data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Ville '{city}' non trouvée. Vérifiez l'orthographe ou ajoutez le code pays.",
            ) from e
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erreur lors de la récupération des données météo: {str(e)}",
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur de connexion à l'API météo: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}") from e


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    city: str = Query(..., description="Nom de la ville"),
    country_code: str | None = Query(None, description="Code pays (ex: FR, US)"),
):
    """Récupère les prévisions météo pour une ville donnée"""

    if city.lower() == "pau":
        pau_search_counter.inc()

    city_search_counter.labels(city=city.lower()).inc()

    try:
        forecast_data = await weather_service.get_forecast(city, country_code)
        return forecast_data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Ville '{city}' non trouvée. Vérifiez l'orthographe ou ajoutez le code pays.",
            ) from e
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erreur lors de la récupération des prévisions météo: {str(e)}",
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur de connexion à l'API météo: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {str(e)}") from e
