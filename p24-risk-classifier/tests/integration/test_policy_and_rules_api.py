"""Integration tests for rules and overrides API endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestPolicyAndRulesApi:
    def test_health_check(self, client: TestClient):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_create_and_list_rules(self, client: TestClient):
        rule_payload = {
            "ruleId": "TEST_DB_FLUSH",
            "name": "Database Flush Rule",
            "conditions": {"operationType": "FLUSH", "payload.target": "ALL"},
            "resultAction": "SET_MIN_CATEGORY",
            "targetCategory": 4,
            "priority": 150,
            "enabled": True,
        }
        res_create = client.post("/api/v1/rules", json=rule_payload)
        assert res_create.status_code == 201
        data_create = res_create.json()
        assert data_create["ruleId"] == "TEST_DB_FLUSH"

        res_list = client.get("/api/v1/rules")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert any(r["ruleId"] == "TEST_DB_FLUSH" for r in data_list)

    def test_create_and_list_overrides(self, client: TestClient):
        override_payload = {
            "name": "Weekend Maintenance Freeze",
            "conditions": {"payload.maintenanceWindow": True},
            "forcedCategory": 4,
            "reason": "Weekend maintenance policy in effect",
            "enabled": True,
            "expiresAt": "2026-09-10T00:00:00Z",
        }
        res_create = client.post("/api/v1/policies/overrides", json=override_payload)
        assert res_create.status_code == 201
        data_create = res_create.json()
        assert data_create["name"] == "Weekend Maintenance Freeze"

        res_list = client.get("/api/v1/policies/overrides")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert any(o["name"] == "Weekend Maintenance Freeze" for o in data_list)
