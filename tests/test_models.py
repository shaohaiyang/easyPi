from src.models.itinerary import Itinerary, DailyPlan, PlanResult, DiscussionEntry


def test_daily_plan_creation():
    plan = DailyPlan(
        day=1,
        date="Day 1",
        attractions=["Great Wall"],
        meals={"lunch": "Peking Duck"},
        budget=500.0,
        tips=["Bring water"],
    )
    assert plan.day == 1
    assert "Great Wall" in plan.attractions
    assert plan.budget == 500.0


def test_itinerary_creation():
    plan = DailyPlan(
        day=1,
        date="Day 1",
        attractions=["Forbidden City"],
        meals={"lunch": "Noodles"},
        budget=300.0,
        tips=[],
    )
    itinerary = Itinerary(
        destination="Beijing",
        total_days=1,
        total_budget=300.0,
        daily_plans=[plan],
        summary="Great trip",
    )
    assert itinerary.destination == "Beijing"
    assert itinerary.total_days == 1
    assert len(itinerary.daily_plans) == 1


def test_plan_result_creation():
    plan = DailyPlan(
        day=1,
        date="Day 1",
        attractions=["Test"],
        meals={"lunch": "Food"},
        budget=100.0,
        tips=[],
    )
    itinerary = Itinerary(
        destination="Test",
        total_days=1,
        total_budget=100.0,
        daily_plans=[plan],
        summary="Test",
    )
    discussion = [DiscussionEntry(agent_name="Guide", content="Go to place A")]
    result = PlanResult(itinerary=itinerary, discussion=discussion)
    assert result.itinerary.destination == "Test"
    assert len(result.discussion) == 1
    assert result.discussion[0].agent_name == "Guide"


def test_fastapi_app_imports():
    from src.app import app

    assert app.title == "Travel Assistant"
