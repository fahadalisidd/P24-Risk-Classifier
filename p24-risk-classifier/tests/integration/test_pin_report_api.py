"""Integration tests for Policy Pins and Review Report API with controllable clock."""
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.core.clock import ControllableClock


class TestPinReportApi:
    def test_pin_review_report_lifecycle(self, client: TestClient, test_clock: ControllableClock):
        # Set clock to 2026-08-01
        test_clock.set_time(datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc))

        # 1. Create a pin with reviewDate = 2026-08-20 and expiresAt = 2026-09-01
        pin_payload = {
            "pinId": "pin-report-123",
            "policyId": "production-policy",
            "reason": "Temporary pin for DB migration",
            "reviewDate": "2026-08-20T00:00:00Z",
            "expiresAt": "2026-09-01T00:00:00Z",
            "enabled": True,
        }
        res = client.post("/api/v1/policies/pins", json=pin_payload)
        assert res.status_code == 201
        assert res.json()["status"] == "ACTIVE"

        # 2. On 2026-08-10 (before reviewDate): Review report is empty
        test_clock.set_time(datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc))
        rep_res1 = client.get("/api/v1/policies/pins/review-report")
        assert rep_res1.status_code == 200
        data1 = rep_res1.json()
        assert data1["overduePinCount"] == 0
        assert len(data1["expiredReviewPins"]) == 0

        # 3. Advance clock to 2026-08-25 (after reviewDate 2026-08-20, before expiresAt 2026-09-01)
        test_clock.set_time(datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc))
        rep_res2 = client.get("/api/v1/policies/pins/review-report")
        assert rep_res2.status_code == 200
        data2 = rep_res2.json()
        assert data2["overduePinCount"] >= 1
        
        target = next((p for p in data2["expiredReviewPins"] if p["pinId"] == "pin-report-123"), None)
        assert target is not None
        assert target["status"] == "REVIEW_OVERDUE"
        assert target["daysOverdue"] == 5
        assert target["policyId"] == "production-policy"

        # 4. Advance clock to 2026-09-05 (past expiresAt) -> Status becomes EXPIRED
        test_clock.set_time(datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc))
        rep_res3 = client.get("/api/v1/policies/pins/review-report")
        assert rep_res3.status_code == 200
        data3 = rep_res3.json()
        target_exp = next((p for p in data3["expiredReviewPins"] if p["pinId"] == "pin-report-123"), None)
        assert target_exp is not None
        assert target_exp["status"] == "EXPIRED"
