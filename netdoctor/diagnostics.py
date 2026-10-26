"""
Evidence-Based Fault Diagnosis Engine for NetDoctor.
Evaluates diagnostic snapshots and identifies root causes based on strict evidence.
Distinguishes between measured facts and hypotheses.
"""

from typing import Dict, List, Any


def diagnose_network_snapshot(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyzes a full diagnostic snapshot and returns evidence-based findings.
    Each finding strictly includes:
    - test_name
    - actual_result
    - likely_cause
    - alternative_causes
    - confidence (HIGH, MEDIUM, LOW)
    - recommended_action
    - rerun_hint
    """
    findings = []

    primary_info = snapshot.get("primary_info", {})
    local_ip = primary_info.get("local_ip", "Unknown")
    gateway_ip = primary_info.get("default_gateway", "Not Detected")
    adapters = snapshot.get("adapters", [])
    gateway_test = snapshot.get("gateway_test", {})
    dns_results = snapshot.get("dns_results", [])
    ping_results = snapshot.get("ping_results", [])
    tcp_results = snapshot.get("tcp_results", [])

    # Fact counters
    active_adapters = [a for a in adapters if a.get("is_up") and a.get("ipv4") and a.get("ipv4") != "Unassigned"]
    dns_failures = [d for d in dns_results if d.get("status") == "FAIL"]
    dns_passes = [d for d in dns_results if d.get("status") == "PASS"]
    ping_failures = [p for p in ping_results if p.get("status") == "FAIL"]
    ping_passes = [p for p in ping_results if p.get("status") == "PASS"]
    tcp_failures = [t for t in tcp_results if t.get("status") == "FAIL"]
    tcp_passes = [t for t in tcp_results if t.get("status") == "PASS"]

    # RULE 1: No active network adapter or media disconnected
    if not active_adapters:
        findings.append({
            "test_name": "Local Network Adapter State",
            "actual_result": "No network interface is reported as operational ('UP') with a valid IPv4 address.",
            "likely_cause": "The Wi-Fi adapter is turned off, in Airplane mode, or the Ethernet cable is unplugged.",
            "alternative_causes": [
                "Network adapter driver is disabled or crashed in Device Manager.",
                "Virtual network adapter conflict or missing hardware drivers."
            ],
            "confidence": "HIGH",
            "recommended_action": "Check your physical Ethernet cable, or ensure Wi-Fi is enabled and connected to your local access point.",
            "rerun_hint": "Click 'Run Diagnostics Now' after connecting to your Wi-Fi or Ethernet network."
        })
        return findings

    # RULE 2: APIPA Autoconfiguration Address (169.254.x.x)
    apipa_adapters = [a for a in active_adapters if str(a.get("ipv4", "")).startswith("169.254.")]
    if apipa_adapters:
        nic_name = apipa_adapters[0].get("interface", "Adapter")
        ip_val = apipa_adapters[0].get("ipv4")
        findings.append({
            "test_name": f"DHCP IP Assignment ({nic_name})",
            "actual_result": f"Interface {nic_name} has an APIPA address: {ip_val}.",
            "likely_cause": "Your computer could not reach a DHCP server to receive a valid local IP address.",
            "alternative_causes": [
                "The local router/DHCP pool is exhausted or DHCP service is stopped.",
                "VLAN mismatch or 802.1X network authentication failed.",
                "Local firewall is blocking DHCP offer packets (UDP 67/68)."
            ],
            "confidence": "HIGH",
            "recommended_action": "Restart your Wi-Fi router, or in Windows Command Prompt run 'ipconfig /release' followed by 'ipconfig /renew'.",
            "rerun_hint": "Check the adapter status again in the Overview tab once an IP address is assigned."
        })

    # RULE 3: Default Gateway Reachability
    if gateway_test.get("status") == "FAIL":
        if len(tcp_passes) >= 2:
            # TCP traffic is flowing through the gateway to external internet targets;
            # ICMP ping is simply blocked or filtered by firewall/container policy.
            pass
        else:
            findings.append({
                "test_name": f"Default Gateway Reachability ({gateway_ip})",
                "actual_result": f"Failed to ping default gateway {gateway_ip} ({gateway_test.get('error', '100% packet loss')}).",
                "likely_cause": "Loss of communication between your PC and the local router or access point.",
                "alternative_causes": [
                    "Incorrect default gateway address configured manually.",
                    "The router is restarting, powered down, or rejecting ICMP echo requests.",
                    "Virtual adapter or VPN driver intercepting local broadcast/gateway traffic."
                ],
                "confidence": "HIGH" if gateway_ip != "Not Detected" else "MEDIUM",
                "recommended_action": "Verify you are connected to the correct Wi-Fi network and check if the router lights indicate normal operation.",
                "rerun_hint": "Test ping to your gateway using the Diagnostics tab."
            })

    # RULE 4: ICMP Blocked vs Internet Working (Crucial Real-World Diagnostic!)
    # Ping fails, but TCP port probes succeed!
    if ping_failures and len(tcp_passes) >= 2:
        findings.append({
            "test_name": "ICMP Ping vs TCP Transport Connectivity",
            "actual_result": f"Ping to destinations {', '.join(p['target'] for p in ping_failures)} failed, but TCP connections to {', '.join(t['service'] for t in tcp_passes)} succeeded.",
            "likely_cause": "An intermediate network firewall or ISP gateway is intentionally dropping ICMP (Ping) packets, while allowing normal TCP web traffic.",
            "alternative_causes": [
                "Local security software (Windows Defender Firewall or third-party antivirus) blocking outbound ICMP echo.",
                "Host-specific ICMP filtering at destination servers."
            ],
            "confidence": "HIGH",
            "recommended_action": "No repair needed for general browsing! Your internet connection is functional. ICMP is simply filtered by network security policies.",
            "rerun_hint": "Verify via the TCP Service Connectivity section in Live Monitoring."
        })

    # RULE 5: Complete Internet Outage (Gateway Up, but both Ping and TCP Fail)
    elif gateway_test.get("status") == "PASS" and (len(ping_failures) == len(ping_results)) and (len(tcp_failures) == len(tcp_results)):
        findings.append({
            "test_name": "Upstream WAN / Internet Connectivity",
            "actual_result": "Local gateway responds normally, but all external ICMP and TCP targets are unreachable.",
            "likely_cause": "The local router has lost its WAN (Internet) uplink connection to the Internet Service Provider (ISP).",
            "alternative_causes": [
                "ISP regional outage or authentication (PPPoE/DHCP) failure at the modem.",
                "Upstream routing table failure on the edge router.",
                "Captive portal / Wi-Fi login screen requiring authentication."
            ],
            "confidence": "HIGH",
            "recommended_action": "Open a browser to check for a captive portal login page, or inspect the internet LED indicator on your broadband modem/router.",
            "rerun_hint": "Run the Diagnostics test again once the modem's WAN light is solid green."
        })

    # RULE 6: DNS Failure with Healthy IP Transport
    if dns_failures and (len(ping_passes) > 0 or len(tcp_passes) > 0):
        failed_domains = [d["hostname"] for d in dns_failures]
        findings.append({
            "test_name": "DNS Name Resolution",
            "actual_result": f"Failed to resolve hostnames: {', '.join(failed_domains)}, while direct IP connectivity is working.",
            "likely_cause": "The configured DNS server is unreachable, slow to respond, or dropping queries on UDP/TCP port 53.",
            "alternative_causes": [
                "Local DNS client resolver cache is corrupted.",
                "Enterprise or ISP content filtering / DNS sinkholing.",
                "Misconfigured static DNS server addresses on your network adapter."
            ],
            "confidence": "HIGH",
            "recommended_action": "Try changing your adapter DNS settings to public resolvers like Cloudflare (1.1.1.1) or Google (8.8.8.8), or run 'ipconfig /flushdns'.",
            "rerun_hint": "Perform an individual DNS lookup in the Diagnostics tab."
        })

    # RULE 7: Degraded Network (Latency / Packet Loss)
    high_latency_pings = [p for p in ping_results if p.get("rtt_avg_ms") and p.get("rtt_avg_ms") > 150.0]
    lossy_pings = [p for p in ping_results if 0 < p.get("loss_pct", 0) < 100.0]

    if high_latency_pings or lossy_pings:
        lat_text = f"High latency ({high_latency_pings[0]['rtt_avg_ms']} ms)" if high_latency_pings else ""
        loss_text = f"Packet loss ({lossy_pings[0]['loss_pct']}%)" if lossy_pings else ""
        details = " and ".join(filter(None, [lat_text, loss_text]))
        findings.append({
            "test_name": "Network Link Quality & Latency",
            "actual_result": f"Detected degraded performance: {details}.",
            "likely_cause": "Wireless channel congestion, weak Wi-Fi signal, or heavy background bandwidth consumption.",
            "alternative_causes": [
                "Bufferbloat or CPU saturation on the local Wi-Fi router.",
                "ISP route congestion along the transit path."
            ],
            "confidence": "MEDIUM",
            "recommended_action": "Move closer to your Wi-Fi access point, switch from 2.4 GHz to 5 GHz, or pause large downloads/streaming.",
            "rerun_hint": "Monitor the live response-time chart over several monitoring intervals."
        })

    # RULE 8: All Healthy
    if not findings:
        findings.append({
            "test_name": "Comprehensive Network Health",
            "actual_result": "All diagnostic tests (Gateway, DNS, ICMP, and TCP Services) passed within normal operational thresholds.",
            "likely_cause": "Network is operating in an optimal state with no detected faults.",
            "alternative_causes": [],
            "confidence": "HIGH",
            "recommended_action": "No action needed. Current network configuration and path latency are healthy.",
            "rerun_hint": "Leave monitoring active to track long-term stability."
        })

    return findings
