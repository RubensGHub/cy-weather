from datetime import datetime

from pydantic import BaseModel, Field


class WeatherRequest(BaseModel):
    """DTO pour la requête météo"""

    city: str = Field(..., description="Nom de la ville", min_length=1)
    country_code: str | None = Field(None, description="Code pays ISO (ex: FR, US)")


class CurrentWeatherData(BaseModel):
    """Données météo actuelles"""

    temperature: float = Field(..., description="Température en degrés Celsius")
    feels_like: float = Field(..., description="Température ressentie en degrés Celsius")
    humidity: float = Field(..., description="Humidité en pourcentage")
    pressure: float = Field(..., description="Pression atmosphérique en hPa")
    wind_speed: float = Field(..., description="Vitesse du vent en m/s")
    description: str = Field(..., description="Description des conditions météo")
    icon: str = Field(..., description="Code de l'icône météo")


class WeatherResponse(BaseModel):
    """DTO pour la réponse météo actuelle"""

    city: str = Field(..., description="Nom de la ville")
    country: str = Field(..., description="Code pays")
    timestamp: datetime = Field(..., description="Horodatage de la donnée")
    weather: CurrentWeatherData


class DailyForecastData(BaseModel):
    """Données météo pour une journée"""

    date: str = Field(..., description="Date au format YYYY-MM-DD")
    temp_min: float = Field(..., description="Température minimale en degrés Celsius")
    temp_max: float = Field(..., description="Température maximale en degrés Celsius")
    temp_day: float = Field(..., description="Température en journée en degrés Celsius")
    temp_night: float = Field(..., description="Température nocturne en degrés Celsius")
    humidity: float = Field(..., description="Humidité moyenne en pourcentage")
    wind_speed: float = Field(..., description="Vitesse du vent en m/s")
    description: str = Field(..., description="Description des conditions météo")
    icon: str = Field(..., description="Code de l'icône météo")
    precipitation_probability: float | None = Field(
        None, description="Probabilité de précipitations en pourcentage"
    )


class ForecastResponse(BaseModel):
    """DTO pour la réponse prévisions 7 jours"""

    city: str = Field(..., description="Nom de la ville")
    country: str = Field(..., description="Code pays")
    forecast: list[DailyForecastData] = Field(
        ..., description="Liste des prévisions pour les 7 prochains jours"
    )
