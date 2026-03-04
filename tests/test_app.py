"""
Comprehensive Backend Tests for High School Management API

This test suite covers all endpoints and scenarios using the AAA (Arrange-Act-Assert) pattern:
- ARRANGE: Set up test data, initial state, and test fixtures
- ACT: Execute the endpoint/function being tested
- ASSERT: Verify the results match expectations

Tests cover:
1. Root endpoint (GET /)
2. Activities list endpoint (GET /activities)
3. Signup endpoint (POST /activities/{activity_name}/signup)
4. Removal endpoint (DELETE /activities/{activity_name}/participants)
5. Error handling and edge cases
6. Integration workflows
"""

from copy import deepcopy
import pytest

from fastapi.testclient import TestClient
from src import app as app_module

# ============================================================================
# SETUP & FIXTURES
# ============================================================================

# Test client using the FastAPI application
client = TestClient(app_module.app)

# Store original activities to reset state between tests
ORIGINAL_ACTIVITIES = deepcopy(app_module.activities)

# Expected activities in the system
EXPECTED_ACTIVITIES = [
    "Chess Club",
    "Programming Class",
    "Gym Class",
    "Basketball",
    "Tennis Club",
    "Art Studio",
    "Drama Club",
    "Debate Team",
    "Science Club"
]

# Required fields for each activity
REQUIRED_ACTIVITY_FIELDS = {"description", "schedule", "max_participants", "participants"}


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dictionary before each test.
    
    This fixture runs before every test to ensure test isolation and
    consistent initial state.
    """
    app_module.activities.clear()
    app_module.activities.update(deepcopy(ORIGINAL_ACTIVITIES))


# ============================================================================
# HELPER FUNCTIONS FOR ARRANGE PHASE
# ============================================================================

def get_test_email(suffix: str = "test@example.com") -> str:
    """Generate a test email address for use in tests."""
    return suffix


def signup_user(activity_name: str, email: str):
    """Helper function to sign up a user for an activity.
    
    This is used in Arrange phase of integration tests.
    """
    return client.post(f"/activities/{activity_name}/signup", params={"email": email})


def remove_user(activity_name: str, email: str):
    """Helper function to remove a user from an activity.
    
    This is used in Arrange phase of integration tests.
    """
    return client.delete(f"/activities/{activity_name}/participants", params={"email": email})


# ============================================================================
# TESTS: ROOT ENDPOINT (GET /)
# ============================================================================

class TestRootEndpoint:
    """Tests for the root endpoint (GET /). Should redirect to static files."""

    def test_root_redirects_to_static_index(self):
        """Test that GET / redirects to /static/index.html"""
        # ARRANGE
        expected_location = "/static/index.html"

        # ACT
        response = client.get("/", follow_redirects=False)

        # ASSERT
        assert response.status_code in (307, 302), "Expected redirect status code (307 or 302)"
        assert response.headers["location"] == expected_location, "Expected redirect to /static/index.html"

    def test_root_redirect_location_header_present(self):
        """Test that redirect response includes location header"""
        # ARRANGE & ACT
        response = client.get("/", follow_redirects=False)

        # ASSERT
        assert "location" in response.headers, "Expected location header in redirect response"


# ============================================================================
# TESTS: GET ACTIVITIES ENDPOINT (GET /activities)
# ============================================================================

class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint. Should return all activities with full structure."""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status code"""
        # ARRANGE & ACT
        response = client.get("/activities")

        # ASSERT
        assert response.status_code == 200

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all expected activities"""
        # ARRANGE
        expected_activity_count = 9

        # ACT
        response = client.get("/activities")
        data = response.json()

        # ASSERT
        assert len(data) == expected_activity_count, f"Expected {expected_activity_count} activities"
        for activity_name in EXPECTED_ACTIVITIES:
            assert activity_name in data, f"Expected activity '{activity_name}' not found in response"

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        # ARRANGE & ACT
        response = client.get("/activities")
        data = response.json()

        # ASSERT
        assert isinstance(data, dict), "Expected response to be a dictionary"

    def test_activity_structure_contains_required_fields(self):
        """Test that each activity has all required fields"""
        # ARRANGE & ACT
        response = client.get("/activities")
        data = response.json()

        # ASSERT
        for activity_name in EXPECTED_ACTIVITIES:
            activity = data[activity_name]
            assert isinstance(activity, dict), f"Activity '{activity_name}' should be a dict"
            for field in REQUIRED_ACTIVITY_FIELDS:
                assert field in activity, f"Activity '{activity_name}' missing required field '{field}'"

    def test_activity_field_types(self):
        """Test that each activity has correct field types"""
        # ARRANGE & ACT
        response = client.get("/activities")
        data = response.json()

        # ASSERT
        for activity_name in EXPECTED_ACTIVITIES:
            activity = data[activity_name]
            assert isinstance(activity["description"], str), f"'{activity_name}' description should be string"
            assert isinstance(activity["schedule"], str), f"'{activity_name}' schedule should be string"
            assert isinstance(activity["max_participants"], int), f"'{activity_name}' max_participants should be int"
            assert isinstance(activity["participants"], list), f"'{activity_name}' participants should be list"

    def test_activity_participants_are_strings(self):
        """Test that participants list contains only strings (emails)"""
        # ARRANGE & ACT
        response = client.get("/activities")
        data = response.json()

        # ASSERT
        for activity_name in EXPECTED_ACTIVITIES:
            participants = data[activity_name]["participants"]
            for participant in participants:
                assert isinstance(participant, str), f"Participant in '{activity_name}' should be string (email)"

    def test_chess_club_contains_initial_participants(self):
        """Test that Chess Club has expected initial participants"""
        # ARRANGE
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

        # ACT
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]

        # ASSERT
        assert chess_club["participants"] == expected_participants, "Chess Club participants mismatch"


# ============================================================================
# TESTS: SIGNUP ENDPOINT (POST /activities/{activity_name}/signup)
# ============================================================================

class TestSignupEndpoint:
    """Tests for signup endpoint. Should add users to activities."""

    # --- SUCCESS CASES ---

    def test_signup_success_adds_user_to_participants(self):
        """Test that successful signup adds user to activity participants"""
        # ARRANGE
        activity_name = "Chess Club"
        test_email = get_test_email("alice@example.com")

        # ACT
        response = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})

        # ASSERT
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert test_email in app_module.activities[activity_name]["participants"], "Email not added to participants"
        assert "message" in response.json(), "Expected message in response"

    def test_signup_success_response_contains_confirmation(self):
        """Test that successful signup response contains confirmation message"""
        # ARRANGE
        activity_name = "Programming Class"
        test_email = get_test_email("bob@example.com")

        # ACT
        response = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
        data = response.json()

        # ASSERT
        assert response.status_code == 200
        assert "Signed up" in data["message"], "Expected 'Signed up' in confirmation message"
        assert test_email in data["message"], "Expected email in confirmation message"

    def test_signup_multiple_different_users(self):
        """Test that multiple different users can sign up for same activity"""
        # ARRANGE
        activity_name = "Art Studio"
        email1 = get_test_email("user1@example.com")
        email2 = get_test_email("user2@example.com")
        email3 = get_test_email("user3@example.com")

        # ACT
        resp1 = client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        resp2 = client.post(f"/activities/{activity_name}/signup", params={"email": email2})
        resp3 = client.post(f"/activities/{activity_name}/signup", params={"email": email3})

        # ASSERT
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp3.status_code == 200
        participants = app_module.activities[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants
        assert email3 in participants
        assert len(participants) >= 5  # Original + 3 new

    def test_signup_to_different_activities(self):
        """Test that same user can sign up for different activities"""
        # ARRANGE
        test_email = get_test_email("versatile@example.com")
        activity1 = "Chess Club"
        activity2 = "Drama Club"

        # ACT
        resp1 = client.post(f"/activities/{activity1}/signup", params={"email": test_email})
        resp2 = client.post(f"/activities/{activity2}/signup", params={"email": test_email})

        # ASSERT
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert test_email in app_module.activities[activity1]["participants"]
        assert test_email in app_module.activities[activity2]["participants"]

    # --- ERROR CASES: DUPLICATE SIGNUP ---

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up with duplicate email returns 400 error"""
        # ARRANGE
        activity_name = "Tennis Club"
        test_email = get_test_email("duplicate@example.com")

        # First signup should succeed
        resp1 = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
        assert resp1.status_code == 200

        # ACT - Try to signup again with same email
        resp2 = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})

        # ASSERT
        assert resp2.status_code == 400, f"Expected 400 for duplicate, got {resp2.status_code}"

    def test_signup_duplicate_email_error_message(self):
        """Test that duplicate signup returns appropriate error message"""
        # ARRANGE
        activity_name = "Science Club"
        test_email = get_test_email("duplicate_msg@example.com")

        # First signup
        client.post(f"/activities/{activity_name}/signup", params={"email": test_email})

        # ACT
        response = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
        data = response.json()

        # ASSERT
        assert response.status_code == 400
        assert "detail" in data, "Expected detail in error response"
        assert "already" in data["detail"].lower(), "Expected 'already' in error message"

    def test_signup_duplicate_does_not_add_again(self):
        """Test that duplicate signup doesn't add user multiple times"""
        # ARRANGE
        activity_name = "Debate Team"
        test_email = get_test_email("unique@example.com")

        # First signup
        client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
        count_after_first = app_module.activities[activity_name]["participants"].count(test_email)

        # ACT - Try duplicate
        client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
        count_after_second = app_module.activities[activity_name]["participants"].count(test_email)

        # ASSERT
        assert count_after_first == 1, "User should appear once after first signup"
        assert count_after_second == 1, "User should still appear only once after duplicate signup"

    # --- ERROR CASES: ACTIVITY NOT FOUND ---

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that signing up for non-existent activity returns 404"""
        # ARRANGE
        fake_activity = "Phony Club"
        test_email = get_test_email("test@example.com")

        # ACT
        response = client.post(f"/activities/{fake_activity}/signup", params={"email": test_email})

        # ASSERT
        assert response.status_code == 404, f"Expected 404 for non-existent activity, got {response.status_code}"

    def test_signup_nonexistent_activity_error_message(self):
        """Test that 404 error contains 'Activity not found' message"""
        # ARRANGE
        fake_activity = "Underwater Basket Weaving"
        test_email = get_test_email("test@example.com")

        # ACT
        response = client.post(f"/activities/{fake_activity}/signup", params={"email": test_email})
        data = response.json()

        # ASSERT
        assert response.status_code == 404
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_nonexistent_activity_does_not_create(self):
        """Test that failed signup to non-existent activity doesn't create it"""
        # ARRANGE
        fake_activity = "Made Up Club"
        test_email = get_test_email("test@example.com")

        # ACT
        client.post(f"/activities/{fake_activity}/signup", params={"email": test_email})

        # ASSERT
        assert fake_activity not in app_module.activities, "Non-existent activity should not be created"

    # --- EDGE CASES ---

    def test_signup_with_empty_email(self):
        """Test signup behavior with empty email string"""
        # ARRANGE
        activity_name = "Basketball"
        empty_email = ""

        # ACT
        response = client.post(f"/activities/{activity_name}/signup", params={"email": empty_email})

        # ASSERT - App accepts it (no validation), so should succeed
        assert response.status_code == 200

    def test_signup_with_whitespace_email(self):
        """Test signup behavior with whitespace-only email"""
        # ARRANGE
        activity_name = "Gym Class"
        whitespace_email = "   "

        # ACT
        response = client.post(f"/activities/{activity_name}/signup", params={"email": whitespace_email})

        # ASSERT - App accepts it (no validation), so should succeed
        assert response.status_code == 200

    def test_signup_case_sensitivity_of_email(self):
        """Test that email addresses are case-sensitive in comparison"""
        # ARRANGE
        activity_name = "Chess Club"
        email_lower = "test@example.com"
        email_upper = "TEST@EXAMPLE.COM"

        # ACT
        resp1 = client.post(f"/activities/{activity_name}/signup", params={"email": email_lower})
        resp2 = client.post(f"/activities/{activity_name}/signup", params={"email": email_upper})

        # ASSERT - Different cases are treated as different emails
        assert resp1.status_code == 200
        assert resp2.status_code == 200  # Different email, so succeeds
        assert email_lower in app_module.activities[activity_name]["participants"]
        assert email_upper in app_module.activities[activity_name]["participants"]

    def test_signup_special_characters_in_email(self):
        """Test signup with special characters in email"""
        # ARRANGE
        activity_name = "Programming Class"
        special_email = "user+tag@example.co.uk"

        # ACT
        response = client.post(f"/activities/{activity_name}/signup", params={"email": special_email})

        # ASSERT - App accepts any string as email
        assert response.status_code == 200
        assert special_email in app_module.activities[activity_name]["participants"]

    def test_signup_case_sensitivity_of_activity_name(self):
        """Test that activity names are case-sensitive"""
        # ARRANGE
        activity_lower = "chess club"
        activity_upper = "CHESS CLUB"
        test_email = get_test_email("test@example.com")

        # ACT
        response = client.post(f"/activities/{activity_lower}/signup", params={"email": test_email})

        # ASSERT - Different case = different activity = 404
        assert response.status_code == 404


# ============================================================================
# TESTS: REMOVAL ENDPOINT (DELETE /activities/{activity_name}/participants)
# ============================================================================

class TestRemovalEndpoint:
    """Tests for removal endpoint. Should remove users from activities."""

    # --- SUCCESS CASES ---

    def test_removal_success_removes_user(self):
        """Test that successful removal removes user from activity participants"""
        # ARRANGE
        activity_name = "Programming Class"
        email_to_remove = ORIGINAL_ACTIVITIES[activity_name]["participants"][0]
        initial_count = len(app_module.activities[activity_name]["participants"])

        # ACT
        response = client.delete(f"/activities/{activity_name}/participants", params={"email": email_to_remove})

        # ASSERT
        assert response.status_code == 200
        assert email_to_remove not in app_module.activities[activity_name]["participants"]
        assert len(app_module.activities[activity_name]["participants"]) == initial_count - 1

    def test_removal_success_response_contains_confirmation(self):
        """Test that successful removal response contains confirmation message"""
        # ARRANGE
        activity_name = "Chess Club"
        email_to_remove = ORIGINAL_ACTIVITIES[activity_name]["participants"][0]

        # ACT
        response = client.delete(f"/activities/{activity_name}/participants", params={"email": email_to_remove})
        data = response.json()

        # ASSERT
        assert response.status_code == 200
        assert "message" in data
        assert "Removed" in data["message"]

    def test_removal_multiple_users(self):
        """Test that multiple users can be removed from an activity"""
        # ARRANGE
        activity_name = "Gym Class"
        initial_participants = ORIGINAL_ACTIVITIES[activity_name]["participants"].copy()
        
        # ACT & ASSERT
        for email in initial_participants:
            response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})
            assert response.status_code == 200
            assert email not in app_module.activities[activity_name]["participants"]

    def test_removal_leaves_other_participants(self):
        """Test that removing one user doesn't remove others"""
        # ARRANGE
        activity_name = "Drama Club"
        initial_participants = app_module.activities[activity_name]["participants"].copy()
        email_to_remove = initial_participants[0]
        others_to_keep = initial_participants[1:] if len(initial_participants) > 1 else []

        # ACT
        client.delete(f"/activities/{activity_name}/participants", params={"email": email_to_remove})

        # ASSERT
        for email in others_to_keep:
            assert email in app_module.activities[activity_name]["participants"]

    # --- ERROR CASES: PARTICIPANT NOT FOUND ---

    def test_removal_nonexistent_participant_returns_400(self):
        """Test that removing non-existent participant returns 400"""
        # ARRANGE
        activity_name = "Art Studio"
        email_not_signed_up = "nothere@example.com"

        # ACT
        response = client.delete(f"/activities/{activity_name}/participants", params={"email": email_not_signed_up})

        # ASSERT
        assert response.status_code == 400

    def test_removal_nonexistent_participant_error_message(self):
        """Test that error message indicates participant not found"""
        # ARRANGE
        activity_name = "Tennis Club"
        email_not_found = "nope@example.com"

        # ACT
        response = client.delete(f"/activities/{activity_name}/participants", params={"email": email_not_found})
        data = response.json()

        # ASSERT
        assert response.status_code == 400
        assert "detail" in data
        assert "not" in data["detail"].lower() or "found" in data["detail"].lower()

    def test_removal_same_email_twice_fails_second_time(self):
        """Test that removing same email twice fails on second attempt"""
        # ARRANGE
        activity_name = "Science Club"
        email_to_remove = ORIGINAL_ACTIVITIES[activity_name]["participants"][0]

        # First removal should succeed
        resp1 = client.delete(f"/activities/{activity_name}/participants", params={"email": email_to_remove})
        assert resp1.status_code == 200

        # ACT - Try to remove again
        resp2 = client.delete(f"/activities/{activity_name}/participants", params={"email": email_to_remove})

        # ASSERT
        assert resp2.status_code == 400

    # --- ERROR CASES: ACTIVITY NOT FOUND ---

    def test_removal_nonexistent_activity_returns_404(self):
        """Test that removing from non-existent activity returns 404"""
        # ARRANGE
        fake_activity = "Fake Club"
        test_email = "test@example.com"

        # ACT
        response = client.delete(f"/activities/{fake_activity}/participants", params={"email": test_email})

        # ASSERT
        assert response.status_code == 404

    def test_removal_nonexistent_activity_error_message(self):
        """Test that 404 error message contains 'Activity not found'"""
        # ARRANGE
        fake_activity = "Nonexistent Activity"
        test_email = "test@example.com"

        # ACT
        response = client.delete(f"/activities/{fake_activity}/participants", params={"email": test_email})
        data = response.json()

        # ASSERT
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()

    # --- EDGE CASES ---

    def test_removal_with_empty_email(self):
        """Test removal behavior with empty email string"""
        # ARRANGE
        activity_name = "Debate Team"

        # ACT
        response = client.delete(f"/activities/{activity_name}/participants", params={"email": ""})

        # ASSERT - Should fail because empty string is not a participant
        assert response.status_code == 400

    def test_removal_case_sensitivity_of_email(self):
        """Test that email addresses are case-sensitive in removal"""
        # ARRANGE
        activity_name = "Basketball"
        initial_participants = app_module.activities[activity_name]["participants"].copy()
        test_email = "test@example.com"

        # Sign up with lowercase
        client.post(f"/activities/{activity_name}/signup", params={"email": test_email})

        # Try to remove with uppercase
        response = client.delete(f"/activities/{activity_name}/participants",
                                params={"email": test_email.upper()})

        # ASSERT - Case mismatch means email not found
        assert response.status_code == 400
        assert test_email in app_module.activities[activity_name]["participants"]

    def test_removal_case_sensitivity_of_activity_name(self):
        """Test that activity names are case-sensitive in removal"""
        # ARRANGE
        activity_correct = "Chess Club"
        activity_wrong_case = "chess club"
        test_email = "test@example.com"

        # Sign up for correct case
        client.post(f"/activities/{activity_correct}/signup", params={"email": test_email})

        # Try to remove using wrong case
        response = client.delete(f"/activities/{activity_wrong_case}/participants", params={"email": test_email})

        # ASSERT - Wrong case activity not found
        assert response.status_code == 404


# ============================================================================
# INTEGRATION TESTS: MULTI-STEP WORKFLOWS
# ============================================================================

class TestIntegrationWorkflows:
    """Integration tests that verify workflows across multiple endpoints."""

    def test_signup_then_view_then_remove_workflow(self):
        """Test complete workflow: signup -> verify in list -> remove -> verify removed"""
        # ARRANGE
        activity_name = "Programming Class"
        test_email = get_test_email("integration@example.com")

        # ACT 1: Sign up
        signup_resp = signup_user(activity_name, test_email)

        # ASSERT 1: Signup successful
        assert signup_resp.status_code == 200

        # ACT 2: View activities
        view_resp = client.get("/activities")
        participants = view_resp.json()[activity_name]["participants"]

        # ASSERT 2: Email appears in participants
        assert test_email in participants

        # ACT 3: Remove
        remove_resp = remove_user(activity_name, test_email)

        # ASSERT 3: Removal successful
        assert remove_resp.status_code == 200

        # ACT 4: View again
        final_view_resp = client.get("/activities")
        final_participants = final_view_resp.json()[activity_name]["participants"]

        # ASSERT 4: Email no longer in participants
        assert test_email not in final_participants

    def test_multiple_users_signup_and_remove_in_sequence(self):
        """Test that multiple users can sign up and be removed in order"""
        # ARRANGE
        activity_name = "Drama Club"
        users = [
            get_test_email("user1@example.com"),
            get_test_email("user2@example.com"),
            get_test_email("user3@example.com"),
        ]

        # ACT & ASSERT: Sign up all
        for idx, user_email in enumerate(users):
            resp = signup_user(activity_name, user_email)
            assert resp.status_code == 200
            view = client.get("/activities").json()
            assert user_email in view[activity_name]["participants"]

        # ACT & ASSERT: Remove in reverse order
        for user_email in reversed(users):
            resp = remove_user(activity_name, user_email)
            assert resp.status_code == 200
            view = client.get("/activities").json()
            assert user_email not in view[activity_name]["participants"]

    def test_user_can_signup_remove_and_signup_again(self):
        """Test that user can signup, remove, and signup again to same activity"""
        # ARRANGE
        activity_name = "Tennis Club"
        test_email = get_test_email("flexible@example.com")

        # ACT 1: First signup
        resp1 = signup_user(activity_name, test_email)
        assert resp1.status_code == 200

        # ACT 2: Remove
        resp2 = remove_user(activity_name, test_email)
        assert resp2.status_code == 200

        # ACT 3: Sign up again
        resp3 = signup_user(activity_name, test_email)

        # ASSERT
        assert resp3.status_code == 200
        assert test_email in app_module.activities[activity_name]["participants"]

    def test_user_signup_multiple_activities_remove_from_one(self):
        """Test that user can sign up for multiple activities and remove from just one"""
        # ARRANGE
        activity1 = "Chess Club"
        activity2 = "Art Studio"
        activity3 = "Debate Team"
        test_email = get_test_email("multi@example.com")

        # ACT 1: Sign up for multiple activities
        resp1 = signup_user(activity1, test_email)
        resp2 = signup_user(activity2, test_email)
        resp3 = signup_user(activity3, test_email)
        assert all(r.status_code == 200 for r in [resp1, resp2, resp3])

        # ACT 2: Remove from just one activity
        remove_resp = remove_user(activity2, test_email)
        assert remove_resp.status_code == 200

        # ASSERT: Verify removal only affects one activity
        view = client.get("/activities").json()
        assert test_email in view[activity1]["participants"], "Should still be in activity1"
        assert test_email not in view[activity2]["participants"], "Should be removed from activity2"
        assert test_email in view[activity3]["participants"], "Should still be in activity3"

    def test_concurrent_users_signup_for_same_activity(self):
        """Test that multiple different users can signup for the same activity independently"""
        # ARRANGE
        activity_name = "Science Club"
        user_emails = [
            get_test_email("concurrent1@example.com"),
            get_test_email("concurrent2@example.com"),
            get_test_email("concurrent3@example.com"),
        ]

        # ACT: All sign up
        responses = [signup_user(activity_name, email) for email in user_emails]

        # ASSERT: All successful
        assert all(r.status_code == 200 for r in responses)

        # ASSERT: All in participants
        view = client.get("/activities").json()
        participants = view[activity_name]["participants"]
        for email in user_emails:
            assert email in participants

    def test_state_persists_across_get_requests(self):
        """Test that state changes persist across multiple GET requests"""
        # ARRANGE
        activity_name = "Basketball"
        test_email = get_test_email("persist@example.com")

        # Get initial count
        initial_view = client.get("/activities").json()
        initial_count = len(initial_view[activity_name]["participants"])

        # ACT: Sign up
        signup_user(activity_name, test_email)

        # ASSERT: State persists - second GET shows the new signup
        second_view = client.get("/activities").json()
        assert len(second_view[activity_name]["participants"]) == initial_count + 1

        # And third GET confirms persistence
        third_view = client.get("/activities").json()
        assert len(third_view[activity_name]["participants"]) == initial_count + 1
