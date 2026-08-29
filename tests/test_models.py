"""Model constraints must reject invalid payloads at the boundary."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from conciergeagent.core.models import (
    AdvisoryRecommendation,
    CustomerProfile,
    ExperienceReview,
    IntentCategory,
    ResolutionStatus,
    SentimentGrade,
    ServiceInteraction,
    WealthTier,
)


def _advisory(allocation):
    return AdvisoryRecommendation(
        portfolio_allocation=allocation,
        yield_enhancement_strategy="s",
        tax_efficiency_notes="t",
        bespoke_opportunity="b",
        advisor_signature="sig",
    )


class TestAllocationInvariant:
    def test_allocation_summing_to_one_is_accepted(self):
        assert _advisory({"Equities": 0.6, "Bonds": 0.4}).portfolio_allocation["Bonds"] == 0.4

    @pytest.mark.parametrize(
        "allocation",
        [
            {"Equities": 0.6, "Bonds": 0.3},
            {"Equities": 1.5},
            {"Equities": 0.0},
            {"Equities": 0.5, "Bonds": 0.6},
        ],
    )
    def test_allocation_not_summing_to_one_is_rejected(self, allocation):
        with pytest.raises(ValidationError, match="must sum to 1.0"):
            _advisory(allocation)

    def test_negative_weight_is_rejected(self):
        with pytest.raises(ValidationError, match="non-negative"):
            _advisory({"Equities": 1.3, "Short": -0.3})

    def test_empty_allocation_is_rejected(self):
        with pytest.raises(ValidationError):
            _advisory({})

    def test_floating_point_drift_within_tolerance_is_accepted(self):
        rec = _advisory({"A": 0.1, "B": 0.2, "C": 0.3, "D": 0.4})
        assert len(rec.portfolio_allocation) == 4


class TestServiceInteraction:
    @pytest.mark.parametrize("score", [-1.0, -0.5, 0.0, 0.5, 1.0])
    def test_sentiment_in_range_is_accepted(self, score):
        interaction = ServiceInteraction(
            customer_profile=CustomerProfile(), user_query="hello", raw_sentiment_score=score
        )
        assert interaction.raw_sentiment_score == score

    @pytest.mark.parametrize("score", [-1.01, 1.01, 42.0, -99.0])
    def test_sentiment_out_of_range_is_rejected(self, score):
        with pytest.raises(ValidationError):
            ServiceInteraction(
                customer_profile=CustomerProfile(), user_query="hello", raw_sentiment_score=score
            )

    def test_empty_query_is_rejected(self):
        with pytest.raises(ValidationError):
            ServiceInteraction(customer_profile=CustomerProfile(), user_query="")

    def test_overlong_query_is_rejected(self):
        with pytest.raises(ValidationError):
            ServiceInteraction(customer_profile=CustomerProfile(), user_query="x" * 4001)

    def test_unknown_intent_is_rejected(self):
        with pytest.raises(ValidationError):
            ServiceInteraction(
                customer_profile=CustomerProfile(),
                user_query="hello",
                intent_category="TELEPORT",
            )

    @pytest.mark.parametrize("intent", list(IntentCategory))
    def test_every_declared_intent_is_accepted(self, intent):
        interaction = ServiceInteraction(
            customer_profile=CustomerProfile(), user_query="hello", intent_category=intent
        )
        assert interaction.intent_category is intent

    def test_intent_defaults_to_advisory(self):
        interaction = ServiceInteraction(customer_profile=CustomerProfile(), user_query="hi")
        assert interaction.intent_category is IntentCategory.ADVISORY


class TestCustomerProfile:
    def test_negative_aum_is_rejected(self):
        with pytest.raises(ValidationError):
            CustomerProfile(assets_under_management_usd=-1.0)

    def test_negative_loyalty_points_are_rejected(self):
        with pytest.raises(ValidationError):
            CustomerProfile(loyalty_points=-5)

    @pytest.mark.parametrize("score", [-0.1, 100.1])
    def test_ltv_score_outside_zero_to_hundred_is_rejected(self, score):
        with pytest.raises(ValidationError):
            CustomerProfile(lifetime_value_score=score)

    def test_blank_name_is_rejected(self):
        with pytest.raises(ValidationError):
            CustomerProfile(name="")

    def test_unknown_wealth_tier_is_rejected(self):
        with pytest.raises(ValidationError):
            CustomerProfile(wealth_tier="BILLIONAIRE")

    @pytest.mark.parametrize("tier", list(WealthTier))
    def test_every_declared_tier_is_accepted(self, tier):
        assert CustomerProfile(wealth_tier=tier).wealth_tier is tier


class TestExperienceReview:
    @pytest.mark.parametrize("rating", [0, 6, -1])
    def test_rating_outside_one_to_five_is_rejected(self, rating):
        with pytest.raises(ValidationError):
            ExperienceReview(
                sentiment_grade=SentimentGrade.NEUTRAL,
                hospitality_rating=rating,
                empathetic_opening="hi",
                closing_courtesy="bye",
            )

    def test_perk_is_optional(self):
        review = ExperienceReview(
            sentiment_grade=SentimentGrade.NEUTRAL,
            hospitality_rating=5,
            empathetic_opening="hi",
            closing_courtesy="bye",
        )
        assert review.loyalty_perk_awarded is None
        assert review.executive_escalation_required is False


class TestEnums:
    @pytest.mark.parametrize("status", list(ResolutionStatus))
    def test_resolution_status_compares_equal_to_its_string(self, status):
        assert status == status.value

    @pytest.mark.parametrize("grade", list(SentimentGrade))
    def test_sentiment_grade_compares_equal_to_its_string(self, grade):
        assert grade == grade.value
