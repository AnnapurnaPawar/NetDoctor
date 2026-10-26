# NetDoctor: 3–5 Minute Demonstration Video Script

This script provides an exact, step-by-step presentation structure for recording your project video or demonstrating live to an evaluator.

---

### [0:00 – 0:45] Introduction & Motivation
**On Screen:** NetDoctor Web Dashboard (Overview Tab) with title clearly visible.  
**Speaker:**  
> "Hello everyone. Today I am presenting **NetDoctor**, a real-time network health monitoring, fault diagnosis, and recovery verification system.  
> Standard networking utilities often say that a network is 'down' without explaining the root cause. NetDoctor bridges this gap by combining real-time multi-layer monitoring of my physical computer with an evidence-based diagnostic engine and a Cisco Packet Tracer Campus Network Lab."

---

### [0:45 – 1:45] Real-Time Windows Monitoring Demonstration
**On Screen:** Switch to **Live Monitoring** tab. Click **"Check Now"** or enable **"Start Auto"**.  
**Speaker:**  
> "Here on the Live Monitoring page, NetDoctor continuously probes multiple layers of my real Windows machine:
> 1. At Layer 3, it verifies my active network card and default gateway reachability with actual round-trip latency and packet loss.
> 2. At Layer 7, it tests DNS resolution against multiple global domains.
> 3. At Layer 4, it performs real TCP handshakes to ports 53, 80, and 443.
> Notice that if ping is blocked by a firewall, NetDoctor does not panic. Its diagnostic engine recognizes that TCP web traffic is functioning and avoids false alarms."

---

### [1:45 – 2:45] Cisco Packet Tracer Campus Network Tour
**On Screen:** Switch window to **Cisco Packet Tracer 9.0.1** showing the 13-device campus network topology.  
**Speaker:**  
> "Next, let's look at our simulated campus environment. This network connects 13 devices:
> - Two Cisco routers: R1 for the main campus and R2 for the remote branch, linked via a routed WAN subnet.
> - A central Core switch and dedicated access switches for Students (VLAN 10) and Faculty (VLAN 20).
> - Dedicated DNS and Web servers in VLAN 30.
> - We implemented 'Router-on-a-Stick' for secure inter-VLAN routing and static routing between sites."

---

### [2:45 – 4:00] Controlled Fault Injection & Recovery Verification
**On Screen:** Split screen: Packet Tracer CLI on the left, NetDoctor **Packet Tracer Lab Mode** on the right.  
**Speaker:**  
> "Now let's demonstrate NetDoctor's diagnostic and recovery engine with a controlled fault.
> 1. In Packet Tracer, on R1-Campus, I shut down the student gateway subinterface: `interface GigabitEthernet0/0/0.10` -> `shutdown`.
> 2. On PC-Student-1, pings to the campus Web Server now fail with 100% packet loss.
> 3. I run `show ip interface brief` on R1, copy the output, and paste it directly into NetDoctor Lab Mode.
> 4. NetDoctor parses the table and immediately flags: 'Interface is administratively shutdown' with high confidence, providing the exact Cisco command: `no shutdown`.
> 5. I apply the fix in Packet Tracer, re-run the ping, and paste the recovery output into NetDoctor.
> 6. As you can see, NetDoctor compares Before and After and confirms: 'Recovery Verified: All services restored!'"

---

### [4:00 – 4:45] Wireshark Evidence & Test History
**On Screen:** Switch to **History & Export** tab in NetDoctor, then briefly show Wireshark with the `icmp` filter.  
**Speaker:**  
> "All measurements and recovery transitions are recorded in NetDoctor's persistent history, which can be downloaded as a CSV report for audit logs.  
> Furthermore, we used Wireshark on our Windows computer to inspect genuine ICMP echo packets, DNS queries, and TCP three-way handshakes, validating that our real-world diagnostic engine generates authentic traffic."

---

### [4:45 – 5:00] Conclusion
**On Screen:** Return to NetDoctor Overview screen showing green **HEALTHY (PASS)** badge.  
**Speaker:**  
> "In summary, NetDoctor delivers a reliable, evidence-based diagnostic platform for both real-world Windows systems and simulated Cisco campus networks. Thank you!"
