# NetDoctor: Master Project Record & Conversation Context

This master record captures the complete architectural, deployment, testing, and demonstration state of **NetDoctor**. Whenever starting a new session or referencing **NetDoctor**, read this document to instantly resume with full project context.

---

## 1. Project Overview & Remote Links

* **Project Name:** NetDoctor — Real-Time Network Monitoring, Fault Diagnosis, and Recovery Verification System
* **GitHub Repository:** [https://github.com/AnnapurnaPawar/NetDoctor.git](https://github.com/AnnapurnaPawar/NetDoctor.git)
* **Deployed Web URL:** [https://netdoctor1208.streamlit.app](https://netdoctor1208.streamlit.app)
* **Local Project Directory:** `C:\Users\annap\.gemini\antigravity\scratch\NetDoctor`
* **Local Web Dashboard:** `http://localhost:8501` (Launch via `streamlit run app.py` or `run_netdoctor.bat`)

---

## 2. Architecture & Deliverables

NetDoctor is divided into two synchronized components:

### A. Real-Time Multi-Layer Network Monitor (Software Engine)
* **Layer 3 (Network Layer):** Default gateway discovery, IP reachability, latency, and packet loss.
* **Layer 4 (Transport Layer):** Active TCP three-way handshakes to ports `53` (DNS), `80` (HTTP), and `443` (HTTPS) to verify true web transport.
* **Layer 7 (Application Layer):** DNS resolution against public resolvers (`google.com`, `cloudflare.com`, etc.).
* **Rule-Based Diagnostic Expert System (`netdoctor/diagnostics.py`):**
  - Isolates APIPA autoconfiguration (`169.254.x.x`).
  - Detects physical network interface down / cable unplugged.
  - Distinguishes between firewall ICMP drops vs. true internet outages (prevents false alarms when TCP works).
  - Pinpoints default gateway failure and degraded wireless link quality.
* **Cloud Container Reconciliation:** Detects when running inside Streamlit Cloud / AWS containers (where raw ICMP sockets are restricted) and verifies health via Layer 4 TCP/DNS forwarding so the system displays `● HEALTHY (PASS)`.
* **Visitor IP Detection:** Displays `Cloud Host IP (10.20.62.181)` alongside the visitor's incoming `Client IP` (`st.context.ip_address`), demonstrating client-server architecture.

### B. Cisco Packet Tracer Campus Network (`campus_network.pkt`)
* **Scale:** 13-device dual-site enterprise topology.
* **Main Campus:**
  - `R1-Campus` Router (Inter-VLAN routing via **Router-on-a-Stick** across subinterfaces `Gi0/0/0.10`, `.20`, `.30`).
  - `SW-Core` Distribution Switch (Aggregates 802.1Q trunk links).
  - `SW-Students` (VLAN 10: `10.10.10.0/24`, `PC-Student-1`, `PC-Student-2`).
  - `SW-Faculty` (VLAN 20: `10.10.20.0/24`, `PC-Faculty-1`, `PC-Faculty-2`).
  - `Server Farm` (VLAN 30: `10.10.30.0/24`, `DNS-Server 10.10.30.2`, `Web-Server 10.10.30.3`).
* **Remote Branch Office:**
  - `R2-Branch` Router (`Gi0/0/1` LAN gateway `10.20.10.1`, `SW-Branch`, `PC-Branch-1`).
* **Routed WAN Link:**
  - Point-to-point `/30` subnet `10.10.99.0/30` connecting `R1` (`10.10.99.1`) and `R2` (`10.10.99.2`) via static routing.
* **Packet Tracer Lab Mode in NetDoctor:**
  - Regex parser for Cisco commands: `show ip interface brief`, `show ip route`, `show vlan brief`, and Cisco PC ping.
  - Generates automated, ready-to-paste Cisco IOS recovery scripts (`no shutdown`, `ip route`, etc.).
  - Performs mathematical before-and-after diff to verify recovery.

---

## 3. Verification & Test Evidence

* **Automated Master Test Suite (`master_test_suite.py`):**
  - Executes 10 complete end-to-end failure and recovery scenarios:
    1. Physical Host Telemetry & Adapter Discovery (PASS)
    2. APIPA DHCP Starvation (PASS)
    3. Default Gateway Unreachable (PASS)
    4. ICMP Firewall Drop vs Active TCP Web (PASS)
    5. Degraded Latency & Wireless Packet Loss (PASS)
    6. Cisco Administratively Shutdown Interface Detection & Fix Generation (PASS)
    7. Cisco Missing WAN Static Route Detection (PASS)
    8. Cisco Switch VLAN Extraction (PASS)
    9. Cisco PC Ping 100% Loss Failure Parsing (PASS)
    10. Before-and-After Recovery Verification Engine (PASS)
  - **Result:** **10/10 SCENARIOS PASSED (100% Success Rate)**
* **Pytest Unit Test Suite (`tests/`):**
  - **Result:** **11/11 PASSED in 1.45s**
* **Wireshark Capture Evidence:**
  - Authentic capture saved at `captures/genuine_network_traffic.pcap`.

---

## 4. Key Documentation Files in the Repository

1. **`DEMO_VIDEO_SCRIPT.md`**: 3–5 minute exact script for recorded video or live demonstration.
2. **`VIVA_QUESTIONS_AND_ANSWERS.md`**: Top technical defense questions and answers.
3. **`PACKET_TRACER_LAB_GUIDE.md`**: Step-by-step device configurations and 3 controlled fault injection scenarios.
4. **`PROJECT_REPORT.md`**: Academic project report with problem statement, methodology, system architecture, and results.
5. **`README.md`**: Full project documentation with badges, installation guide, and usage instructions.

---

## 5. Quick Commands Reference

* **Launch Local Streamlit Web Dashboard:**
  ```powershell
  cd "C:\Users\annap\.gemini\antigravity\scratch\NetDoctor"
  streamlit run app.py
  ```
* **Run Master Verification Suite:**
  ```powershell
  cd "C:\Users\annap\.gemini\antigravity\scratch\NetDoctor"
  python master_test_suite.py
  ```
* **Run Pytest Unit Tests:**
  ```powershell
  cd "C:\Users\annap\.gemini\antigravity\scratch\NetDoctor"
  pytest -v
  ```
* **Push Updates to GitHub (Deploy to Streamlit Cloud):**
  ```powershell
  cd "C:\Users\annap\.gemini\antigravity\scratch\NetDoctor"
  git add .
  git commit -m "Your commit message"
  git push origin main
  git push origin main:master
  ```
