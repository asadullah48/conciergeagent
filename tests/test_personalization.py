import pytest
from conciergeagent.core.models import WealthTier, SentimentGrade
from conciergeagent.core.personalization_engine import PersonalizationEngine

def test_sentiment_classification():
    grade1, s1 = PersonalizationEngine.classify_sentiment("This is brilliant and wonderful service!")
    assert grade1 == SentimentGrade.DELIGHTED
    assert s1 > 0.8

    grade2, s2 = PersonalizationEngine.classify_sentiment("This is completely unacceptable fraud on my account!")
    assert grade2 == SentimentGrade.CRITICAL_DISTRESS
    assert s2 < -0.5

def test_tier_sla_matrix():
    sla_ultra = PersonalizationEngine.get_tier_sla(WealthTier.ULTRA_HNW)
    assert sla_ultra["sla_seconds"] == 30
    assert sla_ultra["max_dispute_auto_credit"] == 50000.0

    sla_retail = PersonalizationEngine.get_tier_sla(WealthTier.RETAIL)
    assert sla_retail["sla_seconds"] == 300
    assert sla_retail["max_dispute_auto_credit"] == 500.0
