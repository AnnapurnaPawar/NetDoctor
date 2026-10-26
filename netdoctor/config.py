"""
Configuration module for NetDoctor.
Contains default targets, thresholds, timeouts, and monitoring intervals.
"""

# Monitoring interval settings (seconds)
DEFAULT_MONITOR_INTERVAL_SEC = 5
MIN_MONITOR_INTERVAL_SEC = 3
MAX_MONITOR_INTERVAL_SEC = 60

# Test timeout settings (seconds)
DEFAULT_GATEWAY_TIMEOUT_SEC = 1.5
DEFAULT_DNS_TIMEOUT_SEC = 2.0
DEFAULT_TCP_TIMEOUT_SEC = 2.0
DEFAULT_PING_TIMEOUT_MS = 1000
DEFAULT_PING_COUNT = 2

# Thresholds for categorizing network health
LATENCY_GOOD_MS = 50.0      # < 50ms is excellent
LATENCY_WARN_MS = 150.0     # 50ms - 150ms is acceptable/warning
                            # > 150ms is high latency

PACKET_LOSS_GOOD_PCT = 0.0  # 0% packet loss is healthy
PACKET_LOSS_WARN_PCT = 25.0 # 1% - 25% packet loss is degraded
                            # > 25% is critical failure

# Default DNS hostnames to resolve
DEFAULT_DNS_TARGETS = [
    "google.com",
    "cloudflare.com",
    "github.com",
    "microsoft.com"
]

# Default TCP service targets (Host, Port, Service Name)
DEFAULT_TCP_TARGETS = [
    {"host": "1.1.1.1", "port": 53, "service": "Cloudflare DNS (TCP 53)"},
    {"host": "8.8.8.8", "port": 53, "service": "Google DNS (TCP 53)"},
    {"host": "google.com", "port": 80, "service": "Google HTTP (Port 80)"},
    {"host": "1.1.1.1", "port": 443, "service": "Cloudflare HTTPS (Port 443)"}
]

# Default destination hosts for ICMP Ping
DEFAULT_PING_TARGETS = [
    {"host": "8.8.8.8", "label": "Google Public DNS"},
    {"host": "1.1.1.1", "label": "Cloudflare DNS"}
]
