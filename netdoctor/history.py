"""
History, State Tracking, and Recovery Verification Module for NetDoctor.
Tracks test transitions (Healthy -> Failed -> Recovered) and manages CSV export.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


class NetworkHistoryTracker:
    """
    Maintains a rolling history of diagnostic runs and detects recovery events.
    """

    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self.history: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []

    def add_snapshot(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Records a new diagnostic snapshot and detects any failure or recovery events
        by comparing against the previous snapshot.
        """
        new_events = []
        current_time = snapshot.get("timestamp", datetime.now().isoformat())

        if self.history:
            prev_snapshot = self.history[-1]
            prev_time = prev_snapshot.get("timestamp", "Previous")

            # 1. Compare Gateway Status
            prev_gw = prev_snapshot.get("gateway_test", {})
            curr_gw = snapshot.get("gateway_test", {})
            gw_target = curr_gw.get("target", "Gateway")

            if prev_gw.get("status") == "FAIL" and curr_gw.get("status") == "PASS":
                new_events.append({
                    "timestamp": current_time,
                    "event_type": "RECOVERY",
                    "category": "Default Gateway",
                    "description": f"Default Gateway ({gw_target}) recovered from FAIL to PASS. RTT: {curr_gw.get('rtt_avg_ms')} ms.",
                    "previous_status": "FAIL",
                    "current_status": "PASS"
                })
            elif prev_gw.get("status") == "PASS" and curr_gw.get("status") == "FAIL":
                new_events.append({
                    "timestamp": current_time,
                    "event_type": "FAILURE",
                    "category": "Default Gateway",
                    "description": f"Default Gateway ({gw_target}) failed reachability test ({curr_gw.get('error', 'Unreachable')}).",
                    "previous_status": "PASS",
                    "current_status": "FAIL"
                })

            # 2. Compare DNS Tests
            prev_dns = {d.get("hostname"): d.get("status") for d in prev_snapshot.get("dns_results", [])}
            for d in snapshot.get("dns_results", []):
                host = d.get("hostname")
                cur_status = d.get("status")
                old_status = prev_dns.get(host)
                if old_status == "FAIL" and cur_status == "PASS":
                    new_events.append({
                        "timestamp": current_time,
                        "event_type": "RECOVERY",
                        "category": "DNS Resolution",
                        "description": f"DNS resolution for '{host}' restored. Latency: {d.get('latency_ms')} ms.",
                        "previous_status": "FAIL",
                        "current_status": "PASS"
                    })
                elif old_status == "PASS" and cur_status == "FAIL":
                    new_events.append({
                        "timestamp": current_time,
                        "event_type": "FAILURE",
                        "category": "DNS Resolution",
                        "description": f"DNS resolution for '{host}' failed ({d.get('error')}).",
                        "previous_status": "PASS",
                        "current_status": "FAIL"
                    })

            # 3. Compare TCP Probes
            prev_tcp = {t.get("service"): t.get("status") for t in prev_snapshot.get("tcp_results", [])}
            for t in snapshot.get("tcp_results", []):
                svc = t.get("service")
                cur_status = t.get("status")
                old_status = prev_tcp.get(svc)
                if old_status == "FAIL" and cur_status == "PASS":
                    new_events.append({
                        "timestamp": current_time,
                        "event_type": "RECOVERY",
                        "category": "TCP Service",
                        "description": f"TCP connection to '{svc}' restored. Handshake time: {t.get('latency_ms')} ms.",
                        "previous_status": "FAIL",
                        "current_status": "PASS"
                    })
                elif old_status == "PASS" and cur_status == "FAIL":
                    new_events.append({
                        "timestamp": current_time,
                        "event_type": "FAILURE",
                        "category": "TCP Service",
                        "description": f"TCP connection to '{svc}' failed ({t.get('error')}).",
                        "previous_status": "PASS",
                        "current_status": "FAIL"
                    })

        self.history.append(snapshot)
        if len(self.history) > self.max_entries:
            self.history.pop(0)

        self.events.extend(new_events)
        return new_events

    def get_history_dataframe(self) -> pd.DataFrame:
        """
        Converts the historical snapshots into a clean Pandas DataFrame for plotting and CSV export.
        """
        rows = []
        for snap in self.history:
            gw = snap.get("gateway_test", {})
            pings = snap.get("ping_results", [])
            dns = snap.get("dns_results", [])
            tcps = snap.get("tcp_results", [])

            # Compute average latency across active ping and tcp
            latencies = []
            if gw.get("rtt_avg_ms"):
                latencies.append(gw["rtt_avg_ms"])
            for p in pings:
                if p.get("rtt_avg_ms"):
                    latencies.append(p["rtt_avg_ms"])
            for t in tcps:
                if t.get("latency_ms"):
                    latencies.append(t["latency_ms"])

            avg_lat = round(sum(latencies) / len(latencies), 1) if latencies else None

            # Compute average packet loss across pings
            losses = []
            if gw.get("loss_pct") is not None:
                losses.append(gw["loss_pct"])
            for p in pings:
                if p.get("loss_pct") is not None:
                    losses.append(p["loss_pct"])

            avg_loss = round(sum(losses) / len(losses), 1) if losses else 0.0

            rows.append({
                "Timestamp": snap.get("timestamp"),
                "Overall Status": snap.get("overall_status"),
                "Local IP": snap.get("primary_info", {}).get("local_ip", "N/A"),
                "Gateway Status": gw.get("status", "N/A"),
                "Gateway RTT (ms)": gw.get("rtt_avg_ms"),
                "DNS Passes": sum(1 for d in dns if d.get("status") == "PASS"),
                "DNS Fails": sum(1 for d in dns if d.get("status") == "FAIL"),
                "TCP Passes": sum(1 for t in tcps if t.get("status") == "PASS"),
                "TCP Fails": sum(1 for t in tcps if t.get("status") == "FAIL"),
                "Avg Latency (ms)": avg_lat,
                "Avg Packet Loss (%)": avg_loss
            })

        return pd.DataFrame(rows)

    def export_to_csv_string(self) -> str:
        """Export history to a CSV string."""
        df = self.get_history_dataframe()
        return df.to_csv(index=False)


def compare_recovery_snapshots(before_snap: Dict[str, Any], after_snap: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares a 'Before Fix' snapshot against an 'After Fix' snapshot
    to verify recovery of specific network services.
    """
    comparison = {
        "before_status": before_snap.get("overall_status", "UNKNOWN"),
        "after_status": after_snap.get("overall_status", "UNKNOWN"),
        "restored_items": [],
        "degraded_items": [],
        "unchanged_items": [],
        "recovery_verified": False
    }

    # Gateway comparison
    gw_before = before_snap.get("gateway_test", {})
    gw_after = after_snap.get("gateway_test", {})
    gw_target = gw_after.get("target", "Gateway")

    if gw_before.get("status") == "FAIL" and gw_after.get("status") == "PASS":
        comparison["restored_items"].append({
            "service": f"Default Gateway ({gw_target})",
            "before": "FAIL",
            "after": f"PASS ({gw_after.get('rtt_avg_ms', 0)} ms)"
        })
    elif gw_before.get("status") == "PASS" and gw_after.get("status") == "FAIL":
        comparison["degraded_items"].append({
            "service": f"Default Gateway ({gw_target})",
            "before": "PASS",
            "after": "FAIL"
        })

    # DNS comparison
    dns_b = {d.get("hostname"): d.get("status") for d in before_snap.get("dns_results", [])}
    for d_a in after_snap.get("dns_results", []):
        host = d_a.get("hostname")
        st_after = d_a.get("status")
        st_before = dns_b.get(host)
        if st_before == "FAIL" and st_after == "PASS":
            comparison["restored_items"].append({
                "service": f"DNS: {host}",
                "before": "FAIL",
                "after": f"PASS ({d_a.get('latency_ms')} ms)"
            })
        elif st_before == "PASS" and st_after == "FAIL":
            comparison["degraded_items"].append({
                "service": f"DNS: {host}",
                "before": "PASS",
                "after": "FAIL"
            })

    # TCP comparison
    tcp_b = {t.get("service"): t.get("status") for t in before_snap.get("tcp_results", [])}
    for t_a in after_snap.get("tcp_results", []):
        svc = t_a.get("service")
        st_after = t_a.get("status")
        st_before = tcp_b.get(svc)
        if st_before == "FAIL" and st_after == "PASS":
            comparison["restored_items"].append({
                "service": f"TCP: {svc}",
                "before": "FAIL",
                "after": f"PASS ({t_a.get('latency_ms')} ms)"
            })
        elif st_before == "PASS" and st_after == "FAIL":
            comparison["degraded_items"].append({
                "service": f"TCP: {svc}",
                "before": "PASS",
                "after": "FAIL"
            })

    # Overall verdict
    if comparison["restored_items"] and not comparison["degraded_items"]:
        comparison["recovery_verified"] = True
    elif after_snap.get("overall_status") == "PASS":
        comparison["recovery_verified"] = True

    return comparison
