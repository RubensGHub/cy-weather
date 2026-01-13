from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests pour l'endpoint /api/health"""

    def test_health_check_success(self):
        """Test que l'endpoint health retourne un statut OK"""
        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAppConfiguration:
    """Tests pour la configuration de l'application"""

    def test_app_metadata(self):
        """Test que les métadonnées de l'application sont correctes"""
        assert app.title == "CY Weather API"
        assert app.version == "0.1.0"


class TestPrometheusMetrics:
    """Tests pour l'endpoint des métriques Prometheus"""

    def test_metrics_endpoint_exists(self):
        """Test que l'endpoint /metrics existe"""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestOpenAPISchema:
    """Tests pour le schéma OpenAPI"""

    def test_openapi_schema_accessible(self):
        """Test que le schéma OpenAPI est accessible"""
        response = client.get("/api/openapi.json")

        assert response.status_code == 200
        assert response.json()["info"]["title"] == "CY Weather API"


class TestErrorHandling:
    """Tests pour la gestion des erreurs"""

    def test_404_on_invalid_endpoint(self):
        """Test qu'un endpoint invalide retourne 404"""
        response = client.get("/api/invalid-endpoint")

        assert response.status_code == 404
