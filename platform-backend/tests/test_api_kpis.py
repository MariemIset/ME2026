import pytest


class TestKpisEndpoint:

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_get_kpis(self, client):
        response = client.get("/api/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "totalCustomers" in data
        assert "churnRisk" in data
        assert "avgClv" in data
        assert "totalRevenue" in data
        assert "value" in data["totalCustomers"]
        assert "goal" in data["totalCustomers"]

    def test_get_kpis_with_filter(self, client):
        response = client.get("/api/kpis?loyalty_cards=Aurora&provinces=Alberta")
        assert response.status_code == 200

    def test_get_revenue_chart(self, client):
        response = client.get("/api/ceo/revenue-chart")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "name" in data[0]
            assert "value" in data[0]

    def test_kpi_goal_values_are_present(self, client):
        response = client.get("/api/kpis")
        data = response.json()
        assert data["totalCustomers"]["goal"] == 20000
        assert data["churnRisk"]["goal"] == 1500
        assert data["avgClv"]["goal"] == 8500
        assert data["totalRevenue"]["goal"] == 1500000