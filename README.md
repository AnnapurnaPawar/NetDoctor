# NetDoctor: Real-Time Network Monitoring & Cisco Lab Diagnosis

**NetDoctor** is a comprehensive Computer Engineering project that combines:
1. **Real-time network monitoring** of your actual Windows PC (Physical NICs, Gateway, DNS, TCP Ports, ICMP ping).
2. An **explainable diagnostic engine** that correlates symptoms to find true root causes.
3. A **Cisco Packet Tracer Lab Mode** that parses Cisco IOS command outputs, pinpoints misconfigurations, and provides CLI recovery commands.
4. **Recovery verification** that compares network state before and after manual fixes.
5. **Wireshark packet capture integration** for Layer 3, Layer 4, and Layer 7 protocol analysis.

---

## 📁 Project Structure

```
NetDoctor/
├── app.py                         # Professional Streamlit web dashboard
├── requirements.txt               # Project dependencies
├── README.md                      # Quick start and documentation
├── PACKET_TRACER_LAB_GUIDE.md     # Step-by-step 13-device Cisco lab guide & CLI configs
├── WIRESHARK_CAPTURE_GUIDE.md     # Step-by-step Wireshark capture & display filters guide
├── PROJECT_REPORT.md              # Academic engineering project report
├── VIVA_QUESTIONS_AND_ANSWERS.md  # Viva defense preparation Q&A
├── DEMO_VIDEO_SCRIPT.md           # 3-5 minute demonstration video script
├── netdoctor/
│   ├── __init__.py
│   ├── config.py                  # Thresholds, timeouts, and target lists
│   ├── monitor.py                 # Real Windows network diagnostic engine
│   ├── diagnostics.py             # Rule-based fault diagnosis expert system
│   ├── pt_parser.py               # Cisco Packet Tracer CLI output parser
│   └── history.py                 # Historical tracking, recovery diffs & CSV export
└── tests/
    ├── __init__.py
    ├── test_monitor.py            # Unit tests for host validation and adapters
    ├── test_diagnostics.py        # Unit tests for diagnostic rules (APIPA, ICMP, DNS)
    ├── test_pt_parser.py          # Unit tests for Cisco CLI parsing
    └── test_history.py            # Unit tests for recovery events & comparisons
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Operating System:** Windows 10/11
- **Python:** 3.10+ (Verified on Python 3.13)
- **Cisco Packet Tracer:** 8.x or 9.x (Installed on your system)
- **Wireshark:** (Installed on your system)

### 2. Run Automated Unit Tests
To verify all parsers, host validation, and diagnostic rules:
```powershell
cd C:\Users\annap\.gemini\antigravity\scratch\NetDoctor
pytest -v
```
*(All 11 unit tests should pass with 100% success).*

### 3. Launch the NetDoctor Web Dashboard
To start the dashboard in your browser:
```powershell
cd C:\Users\annap\.gemini\antigravity\scratch\NetDoctor
streamlit run app.py
```
Open your browser to: **`http://localhost:8501`**

---

## 🧭 How to Use NetDoctor

### 1. Overview Tab
- View your real Windows local IPv4, adapter state, and default gateway.
- Review recent failure and recovery events.
- Click **"Check Now"** for an immediate on-demand diagnostic run.
- Click **"Start Auto"** to enable background polling (interval configurable in Settings).

### 2. Live Monitoring Tab
- View real-time response time trends (ms) and packet loss (%).
- Inspect tabbed breakdowns for Default Gateway, DNS resolution, TCP ports (80, 443, 53), and physical adapters.

### 3. Fault Diagnosis Tab
- Read plain-English explanations of any detected issues with confidence metrics and recommended actions.
- Explains why a failed ping does not necessarily mean the network is down if TCP web traffic is active.

### 4. Packet Tracer Lab Mode
- Build your campus network following `PACKET_TRACER_LAB_GUIDE.md`.
- Copy command outputs from Packet Tracer (`show ip interface brief`, `show ip route`, `show vlan brief`, or `ping`).
- Paste into the text box and click **Analyze Packet Tracer Evidence**.
- Review detected issues, root cause explanation, and exact Cisco CLI commands to fix the problem.
- Compare **Before Fix** vs **After Fix** to verify recovery!

### 5. History & Export Tab
- View timestamped historical diagnostic runs.
- Click **Download CSV** to export genuine test measurements for project documentation.

---

## 📚 Documentation & Reference Guides

- **Campus Lab Setup & Cisco CLI:** [PACKET_TRACER_LAB_GUIDE.md](PACKET_TRACER_LAB_GUIDE.md)
- **Wireshark Traffic Capture:** [WIRESHARK_CAPTURE_GUIDE.md](WIRESHARK_CAPTURE_GUIDE.md)
- **Viva Defense Questions & Answers:** [VIVA_QUESTIONS_AND_ANSWERS.md](VIVA_QUESTIONS_AND_ANSWERS.md)
- **Video Presentation Script:** [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md)
- **Complete Project Report:** [PROJECT_REPORT.md](PROJECT_REPORT.md)
