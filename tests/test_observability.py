"""Log formatting and Prometheus metrics exposition."""
from __future__ import annotations

import json
import logging
import sys
import threading

import pytest

from conciergeagent.core.observability import (
    LATENCY_BUCKETS_MS,
    METRICS,
    JsonLogFormatter,
    MetricsRegistry,
    configure_logging,
    track_latency,
)


def _record(**extra) -> logging.LogRecord:
    record = logging.LogRecord(
        "test.logger", logging.INFO, __file__, 1, "hello %s", ("world",), None
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


class TestJsonLogFormatter:
    def test_output_is_valid_json(self):
        assert json.loads(JsonLogFormatter().format(_record()))

    def test_core_fields_are_present(self):
        payload = json.loads(JsonLogFormatter().format(_record()))
        assert payload["level"] == "INFO"
        assert payload["logger"] == "test.logger"
        assert payload["message"] == "hello world"
        assert payload["timestamp"].endswith("Z")

    def test_extra_fields_are_promoted_to_top_level(self):
        payload = json.loads(
            JsonLogFormatter().format(_record(customer_id="CUST-1", tier="RETAIL"))
        )
        assert payload["customer_id"] == "CUST-1"
        assert payload["tier"] == "RETAIL"

    @pytest.mark.parametrize("noisy", ["args", "msg", "levelno", "pathname", "relativeCreated"])
    def test_reserved_record_attributes_are_not_leaked(self, noisy):
        assert noisy not in json.loads(JsonLogFormatter().format(_record()))

    def test_exception_is_rendered(self):
        try:
            raise ValueError("boom")
        except ValueError:
            record = _record()
            record.exc_info = sys.exc_info()
            payload = json.loads(JsonLogFormatter().format(record))
        assert "ValueError: boom" in payload["exception"]

    def test_non_serialisable_extra_does_not_crash(self):
        payload = json.loads(JsonLogFormatter().format(_record(obj=object())))
        assert "obj" in payload

    def test_output_is_a_single_line(self):
        assert "\n" not in JsonLogFormatter().format(_record(note="multi\nline"))


class TestConfigureLogging:
    def test_installs_exactly_one_handler_when_called_repeatedly(self):
        configure_logging("INFO", json_logs=True)
        configure_logging("INFO", json_logs=True)
        assert len(logging.getLogger().handlers) == 1

    @pytest.mark.parametrize(
        "level,expected", [("debug", logging.DEBUG), ("WARNING", logging.WARNING)]
    )
    def test_level_is_applied(self, level, expected):
        configure_logging(level)
        assert logging.getLogger().level == expected

    def test_unknown_level_falls_back_to_info(self):
        configure_logging("NONSENSE")
        assert logging.getLogger().level == logging.INFO

    def test_json_formatter_is_used_by_default(self):
        configure_logging("INFO", json_logs=True)
        assert isinstance(logging.getLogger().handlers[0].formatter, JsonLogFormatter)

    def test_plain_formatter_when_json_disabled(self):
        configure_logging("INFO", json_logs=False)
        assert not isinstance(logging.getLogger().handlers[0].formatter, JsonLogFormatter)


class TestMetricsRegistry:
    def test_counter_accumulates(self):
        registry = MetricsRegistry()
        registry.increment("hits")
        registry.increment("hits", amount=4)
        assert registry.snapshot()["counters"]["hits"] == 5

    def test_labels_produce_separate_series(self):
        registry = MetricsRegistry()
        registry.increment("hits", {"tier": "RETAIL"})
        registry.increment("hits", {"tier": "ULTRA_HNW"})
        assert len(registry.snapshot()["counters"]) == 2

    def test_label_order_does_not_split_a_series(self):
        registry = MetricsRegistry()
        registry.increment("hits", {"a": "1", "b": "2"})
        registry.increment("hits", {"b": "2", "a": "1"})
        assert len(registry.snapshot()["counters"]) == 1

    def test_reset_clears_counters_and_histogram(self):
        registry = MetricsRegistry()
        registry.increment("hits")
        registry.observe_latency_ms(5.0)
        registry.reset()
        snapshot = registry.snapshot()
        assert snapshot["counters"] == {}
        assert snapshot["latency_count"] == 0
        assert snapshot["latency_sum_ms"] == 0.0

    def test_latency_sum_is_tracked(self):
        registry = MetricsRegistry()
        registry.observe_latency_ms(2.5)
        registry.observe_latency_ms(7.5)
        assert registry.snapshot()["latency_sum_ms"] == 10.0

    def test_latency_buckets_are_cumulative(self):
        registry = MetricsRegistry()
        registry.observe_latency_ms(7.0)
        rendered = registry.render_prometheus()
        assert 'concierge_interaction_latency_ms_bucket{le="5.0"} 0' in rendered
        assert 'concierge_interaction_latency_ms_bucket{le="10.0"} 1' in rendered

    def test_latency_above_largest_bucket_lands_only_in_inf(self):
        registry = MetricsRegistry()
        largest = max(LATENCY_BUCKETS_MS)
        registry.observe_latency_ms(largest * 10)
        rendered = registry.render_prometheus()
        assert f'concierge_interaction_latency_ms_bucket{{le="{largest}"}} 0' in rendered
        assert 'concierge_interaction_latency_ms_bucket{le="+Inf"} 1' in rendered

    def test_render_includes_help_and_type_lines(self):
        registry = MetricsRegistry()
        registry.increment("concierge_interactions_total", {"tier": "RETAIL"})
        rendered = registry.render_prometheus()
        assert "# HELP concierge_interactions_total" in rendered
        assert "# TYPE concierge_interactions_total counter" in rendered

    def test_render_emits_labels_in_prometheus_syntax(self):
        registry = MetricsRegistry()
        registry.increment("hits", {"tier": "RETAIL", "intent": "SUPPORT"})
        assert 'hits{intent="SUPPORT",tier="RETAIL"} 1' in registry.render_prometheus()

    def test_render_is_newline_terminated(self):
        assert MetricsRegistry().render_prometheus().endswith("\n")

    def test_empty_registry_still_renders_the_histogram(self):
        assert "concierge_interaction_latency_ms_count 0" in MetricsRegistry().render_prometheus()

    def test_concurrent_increments_are_not_lost(self):
        registry = MetricsRegistry()

        def worker():
            for _ in range(500):
                registry.increment("hits")

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert registry.snapshot()["counters"]["hits"] == 2000


class TestTrackLatency:
    def test_observation_is_recorded(self):
        METRICS.reset()
        with track_latency():
            pass
        assert METRICS.snapshot()["latency_count"] == 1

    def test_observation_is_recorded_even_when_the_body_raises(self):
        METRICS.reset()
        with pytest.raises(RuntimeError), track_latency():
            raise RuntimeError("boom")
        assert METRICS.snapshot()["latency_count"] == 1
