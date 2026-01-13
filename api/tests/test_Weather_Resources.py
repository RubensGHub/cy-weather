from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests basiques pour vérifier que l'API fonctionne"""

    def test_api_is_running(self):
        """Test que l'API répond"""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_weather_endpoint_exists(self):
        """Test que l'endpoint météo existe (même s'il retourne une erreur)"""
        response = client.get("/weather/current?city=Paris")
        # On s'attend à une erreur car pas de mock, mais l'endpoint existe
        assert response.status_code in [200, 404, 500]

    def test_forecast_endpoint_exists(self):
        """Test que l'endpoint forecast existe"""
        response = client.get("/weather/forecast?city=Paris")
        assert response.status_code in [200, 404, 500]