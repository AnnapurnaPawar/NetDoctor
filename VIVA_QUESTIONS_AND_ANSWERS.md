# NetDoctor: Viva Defense Questions and Answers

This reference guide prepares you to answer questions confidently during your project presentation or oral examination (viva).

---

### Q1: What is NetDoctor, and what core problem does it solve?
**Answer:**  
NetDoctor is an end-to-end network health monitoring, fault diagnosis, and recovery verification system.  
Most basic network tools simply tell you *"Network is down"* without explaining why. NetDoctor combines:
1. **Real-time multi-layer monitoring** of a genuine Windows computer (Physical NIC, Gateway, DNS, ICMP, and TCP).
2. An **evidence-based diagnostic engine** that correlates symptoms to find the true root cause (e.g. distinguishing between a total outage vs. an ISP blocking ICMP).
3. A **Cisco Packet Tracer Lab Mode** that parses simulated router and switch CLI outputs, detects network misconfigurations, suggests exact Cisco commands to fix them, and proves that recovery occurred.

---

### Q2: Why is testing both ICMP (Ping) and TCP essential? Isn't Ping enough?
**Answer:**  
No, relying solely on Ping (ICMP) leads to false alarms. Many modern network administrators, enterprise firewalls, and cloud providers intentionally filter or drop ICMP Echo packets to prevent denial-of-service scans, while keeping standard web traffic (TCP Port 80/443) open.  
If NetDoctor finds that Ping fails but TCP port probes succeed, it accurately reports that the internet is working normally and that ICMP is merely being filtered by security policies.

---

### Q3: What is a Default Gateway, and what does it mean if it fails to respond?
**Answer:**  
The Default Gateway is the local router interface that connects your local network (LAN) to outside networks (the Internet).  
If the default gateway is unreachable:
- Your computer cannot communicate with any device outside its immediate local subnet.
- Likely causes include: disconnected Wi-Fi/Ethernet cable, router rebooting, or an incorrect static gateway IP assigned to your machine.

---

### Q4: What is an APIPA address (169.254.x.x), and why does it appear?
**Answer:**  
APIPA stands for *Automatic Private IP Addressing*. When a computer is configured for DHCP (Automatic IP) but cannot reach a DHCP server or receive a lease offer within the timeout window, Windows self-assigns an address in the range `169.254.0.1` to `169.254.255.254`.  
NetDoctor detects APIPA addresses and immediately flags that the DHCP server or local router DHCP pool is unreachable.

---

### Q5: How does DNS work, and what symptom indicates a DNS failure in NetDoctor?
**Answer:**  
DNS (Domain Name System) translates human-readable domain names (like `google.com`) into numerical IP addresses (like `142.250.190.46`).  
In NetDoctor, a DNS failure is diagnosed when domain name resolution fails, but direct IP communication (such as pinging `8.8.8.8` or TCP handshake to `1.1.1.1:53`) still succeeds. This proves the physical and routing layers are healthy, but the DNS resolver is offline or misconfigured.

---

### Q6: What is a VLAN, and what advantages does it provide in the campus topology?
**Answer:**  
A VLAN (Virtual Local Area Network) logically segments a single physical switch into multiple isolated broadcast domains.  
In our campus topology:
- **VLAN 10** is reserved for Students.
- **VLAN 20** is reserved for Faculty.
- **VLAN 30** is reserved for Campus Servers.  
This enhances security (preventing students from snooping faculty traffic) and reduces broadcast domain congestion.

---

### Q7: What is an 802.1Q trunk port, and how does it differ from an access port?
**Answer:**  
- An **Access Port** belongs to a single VLAN and transmits untagged Ethernet frames to end devices like PCs or printers.
- A **Trunk Port** connects switches together or connects a switch to a router. It uses the IEEE 802.1Q protocol to insert a 4-byte VLAN tag into the Ethernet header, allowing traffic from multiple VLANs to travel across a single physical cable.

---

### Q8: What is "Router-on-a-Stick", and how was it configured on R1-Campus?
**Answer:**  
Router-on-a-Stick is an inter-VLAN routing technique where a single physical router interface (GigabitEthernet0/0/0) is divided into virtual subinterfaces (e.g., `Gi0/0/0.10`, `Gi0/0/0.20`, `Gi0/0/0.30`).  
Each subinterface is assigned an 802.1Q VLAN encapsulation tag and acts as the default gateway for that specific VLAN.

---

### Q9: Why did you choose submitted CLI analysis for Packet Tracer rather than claiming automated real-time sockets?
**Answer:**  
Because Cisco Packet Tracer is an educational simulation sandbox that does not provide a general-purpose, supported bi-directional REST or socket API for external Python scripts without fragile proprietary plugins.  
Rather than fabricating fake results or using brittle screen scrapers, NetDoctor implements a genuine evidence-based CLI parser. We copy real terminal outputs from Packet Tracer, parse the exact Cisco tables, diagnose faults, and verify recovery. This reflects how real network engineers paste diagnostic outputs into analysis tools.

---

### Q10: How does NetDoctor verify recovery?
**Answer:**  
NetDoctor stores timestamped snapshots. When a user applies a fix in Packet Tracer (or on their Windows machine) and re-runs the test, NetDoctor executes a **diff analysis** comparing the before and after state. If a previously failing test (such as 0% ping success or an administratively down port) transitions to PASS, NetDoctor logs a formal **Recovery Event** proving restoration of service.
