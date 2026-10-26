"""
Unit tests for netdoctor.history
"""

import pytest
from netdoctor.history import NetworkHistoryTracker, compare_recovery_snapshots


def test_recovery_event_detection():
    tracker = NetworkHistoryTracker(max_entries=10)

    # First snapshot: Gateway failing
    snap1 = {
        "timestamp": "2026-10-24T12:00:00",
        "overall_status": "FAIL",
        "gateway_test": {"target": "192.168.1.1", "status": "FAIL", "error": "Timed out"},
        "dns_results": [{"hostname": "google.com", "status": "PASS"}],
        "tcp_results": []
    }
    events1 = tracker.add_snapshot(snap1)
    assert len(events1) == 0  # No previous snapshot to compare against

    # Second snapshot: Gateway recovers!
    snap2 = {
        "timestamp": "2026-10-24T12:00:05",
        "overall_status": "PASS",
        "gateway_test": {"target": "192.168.1.1", "status": "PASS", "rtt_avg_ms": 2.1},
        "dns_results": [{"hostname": "google.com", "status": "PASS"}],
        "tcp_results": []
    }
    events2 = tracker.add_snapshot(snap2)
    assert len(events2) == 1
    assert events2[0]["event_type"] == "RECOVERY"
    assert "Default Gateway" in events2[0]["category"]


def test_compare_recovery_snapshots():
    before = {
        "overall_status": "FAIL",
        "gateway_test": {"target": "192.168.1.1", "status": "FAIL"},
        "dns_results": [{"hostname": "google.com", "status": "FAIL"}],
        "tcp_results": []
    }
    after = {
        "overall_status": "PASS",
        "gateway_test": {"target": "192.168.1.1", "status": "PASS", "rtt_avg_ms": 3.0},
        "dns_results": [{"hostname": "google.com", "status": "PASS", "latency_ms": 15.0}],
        "tcp_results": []
    }

    comp = compare_recovery_snapshots(before, after)
    assert comp["recovery_verified"] is True
    assert len(comp["restored_items"]) == 2
    assert len(comp["degraded_items"]) == 0
