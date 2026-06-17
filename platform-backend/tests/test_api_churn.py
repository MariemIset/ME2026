import pytest


class TestChurnEndpoint:

    def test_get_churn_stats(self, client):
        response = client.get("/api/churn/stats")
        assert response.status_code == 200
        data = response.json()
        assert "churnBySegment" in data
        assert "barData" in data
        assert "scatterActive" in data
        assert "scatterChurned" in data

    def test_churn_by_segment_shape(self, client):
        response = client.get("/api/churn/stats")
        data = response.json()
        for seg in data["churnBySegment"]:
            assert "name" in seg
            assert "value" in seg

    def test_bar_data_shape(self, client):
        response = client.get("/api/churn/stats")
        data = response.json()
        for bar in data["barData"]:
            assert "name" in bar
            assert "value" in bar

    def test_scatter_data_shape(self, client):
        response = client.get("/api/churn/stats")
        data = response.json()
        if data["scatterActive"]:
            assert "x" in data["scatterActive"][0]
            assert "y" in data["scatterActive"][0]
        if data["scatterChurned"]:
            assert "x" in data["scatterChurned"][0]
            assert "y" in data["scatterChurned"][0]

    def test_churn_with_filters(self, client):
        response = client.get("/api/churn/stats?loyalty_cards=Aurora,Nova&provinces=Ontario")
        assert response.status_code == 200