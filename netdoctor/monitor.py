"""
Real-time Network Diagnostics and Monitoring Module for NetDoctor.
Performs genuine Windows network tests:
- Network Adapter configuration (IP, subnet mask, MAC, status)
- Default Gateway detection and reachability
- DNS hostname resolution and latency
- Destination reachability (ICMP Ping)
- TCP service port connectivity
"""

import re
import socket
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import psutil

from netdoctor.config import (
    DEFAULT_GATEWAY_TIMEOUT_SEC,
    DEFAULT_DNS_TIMEOUT_SEC,
    DEFAULT_TCP_TIMEOUT_SEC,
    DEFAULT_PING_TIMEOUT_MS,
    DEFAULT_PING_COUNT,
    LATENCY_GOOD_MS,
    LATENCY_WARN_MS,
    PACKET_LOSS_GOOD_PCT,
    PACKET_LOSS_WARN_PCT,
    DEFAULT_DNS_TARGETS,
    DEFAULT_TCP_TARGETS,
    DEFAULT_PING_TARGETS,
)

# Regex to validate hostname or IPv4 strictly to prevent command injection
HOST_REGEX = re.compile(r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|localhost)$")


def is_valid_host(host: str) -> bool:
    """Validate that host is a safe domain name or IPv4 address."""
    if not host or not isinstance(host, str):
        return False
    host = host.strip()
    return bool(HOST_REGEX.match(host))


def get_network_adapters() -> List[Dict[str, Any]]:
    """
    Retrieve active and inactive network adapters using psutil.
    Returns details including interface name, IPv4, netmask, MAC, and operational status.
    """
    adapters = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for nic_name, nic_addrs in addrs.items():
            stat = stats.get(nic_name)
            is_up = stat.isup if stat else False
            speed_mbps = stat.speed if stat else 0

            ipv4 = None
            netmask = None
            mac = None
            ipv6 = None

            for addr in nic_addrs:
                if addr.family == socket.AF_INET:
                    ipv4 = addr.address
                    netmask = addr.netmask
                elif addr.family == psutil.AF_LINK or addr.family == -1:
                    mac = addr.address
                elif hasattr(socket, "AF_INET6") and addr.family == socket.AF_INET6:
                    ipv6 = addr.address

            # Filter out virtual loopback unless it's the only one
            if nic_name.lower().startswith("loopback") and not ipv4:
                continue

            adapters.append({
                "interface": nic_name,
                "is_up": is_up,
                "speed_mbps": speed_mbps,
                "ipv4": ipv4 or "Unassigned",
                "netmask": netmask or "N/A",
                "mac": mac or "N/A",
                "ipv6": ipv6 or "N/A"
            })
    except Exception as e:
        adapters.append({
            "interface": "Error",
            "is_up": False,
            "speed_mbps": 0,
            "ipv4": f"Detection error: {e}",
            "netmask": "N/A",
            "mac": "N/A",
            "ipv6": "N/A"
        })
    return adapters


def get_primary_adapter_and_gateway() -> Dict[str, Any]:
    """
    Finds the active network adapter, local IP, and default gateway using Windows route print and ipconfig.
    """
    primary_ip = None
    default_gateway = None
    primary_interface = None

    # Method 1: Query 'route print 0.0.0.0'
    try:
        res = subprocess.run(
            ["route", "print", "0.0.0.0"],
            capture_output=True,
            text=True,
            timeout=3
        )
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            for line in lines:
                parts = line.strip().split()
                # Line format: 0.0.0.0  0.0.0.0  <Gateway>  <Interface>  <Metric>
                if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                    candidate_gw = parts[2]
                    candidate_ip = parts[3]
                    if is_valid_host(candidate_gw) and candidate_gw != "On-link":
                        default_gateway = candidate_gw
                        primary_ip = candidate_ip
                        break
    except Exception:
        pass

    # Method 2: Fallback to ipconfig if route print did not return gateway
    if not default_gateway:
        try:
            res = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                current_adapter = None
                for line in res.stdout.splitlines():
                    if "adapter" in line.lower() and not line.startswith(" "):
                        current_adapter = line.strip().strip(":")
                    elif "ipv4" in line.lower() and ":" in line:
                        ip_val = line.split(":", 1)[1].strip().replace("(Preferred)", "").strip()
                        if not primary_ip and is_valid_host(ip_val):
                            primary_ip = ip_val
                            primary_interface = current_adapter
                    elif "default gateway" in line.lower() and ":" in line:
                        gw_val = line.split(":", 1)[1].strip()
                        if gw_val and is_valid_host(gw_val):
                            default_gateway = gw_val
                            if current_adapter:
                                primary_interface = current_adapter
                            break
        except Exception:
            pass

    # Fallback to socket local IP if needed
    if not primary_ip:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
        except Exception:
            primary_ip = "127.0.0.1"

    return {
        "local_ip": primary_ip or "Unknown",
        "default_gateway": default_gateway or "Not Detected",
        "interface": primary_interface or "Active Connection"
    }


def ping_host(host: str, count: int = DEFAULT_PING_COUNT, timeout_ms: int = DEFAULT_PING_TIMEOUT_MS) -> Dict[str, Any]:
    """
    Execute genuine Windows ping command to check ICMP reachability, response time, and packet loss.
    """
    clean_host = host.strip() if host else ""
    if not is_valid_host(clean_host):
        return {
            "target": clean_host,
            "status": "FAIL",
            "sent": count,
            "received": 0,
            "loss_pct": 100.0,
            "rtt_avg_ms": None,
            "rtt_min_ms": None,
            "rtt_max_ms": None,
            "error": "Invalid or unsafe hostname/IP address"
        }

    cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), clean_host]
    timeout_total = max(4.0, (timeout_ms / 1000.0) * count + 2.0)

    try:
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_total)
        elapsed_sec = time.perf_counter() - t0
        output = proc.stdout + proc.stderr

        # Check for immediate driver or general failures
        if "General failure" in output or "Unable to contact IP driver" in output:
            return {
                "target": clean_host,
                "status": "FAIL",
                "sent": count,
                "received": 0,
                "loss_pct": 100.0,
                "rtt_avg_ms": None,
                "rtt_min_ms": None,
                "rtt_max_ms": None,
                "error": "General failure / raw socket access restricted"
            }

        # Parse packets sent, received, lost
        # Format: "Packets: Sent = 2, Received = 2, Lost = 0 (0% loss)"
        packets_match = re.search(r"Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)\s*\(([\d.]+)%\s*loss\)", output, re.IGNORECASE)
        sent = count
        received = 0
        loss_pct = 100.0
        if packets_match:
            sent = int(packets_match.group(1))
            received = int(packets_match.group(2))
            loss_pct = float(packets_match.group(4))

        # Parse round trip times in ms
        # Format: "Minimum = 12ms, Maximum = 15ms, Average = 13ms"
        # Or: "time<1ms" or "time=12ms"
        rtt_min = None
        rtt_max = None
        rtt_avg = None
        rtt_match = re.search(r"Minimum\s*=\s*(\d+)ms,\s*Maximum\s*=\s*(\d+)ms,\s*Average\s*=\s*(\d+)ms", output, re.IGNORECASE)
        if rtt_match:
            rtt_min = float(rtt_match.group(1))
            rtt_max = float(rtt_match.group(2))
            rtt_avg = float(rtt_match.group(3))
        elif received > 0:
            times = re.findall(r"time[<=](\d+)ms", output, re.IGNORECASE)
            if times:
                nums = [float(t) for t in times]
                rtt_min = min(nums)
                rtt_max = max(nums)
                rtt_avg = round(sum(nums) / len(nums), 1)
            else:
                rtt_avg = round(elapsed_sec * 1000 / max(1, received), 1)

        # Evaluate status
        if received == 0 or loss_pct == 100.0:
            status = "FAIL"
            err = "Request timed out or destination host unreachable"
        elif loss_pct > PACKET_LOSS_WARN_PCT or (rtt_avg and rtt_avg > LATENCY_WARN_MS):
            status = "WARNING"
            err = f"Degraded performance: {loss_pct}% loss, latency {rtt_avg} ms"
        else:
            status = "PASS"
            err = None

        return {
            "target": clean_host,
            "status": status,
            "sent": sent,
            "received": received,
            "loss_pct": loss_pct,
            "rtt_avg_ms": rtt_avg,
            "rtt_min_ms": rtt_min,
            "rtt_max_ms": rtt_max,
            "error": err
        }
    except subprocess.TimeoutExpired:
        return {
            "target": clean_host,
            "status": "FAIL",
            "sent": count,
            "received": 0,
            "loss_pct": 100.0,
            "rtt_avg_ms": None,
            "rtt_min_ms": None,
            "rtt_max_ms": None,
            "error": "Ping subprocess timed out"
        }
    except Exception as e:
        return {
            "target": clean_host,
            "status": "FAIL",
            "sent": count,
            "received": 0,
            "loss_pct": 100.0,
            "rtt_avg_ms": None,
            "rtt_min_ms": None,
            "rtt_max_ms": None,
            "error": str(e)
        }


def resolve_dns(hostname: str, timeout_sec: float = DEFAULT_DNS_TIMEOUT_SEC) -> Dict[str, Any]:
    """
    Resolve a hostname to IPv4 addresses and measure DNS lookup latency in milliseconds.
    """
    clean_host = hostname.strip() if hostname else ""
    if not is_valid_host(clean_host):
        return {
            "hostname": clean_host,
            "status": "FAIL",
            "resolved_ips": [],
            "latency_ms": None,
            "error": "Invalid hostname"
        }

    t0 = time.perf_counter()
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout_sec)
        # getaddrinfo performs DNS query for AF_INET
        addr_info = socket.getaddrinfo(clean_host, None, socket.AF_INET, socket.SOCK_STREAM)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        ips = list({item[4][0] for item in addr_info if item[4]})
        return {
            "hostname": clean_host,
            "status": "PASS",
            "resolved_ips": sorted(ips),
            "latency_ms": latency_ms,
            "error": None
        }
    except socket.gaierror as e:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "hostname": clean_host,
            "status": "FAIL",
            "resolved_ips": [],
            "latency_ms": latency_ms,
            "error": f"DNS resolution failed (getaddrinfo: {e})"
        }
    except socket.timeout:
        return {
            "hostname": clean_host,
            "status": "FAIL",
            "resolved_ips": [],
            "latency_ms": round(timeout_sec * 1000, 2),
            "error": "DNS resolution timed out"
        }
    except Exception as e:
        return {
            "hostname": clean_host,
            "status": "FAIL",
            "resolved_ips": [],
            "latency_ms": None,
            "error": str(e)
        }
    finally:
        socket.setdefaulttimeout(old_timeout)


def test_tcp_port(host: str, port: int, timeout_sec: float = DEFAULT_TCP_TIMEOUT_SEC) -> Dict[str, Any]:
    """
    Test TCP connectivity to a specific destination host and port.
    Measures TCP 3-way handshake connection time.
    """
    clean_host = host.strip() if host else ""
    if not is_valid_host(clean_host):
        return {
            "host": clean_host,
            "port": port,
            "status": "FAIL",
            "latency_ms": None,
            "error": "Invalid host"
        }

    t0 = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_sec)
    try:
        sock.connect((clean_host, port))
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        sock.close()
        return {
            "host": clean_host,
            "port": port,
            "status": "PASS",
            "latency_ms": latency_ms,
            "error": None
        }
    except socket.timeout:
        return {
            "host": clean_host,
            "port": port,
            "status": "FAIL",
            "latency_ms": round(timeout_sec * 1000, 2),
            "error": f"Connection timed out ({timeout_sec}s)"
        }
    except ConnectionRefusedError:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "host": clean_host,
            "port": port,
            "status": "FAIL",
            "latency_ms": latency_ms,
            "error": "Connection refused by target port (Port closed or reset)"
        }
    except Exception as e:
        return {
            "host": clean_host,
            "port": port,
            "status": "FAIL",
            "latency_ms": None,
            "error": str(e)
        }
    finally:
        try:
            sock.close()
        except Exception:
            pass


def run_full_system_diagnostic(
    dns_targets: Optional[List[str]] = None,
    tcp_targets: Optional[List[Dict[str, Any]]] = None,
    ping_targets: Optional[List[Dict[str, str]]] = None,
    gateway_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a full diagnostic check across all layers:
    1. Local adapters & Gateway detection
    2. Default Gateway Ping
    3. DNS Resolution
    4. Destination Pings
    5. TCP Port Probes
    """
    timestamp = datetime.now().isoformat()
    dns_targets = dns_targets or DEFAULT_DNS_TARGETS
    tcp_targets = tcp_targets or DEFAULT_TCP_TARGETS
    ping_targets = ping_targets or DEFAULT_PING_TARGETS

    # 1. Local Adapter and Gateway info
    primary_info = get_primary_adapter_and_gateway()
    gateway_ip = gateway_override or primary_info.get("default_gateway")
    adapters = get_network_adapters()

    # 2. Check Gateway reachability
    gateway_test = None
    if gateway_ip and gateway_ip != "Not Detected" and is_valid_host(gateway_ip):
        gateway_test = ping_host(gateway_ip, count=2, timeout_ms=1000)
    else:
        gateway_test = {
            "target": gateway_ip or "None",
            "status": "FAIL",
            "sent": 0,
            "received": 0,
            "loss_pct": 100.0,
            "rtt_avg_ms": None,
            "error": "No valid default gateway configured or detected"
        }

    # 3. DNS Tests
    dns_results = []
    for host in dns_targets:
        res = resolve_dns(host, timeout_sec=DEFAULT_DNS_TIMEOUT_SEC)
        dns_results.append(res)

    # 4. ICMP Ping Targets
    ping_results = []
    for tgt in ping_targets:
        host = tgt.get("host")
        label = tgt.get("label", host)
        res = ping_host(host, count=DEFAULT_PING_COUNT, timeout_ms=DEFAULT_PING_TIMEOUT_MS)
        res["label"] = label
        ping_results.append(res)

    # 5. TCP Service Targets
    tcp_results = []
    for tgt in tcp_targets:
        host = tgt["host"]
        port = tgt["port"]
        service = tgt.get("service", f"{host}:{port}")
        res = test_tcp_port(host, port, timeout_sec=DEFAULT_TCP_TIMEOUT_SEC)
        res["service"] = service
        tcp_results.append(res)

    # Determine overall status
    has_fail = False
    has_warn = False

    if gateway_test["status"] == "FAIL":
        has_fail = True
    elif gateway_test["status"] == "WARNING":
        has_warn = True

    for d in dns_results:
        if d["status"] == "FAIL":
            has_fail = True

    for p in ping_results:
        if p["status"] == "FAIL":
            has_fail = True
        elif p["status"] == "WARNING":
            has_warn = True

    for t in tcp_results:
        if t["status"] == "FAIL":
            has_fail = True

    if has_fail:
        overall_status = "FAIL"
    elif has_warn:
        overall_status = "WARNING"
    else:
        overall_status = "PASS"

    return {
        "timestamp": timestamp,
        "overall_status": overall_status,
        "primary_info": primary_info,
        "adapters": adapters,
        "gateway_test": gateway_test,
        "dns_results": dns_results,
        "ping_results": ping_results,
        "tcp_results": tcp_results
    }
