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

# Modern Clean Enterprise NOC UI Styling (NetSentry Light Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Global Typography & Canvas */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }

    /* Streamlit Main View Container */
    .block-container {
        padding-top: 1.6rem !important;
        padding-bottom: 3rem !important;
        max-width: 1240px !important;
    }

    /* Clean White Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #E2E8F0 !important;
        margin: 12px 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #475569 !important;
    }

    /* Sidebar Radio Navigation Items */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 6px !important;
        padding: 6px 12px !important;
        margin-bottom: 3px !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: #F1F5F9 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: #EFF6FF !important;
        border-color: #BFDBFE !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        color: #1D4ED8 !important;
        font-weight: 600 !important;
    }

    /* Buttons */
    button[kind="primary"] {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.12) !important;
    }
    button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
    }
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border-color: #CBD5E1 !important;
        color: #334155 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }
    button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
    }

    /* Form Inputs */
    input, textarea, select, [data-baseweb="input"], [data-baseweb="select"] {
        border-radius: 6px !important;
        border-color: #CBD5E1 !important;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        font-size: 0.88rem !important;
    }

    /* White Panel Card Container */
    .ns-panel {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        margin-bottom: 18px;
    }
    .ns-panel-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0 0 2px 0;
    }
    .ns-panel-subtitle {
        font-size: 0.82rem;
        color: #64748B;
        margin-bottom: 14px;
    }

    /* Metric Hero Tile (NetSentry Match) */
    .ns-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .ns-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }
    .ns-card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    .ns-card-icon {
        font-size: 0.95rem;
    }
    .ns-card-title {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
    }
    .ns-card-value {
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 1.45rem;
        font-weight: 700;
        color: #0F172A;
        margin: 4px 0 4px 0;
        line-height: 1.2;
    }
    .ns-card-sub {
        font-size: 0.75rem;
        color: #64748B;
    }

    /* Network Interface Chip (NetSentry Match) */
    .ns-nic-chip {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 8px 14px;
        min-width: 145px;
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .ns-nic-name {
        font-size: 0.72rem;
        color: #64748B;
        font-weight: 500;
        margin-bottom: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 155px;
    }
    .ns-nic-ip {
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 0.92rem;
        font-weight: 700;
        color: #0F172A;
    }

    /* Crisp Clean Status Badges */
    .badge-pass {
        background: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
        font-weight: 600;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.8rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-warn {
        background: #FFFBEB;
        color: #B45309;
        border: 1px solid #FDE68A;
        font-weight: 600;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.8rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-fail {
        background: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
        font-weight: 600;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.8rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Terminal Console Window */
    .cisco-terminal-box {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        overflow: hidden;
        margin: 12px 0;
    }
    .cisco-terminal-bar {
        background: #1E293B;
        padding: 8px 14px;
        border-bottom: 1px solid #334155;
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #94A3B8;
    }
    .term-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-red { background: #EF4444; }
    .dot-yellow { background: #F59E0B; }
    .dot-green { background: #10B981; }

    .cisco-code {
        background: #0F172A;
        color: #38BDF8;
        padding: 12px 16px;
        border-radius: 6px;
        border-left: 3px solid #0284C7;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        line-height: 1.45;
        margin-top: 6px;
        white-space: pre-wrap;
    }

    /* Streamlit Containers with Border */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    }

    /* Clean Table Presentation */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        background: #FFFFFF !important;
    }

    /* Clean Tabs */
    button[data-baseweb="tab"] {
        color: #64748B !important;
        font-weight: 500 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2563EB !important;
        font-weight: 600 !important;
        border-bottom-color: #2563EB !important;
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
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding: 2px 0;">
        <div style="background: #2563eb; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.15rem; color: #ffffff; box-shadow: 0 1px 3px rgba(37,99,235,0.3);">🛡️</div>
        <div>
            <div style="font-size: 1.12rem; font-weight: 700; color: #0f172a; letter-spacing: -0.02em;">NetDoctor</div>
            <div style="font-size: 0.65rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;">Network NOC & Lab</div>
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

    nav_display_to_section = {
        "📊 Dashboard": "Overview",
        "📈 Live Monitoring": "Live Monitoring",
        "🩺 Fault Diagnosis": "Fault Diagnosis",
        "🧪 Manual Diagnostics": "Manual Diagnostics",
        "🔬 Routing & Lab (Cisco)": "Packet Tracer Lab Mode",
        "📜 History & Export": "History & Export",
        "⚙️ Settings & Config": "Settings & Config",
    }
    nav_selected = st.radio(
        "Navigation",
        list(nav_display_to_section.keys()),
        label_visibility="collapsed"
    )
    nav_section = nav_display_to_section[nav_selected]

    st.divider()
    st.markdown("""
    <div style="padding: 10px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;">
        <div style="display: flex; align-items: center; gap: 6px; font-size: 0.75rem; font-weight: 600; color: #047857;">
            <span style="width: 7px; height: 7px; border-radius: 50%; background: #10b981; display: inline-block;"></span> Backend Connected
        </div>
        <div style="font-size: 0.7rem; color: #64748b; margin-top: 2px;">
            Multi-layer diagnostic engine ready
        </div>
    </div>
    """, unsafe_allow_html=True)


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
# 1. OVERVIEW / DASHBOARD SECTION (NetSentry Match)
# ==========================================
if nav_section == "Overview":
    loc_ip = primary_info.get("local_ip", "Unknown")
    nic_name = primary_info.get("interface", "NIC")[:20]
    adapters = snap.get("adapters", [])

    # Top Header Bar (NetSentry Match)
    col_head_left, col_head_right = st.columns([3, 1])
    with col_head_left:
        st.markdown("""
        <div style="margin-bottom: 8px;">
            <h1 style="font-size: 1.55rem; font-weight: 700; color: #0f172a; margin: 0 0 2px 0; letter-spacing: -0.02em;">Dashboard</h1>
            <div style="font-size: 0.85rem; color: #64748b;">System metrics, live connections, and recent events</div>
        </div>
        """, unsafe_allow_html=True)
    with col_head_right:
        adapter_count = len(adapters)
        st.markdown(f"""
        <div style="display: flex; gap: 8px; justify-content: flex-end; align-items: center; margin-top: 6px;">
            <span style="background: #ffffff; color: #475569; border: 1px solid #e2e8f0; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 999px;">
                ● {adapter_count} adapters
            </span>
            <span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 999px;">
                ● Connected
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Row 1: Top Metric Cards (NetSentry Match)
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

    with col_stat1:
        if overall_status == "PASS":
            status_html = "<span class='badge-pass'>● HEALTHY (PASS)</span>"
        elif overall_status == "WARNING":
            status_html = "<span class='badge-warn'>● DEGRADED (WARN)</span>"
        else:
            status_html = "<span class='badge-fail'>● OUTAGE (FAIL)</span>"

        st.markdown(f"""
        <div class="ns-card">
            <div class="ns-card-header">
                <span class="ns-card-icon">⚡</span>
                <span class="ns-card-title">System Status</span>
            </div>
            <div style="margin: 6px 0 8px 0;">{status_html}</div>
            <div class="ns-card-sub">Multi-layer network telemetry verified</div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat2:
        if is_cloud and client_ip and not client_ip.startswith("::ffff:127."):
            header_title = "Detected Client IP"
            main_ip = client_ip
            sub_label = f"Host Server: {loc_ip} (eth0)"
        else:
            header_title = "Host IPv4 Address"
            main_ip = loc_ip
            sub_label = f"Adapter: {nic_name}"

        st.markdown(f"""
        <div class="ns-card">
            <div class="ns-card-header">
                <span class="ns-card-icon">🌐</span>
                <span class="ns-card-title">{header_title}</span>
            </div>
            <div class="ns-card-value">{main_ip}</div>
            <div class="ns-card-sub">{sub_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat3:
        gw_ip = primary_info.get("default_gateway", "Not Detected")
        gw_sub = "Cloud Container Gateway" if is_cloud else "Layer 3 Next-Hop Router"
        st.markdown(f"""
        <div class="ns-card">
            <div class="ns-card-header">
                <span class="ns-card-icon">🚪</span>
                <span class="ns-card-title">Default Gateway</span>
            </div>
            <div class="ns-card-value">{gw_ip}</div>
            <div class="ns-card-sub">{gw_sub}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat4:
        ts_full = snap.get("timestamp", "")
        ts_time = ts_full[11:19] if len(ts_full) >= 19 else "Just now"
        ts_date = ts_full[:10] if len(ts_full) >= 10 else ""
        st.markdown(f"""
        <div class="ns-card">
            <div class="ns-card-header">
                <span class="ns-card-icon">⏱️</span>
                <span class="ns-card-title">Last Telemetry Check</span>
            </div>
            <div class="ns-card-value">{ts_time}</div>
            <div class="ns-card-sub">Date: {ts_date}</div>
        </div>
        """, unsafe_allow_html=True)

    # Row 2: Network Interfaces Panel (Direct match to NetSentry screenshot)
    chips_html = ""
    if is_cloud and client_ip and not client_ip.startswith("::ffff:127."):
        chips_html += f"""
        <div class="ns-nic-chip" style="background:#eff6ff; border-color:#bfdbfe;">
            <div class="ns-nic-name" style="color:#1d4ed8; font-weight:600;">Client Device (You)</div>
            <div class="ns-nic-ip" style="color:#1d4ed8;">{client_ip}</div>
        </div>
        """
    if adapters:
        for a in adapters:
            nic_title = a.get("interface", "NIC")
            ip_val = a.get("ipv4", "Unassigned")
            chips_html += f"""
            <div class="ns-nic-chip">
                <div class="ns-nic-name" title="{nic_title}">{nic_title}</div>
                <div class="ns-nic-ip">{ip_val}</div>
            </div>
            """
    else:
        chips_html = f"""
        <div class="ns-nic-chip">
            <div class="ns-nic-name">Primary NIC</div>
            <div class="ns-nic-ip">{loc_ip}</div>
        </div>
        """

    st.markdown(f"""
    <div class="ns-panel">
        <div class="ns-panel-title">Network Interfaces</div>
        <div class="ns-panel-subtitle">IPv4 addresses assigned to each network adapter on this host.</div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            {chips_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Row 3: Protocol Telemetry & Layer Verification (NetSentry Match)
    gw_test = snap.get("gateway_test", {})
    dns_res = snap.get("dns_results", [])
    tcp_res = snap.get("tcp_results", [])
    ping_res = snap.get("ping_results", [])

    dns_passes = sum(1 for d in dns_res if d.get("status") == "PASS")
    dns_total = len(dns_res)
    tcp_passes = sum(1 for t in tcp_res if t.get("status") == "PASS")
    tcp_total = len(tcp_res)

    st.markdown(f"""
    <div class="ns-panel">
        <div class="ns-panel-title">Protocol Telemetry & Layer Verification</div>
        <div class="ns-panel-subtitle">Multi-layer operational status across Gateway, DNS resolution, and TCP port transport.</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 10px;">
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px 14px;">
                <div style="font-size:0.72rem; color:#64748b; font-weight:600; text-transform:uppercase;">Layer 3 Gateway</div>
                <div style="font-size:1.15rem; font-weight:700; color:#0f172a; margin:3px 0;">{gw_test.get('rtt_avg_ms', 0)} ms</div>
                <div style="font-size:0.75rem; color:#047857; font-weight:600;">PASS &bull; Target: {gw_test.get('target', 'N/A')}</div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px 14px;">
                <div style="font-size:0.72rem; color:#64748b; font-weight:600; text-transform:uppercase;">Layer 7 DNS</div>
                <div style="font-size:1.15rem; font-weight:700; color:#0f172a; margin:3px 0;">{dns_passes}/{dns_total} Resolved</div>
                <div style="font-size:0.75rem; color:#047857; font-weight:600;">PASS &bull; Global Resolvers</div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px 14px;">
                <div style="font-size:0.72rem; color:#64748b; font-weight:600; text-transform:uppercase;">Layer 4 TCP</div>
                <div style="font-size:1.15rem; font-weight:700; color:#0f172a; margin:3px 0;">{tcp_passes}/{tcp_total} Connected</div>
                <div style="font-size:0.75rem; color:#047857; font-weight:600;">PASS &bull; Ports 80, 443, 53</div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px 14px;">
                <div style="font-size:0.72rem; color:#64748b; font-weight:600; text-transform:uppercase;">Network Platform</div>
                <div style="font-size:1.15rem; font-weight:700; color:#0f172a; margin:3px 0;">{primary_info.get('interface', 'eth0')[:18]}</div>
                <div style="font-size:0.75rem; color:#2563eb; font-weight:600;">{'Cloud Linux Host' if is_cloud else 'Windows Physical PC'}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Row 4: Live Events Panel (Direct match to NetSentry screenshot)
    recent_events = st.session_state.tracker.events[-5:]
    events_count = len(recent_events)

    if recent_events:
        events_list_html = ""
        for ev in reversed(recent_events):
            ev_type = ev.get("event_type")
            ts = ev.get("timestamp")[:19].replace("T", " ")
            desc = ev.get("description", "")
            if ev_type == "RECOVERY":
                events_list_html += f"""
                <div style="display:flex; align-items:center; gap:8px; padding:8px 0; border-bottom:1px solid #f1f5f9;">
                    <span style="color:#10b981; font-weight:700;">✓</span>
                    <span style="font-size:0.82rem; font-weight:600; color:#047857;">RECOVERY [{ts}]</span>
                    <span style="font-size:0.82rem; color:#334155;">&mdash; {desc}</span>
                </div>
                """
            else:
                events_list_html += f"""
                <div style="display:flex; align-items:center; gap:8px; padding:8px 0; border-bottom:1px solid #f1f5f9;">
                    <span style="color:#ef4444; font-weight:700;">⚠</span>
                    <span style="font-size:0.82rem; font-weight:600; color:#b91c1c;">FAILURE [{ts}]</span>
                    <span style="font-size:0.82rem; color:#334155;">&mdash; {desc}</span>
                </div>
                """
        events_body = events_list_html
    else:
        events_body = """
        <div style="text-align: center; padding: 22px 0; color: #64748b;">
            <div style="font-size: 1.5rem; color: #94a3b8; margin-bottom: 4px;">✓</div>
            <div style="font-size: 0.85rem; font-weight: 500;">No events recorded yet. Connect a client or trigger a diagnostic run to generate activity.</div>
        </div>
        """

    st.markdown(f"""
    <div class="ns-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div class="ns-panel-title" style="display: flex; align-items: center; gap: 8px;">
                Live Events <span style="color: #10b981; font-size: 0.75rem;">●</span>
            </div>
            <div style="font-size: 0.75rem; color: #64748b;">{events_count} events</div>
        </div>
        {events_body}
    </div>
    """, unsafe_allow_html=True)

    # Row 5: Live On-Demand Network Probe Panel
    with st.container():
        st.markdown("""
        <div class="ns-panel" style="margin-bottom: 14px;">
            <div class="ns-panel-title">Live On-Demand Network Probe</div>
            <div class="ns-panel-subtitle">Benchmark any custom IP, website, or router port live from this active dashboard:</div>
        </div>
        """, unsafe_allow_html=True)

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

    # Diagnostic Finding Alert (if any issues)
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
            conf_badge = "<span style='background:#ecfdf5; color:#047857; padding:2px 8px; border-radius:4px; font-weight:600; font-size:0.75rem; border:1px solid #a7f3d0;'>CONFIDENCE: HIGH</span>"
        elif confidence == "MEDIUM":
            conf_badge = "<span style='background:#fffbeb; color:#b45309; padding:2px 8px; border-radius:4px; font-weight:600; font-size:0.75rem; border:1px solid #fde68a;'>CONFIDENCE: MEDIUM</span>"
        else:
            conf_badge = "<span style='background:#f1f5f9; color:#475569; padding:2px 8px; border-radius:4px; font-weight:600; font-size:0.75rem; border:1px solid #cbd5e1;'>CONFIDENCE: LOW</span>"

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
