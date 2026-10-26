"""
Cisco Packet Tracer Lab Mode Parser & Diagnostic Engine.
Parses user-submitted command outputs from Cisco IOS devices:
- show ip interface brief
- show ip route
- show vlan brief
- show interfaces trunk
- ping results
Identifies faults, misconfigurations, and provides actionable Cisco CLI recovery steps.
"""

import re
from typing import Dict, List, Any


def parse_show_ip_interface_brief(raw_text: str, device_name: str = "Device") -> Dict[str, Any]:
    """
    Parses 'show ip interface brief' output.
    Format typically:
    Interface              IP-Address      OK? Method Status                Protocol
    GigabitEthernet0/0/0   192.168.1.1     YES manual up                    up
    GigabitEthernet0/0/1   unassigned      YES unset  administratively down down
    """
    interfaces = []
    issues = []

    lines = raw_text.strip().splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.lower().startswith("interface"):
            continue

        parts = re.split(r"\s{2,}|\t+|\s+(?=YES|NO|manual|unset|up|down|administratively)", line_clean)
        # Fallback split if spacing varies
        if len(parts) < 4:
            parts = line_clean.split()

        if len(parts) >= 4:
            iface_name = parts[0]
            ip_addr = parts[1]
            status = "unknown"
            protocol = "unknown"

            # Check for administratively down
            lower_line = line_clean.lower()
            if "administratively down" in lower_line:
                status = "administratively down"
            elif " down" in lower_line:
                status = "down"
            elif " up" in lower_line:
                status = "up"

            # Check protocol (last item typically)
            if parts[-1].lower() in ["up", "down"]:
                protocol = parts[-1].lower()

            record = {
                "interface": iface_name,
                "ip_address": ip_addr,
                "status": status,
                "protocol": protocol
            }
            interfaces.append(record)

            # Analyze interface issues
            if "administratively down" in status:
                issues.append({
                    "interface": iface_name,
                    "condition": "Interface is administratively shutdown",
                    "likely_cause": f"The '{iface_name}' port has been disabled by the administrator via the 'shutdown' command.",
                    "alternative_causes": ["New interface that was never enabled with 'no shutdown'."],
                    "cisco_fix": f"enable\nconfigure terminal\ninterface {iface_name}\nno shutdown\nend\nwrite memory",
                    "next_command": f"show ip interface brief"
                })
            elif status == "down" or protocol == "down":
                issues.append({
                    "interface": iface_name,
                    "condition": "Interface is Down / Down (Physical or Data Link Layer failure)",
                    "likely_cause": f"No physical cable connected, wrong cable type, or the device on the other end is powered off/shutdown.",
                    "alternative_causes": [
                        "Duplex or speed mismatch between connected switches/routers.",
                        "Layer 2 keepalive failure or encapsulation mismatch."
                    ],
                    "cisco_fix": f"Check cable connection in Packet Tracer to {iface_name}, verify the opposite interface is 'no shutdown'.",
                    "next_command": f"show interface {iface_name}"
                })
            elif ip_addr.lower() == "unassigned" and status == "up":
                # Only a warning if it's a routed port that needs an IP
                pass

    return {
        "command": "show ip interface brief",
        "device_name": device_name,
        "parsed_interfaces": interfaces,
        "issue_count": len(issues),
        "issues": issues
    }


def parse_show_ip_route(raw_text: str, device_name: str = "Device") -> Dict[str, Any]:
    """
    Parses 'show ip route' output.
    Identifies connected (C), local (L), static (S), and OSPF (O) routes.
    Detects if default gateway or remote subnets are missing.
    """
    routes = []
    issues = []
    lines = raw_text.strip().splitlines()

    has_gateway_of_last_resort = False
    gateway_text = ""

    for line in lines:
        line_clean = line.strip()
        if "Gateway of last resort is" in line_clean:
            gateway_text = line_clean
            if "not set" not in line_clean.lower():
                has_gateway_of_last_resort = True

        # Match routes e.g.:
        # C        192.168.1.0/24 is directly connected, GigabitEthernet0/0/0
        # S        10.20.10.0/24 [1/0] via 10.10.99.2
        # O        10.10.20.0/24 [110/2] via 10.10.99.1, ...
        route_match = re.match(r"^([C|L|S|O|R|B|D]\*?)\s+([\d\.\/]+)\s+(?:\[\d+\/\d+\]\s+)?(?:via\s+([\d\.]+)|is directly connected)", line_clean)
        if route_match:
            code = route_match.group(1).strip()
            network = route_match.group(2).strip()
            next_hop = route_match.group(3) or "Directly Connected"
            routes.append({
                "type": code,
                "network": network,
                "next_hop": next_hop
            })

    # Analysis
    if not routes:
        issues.append({
            "condition": "Routing Table is empty or unpopulated",
            "likely_cause": "No active routed interfaces or routing protocols have been configured on this router.",
            "alternative_causes": ["All router interfaces are in 'down' state."],
            "cisco_fix": "Configure IP addresses on router interfaces and run 'no shutdown', or add static routes.",
            "next_command": "show ip interface brief"
        })

    return {
        "command": "show ip route",
        "device_name": device_name,
        "gateway_of_last_resort": gateway_text or "Gateway of last resort is not set",
        "has_default_route": has_gateway_of_last_resort,
        "total_routes": len(routes),
        "parsed_routes": routes,
        "issue_count": len(issues),
        "issues": issues
    }


def parse_show_vlan_brief(raw_text: str, device_name: str = "Switch") -> Dict[str, Any]:
    """
    Parses 'show vlan brief' output from Cisco switches.
    Identifies VLAN IDs, names, status, and assigned ports.
    """
    vlans = []
    lines = raw_text.strip().splitlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.lower().startswith("vlan") or set(line_clean) == {"-"} or "----" in line_clean:
            continue

        # Format: 1    default    active    Fa0/1, Fa0/2, Fa0/3
        # Format: 10   Students   active    Fa0/5, Fa0/6
        match = re.match(r"^(\d+)\s+([a-zA-Z0-9_\-]+)\s+(active|act\/unsup|suspended)\s*(.*)$", line_clean, re.IGNORECASE)
        if match:
            vlan_id = int(match.group(1))
            vlan_name = match.group(2)
            status = match.group(3)
            ports_raw = match.group(4).strip()
            port_list = [p.strip() for p in ports_raw.split(",") if p.strip()] if ports_raw else []

            vlans.append({
                "vlan_id": vlan_id,
                "name": vlan_name,
                "status": status,
                "ports": port_list
            })

    issues = []
    vlan_ids = [v["vlan_id"] for v in vlans]
    # Check if standard campus VLANs are configured
    if vlan_ids and 10 not in vlan_ids and 20 not in vlan_ids and max(vlan_ids) == 1:
        issues.append({
            "condition": "Only default VLAN 1 exists; custom campus VLANs (Students, Faculty) missing",
            "likely_cause": "VLANs 10 and 20 have not been created on this switch yet.",
            "alternative_causes": ["Switch was recently reloaded or erased without saving vlan.dat."],
            "cisco_fix": "enable\nconfigure terminal\nvlan 10\n name Students\nvlan 20\n name Faculty\nexit",
            "next_command": "show vlan brief"
        })

    return {
        "command": "show vlan brief",
        "device_name": device_name,
        "vlans": vlans,
        "issue_count": len(issues),
        "issues": issues
    }


def parse_show_interfaces_trunk(raw_text: str, device_name: str = "Switch") -> Dict[str, Any]:
    """
    Parses 'show interfaces trunk' output.
    Format:
    Port        Mode         Encapsulation  Status        Native vlan
    Gig0/1      on           802.1q         trunking      1
    """
    trunks = []
    issues = []
    lines = raw_text.strip().splitlines()

    is_trunk_section = False
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if "Port" in line_clean and "Mode" in line_clean and "Status" in line_clean:
            is_trunk_section = True
            continue
        if "Port" in line_clean and "Vlans allowed" in line_clean:
            is_trunk_section = False
            continue

        if is_trunk_section:
            parts = line_clean.split()
            if len(parts) >= 5:
                port = parts[0]
                mode = parts[1]
                encap = parts[2]
                status = parts[3]
                native_vlan = parts[4]
                trunks.append({
                    "port": port,
                    "mode": mode,
                    "encapsulation": encap,
                    "status": status,
                    "native_vlan": native_vlan
                })

    if not trunks and raw_text.strip():
        # No trunk lines found
        issues.append({
            "condition": "No active trunk interfaces detected",
            "likely_cause": "The switchport uplink to the router or distribution switch is configured as 'access' mode instead of 'trunk', or the interface is down.",
            "alternative_causes": ["DTP (Dynamic Trunking Protocol) negotiation failed or was set to 'access'."],
            "cisco_fix": "enable\nconfigure terminal\ninterface <uplink_interface>\nswitchport mode trunk\nno shutdown\nend",
            "next_command": "show interfaces trunk"
        })

    return {
        "command": "show interfaces trunk",
        "device_name": device_name,
        "trunks": trunks,
        "issue_count": len(issues),
        "issues": issues
    }


def parse_cisco_ping_output(raw_text: str, source_device: str = "PC / Router") -> Dict[str, Any]:
    """
    Parses Packet Tracer ping outputs from both Cisco IOS router/switch and Cisco PC terminal:
    Router format:
    Sending 5, 100-byte ICMP Echos to 10.10.10.1, timeout is 2 seconds:
    !!!!! (or ..... or U.U.U)
    Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms

    PC format:
    Pinging 10.10.10.1 with 32 bytes of data:
    Reply from 10.10.10.1: bytes=32 time=1ms TTL=128
    Ping statistics for 10.10.10.1:
        Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
    """
    success_rate = 0.0
    sent = 0
    received = 0
    target_ip = "Unknown"
    issues = []

    # Check Cisco IOS Router format
    # "Success rate is 100 percent (5/5)" or "Success rate is 0 percent (0/5)"
    ios_match = re.search(r"Success rate is\s+(\d+)\s+percent\s*\((\d+)\/(\d+)\)", raw_text, re.IGNORECASE)
    # Target from "Sending 5, 100-byte ICMP Echos to 10.10.10.1"
    target_match = re.search(r"ICMP Echos to\s+([\d\.]+)", raw_text, re.IGNORECASE)
    if target_match:
        target_ip = target_match.group(1)

    if ios_match:
        success_rate = float(ios_match.group(1))
        received = int(ios_match.group(2))
        sent = int(ios_match.group(3))
    else:
        # Check PC ping format
        pc_target = re.search(r"Pinging\s+([\d\.]+)", raw_text, re.IGNORECASE)
        if pc_target:
            target_ip = pc_target.group(1)

        pc_stats = re.search(r"Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)", raw_text, re.IGNORECASE)
        if pc_stats:
            sent = int(pc_stats.group(1))
            received = int(pc_stats.group(2))
            if sent > 0:
                success_rate = round((received / sent) * 100.0, 1)

    # Diagnostic analysis based on output strings
    if "U.U.U" in raw_text or "Destination host unreachable" in raw_text:
        issues.append({
            "condition": f"Destination Host Unreachable ({target_ip})",
            "likely_cause": "The local router has no route to the destination network, or ARP resolution failed on the local subnet.",
            "alternative_causes": [
                "Default gateway is not configured on the sending PC.",
                "Subnet mask mismatch between sender and receiver.",
                "Missing static route or routing protocol advertisement."
            ],
            "cisco_fix": "Verify IP configuration on sender ('ipconfig') and check routing table on router ('show ip route').",
            "next_command": f"ping {target_ip}"
        })
    elif success_rate == 0.0:
        issues.append({
            "condition": f"Complete Connectivity Failure (0% Success Rate to {target_ip})",
            "likely_cause": "Target device is powered off, port is shutdown, wrong VLAN assigned, or incorrect default gateway.",
            "alternative_causes": [
                "VLAN trunk native mismatch or trunk link down.",
                "Firewall or ACL blocking ICMP.",
                "IP address conflict on target network."
            ],
            "cisco_fix": f"1. Ping local gateway first.\n2. Verify target interface status ('show ip interface brief').\n3. Verify VLAN assignment ('show vlan brief').",
            "next_command": f"ping {target_ip}"
        })
    elif success_rate < 100.0:
        # First packet lost due to ARP resolution is normal in Cisco Packet Tracer (.!!!!)
        if ".!" in raw_text or (sent == 5 and received == 4) or (sent == 4 and received == 3):
            # Normal ARP learning in Packet Tracer
            pass
        else:
            issues.append({
                "condition": f"Packet Loss Detected ({100 - success_rate}% lost)",
                "likely_cause": "Initial ARP table resolution delay, duplex mismatch, or unstable link.",
                "alternative_causes": ["High network load or buffer drops in simulation."],
                "cisco_fix": f"Repeat the ping command. In Packet Tracer, the first ping often drops while ARP resolves the MAC address.",
                "next_command": f"ping {target_ip}"
            })

    return {
        "command": "ping",
        "device_name": source_device,
        "target_ip": target_ip,
        "sent": sent,
        "received": received,
        "success_rate_pct": success_rate,
        "issue_count": len(issues),
        "issues": issues,
        "raw_text": raw_text.strip()
    }


def analyze_pt_evidence(command_type: str, raw_text: str, device_name: str = "Device") -> Dict[str, Any]:
    """
    Main entry point for analyzing submitted Cisco Packet Tracer output.
    Autodetects command type from raw text if user dropdown differs.
    """
    text_lower = raw_text.lower()
    cmd = command_type.lower()

    # Intelligent Auto-Detection based on signature Cisco CLI headers
    if "ip-address" in text_lower or ("interface" in text_lower and "protocol" in text_lower):
        return parse_show_ip_interface_brief(raw_text, device_name)
    elif "vlan name" in text_lower or ("vlan" in text_lower and "status" in text_lower and "ports" in text_lower):
        return parse_show_vlan_brief(raw_text, device_name)
    elif "encapsulation" in text_lower and ("trunking" in text_lower or "native vlan" in text_lower):
        return parse_show_interfaces_trunk(raw_text, device_name)
    elif "pinging" in text_lower or "icmp echos to" in text_lower or "success rate is" in text_lower:
        return parse_cisco_ping_output(raw_text, device_name)
    elif "gateway of last resort" in text_lower or "directly connected" in text_lower:
        return parse_show_ip_route(raw_text, device_name)

    # Fallback to selected dropdown
    if "brief" in cmd and "ip" in cmd:
        return parse_show_ip_interface_brief(raw_text, device_name)
    elif "route" in cmd:
        return parse_show_ip_route(raw_text, device_name)
    elif "vlan" in cmd:
        return parse_show_vlan_brief(raw_text, device_name)
    elif "trunk" in cmd:
        return parse_show_interfaces_trunk(raw_text, device_name)
    elif "ping" in cmd:
        return parse_cisco_ping_output(raw_text, device_name)
    else:
        # Generic heuristic parser
        issues = []
        if "administratively down" in text_lower:
            issues.append({
                "condition": "Administrative Shutdown detected",
                "likely_cause": "One or more ports are shutdown.",
                "alternative_causes": [],
                "cisco_fix": "interface <id> -> no shutdown",
                "next_command": "show ip interface brief"
            })
        return {
            "command": command_type,
            "device_name": device_name,
            "issue_count": len(issues),
            "issues": issues,
            "raw_text": raw_text
        }
