"""
Unit tests for netdoctor.monitor
"""

import pytest
from netdoctor.monitor import is_valid_host, get_network_adapters, resolve_dns


def test_is_valid_host():
    assert is_valid_host("google.com") is True
    assert is_valid_host("192.168.1.1") is True
    assert is_valid_host("8.8.8.8") is True
    assert is_valid_host("localhost") is True
    assert is_valid_host("sub.domain.example.org") is True

    # Invalid / injection attempts
    assert is_valid_host("") is False
    assert is_valid_host("google.com; rm -rf") is False
    assert is_valid_host("192.168.1.1 & calc.exe") is False
    assert is_valid_host("$(whoami)") is False
    assert is_valid_host("   ") is False


def test_get_network_adapters():
    adapters = get_network_adapters()
    assert isinstance(adapters, list)
    assert len(adapters) > 0
    # Check keys
    for a in adapters:
        assert "interface" in a
        assert "is_up" in a
        assert "ipv4" in a
        assert "mac" in a
