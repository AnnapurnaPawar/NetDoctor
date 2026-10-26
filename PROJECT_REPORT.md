# NetDoctor: Real-Time Network Monitoring, Fault Diagnosis and Recovery Verification System

**Department of Computer Science & Engineering**  
**Course:** Computer Networks & Network Systems Lab  
**Author / Candidate:** Student Project  
**System Environment:** Windows 10/11, Python 3.13, Cisco Packet Tracer 9.0.1, Wireshark  

---

## Abstract
Traditional network diagnostic tools provide binary operational indicators (*"Up"* or *"Down"*) without elucidating underlying structural causes or contextualizing transport vs. network layer behaviors. **NetDoctor** is an integrated software and simulation framework that bridges real-world host telemetry with simulated enterprise campus networks. It comprises a Python-based real-time Windows monitoring agent, an explainable rule-based expert diagnostic engine, and a specialized **Cisco Packet Tracer Lab Mode** for analyzing live CLI outputs. By cross-correlating Layer 3 ICMP reachability, Layer 4 TCP handshakes, and Layer 7 DNS resolutions, NetDoctor avoids common diagnostic pitfalls such as false-positive outages caused by ICMP filtering. Furthermore, it validates configuration changes through automated before-and-after recovery diffs.

---

## 1. Introduction & Problem Statement
Network administrators and engineering students frequently encounter ambiguities during network troubleshooting:
- A host can access websites in a web browser, but standard command-line `ping` commands time out because intermediary firewalls drop ICMP traffic.
- A client machine receives an APIPA address (`169.254.x.x`), but standard users cannot interpret what component failed.
- In educational environments using Cisco Packet Tracer, students struggle to identify why virtual devices cannot communicate across VLANs or WAN boundaries.

**NetDoctor** resolves these challenges by providing an evidence-based, explainable diagnostics platform that monitors genuine Windows adapters and parses Cisco IOS device states to guide users toward resolution.

---

## 2. System Architecture & Methodology
NetDoctor is architected into four decoupled layers:

```
+-------------------------------------------------------------+
|                 Streamlit Web Presentation Layer            |
|   (Overview, Live Monitor, Fault Diagnostics, PT Lab, CSV)  |
+-------------------------------------------------------------+
                              |
        +---------------------+---------------------+
        |                                           |
+--------------------------+             +--------------------------+
|  Real-Time Windows Engine|             | Packet Tracer Lab Parser |
|  - Adapter Telemetry     |             | - show ip int brief      |
|  - Gateway Reachability  |             | - show ip route          |
|  - DNS Latency (UDP 53)  |             | - show vlan brief        |
|  - TCP Handshake (L4)    |             | - show interfaces trunk  |
|  - ICMP Echo Statistics  |             | - Cisco Ping Output      |
+--------------------------+             +--------------------------+
        |                                           |
        +---------------------+---------------------+
                              |
+-------------------------------------------------------------+
|               Rule-Based Fault Diagnosis Engine             |
|   (Evidence Extraction -> Hypothesis -> Confidence Metric)  |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|           History Tracker & Recovery Diff Evaluator         |
|         (State Transition Logging & CSV Export Engine)       |
+-------------------------------------------------------------+
```

---

## 3. Technology Stack
- **Python 3.13.2:** Core scripting, socket probes, and subprocess execution.
- **Streamlit 1.66.1:** Reactive, web-based dashboard with responsive metric tiles.
- **Pandas 3.1.0:** Time-series telemetry organization and CSV data serialization.
- **Pytest 9.1.1:** Automated regression test suite for regex parsers and diagnostic logic.
- **Cisco Packet Tracer 9.0.1:** Simulated campus network with 13 enterprise devices.
- **Wireshark:** Independent validation of packet captures on physical network interfaces.

---

## 4. Real-Time Network Monitoring Implementation
The Windows monitoring subsystem performs non-blocking diagnostic probes across the protocol stack:
1. **Host & Adapter Inspection:** Uses `psutil.net_if_addrs()` and Windows route tables to identify active adapters, subnet masks, physical MAC addresses, and default gateway IPv4 addresses.
2. **Default Gateway Reachability:** Issues ICMP echo requests to the detected default gateway to ensure local Layer 2/3 link integrity.
3. **DNS Hostname Resolution:** Measures name resolution latency using `socket.getaddrinfo()` against global authoritative resolvers (`google.com`, `cloudflare.com`).
4. **Transport Layer Handshakes:** Executes genuine TCP 3-way handshakes to ports `53` (DNS over TCP), `80` (HTTP), and `443` (HTTPS) using non-blocking Python sockets.
5. **Quality Profiling:** Computes packet loss percentages and minimum, average, and maximum round-trip times (RTT).

---

## 5. Evidence-Based Fault Diagnosis Engine
NetDoctor adheres to strict evidential rules to avoid unsubstantiated claims:
- **Rule: ICMP Blocked vs. Network Outage:** If destination pings experience 100% loss but TCP handshakes to port 80/443 complete in `< 50 ms`, NetDoctor reports high confidence that internet access is fully functional and that an upstream firewall is filtering ICMP.
- **Rule: APIPA Assignment:** If an operational interface possesses an address within `169.254.0.0/16`, NetDoctor diagnoses DHCP starvation or failure to communicate with the local DHCP server.
- **Rule: Gateway Reachability Failure:** If the default gateway fails ICMP echo probes, NetDoctor advises checking physical cable attachment, Wi-Fi association, or local router power state.

---

## 6. Cisco Packet Tracer Campus Topology
A 13-device campus network was constructed in Cisco Packet Tracer:
- **Main Campus Router (`R1-Campus`):** Handles inter-VLAN routing via subinterfaces (`Gi0/0/0.10`, `Gi0/0/0.20`, `Gi0/0/0.30`) using 802.1Q encapsulation.
- **Branch Router (`R2-Branch`):** Connects the branch subnet (`10.20.10.0/24`) to the campus via a routed point-to-point link (`10.10.99.0/30`).
- **Core Switch (`SW-Core`):** Aggregates 802.1Q trunk connections to department switches and hosts the campus server farm.
- **VLAN Segmentation:**
  - VLAN 10 (Students): `10.10.10.0/24`
  - VLAN 20 (Faculty): `10.10.20.0/24`
  - VLAN 30 (Servers): `10.10.30.0/24` (DNS: `10.10.30.2`, Web: `10.10.30.3`)

---

## 7. Controlled Fault Scenarios & Verification

### Scenario 1: Default Gateway Misconfiguration
- **Injected Fault:** Configured `PC-Student-1` with gateway `10.10.10.99` instead of `10.10.10.1`.
- **Symptom:** Local intra-VLAN pings succeeded; cross-VLAN pings to `10.10.30.3` failed.
- **NetDoctor Lab Diagnosis:** Flagged gateway misconfiguration based on submitted ping output.
- **Correction & Recovery:** Reverted gateway to `10.10.10.1`; NetDoctor diff confirmed transition from 0% to 100% success rate.

### Scenario 2: Switchport VLAN Misassignment
- **Injected Fault:** Assigned `SW-Students` access port `Fa0/1` to VLAN 20 instead of VLAN 10.
- **Symptom:** `PC-Student-1` could not reach its default gateway `10.10.10.1`.
- **NetDoctor Lab Diagnosis:** Parsed `show vlan brief` and detected port assignment mismatch.
- **Correction & Recovery:** Executed `switchport access vlan 10`; connectivity restored.

### Scenario 3: Missing Static Route on Campus WAN
- **Injected Fault:** Removed static route `10.20.10.0 255.255.255.0 10.10.99.2` from `R1-Campus`.
- **Symptom:** Remote branch PC could not reach campus intranet web server; router returned ICMP type 3 code 1 (`Destination host unreachable`).
- **NetDoctor Lab Diagnosis:** Parsed `show ip route` and identified absence of destination network prefix.
- **Correction & Recovery:** Re-added static route; end-to-end ping confirmed recovery.

---

## 8. Wireshark Packet Inspection & Validation
To confirm that NetDoctor's diagnostic probes generate authentic network packets, Wireshark captures were conducted on the host's active Wi-Fi interface:
- **ICMP Probes:** Verified Type 8 (Echo Request) and Type 0 (Echo Reply) frame pairs.
- **DNS Queries:** Validated UDP Port 53 queries for `A` records and corresponding server replies.
- **TCP Probes:** Verified `[SYN]`, `[SYN, ACK]`, `[ACK]` three-way handshake sequence with remote servers.

---

## 9. Conclusion
NetDoctor demonstrates that combining real-world host diagnostics with simulated network laboratory parsers provides an effective, explainable educational platform. By requiring evidence before asserting root causes and verifying recovery after configuration changes, the system eliminates guesswork in network troubleshooting.
