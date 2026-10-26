"""
Unit tests for netdoctor.diagnostics
"""

import pytest
from netdoctor.diagnostics import diagnose_network_snapshot


def test_diagnose_healthy_network():
    snapshot = {
        "primary_info": {"local_ip": "192.168.1.50", "default_gateway": "192.168.1.1"},
        "adapters": [{"interface": "Wi-Fi", "is_up": True, "ipv4": "192.168.1.50"}],
        "gateway_test": {"status": "PASS", "target": "192.168.1.1", "rtt_avg_ms": 2.5, "loss_pct": 0.0},
        "dns_results": [{"hostname": "google.com", "status": "PASS", "latency_ms": 15.0}],
        "ping_results": [{"target": "8.8.8.8", "status": "PASS", "rtt_avg_ms": 14.0, "loss_pct": 0.0}],
        "tcp_results": [{"service": "Google HTTP", "status": "PASS", "latency_ms": 20.0}]
    }

    findings = diagnose_network_snapshot(snapshot)
    assert len(findings) == 1
    assert "Comprehensive Network Health" in findings[0]["test_name"]
    assert findings[0]["confidence"] == "HIGH"


def test_diagnose_apipa_failure():
    snapshot = {
        "primary_info": {"local_ip": "169.254.12.34", "default_gateway": "Not Detected"},
        "adapters": [{"interface": "Ethernet", "is_up": True, "ipv4": "169.254.12.34"}],
        "gateway_test": {"status": "FAIL", "target": "Not Detected"},
        "dns_results": [],
        "ping_results": [],
        "tcp_results": []
    }

    findings = diagnose_network_snapshot(snapshot)
    apipa_findings = [f for f in findings if "DHCP IP Assignment" in f["test_name"]]
    assert len(apipa_findings) == 1
    assert "APIPA" in apipa_findings[0]["actual_result"]
    assert apipa_findings[0]["confidence"] == "HIGH"


def test_diagnose_icmp_blocked_firewall():
    # ICMP fails, but TCP port probes pass!
    snapshot = {
        "primary_info": {"local_ip": "192.168.1.50", "default_gateway": "192.168.1.1"},
        "adapters": [{"interface": "Wi-Fi", "is_up": True, "ipv4": "192.168.1.50"}],
        "gateway_test": {"status": "PASS", "target": "192.168.1.1", "rtt_avg_ms": 2.0},
        "dns_results": [{"hostname": "google.com", "status": "PASS", "latency_ms": 12.0}],
        "ping_results": [
            {"target": "8.8.8.8", "status": "FAIL", "error": "Request timed out"},
            {"target": "1.1.1.1", "status": "FAIL", "error": "Request timed out"}
        ],
        "tcp_results": [
            {"service": "Google HTTP (80)", "status": "PASS", "latency_ms": 22.0},
            {"service": "Cloudflare HTTPS (443)", "status": "PASS", "latency_ms": 24.0}
        ]
    }

    findings = diagnose_network_snapshot(snapshot)
    icmp_findings = [f for f in findings if "ICMP Ping vs TCP Transport" in f["test_name"]]
    assert len(icmp_findings) == 1
    assert "dropping ICMP" in icmp_findings[0]["likely_cause"]
    assert icmp_findings[0]["confidence"] == "HIGH"
