from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.models.Weather import WeatherRequest, WeatherResponse, ForecastResponse
from src.services.weather_service import weather_service
import httpx


# Router pour les endpoints météo
router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    city: str = Query(..., description="Nom de la ville", min_length=1),
    country_code: Optional[str] = Query(
        None, description="Code pays ISO (ex: FR, US)", max_length=2
    ),
):
    """
    Récupère la météo actuelle pour une ville donnée.

    Args:
        city: Nom de la ville
        country_code: Code pays ISO optionnel (ex: FR, US)

    Returns:
        WeatherResponse: Données météo actuelles avec température, humidité, etc.

    Raises:
        HTTPException: 404 si la ville n'est pas trouvée, 500 en cas d'erreur serveur
    """
    try:
        weather_data = await weather_service.get_current_weather(city, country_code)
        return weather_data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Ville '{city}' non trouvée. Vérifiez l'orthographe ou ajoutez le code pays.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erreur lors de la récupération des données météo: {str(e)}",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur de connexion à l'API météo: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur interne du serveur: {str(e)}"
        )


@router.get("/forecast", response_model=ForecastResponse)
async def get_weather_forecast(
    city: str = Query(..., description="Nom de la ville", min_length=1),
    country_code: Optional[str] = Query(
        None, description="Code pays ISO (ex: FR, US)", max_length=2
    ),
):
    """
    Récupère les prévisions météo sur 7 jours pour une ville donnée.

    Args:
        city: Nom de la ville
        country_code: Code pays ISO optionnel (ex: FR, US)

    Returns:
        ForecastResponse: Prévisions météo pour les 7 prochains jours avec températures min/max,
                         humidité, vitesse du vent, etc.

    Raises:
        HTTPException: 404 si la ville n'est pas trouvée, 500 en cas d'erreur serveur
    """
    try:
        forecast_data = await weather_service.get_forecast(city, country_code)
        return forecast_data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Ville '{city}' non trouvée. Vérifiez l'orthographe ou ajoutez le code pays.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erreur lors de la récupération des prévisions météo: {str(e)}",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur de connexion à l'API météo: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur interne du serveur: {str(e)}"
        )
