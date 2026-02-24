"""Integration tests for the FastAPI API."""
import pytest
from fastapi.testclient import TestClient

from irt_cat_engine.api.main import app
from irt_cat_engine.api.session_manager import session_manager
from irt_cat_engine.data.database import init_db, engine, Base
from irt_cat_engine.config import VOCAB_DB_PATH


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Create fresh DB tables for testing."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def load_vocab():
    """Load vocabulary data (once for all tests)."""
    if not VOCAB_DB_PATH.exists():
        pytest.skip(f"Vocabulary DB not found: {VOCAB_DB_PATH}")
    session_manager.load_data()


@pytest.fixture(scope="module")
def client(load_vocab):
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["service"] == "IRT Vocabulary Diagnostic Test"
        assert data["status"] == "ready"
        assert data["vocab_count"] > 9000

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["data_loaded"] is True

    def test_admin_stats(self, client):
        r = client.get("/api/v1/admin/stats")
        assert r.status_code == 200
        assert r.json()["vocab_loaded"] is True


class TestTestSession:
    """Test the full test session lifecycle."""

    def test_start_test_new_user(self, client):
        """Starting a test with no user_id should create a new user."""
        r = client.post("/api/v1/test/start", json={
            "nickname": "test_student",
            "grade": "중2",
            "self_assess": "intermediate",
            "exam_experience": "none",
        })
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data
        assert "user_id" in data
        assert "first_item" in data
        assert data["first_item"]["item_id"] >= 0
        assert data["first_item"]["stem"] is not None
        assert data["first_item"]["options"] is not None
        assert len(data["first_item"]["options"]) == 4
        assert data["progress"]["items_completed"] == 0

    def test_start_test_invalid_user(self, client):
        """Starting with a non-existent user_id should return 404."""
        r = client.post("/api/v1/test/start", json={
            "user_id": "nonexistent_user_id_12345",
        })
        assert r.status_code == 404

    def test_full_session_flow(self, client):
        """Run a complete test session: start -> respond x N -> results."""
        # Start
        r = client.post("/api/v1/test/start", json={
            "nickname": "full_test_student",
            "grade": "중2",
        })
        assert r.status_code == 200
        start_data = r.json()
        session_id = start_data["session_id"]
        user_id = start_data["user_id"]

        current_item = start_data["first_item"]
        items_answered = 0

        # Answer items until complete (max 50 to prevent infinite loop)
        for _ in range(50):
            # Simulate: answer correct if item_id is even, incorrect if odd
            is_correct = current_item["item_id"] % 2 == 0

            r = client.post(f"/api/v1/test/{session_id}/respond", json={
                "item_id": current_item["item_id"],
                "is_correct": is_correct,
                "response_time_ms": 3000,
            })
            assert r.status_code == 200
            resp_data = r.json()
            items_answered += 1

            if resp_data["is_complete"]:
                # Verify results
                results = resp_data["results"]
                assert results is not None
                assert results["session_id"] == session_id
                assert results["cefr_level"] in ("A1", "A2", "B1", "B2", "C1")
                assert results["vocab_size_estimate"] > 0
                assert results["total_items"] == items_answered
                assert 0 <= results["accuracy"] <= 1
                break

            # Get next item
            current_item = resp_data["next_item"]
            assert current_item is not None
            assert current_item["options"] is not None

        assert items_answered >= 15, "Should have at least min_items responses"

        # Verify results endpoint
        r = client.get(f"/api/v1/test/{session_id}/results")
        assert r.status_code == 200
        stored = r.json()
        assert stored["cefr_level"] in ("A1", "A2", "B1", "B2", "C1")

        # Verify user history
        r = client.get(f"/api/v1/user/{user_id}/history")
        assert r.status_code == 200
        history = r.json()
        assert history["total_sessions"] >= 1
        assert any(s["session_id"] == session_id for s in history["sessions"])

    def test_respond_invalid_session(self, client):
        """Responding to a non-existent session should return 404."""
        r = client.post("/api/v1/test/nonexistent123/respond", json={
            "item_id": 0,
            "is_correct": True,
        })
        assert r.status_code == 404

    def test_results_incomplete_session(self, client):
        """Getting results for an in-progress session should fail."""
        # Start a new session but don't complete it
        r = client.post("/api/v1/test/start", json={"nickname": "incomplete"})
        assert r.status_code == 200
        session_id = r.json()["session_id"]

        # Try to get results
        r = client.get(f"/api/v1/test/{session_id}/results")
        assert r.status_code == 400


class TestAdmin:
    def test_recalibrate(self, client):
        """Recalibration should work even with no data."""
        r = client.post("/api/v1/admin/recalibrate")
        assert r.status_code == 200
        assert "items_recalibrated" in r.json()

    def test_cleanup(self, client):
        r = client.post("/api/v1/admin/cleanup")
        assert r.status_code == 200
        assert "remaining" in r.json()


class TestMultipleQuestionTypes:
    def test_start_with_different_types(self, client):
        """Should be able to start tests with different question types."""
        for qtype in [1, 2]:
            r = client.post("/api/v1/test/start", json={
                "nickname": f"qtype_{qtype}",
                "question_type": qtype,
            })
            assert r.status_code == 200
            data = r.json()
            assert data["first_item"]["stem"] is not None
