"""
NetDoctor: Real-Time Network Monitoring, Fault Diagnosis and Recovery Verification System
Streamlit Web Dashboard
"""

import sys
import os
import time
from datetime import datetime
import streamlit as st
import pandas as pd

from netdoctor.config import (
    DEFAULT_MONITOR_INTERVAL_SEC,
    DEFAULT_GATEWAY_TIMEOUT_SEC,
    DEFAULT_DNS_TIMEOUT_SEC,
    DEFAULT_TCP_TIMEOUT_SEC,
    DEFAULT_PING_TIMEOUT_MS,
    DEFAULT_DNS_TARGETS,
    DEFAULT_TCP_TARGETS,
    DEFAULT_PING_TARGETS,
)
from netdoctor.monitor import (
    run_full_system_diagnostic,
    resolve_dns,
    test_tcp_port,
    ping_host,
    get_network_adapters,
    get_primary_adapter_and_gateway,
    is_valid_host,
)
from netdoctor.diagnostics import diagnose_network_snapshot
from netdoctor.history import NetworkHistoryTracker, compare_recovery_snapshots
from netdoctor.pt_parser import analyze_pt_evidence

# Configure Streamlit page
st.set_page_config(
    page_title="NetDoctor | Network Monitor & Lab Diagnosis",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Enterprise NOC UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Top Level Status Badges with Pulsing Animation */
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    @keyframes pulse-yellow {
        0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
        70% { box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); }
        100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
    }

    .badge-pass {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.1) 100%);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 8px 18px;
        border-radius: 24px;
        font-weight: 700;
        font-size: 0.95em;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        animation: pulse-green 2.5s infinite;
    }
    .badge-warn {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.1) 100%);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.35);
        padding: 8px 18px;
        border-radius: 24px;
        font-weight: 700;
        font-size: 0.95em;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        animation: pulse-yellow 2.5s infinite;
    }
    .badge-fail {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 8px 18px;
        border-radius: 24px;
        font-weight: 700;
        font-size: 0.95em;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        animation: pulse-red 2.5s infinite;
    }

    /* Modern Glassmorphic Metric Tile */
    .metric-hero {
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 20px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-hero:hover {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        transform: translateY(-2px);
    }
    .metric-hero::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #06b6d4);
        border-radius: 12px 12px 0 0;
    }

    /* Terminal Console Faux Window */
    .cisco-terminal-box {
        background: #090d16;
        border: 1px solid #1e293b;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        margin: 12px 0;
    }
    .cisco-terminal-bar {
        background: #0f172a;
        padding: 8px 14px;
        border-bottom: 1px solid #1e293b;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8em;
        color: #94a3b8;
    }
    .term-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-red { background: #ef4444; }
    .dot-yellow { background: #f59e0b; }
    .dot-green { background: #10b981; }

    /* Polished Code Box */
    .cisco-code {
        background: #090d16;
        color: #38bdf8;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 3px solid #0284c7;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9em;
        line-height: 1.5;
        margin-top: 8px;
        white-space: pre-wrap;
    }

    /* Header Accent */
    .header-pill {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 10px;
        border-radius: 6px;
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.25);
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "tracker" not in st.session_state:
    st.session_state.tracker = NetworkHistoryTracker(max_entries=200)

if "latest_snapshot" not in st.session_state:
    # Run initial baseline check
    snap = run_full_system_diagnostic()
    st.session_state.tracker.add_snapshot(snap)
    st.session_state.latest_snapshot = snap

if "monitoring_active" not in st.session_state:
    st.session_state.monitoring_active = False

if "monitor_interval" not in st.session_state:
    st.session_state.monitor_interval = DEFAULT_MONITOR_INTERVAL_SEC

if "pt_history" not in st.session_state:
    st.session_state.pt_history = []

if "pt_baseline" not in st.session_state:
    st.session_state.pt_baseline = None


# Helper to run diagnostics and record to history
def trigger_diagnostic_run():
    snap = run_full_system_diagnostic(
        dns_targets=st.session_state.get("cfg_dns", DEFAULT_DNS_TARGETS),
        tcp_targets=st.session_state.get("cfg_tcp", DEFAULT_TCP_TARGETS),
        ping_targets=st.session_state.get("cfg_ping", DEFAULT_PING_TARGETS),
    )
    st.session_state.tracker.add_snapshot(snap)
    st.session_state.latest_snapshot = snap
    st.session_state.last_run_time = datetime.now()


# Sidebar Navigation & Controls
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
        <div style="background: linear-gradient(135deg, #2563eb, #06b6d4); width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; box-shadow: 0 4px 14px rgba(37,99,235,0.4);">🩺</div>
        <div>
            <h2 style="margin: 0; font-size: 1.35rem; font-weight: 800; letter-spacing: -0.5px;">NetDoctor</h2>
            <span style="font-size: 0.72rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">Enterprise NOC & Lab</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.subheader("⚙️ Live Monitor Control")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Check Now", use_container_width=True, type="primary"):
            trigger_diagnostic_run()
            st.rerun()

    with col_btn2:
        if not st.session_state.monitoring_active:
            if st.button("▶️ Start Auto", use_container_width=True):
                st.session_state.monitoring_active = True
                st.rerun()
        else:
            if st.button("⏹️ Stop Auto", use_container_width=True):
                st.session_state.monitoring_active = False
                st.rerun()

    if st.session_state.monitoring_active:
        st.markdown(f"<div style='margin-top:6px;'><span class='badge-pass'>● ACTIVE • {st.session_state.monitor_interval}s POLL</span></div>", unsafe_allow_html=True)
    else:
        st.caption("⚪ Monitoring Idle (Manual mode)")

    st.divider()
    nav_section = st.radio(
        "📍 Navigation Section:",
        [
            "Overview",
            "Live Monitoring",
            "Fault Diagnosis",
            "Manual Diagnostics",
            "Packet Tracer Lab Mode",
            "History & Export",
            "Settings & Config",
        ]
    )

    st.divider()
    st.caption("NetDoctor Enterprise v2.0 • Computer Engineering Project")


# Read current network snapshot
snap = st.session_state.latest_snapshot
overall_status = snap.get("overall_status", "UNKNOWN")
primary_info = snap.get("primary_info", {})
findings = diagnose_network_snapshot(snap)

is_cloud = (
    sys.platform != "win32"
    or str(primary_info.get("default_gateway", "")).startswith("169.254.")
    or primary_info.get("interface", "") == "eth0"
)

# Extract client IP if available via Streamlit context
client_ip = None
if hasattr(st.context, "headers") and st.context.headers:
    try:
        raw_forwarded = st.context.headers.get("x-forwarded-for") or st.context.headers.get("x-real-ip")
        if raw_forwarded:
            client_ip = raw_forwarded.split(",")[0].strip()
    except Exception:
        pass

if not client_ip or client_ip in ("::ffff:127.0.0.1", "127.0.0.1", "localhost"):
    ctx_ip = getattr(st.context, "ip_address", None)
    if ctx_ip and ctx_ip not in ("::ffff:127.0.0.1", "127.0.0.1", "localhost"):
        client_ip = ctx_ip

# Human-readable client label for UI
client_label = client_ip if client_ip and not client_ip.startswith("::ffff:127.") else "Remote Web Client (Proxy Routed)"

# ==========================================
# 1. OVERVIEW SECTION
# ==========================================
if nav_section == "Overview":
    st.title("🌐 Network Operations Center (NOC) Overview")
    loc_ip = primary_info.get("local_ip", "Unknown")
    nic_name = primary_info.get("interface", "NIC")[:20]

    if is_cloud:
        active_client = client_ip if (client_ip and not client_ip.startswith("::ffff:127.")) else "Dynamic Web Client"
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, rgba(59, 130, 246, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%); border-left: 4px solid #38bdf8; border-radius: 8px; padding: 12px 18px; margin-bottom: 20px;">
            <div style="font-size: 0.95rem; font-weight: 500; color: #f1f5f9;">
                🌐 <b>Real-Time Dynamic Client Telemetry:</b> Connected from client endpoint <code style="color:#38bdf8; background:#0f172a; padding:2px 8px; border-radius:4px;">{active_client}</code> &bull; Host Gateway: <code style="color:#818cf8; background:#0f172a; padding:2px 8px; border-radius:4px;">{loc_ip}</code>
            </div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                NetDoctor detects each visitor's incoming device endpoint dynamically and cross-probes Layer 3, Layer 4 TCP transport, and Layer 7 DNS services.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("💻 **Running on Local Workstation (Windows PC Mode)** • Probing physical Wi-Fi/Ethernet network adapter, Layer 3 home gateway, Layer 4 transport, and Layer 7 DNS services.")

    # Status Banner Cards
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

    with col_stat1:
        if overall_status == "PASS":
            status_html = "<span class='badge-pass'>● HEALTHY (PASS)</span>"
        elif overall_status == "WARNING":
            status_html = "<span class='badge-warn'>● DEGRADED (WARN)</span>"
        else:
            status_html = "<span class='badge-fail'>● OUTAGE (FAIL)</span>"

        st.markdown(f"""
        <div class="metric-hero">
            <div class="header-pill">System Status</div>
            <div style="margin: 12px 0 6px 0;">{status_html}</div>
            <div style="font-size: 0.8rem; opacity: 0.7;">Multi-layer network telemetry</div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat2:
        if is_cloud and client_ip and not client_ip.startswith("::ffff:127."):
            header_title = "Detected Client IP"
            main_ip = client_ip
            sub_label = f"Host Server: {loc_ip} (eth0)"
        else:
            header_title = "Local IPv4 Address"
            main_ip = loc_ip
            sub_label = f"Adapter: {nic_name}"

        st.markdown(f"""
        <div class="metric-hero">
            <div class="header-pill">{header_title}</div>
            <div class="metric-value" style="font-family:'JetBrains Mono', monospace; font-size:1.35rem; color:#38bdf8;">{main_ip}</div>
            <div style="font-size: 0.8rem; opacity: 0.7;">{sub_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat3:
        gw_ip = primary_info.get("default_gateway", "Not Detected")
        gw_sub = "Cloud Container Gateway" if is_cloud else "Layer 3 Next-Hop Router"
        st.markdown(f"""
        <div class="metric-hero">
            <div class="header-pill">Default Gateway</div>
            <div class="metric-value" style="font-family:'JetBrains Mono', monospace; font-size:1.35rem; color:#818cf8;">{gw_ip}</div>
            <div style="font-size: 0.8rem; opacity: 0.7;">{gw_sub}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat4:
        ts_full = snap.get("timestamp", "")
        ts_time = ts_full[11:19] if len(ts_full) >= 19 else "Just now"
        ts_date = ts_full[:10] if len(ts_full) >= 10 else ""
        st.markdown(f"""
        <div class="metric-hero">
            <div class="header-pill">Last Telemetry Check</div>
            <div class="metric-value" style="font-family:'JetBrains Mono', monospace; font-size:1.35rem; color:#34d399;">{ts_time}</div>
            <div style="font-size: 0.8rem; opacity: 0.7;">Date: {ts_date}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Recent Events (Failures and Recoveries)
    st.subheader("🔔 Recent State Transitions & Recovery Events")
    recent_events = st.session_state.tracker.events[-5:]
    if recent_events:
        for ev in reversed(recent_events):
            ev_type = ev.get("event_type")
            ts = ev.get("timestamp")[:19].replace("T", " ")
            if ev_type == "RECOVERY":
                st.success(f"🎉 **RECOVERY [{ts}]** — {ev.get('description')}")
            else:
                st.error(f"⚠️ **FAILURE [{ts}]** — {ev.get('description')}")
    else:
        st.caption("No state transitions recorded yet. Running stably.")

    st.divider()

    # Quick Live Benchmark Section (100% Dynamic for Any Visitor)
    st.subheader("⚡ Live On-Demand Network Probe")
    st.caption("Benchmark any custom IP, website, or router port live from this active dashboard:")
    c_prb1, c_prb2, c_prb3 = st.columns([3, 1, 1.2])
    with c_prb1:
        probe_target = st.text_input("Target Host or Domain:", value="google.com", key="quick_probe_target", label_visibility="collapsed")
    with c_prb2:
        probe_port = st.number_input("Port:", min_value=1, max_value=65535, value=443, key="quick_probe_port", label_visibility="collapsed")
    with c_prb3:
        do_quick_probe = st.button("🚀 Probe Live Now", use_container_width=True)

    if do_quick_probe and probe_target:
        with st.spinner(f"Probing {probe_target}:{probe_port}..."):
            t_res = test_tcp_port(probe_target.strip(), int(probe_port), timeout_sec=2.0)
            d_res = resolve_dns(probe_target.strip(), timeout_sec=2.0)
            col_pr1, col_pr2 = st.columns(2)
            with col_pr1:
                if t_res.get("status") == "PASS":
                    st.success(f"🔌 **TCP Port {probe_port}:** Handshake Verified in **{t_res.get('latency_ms')} ms** (PASS)")
                else:
                    st.error(f"❌ **TCP Port {probe_port}:** Failed ({t_res.get('error', 'Unreachable')})")
            with col_pr2:
                if d_res.get("status") == "PASS":
                    st.success(f"🌐 **DNS Resolution:** Resolved to `{d_res.get('addresses')}` in **{d_res.get('latency_ms')} ms**")
                else:
                    st.error(f"❌ **DNS Resolution:** Failed ({d_res.get('error')})")

    st.divider()

    # Top Level Health Summary Cards
    st.subheader("📊 Layer Health Breakdown")
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)

    gw_test = snap.get("gateway_test", {})
    dns_res = snap.get("dns_results", [])
    tcp_res = snap.get("tcp_results", [])
    ping_res = snap.get("ping_results", [])

    with col_l1:
        with st.container(border=True):
            st.markdown("### 🚪 Layer 3")
            st.markdown("**Default Gateway**")
            st.caption(f"Target: `{gw_test.get('target', 'N/A')}`")
            if gw_test.get("status") == "PASS":
                st.success(f"PASS • {gw_test.get('rtt_avg_ms', 0)} ms")
            elif gw_test.get("status") == "WARNING":
                st.warning(f"WARN • {gw_test.get('loss_pct', 0)}% loss")
            else:
                st.error(f"FAIL • {gw_test.get('error', 'Unreachable')}")

    with col_l2:
        with st.container(border=True):
            st.markdown("### 🌐 Layer 7")
            st.markdown("**DNS Resolution**")
            dns_passes = sum(1 for d in dns_res if d.get("status") == "PASS")
            dns_total = len(dns_res)
            st.caption(f"{dns_passes}/{dns_total} Domains Resolved")
            if dns_passes == dns_total and dns_total > 0:
                st.success("PASS • Normal")
            else:
                st.error(f"FAIL • {dns_total - dns_passes} Failed")

    with col_l3:
        with st.container(border=True):
            st.markdown("### 🔌 Layer 4")
            st.markdown("**TCP Connectivity**")
            tcp_passes = sum(1 for t in tcp_res if t.get("status") == "PASS")
            tcp_total = len(tcp_res)
            st.caption(f"{tcp_passes}/{tcp_total} Services Connected")
            if tcp_passes == tcp_total and tcp_total > 0:
                st.success("PASS • Active Handshakes")
            else:
                st.error(f"FAIL • {tcp_total - tcp_passes} Failed")

    with col_l4:
        with st.container(border=True):
            st.markdown("### 💻 Network NIC")
            st.markdown("**Active Adapters**")
            adapters = snap.get("adapters", [])
            up_count = sum(1 for a in adapters if a.get("is_up") and a.get("ipv4") != "Unassigned")
            st.caption(f"{up_count} Active Interface(s)")
            st.info(f"{primary_info.get('interface', 'Active')[:18]}")

    # Active Diagnostic Finding Alert
    if findings:
        primary_find = findings[0]
        if "Comprehensive Network Health" not in primary_find.get("test_name", ""):
            if "ICMP Ping vs TCP Transport" in primary_find.get("test_name", ""):
                st.info(f"ℹ️ **Security Policy Notice:** {primary_find.get('test_name')} — {primary_find.get('likely_cause')}")
            else:
                st.warning(f"⚠️ **Attention Needed:** {primary_find.get('test_name')} — {primary_find.get('likely_cause')}")
                st.info(f"💡 Recommended Action: {primary_find.get('recommended_action')}")


# ==========================================
# 2. LIVE MONITORING SECTION
# ==========================================
elif nav_section == "Live Monitoring":
    st.title("📈 Real-Time Monitoring & Metrics")
    st.markdown("Live response-time measurements and packet-loss statistics from your genuine network interface.")

    # Live Monitoring Status & Quick Control Banner
    col_stat_banner, col_stat_ctrl = st.columns([3, 1])
    with col_stat_banner:
        data_count = len(st.session_state.tracker.history)
        if st.session_state.monitoring_active:
            st.success(f"🟢 **Continuous Monitoring Active:** Gathering live measurements every **{st.session_state.monitor_interval} seconds** automatically! *(Data points collected: {data_count})*")
        else:
            st.info(f"⚪ **Monitoring Idle:** Click **'Start Auto'** in the sidebar or click **'Add Data Point'** to record live trend data.")

    with col_stat_ctrl:
        if st.button("🔄 Add Data Point Now", use_container_width=True):
            trigger_diagnostic_run()
            st.rerun()

    # Live Charts if history exists
    df_hist = st.session_state.tracker.get_history_dataframe()
    if not df_hist.empty and len(df_hist) >= 2:
        st.subheader("📉 Historical Response Time & Quality Trends")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**Average Round-Trip Latency (ms)**")
            lat_series = df_hist.dropna(subset=["Avg Latency (ms)"])
            if not lat_series.empty:
                st.line_chart(lat_series.set_index("Timestamp")["Avg Latency (ms)"], height=230)
            else:
                st.caption("Collecting latency data...")
        with col_c2:
            st.markdown("**Packet Loss Percentage (%)**")
            st.line_chart(df_hist.set_index("Timestamp")["Avg Packet Loss (%)"], height=230)
    else:
        st.info("💡 Tip: Click **'Add Data Point Now'** or turn on **'Start Auto'** to record multiple points and see the trend curves draw live!")

    st.divider()

    # Detailed Results Tables
    st.subheader("🔍 Detailed Live Check Breakdown")

    # Tabbed view for different test categories
    t_gw, t_dns, t_tcp, t_nic = st.tabs(["Default Gateway", "DNS Hostnames", "TCP Ports", "Local Network Adapters"])

    with t_gw:
        gw_test = snap.get("gateway_test", {})
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Gateway Target", gw_test.get("target", "N/A"))
        col_g2.metric("Latency", f"{gw_test.get('rtt_avg_ms', 'N/A')} ms")
        col_g3.metric("Packet Loss", f"{gw_test.get('loss_pct', 'N/A')}%")
        if gw_test.get("error"):
            st.error(f"Error: {gw_test.get('error')}")
        else:
            st.success("Default gateway responded cleanly.")

    with t_dns:
        dns_res = snap.get("dns_results", [])
        if dns_res:
            dns_table = []
            for d in dns_res:
                dns_table.append({
                    "Hostname": d.get("hostname"),
                    "Status": d.get("status"),
                    "Resolved IPs": ", ".join(d.get("resolved_ips", [])) or "None",
                    "Latency (ms)": d.get("latency_ms"),
                    "Error": d.get("error") or "None"
                })
            st.dataframe(pd.DataFrame(dns_table), use_container_width=True)

    with t_tcp:
        tcp_res = snap.get("tcp_results", [])
        if tcp_res:
            tcp_table = []
            for t in tcp_res:
                tcp_table.append({
                    "Service": t.get("service"),
                    "Host": t.get("host"),
                    "Port": t.get("port"),
                    "Status": t.get("status"),
                    "Handshake Latency (ms)": t.get("latency_ms"),
                    "Error": t.get("error") or "None"
                })
            st.dataframe(pd.DataFrame(tcp_table), use_container_width=True)

    with t_nic:
        adapters = snap.get("adapters", [])
        if adapters:
            nic_table = []
            for a in adapters:
                nic_table.append({
                    "Interface Name": a.get("interface"),
                    "Status": "UP" if a.get("is_up") else "DOWN",
                    "IPv4 Address": a.get("ipv4"),
                    "Subnet Mask": a.get("netmask"),
                    "MAC Address": a.get("mac"),
                    "Speed": f"{a.get('speed_mbps')} Mbps" if a.get("speed_mbps") else "N/A"
                })
            st.dataframe(pd.DataFrame(nic_table), use_container_width=True)


# ==========================================
# 3. FAULT DIAGNOSIS SECTION
# ==========================================
elif nav_section == "Fault Diagnosis":
    st.title("🩺 Evidence-Based Fault Diagnosis Engine")
    st.markdown("Explains network issues by correlating observed symptoms against strict diagnostic rules. Clearly distinguishes facts from hypotheses.")

    st.subheader(f"Current Diagnosis Report ({len(findings)} Finding(s))")

    for idx, f in enumerate(findings, 1):
        test_name = f.get("test_name")
        actual_result = f.get("actual_result")
        likely_cause = f.get("likely_cause")
        alt_causes = f.get("alternative_causes", [])
        confidence = f.get("confidence", "MEDIUM")
        rec_action = f.get("recommended_action")
        rerun_hint = f.get("rerun_hint")

        if confidence == "HIGH":
            conf_badge = "<span style='background:rgba(16,185,129,0.18); color:#10b981; padding:3px 10px; border-radius:12px; font-weight:700; font-size:0.8em; border:1px solid rgba(16,185,129,0.35);'>CONFIDENCE: HIGH</span>"
        elif confidence == "MEDIUM":
            conf_badge = "<span style='background:rgba(245,158,11,0.18); color:#f59e0b; padding:3px 10px; border-radius:12px; font-weight:700; font-size:0.8em; border:1px solid rgba(245,158,11,0.35);'>CONFIDENCE: MEDIUM</span>"
        else:
            conf_badge = "<span style='background:rgba(148,163,184,0.18); color:#94a3b8; padding:3px 10px; border-radius:12px; font-weight:700; font-size:0.8em; border:1px solid rgba(148,163,184,0.35);'>CONFIDENCE: LOW</span>"

        with st.container(border=True):
            if "Comprehensive" in test_name:
                st.markdown(f"### #{idx} — {test_name} &nbsp; {conf_badge}", unsafe_allow_html=True)
                st.markdown(f"**Observed Evidence:** `{actual_result}`")
                st.markdown(f"**Network State:** {likely_cause}")
            else:
                st.markdown(f"### #{idx} — {test_name} &nbsp; {conf_badge}", unsafe_allow_html=True)
                st.markdown(f"**Observed Evidence:** `{actual_result}`")
                st.markdown(f"**Likely Root Cause:** {likely_cause}")

        if alt_causes:
            with st.expander(f"🔎 View Alternative Possible Causes for #{idx}"):
                for alt in alt_causes:
                    st.markdown(f"- {alt}")

        st.markdown(f"💡 **Recommended Action:** {rec_action}")
        st.caption(f"🔄 How to verify again: {rerun_hint}")
        st.divider()


# ==========================================
# 4. MANUAL DIAGNOSTICS SECTION
# ==========================================
elif nav_section == "Manual Diagnostics":
    st.title("🧪 Ad-Hoc Diagnostic Probes")
    st.markdown("Run specific individual network tests on demand.")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.subheader("🌐 Ad-Hoc DNS Resolution")
        custom_domain = st.text_input("Enter Domain Name:", value="google.com", key="manual_dns_input")
        if st.button("Run DNS Lookup", key="btn_dns_run"):
            if is_valid_host(custom_domain):
                with st.spinner(f"Resolving {custom_domain}..."):
                    res = resolve_dns(custom_domain)
                    st.session_state.manual_dns_result = (custom_domain, res)
            else:
                st.session_state.manual_dns_result = (custom_domain, {"status": "FAIL", "error": "Invalid hostname format."})

        # Display DNS result (only if it matches the current input)
        if "manual_dns_result" in st.session_state:
            target_dom, res = st.session_state.manual_dns_result
            if target_dom == custom_domain.strip():
                if res["status"] == "PASS":
                    # Check for ISP DNS hijacking (e.g. 218.93.250.18 or .invalid domains)
                    resolved_ips = res.get("resolved_ips", [])
                    is_hijacked = any(ip.startswith("218.93.") or ip.startswith("198.18.") for ip in resolved_ips) or target_dom.endswith(".invalid")
                    
                    if is_hijacked:
                        st.warning(f"⚠️ **ISP Wildcard Redirection Detected!**\n\nDomain `{target_dom}` was redirected to `{', '.join(resolved_ips)}` by your ISP in {res['latency_ms']} ms.\n\n*(Your Internet Provider intercepts fake domains instead of returning an error).*")
                    else:
                        st.success(f"✅ Resolved in {res['latency_ms']} ms")
                        st.write("**IP Addresses:**", resolved_ips)
                else:
                    st.error(f"❌ Resolution Failed: {res['error']}")

    with col_t2:
        st.subheader("🔌 Ad-Hoc TCP Port Probe")
        col_hp1, col_hp2 = st.columns([3, 1])
        with col_hp1:
            custom_tcp_host = st.text_input("Target Host/IP:", value="google.com", key="manual_tcp_host")
        with col_hp2:
            custom_tcp_port = st.number_input("Port:", value=443, min_value=1, max_value=65535, key="manual_tcp_port")

        if st.button("Probe TCP Port", key="btn_tcp_run"):
            clean_host = custom_tcp_host.strip()
            clean_port = int(custom_tcp_port)
            if not clean_host:
                st.session_state.manual_tcp_result = (clean_host, clean_port, {"status": "FAIL", "error": "Target Host/IP cannot be blank. Please enter a domain name (like wikipedia.org) or an IP address."})
            elif is_valid_host(clean_host):
                with st.spinner(f"Connecting to {clean_host}:{clean_port}..."):
                    res = test_tcp_port(clean_host, clean_port)
                    st.session_state.manual_tcp_result = (clean_host, clean_port, res)
            else:
                st.session_state.manual_tcp_result = (clean_host, clean_port, {"status": "FAIL", "error": f"'{clean_host}' is not a valid domain or IPv4 address."})

        # Display TCP result (only if it matches the current input)
        if "manual_tcp_result" in st.session_state:
            target_h, target_p, res = st.session_state.manual_tcp_result
            if target_h == custom_tcp_host.strip() and target_p == int(custom_tcp_port):
                if res["status"] == "PASS":
                    st.success(f"✅ Port Open! 3-Way Handshake with {target_h}:{target_p} completed in {res['latency_ms']} ms")
                else:
                    target_label = f"{target_h}:{target_p}" if target_h else f"Port {target_p}"
                    st.error(f"❌ Connection to {target_label} Failed: {res['error']}")

    st.divider()

    st.subheader("📡 Ad-Hoc ICMP Ping")
    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        custom_ping_host = st.text_input("Ping Target Host / IP:", value="8.8.8.8", key="manual_ping_host")
    with col_p2:
        custom_ping_count = st.number_input("Count:", value=2, min_value=1, max_value=4, key="manual_ping_count")

    if st.button("Send Ping", key="btn_ping_run"):
        clean_p_host = custom_ping_host.strip()
        if is_valid_host(clean_p_host):
            with st.spinner(f"Pinging {clean_p_host}..."):
                res = ping_host(clean_p_host, count=int(custom_ping_count))
                st.session_state.manual_ping_result = (clean_p_host, res)
        else:
            st.session_state.manual_ping_result = (clean_p_host, {"status": "FAIL", "error": f"'{clean_p_host}' is not a valid IP address or domain."})

    # Display Ping result (only if it matches the current input)
    if "manual_ping_result" in st.session_state:
        target_p_host, res = st.session_state.manual_ping_result
        if target_p_host == custom_ping_host.strip():
            if res["status"] == "PASS":
                st.success(f"✅ Ping to {target_p_host} successful! Avg Latency: {res['rtt_avg_ms']} ms, Loss: {res['loss_pct']}%")
            elif res["status"] == "WARNING":
                st.warning(f"⚠️ Degraded: Avg Latency: {res['rtt_avg_ms']} ms, Loss: {res['loss_pct']}%")
            else:
                st.error(f"❌ Ping to {target_p_host} failed: {res['error']}")


# ==========================================
# 5. PACKET TRACER LAB MODE SECTION
# ==========================================
elif nav_section == "Packet Tracer Lab Mode":
    st.title("🔬 Packet Tracer Lab Mode — Analysis of Submitted Results")
    st.markdown("""
    Paste genuine command outputs from your **Cisco Packet Tracer** devices below.
    NetDoctor will parse the configuration, detect faults, provide Cisco CLI commands to fix them, and verify recovery.
    """)

    col_pt1, col_pt2 = st.columns([1, 2])

    with col_pt1:
        st.subheader("Device & Command Info")
        device_type = st.selectbox("Device Type:", ["Router", "Switch", "Host PC"])
        device_name = st.text_input("Device Name:", value="R1-Campus" if device_type == "Router" else "SW-Core")
        command_type = st.selectbox(
            "Cisco Command Executed:",
            [
                "show ip interface brief",
                "show ip route",
                "show vlan brief",
                "show interfaces trunk",
                "ping (Cisco Router or PC)"
            ]
        )
        sample_choice = st.selectbox(
            "Load Sample Fault / Baseline Output:",
            [
                "-- Type or Paste Your Own Output --",
                "Sample Fault 1: PC Gateway Failure (ping)",
                "Sample Fault 2: Interface Administratively Shutdown",
                "Sample Fault 3: Missing Route to Branch (show ip route)",
                "Sample Baseline: Healthy Router (show ip interface brief)",
                "Sample Baseline: Healthy Switch VLANs (show vlan brief)"
            ]
        )

    # Pre-canned samples for rapid demonstration
    default_text = ""
    if sample_choice == "Sample Fault 1: PC Gateway Failure (ping)":
        default_text = """Pinging 10.10.10.1 with 32 bytes of data:
Request timed out.
Request timed out.
Request timed out.
Request timed out.
Ping statistics for 10.10.10.1:
    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)"""
    elif sample_choice == "Sample Fault 2: Interface Administratively Shutdown":
        default_text = """Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0/0   10.10.10.1      YES manual up                    up      
GigabitEthernet0/0/1   10.10.20.1      YES manual administratively down down    
GigabitEthernet0/0/2   10.10.99.1      YES manual up                    up"""
    elif sample_choice == "Sample Fault 3: Missing Route to Branch (show ip route)":
        default_text = """Codes: L - local, C - connected, S - static, R - RIP
Gateway of last resort is not set

C    10.10.10.0/24 is directly connected, GigabitEthernet0/0/0.10
L    10.10.10.1/32 is directly connected, GigabitEthernet0/0/0.10
C    10.10.20.0/24 is directly connected, GigabitEthernet0/0/0.20
L    10.10.20.1/32 is directly connected, GigabitEthernet0/0/0.20
C    10.10.99.0/30 is directly connected, GigabitEthernet0/0/2"""
    elif sample_choice == "Sample Baseline: Healthy Router (show ip interface brief)":
        default_text = """Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0/0   unassigned      YES unset  up                    up      
GigabitEthernet0/0/0.10 10.10.10.1     YES manual up                    up      
GigabitEthernet0/0/0.20 10.10.20.1     YES manual up                    up      
GigabitEthernet0/0/2   10.10.99.1      YES manual up                    up"""
    elif sample_choice == "Sample Baseline: Healthy Switch VLANs (show vlan brief)":
        default_text = """VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4
10   Students                         active    Fa0/5, Fa0/6
20   Faculty                          active    Fa0/7, Fa0/8"""

    with col_pt2:
        st.subheader("Raw Terminal Output")
        st.markdown(f"""
        <div class="cisco-terminal-bar" style="border-radius: 8px 8px 0 0; margin-bottom: 2px;">
            <span class="term-dot dot-red"></span>
            <span class="term-dot dot-yellow"></span>
            <span class="term-dot dot-green"></span>
            <span style="font-weight:600;">Cisco IOS Serial Console — {device_name} (9600 8-N-1)</span>
        </div>
        """, unsafe_allow_html=True)
        raw_pt_input = st.text_area("Paste Packet Tracer Output Here:", value=default_text, height=200, label_visibility="collapsed")
        btn_analyze = st.button("🔬 Analyze Packet Tracer Evidence", type="primary", use_container_width=True)

    if btn_analyze and raw_pt_input.strip():
        analysis = analyze_pt_evidence(command_type, raw_pt_input, device_name)
        st.session_state.pt_history.append({
            "timestamp": datetime.now().isoformat(),
            "device": device_name,
            "command": command_type,
            "analysis": analysis
        })

        st.divider()
        st.subheader(f"📋 Diagnostic Findings for {device_name}")

        issues = analysis.get("issues", [])
        if issues:
            st.markdown(f"<div style='margin-bottom:14px;'><span class='badge-fail'>❌ DETECTED {len(issues)} MISCONFIGURATION(S) OR FAULT(S)</span></div>", unsafe_allow_html=True)
            for idx, issue in enumerate(issues, 1):
                with st.container(border=True):
                    st.error(f"### Issue #{idx}: {issue.get('condition')}")
                    st.markdown(f"**Likely Root Cause:** {issue.get('likely_cause')}")
                    if issue.get('alternative_causes'):
                        st.markdown(f"**Alternative Possibilities:** {', '.join(issue.get('alternative_causes'))}")
                    st.markdown("**Recommended Cisco IOS Commands to Remediate:**")
                    st.code(issue.get('cisco_fix'), language="cisco")
                    st.markdown(f"**Verification Command:** `{issue.get('next_command')}`")
        else:
            st.markdown(f"<div style='margin-bottom:14px;'><span class='badge-pass'>✅ CLEAN CONFIGURATION • ZERO FAULTS DETECTED</span></div>", unsafe_allow_html=True)
            st.success(f"Clean configuration verified for device **{device_name}** under command `{command_type}`.")

        # Display structured parsed table if available
        if "parsed_interfaces" in analysis:
            st.write("**Parsed Interfaces Table:**")
            st.dataframe(pd.DataFrame(analysis["parsed_interfaces"]), use_container_width=True)
        elif "parsed_routes" in analysis:
            st.write("**Parsed Routing Table:**")
            st.dataframe(pd.DataFrame(analysis["parsed_routes"]), use_container_width=True)
        elif "vlans" in analysis:
            st.write("**Parsed VLANs:**")
            st.dataframe(pd.DataFrame(analysis["vlans"]), use_container_width=True)

    # Comparison / Recovery Verification Section
    if st.session_state.pt_history:
        st.divider()
        st.subheader("🔄 Before-and-After Recovery Comparison")
        st.markdown("Select two submitted tests to verify that fixing the Cisco configuration restored connectivity:")

        history_labels = [f"{h['timestamp'][11:19]} — {h['device']} ({h['command']})" for h in st.session_state.pt_history]
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            idx1 = st.selectbox("Select 'Before Fix' (Fault) Run:", range(len(history_labels)), index=0, format_func=lambda i: history_labels[i])
        with col_c2:
            idx2 = st.selectbox("Select 'After Fix' (Recovery) Run:", range(len(history_labels)), index=len(history_labels)-1, format_func=lambda i: history_labels[i])

        if st.button("Compare Before & After"):
            h1 = st.session_state.pt_history[idx1]
            h2 = st.session_state.pt_history[idx2]

            issues1 = len(h1["analysis"].get("issues", []))
            issues2 = len(h2["analysis"].get("issues", []))

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown(f"**Before ({h1['device']})**")
                if issues1 > 0:
                    st.error(f"❌ {issues1} Issue(s) Present")
                else:
                    st.success("✅ Clean")
            with col_r2:
                st.markdown(f"**After ({h2['device']})**")
                if issues2 == 0:
                    st.success("🎉 RECOVERY VERIFIED: 0 Issues Remaining!")
                else:
                    st.warning(f"⚠️ {issues2} Issue(s) Still Present")


# ==========================================
# 6. HISTORY & EXPORT SECTION
# ==========================================
elif nav_section == "History & Export":
    st.title("📜 Test History & CSV Export")
    st.markdown("Review historical diagnostic snapshots and export genuine test results to CSV for documentation.")

    df_history = st.session_state.tracker.get_history_dataframe()

    if not df_history.empty:
        st.dataframe(df_history, use_container_width=True)

        col_h1, col_h2 = st.columns([1, 4])
        with col_h1:
            csv_data = st.session_state.tracker.export_to_csv_string()
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"netdoctor_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        with col_h2:
            if st.button("🗑️ Clear History"):
                st.session_state.tracker.history = []
                st.session_state.tracker.events = []
                st.rerun()
    else:
        st.info("No history recorded yet.")


# ==========================================
# 7. SETTINGS & CONFIG SECTION
# ==========================================
elif nav_section == "Settings & Config":
    st.title("⚙️ Diagnostics & Monitoring Settings")
    st.markdown("Customize test parameters, timeouts, and monitoring intervals.")

    st.subheader("⏱️ Monitoring Interval")
    interval = st.slider(
        "Auto-refresh interval (seconds):",
        min_value=3,
        max_value=60,
        value=st.session_state.monitor_interval,
        step=1
    )
    st.session_state.monitor_interval = interval

    st.divider()

    st.subheader("🎯 Diagnostic Targets")
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("**DNS Resolution Targets (one per line):**")
        current_dns_txt = "\n".join(st.session_state.get("cfg_dns", DEFAULT_DNS_TARGETS))
        new_dns_txt = st.text_area("DNS Targets:", value=current_dns_txt, height=120)
        st.session_state.cfg_dns = [h.strip() for h in new_dns_txt.splitlines() if is_valid_host(h.strip())]

    with col_t2:
        st.markdown("**ICMP Ping Target Hosts (one per line):**")
        current_ping_txt = "\n".join([p["host"] for p in st.session_state.get("cfg_ping", DEFAULT_PING_TARGETS)])
        new_ping_txt = st.text_area("Ping Targets:", value=current_ping_txt, height=120)
        st.session_state.cfg_ping = [{"host": h.strip(), "label": h.strip()} for h in new_ping_txt.splitlines() if is_valid_host(h.strip())]

    st.success("Settings saved automatically.")


# ==========================================
# CONTINUOUS LIVE MONITORING REPEAT LOOP
# ==========================================
if st.session_state.monitoring_active:
    time.sleep(st.session_state.monitor_interval)
    trigger_diagnostic_run()
    st.rerun()
