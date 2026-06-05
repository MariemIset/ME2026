import pytest


class TestSatisfactionEndpoint:

    def test_get_satisfaction_stats(self, client):
        response = client.get("/api/satisfaction/stats")
        assert response.status_code == 200
        data = response.json()
        assert "pieData" in data
        assert "wifi" in data
        assert "seatComfort" in data
        assert "foodDrink" in data
        assert "avgDelay" in data
        assert "volume" in data
        assert "nps" in data
        assert "heatmap" in data
        assert "recentFeedback" in data
        assert "scatter" in data

    def test_pie_data_shape(self, client):
        response = client.get("/api/satisfaction/stats")
        data = response.json()
        for item in data["pieData"]:
            assert "name" in item
            assert "value" in item

    def test_heatmap_shape(self, client):
        response = client.get("/api/satisfaction/stats")
        data = response.json()
        for h in data["heatmap"]:
            assert "name" in h
            assert "legRoom" in h
            assert "wifi" in h
            assert "food" in h

    def test_recent_feedback_shape(self, client):
        response = client.get("/api/satisfaction/stats")
        data = response.json()
        for fb in data["recentFeedback"]:
            assert "id" in fb
            assert "text" in fb
            assert "sentiment" in fb
            assert "score" in fb
            assert "time" in fb

    def test_scatter_shape(self, client):
        response = client.get("/api/satisfaction/stats")
        data = response.json()
        for sc in data["scatter"]:
            assert "x" in sc
            assert "y" in sc

    def test_satisfaction_with_filters(self, client):
        response = client.get("/api/satisfaction/stats?travel_types=Business&flight_classes=Economy")
        assert response.status_code == 200

    def test_comments_endpoint(self, client):
        response = client.get("/api/satisfaction/comments?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "text" in data[0]
            assert "sentiment" in data[0]