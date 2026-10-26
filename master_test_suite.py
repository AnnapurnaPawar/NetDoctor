"""
NetDoctor Master Automated End-to-End Test Suite.
Executes 10 distinct, rigorous test scenarios across all subsystems:
1. Real Windows Host Diagnostic Sweep
2. APIPA DHCP Starvation Failure Scenario
3. Default Gateway Loss Scenario
4. ICMP Blocked vs TCP Open Firewall Scenario
5. Degraded Link Quality / High Latency Scenario
6. Cisco Packet Tracer Interface Shutdown Parser
7. Cisco Packet Tracer Missing Route Parser
8. Cisco Packet Tracer VLAN Configuration Parser
9. Cisco Packet Tracer 100% Packet Loss Ping Parser
10. Before-and-After Recovery Verification Diff Engine
"""

import sys
import os
sys.path.insert(0, r"C:\Users\annap\.gemini\antigravity\scratch\NetDoctor")

from netdoctor.monitor import (
    get_network_adapters,
    get_primary_adapter_and_gateway,
    resolve_dns,
    test_tcp_port,
    ping_host,
    run_full_system_diagnostic,
    is_valid_host
)
from netdoctor.diagnostics import diagnose_network_snapshot
from netdoctor.pt_parser import (
    parse_show_ip_interface_brief,
    parse_show_ip_route,
    parse_show_vlan_brief,
    parse_show_interfaces_trunk,
    parse_cisco_ping_output,
    analyze_pt_evidence
)
from netdoctor.history import NetworkHistoryTracker, compare_recovery_snapshots

def run_all_comprehensive_tests():
    print("=" * 70)
    print("NETDOCTOR: MASTER MULTI-SCENARIO VERIFICATION TEST RUNNER")
    print("=" * 70)
    passed_scenarios = 0
    total_scenarios = 10

    # -------------------------------------------------------------
    # TEST CASE 1: Host Telemetry & Local Interface Discovery
    # -------------------------------------------------------------
    print("\n[TEST CASE 1] Physical Host Telemetry & Adapter Discovery")
    adapters = get_network_adapters()
    primary = get_primary_adapter_and_gateway()
    print(f"  -> Discovered {len(adapters)} total network adapter(s).")
    print(f"  -> Primary Local IP: {primary['local_ip']}")
    print(f"  -> Default Gateway:  {primary['default_gateway']}")
    print(f"  -> Active Interface: {primary['interface']}")
    assert len(adapters) > 0, "Failed to discover adapters"
    assert primary['local_ip'] != "Unknown", "Local IP discovery failed"
    print("  => RESULT: PASS (Host telemetry fully operational)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 2: APIPA DHCP Auto-Configuration Failure Rule
    # -------------------------------------------------------------
    print("\n[TEST CASE 2] Diagnostic Engine: APIPA (169.254.x.x) DHCP Starvation")
    apipa_snapshot = {
        "primary_info": {"local_ip": "169.254.88.99", "default_gateway": "Not Detected"},
        "adapters": [{"interface": "Ethernet", "is_up": True, "ipv4": "169.254.88.99"}],
        "gateway_test": {"status": "FAIL", "target": "Not Detected"},
        "dns_results": [],
        "ping_results": [],
        "tcp_results": []
    }
    findings = diagnose_network_snapshot(apipa_snapshot)
    assert any("DHCP IP Assignment" in f["test_name"] for f in findings)
    assert findings[0]["confidence"] == "HIGH"
    print(f"  -> Detected: {findings[0]['test_name']}")
    print(f"  -> Diagnosis: {findings[0]['likely_cause']}")
    print(f"  -> Confidence: {findings[0]['confidence']}")
    print("  => RESULT: PASS (APIPA starvation correctly diagnosed)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 3: Gateway Unreachable / Physical Link Drop
    # -------------------------------------------------------------
    print("\n[TEST CASE 3] Diagnostic Engine: Default Gateway Unreachable")
    gw_fail_snapshot = {
        "primary_info": {"local_ip": "192.168.1.100", "default_gateway": "192.168.1.1"},
        "adapters": [{"interface": "Wi-Fi", "is_up": True, "ipv4": "192.168.1.100"}],
        "gateway_test": {"status": "FAIL", "target": "192.168.1.1", "error": "Request timed out"},
        "dns_results": [],
        "ping_results": [],
        "tcp_results": []
    }
    findings = diagnose_network_snapshot(gw_fail_snapshot)
    assert any("Default Gateway Reachability" in f["test_name"] for f in findings)
    print(f"  -> Detected: {findings[0]['test_name']}")
    print(f"  -> Recommended Action: {findings[0]['recommended_action']}")
    print("  => RESULT: PASS (Gateway failure correctly diagnosed)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 4: ICMP Blocked vs TCP Open (Firewall Filter)
    # -------------------------------------------------------------
    print("\n[TEST CASE 4] Diagnostic Engine: ICMP Firewall Drop vs Active TCP Web")
    firewall_snapshot = {
        "primary_info": {"local_ip": "192.168.1.100", "default_gateway": "192.168.1.1"},
        "adapters": [{"interface": "Wi-Fi", "is_up": True, "ipv4": "192.168.1.100"}],
        "gateway_test": {"status": "PASS", "target": "192.168.1.1", "rtt_avg_ms": 1.5},
        "dns_results": [{"hostname": "google.com", "status": "PASS", "latency_ms": 12.0}],
        "ping_results": [{"target": "8.8.8.8", "status": "FAIL", "error": "100% loss"}],
        "tcp_results": [
            {"service": "Google HTTP (80)", "status": "PASS", "latency_ms": 18.0},
            {"service": "Cloudflare HTTPS (443)", "status": "PASS", "latency_ms": 20.0}
        ]
    }
    findings = diagnose_network_snapshot(firewall_snapshot)
    assert any("ICMP Ping vs TCP Transport" in f["test_name"] for f in findings)
    print(f"  -> Detected: {findings[0]['test_name']}")
    print(f"  -> Explanation: {findings[0]['likely_cause']}")
    print(f"  -> Confidence: {findings[0]['confidence']}")
    print("  => RESULT: PASS (Firewall ICMP filter distinguished from outage)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 5: Degraded Link Quality (High Latency & Packet Loss)
    # -------------------------------------------------------------
    print("\n[TEST CASE 5] Diagnostic Engine: Degraded Latency & Packet Loss")
    degraded_snapshot = {
        "primary_info": {"local_ip": "192.168.1.100", "default_gateway": "192.168.1.1"},
        "adapters": [{"interface": "Wi-Fi", "is_up": True, "ipv4": "192.168.1.100"}],
        "gateway_test": {"status": "PASS", "target": "192.168.1.1", "rtt_avg_ms": 2.0},
        "dns_results": [{"hostname": "google.com", "status": "PASS", "latency_ms": 18.0}],
        "ping_results": [{"target": "8.8.8.8", "status": "WARNING", "rtt_avg_ms": 220.0, "loss_pct": 20.0}],
        "tcp_results": [{"service": "HTTPS", "status": "PASS", "latency_ms": 210.0}]
    }
    findings = diagnose_network_snapshot(degraded_snapshot)
    assert any("Network Link Quality" in f["test_name"] for f in findings)
    print(f"  -> Detected: {findings[0]['test_name']}")
    print(f"  -> Evidence: {findings[0]['actual_result']}")
    print("  => RESULT: PASS (Degraded wireless link quality detected)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 6: Cisco IOS CLI: Interface Administratively Shutdown
    # -------------------------------------------------------------
    print("\n[TEST CASE 6] Cisco Lab Parser: Interface Administratively Shutdown")
    cisco_int_cli = """
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0/0   10.10.10.1      YES manual up                    up      
GigabitEthernet0/0/1   10.10.20.1      YES manual administratively down down    
GigabitEthernet0/0/2   10.10.99.1      YES manual up                    up      
"""
    parsed_cli = parse_show_ip_interface_brief(cisco_int_cli, "R1-Campus")
    assert parsed_cli["issue_count"] == 1
    issue = parsed_cli["issues"][0]
    assert issue["interface"] == "GigabitEthernet0/0/1"
    assert "no shutdown" in issue["cisco_fix"]
    print(f"  -> Device: {parsed_cli['device_name']}")
    print(f"  -> Flagged Fault: {issue['condition']} on {issue['interface']}")
    print(f"  -> Generated Cisco Fix:\n{issue['cisco_fix']}")
    print("  => RESULT: PASS (Shutdown interface isolated with exact Cisco CLI fix)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 7: Cisco IOS CLI: Missing Static Route to Branch
    # -------------------------------------------------------------
    print("\n[TEST CASE 7] Cisco Lab Parser: Missing WAN Static Route")
    cisco_route_cli = """
Codes: L - local, C - connected, S - static, R - RIP
Gateway of last resort is not set

C    10.10.10.0/24 is directly connected, GigabitEthernet0/0/0.10
L    10.10.10.1/32 is directly connected, GigabitEthernet0/0/0.10
C    10.10.20.0/24 is directly connected, GigabitEthernet0/0/0.20
C    10.10.99.0/30 is directly connected, GigabitEthernet0/0/2
"""
    parsed_route = parse_show_ip_route(cisco_route_cli, "R1-Campus")
    assert parsed_route["total_routes"] == 4
    assert parsed_route["has_default_route"] is False
    print(f"  -> Total Extracted Routes: {parsed_route['total_routes']}")
    print(f"  -> Default Gateway Set: {parsed_route['has_default_route']}")
    print("  => RESULT: PASS (Routing table correctly parsed and audited)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 8: Cisco IOS CLI: Switch VLAN Brief Configuration
    # -------------------------------------------------------------
    print("\n[TEST CASE 8] Cisco Lab Parser: Switch VLAN Brief Configuration")
    cisco_vlan_cli = """
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4
10   Students                         active    Fa0/5, Fa0/6
20   Faculty                          active    Fa0/7, Fa0/8
"""
    parsed_vlan = parse_show_vlan_brief(cisco_vlan_cli, "SW-Core")
    assert len(parsed_vlan["vlans"]) == 3
    assert parsed_vlan["vlans"][1]["name"] == "Students"
    assert parsed_vlan["vlans"][2]["name"] == "Faculty"
    print(f"  -> Extracted {len(parsed_vlan['vlans'])} VLAN entries.")
    print(f"  -> VLAN 10 Ports: {parsed_vlan['vlans'][1]['ports']}")
    print(f"  -> VLAN 20 Ports: {parsed_vlan['vlans'][2]['ports']}")
    print("  => RESULT: PASS (VLAN assignments extracted cleanly)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 9: Cisco IOS CLI: PC Ping Failure (100% Loss)
    # -------------------------------------------------------------
    print("\n[TEST CASE 9] Cisco Lab Parser: Host PC Ping 100% Loss Failure")
    cisco_ping_cli = """
Pinging 10.10.10.1 with 32 bytes of data:
Request timed out.
Request timed out.
Request timed out.
Request timed out.

Ping statistics for 10.10.10.1:
    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)
"""
    parsed_ping = parse_cisco_ping_output(cisco_ping_cli, "PC-Student-1")
    assert parsed_ping["success_rate_pct"] == 0.0
    assert parsed_ping["target_ip"] == "10.10.10.1"
    assert parsed_ping["issue_count"] == 1
    print(f"  -> Target IP: {parsed_ping['target_ip']}")
    print(f"  -> Success Rate: {parsed_ping['success_rate_pct']}%")
    print(f"  -> Diagnosis: {parsed_ping['issues'][0]['condition']}")
    print("  => RESULT: PASS (Cisco PC ping failure parsed accurately)")
    passed_scenarios += 1

    # -------------------------------------------------------------
    # TEST CASE 10: Before-and-After Recovery Diff Verification
    # -------------------------------------------------------------
    print("\n[TEST CASE 10] Recovery Engine: Before-and-After Recovery Verification")
    tracker = NetworkHistoryTracker(max_entries=50)

    # State A: Gateway failed
    snap_before = {
        "timestamp": "2026-10-26T14:00:00",
        "overall_status": "FAIL",
        "gateway_test": {"status": "FAIL", "target": "192.168.0.1", "error": "Request timed out"},
        "dns_results": [],
        "tcp_results": []
    }
    tracker.add_snapshot(snap_before)

    # State B: Gateway fixed & recovered
    snap_after = {
        "timestamp": "2026-10-26T14:00:05",
        "overall_status": "PASS",
        "gateway_test": {"status": "PASS", "target": "192.168.0.1", "rtt_avg_ms": 2.1},
        "dns_results": [],
        "tcp_results": []
    }
    events = tracker.add_snapshot(snap_after)
    diff = compare_recovery_snapshots(snap_before, snap_after)

    assert len(events) == 1
    assert events[0]["event_type"] == "RECOVERY"
    assert diff["recovery_verified"] is True
    assert len(diff["restored_items"]) == 1
    print(f"  -> Transition Event: {events[0]['event_type']} - {events[0]['description']}")
    print(f"  -> Restored Item: {diff['restored_items'][0]['service']} (Before: {diff['restored_items'][0]['before']} -> After: {diff['restored_items'][0]['after']})")
    print(f"  -> Formal Recovery Verified: {diff['recovery_verified']}")
    print("  => RESULT: PASS (Recovery verification algorithm mathematically verified)")
    passed_scenarios += 1

    print("\n" + "=" * 70)
    print(f"MASTER TEST SUITE SUMMARY: {passed_scenarios}/{total_scenarios} SCENARIOS PASSED (100% SUCCESS)")
    print("=" * 70)

if __name__ == "__main__":
    run_all_comprehensive_tests()
