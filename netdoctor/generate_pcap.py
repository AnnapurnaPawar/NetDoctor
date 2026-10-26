"""
Generates an authentic PCAP file containing valid ICMP Echo, DNS Query/Response,
and TCP 3-Way Handshake packets for Wireshark inspection.
"""

import os
from scapy.all import IP, ICMP, TCP, UDP, DNS, DNSQR, DNSRR, Ether, wrpcap

def create_sample_pcap(filepath: str):
    packets = []

    # 1. ICMP Ping Request & Reply
    p_icmp_req = Ether()/IP(src="192.168.0.103", dst="8.8.8.8", id=101)/ICMP(type=8, seq=1)
    p_icmp_rep = Ether()/IP(src="8.8.8.8", dst="192.168.0.103", id=102)/ICMP(type=0, seq=1)
    packets.extend([p_icmp_req, p_icmp_rep])

    # 2. DNS Query & Response
    p_dns_req = Ether()/IP(src="192.168.0.103", dst="1.1.1.1")/UDP(sport=54321, dport=53)/DNS(
        rd=1, qd=DNSQR(qname="google.com")
    )
    p_dns_rep = Ether()/IP(src="1.1.1.1", dst="192.168.0.103")/UDP(sport=53, dport=54321)/DNS(
        id=p_dns_req[DNS].id, qr=1, aa=0, rcode=0,
        qd=p_dns_req[DNS].qd,
        an=DNSRR(rrname="google.com", type='A', rclass='IN', ttl=300, rdata="142.250.190.46")
    )
    packets.extend([p_dns_req, p_dns_rep])

    # 3. TCP 3-Way Handshake (SYN -> SYN-ACK -> ACK)
    seq_init = 1000
    ack_init = 2000
    p_syn = Ether()/IP(src="192.168.0.103", dst="1.1.1.1")/TCP(sport=49152, dport=443, flags="S", seq=seq_init)
    p_synack = Ether()/IP(src="1.1.1.1", dst="192.168.0.103")/TCP(sport=443, dport=49152, flags="SA", seq=ack_init, ack=seq_init + 1)
    p_ack = Ether()/IP(src="192.168.0.103", dst="1.1.1.1")/TCP(sport=49152, dport=443, flags="A", seq=seq_init + 1, ack=ack_init + 1)
    packets.extend([p_syn, p_synack, p_ack])

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wrpcap(filepath, packets)
    print(f"Successfully generated {len(packets)} packets into {filepath}")

if __name__ == "__main__":
    out_path = r"C:\Users\annap\.gemini\antigravity\scratch\NetDoctor\captures\genuine_network_traffic.pcap"
    create_sample_pcap(out_path)
