"""
Unit tests for netdoctor.pt_parser
"""

import pytest
from netdoctor.pt_parser import (
    parse_show_ip_interface_brief,
    parse_show_ip_route,
    parse_show_vlan_brief,
    parse_show_interfaces_trunk,
    parse_cisco_ping_output
)


def test_parse_show_ip_interface_brief():
    sample_output = """
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0/0   10.10.10.1      YES manual up                    up      
GigabitEthernet0/0/1   10.10.20.1      YES manual administratively down down    
GigabitEthernet0/0/2   unassigned      YES unset  down                  down    
"""
    result = parse_show_ip_interface_brief(sample_output, "R1-Campus")
    assert len(result["parsed_interfaces"]) == 3
    assert result["issue_count"] >= 1
    # Check shutdown detection
    admin_down_issues = [i for i in result["issues"] if "administratively shutdown" in i["condition"]]
    assert len(admin_down_issues) == 1
    assert admin_down_issues[0]["interface"] == "GigabitEthernet0/0/1"
    assert "no shutdown" in admin_down_issues[0]["cisco_fix"]


def test_parse_show_ip_route():
    sample_output = """
Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 

Gateway of last resort is not set

C    10.10.10.0/24 is directly connected, GigabitEthernet0/0/0.10
L    10.10.10.1/32 is directly connected, GigabitEthernet0/0/0.10
S    10.20.10.0/24 [1/0] via 10.10.99.2
"""
    result = parse_show_ip_route(sample_output, "R1-Campus")
    assert result["total_routes"] >= 2
    assert result["has_default_route"] is False
    static_routes = [r for r in result["parsed_routes"] if "S" in r["type"]]
    assert len(static_routes) == 1
    assert static_routes[0]["network"] == "10.20.10.0/24"


def test_parse_show_vlan_brief():
    sample_output = """
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4
10   Students                         active    Fa0/5, Fa0/6
20   Faculty                          active    Fa0/7, Fa0/8
"""
    result = parse_show_vlan_brief(sample_output, "SW-Core")
    assert len(result["vlans"]) == 3
    vlan_names = [v["name"] for v in result["vlans"]]
    assert "Students" in vlan_names
    assert "Faculty" in vlan_names


def test_parse_cisco_ping_success_and_failure():
    # Router 100% success
    router_success = """
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 10.10.10.1, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms
"""
    res1 = parse_cisco_ping_output(router_success, "R2-Branch")
    assert res1["success_rate_pct"] == 100.0
    assert res1["target_ip"] == "10.10.10.1"
    assert res1["issue_count"] == 0

    # PC 0% failure
    pc_failure = """
Pinging 10.10.30.3 with 32 bytes of data:
Request timed out.
Request timed out.
Request timed out.
Request timed out.
Ping statistics for 10.10.30.3:
    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)
"""
    res2 = parse_cisco_ping_output(pc_failure, "PC-Student-1")
    assert res2["success_rate_pct"] == 0.0
    assert res2["target_ip"] == "10.10.30.3"
    assert res2["issue_count"] >= 1
    assert "Complete Connectivity Failure" in res2["issues"][0]["condition"]
