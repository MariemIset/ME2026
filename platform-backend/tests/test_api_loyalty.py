import pytest


class TestLoyaltyEndpoint:

    def test_get_loyalty_stats(self, client):
        response = client.get("/api/loyalty/stats")
        assert response.status_code == 200
        data = response.json()
        assert "goldTier" in data
        assert "avgPoints" in data
        assert "redemptionRate" in data
        assert "dollarCost" in data
        assert "liability" in data
        assert "segmentation" in data

    def test_loyalty_timeline(self, client):
        response = client.get("/api/loyalty/timeline")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "name" in data[0]
            assert "accumulated" in data[0]
            assert "redeemed" in data[0]

    def test_loyalty_stats_with_filters(self, client):
        response = client.get("/api/loyalty/stats?loyalty_cards=Aurora")
        assert response.status_code == 200

    def test_loyalty_segmentation_shape(self, client):
        response = client.get("/api/loyalty/stats")
        data = response.json()
        for seg in data["segmentation"]:
            assert "name" in seg
            assert "value" in seg