# Wireshark Network Packet Capture Guide for NetDoctor

This guide shows you step-by-step how to capture and inspect genuine network traffic from your physical Windows computer using **Wireshark**.

---

## 1. Opening Wireshark & Selecting Your Interface

1. Press the **Windows Key**, type `Wireshark`, and press **Enter** (or open `C:\Program Files\Wireshark\Wireshark.exe`).
2. On the Wireshark welcome screen, you will see a list of network interfaces (e.g., `Wi-Fi`, `Ethernet`, `Local Area Connection`).
3. Look for the interface with a **fluctuating activity line** (this indicates active network traffic). On most laptops, this will be **Wi-Fi**.
4. **Double-click your active interface** (e.g., `Wi-Fi`) to begin capturing packets immediately.

---

## 2. Capture Scenario 1: ICMP Ping (Echo Request & Reply)

### Step 1: Apply Display Filter
In the green filter bar at the top of Wireshark, type:
```text
icmp
```
and press **Enter**. (The packet list will appear blank until you send a ping).

### Step 2: Generate Traffic
Open **Command Prompt** on Windows or use NetDoctor's **Manual Diagnostics** tab, and run:
```shell
ping 8.8.8.8 -n 2
```

### Step 3: Inspect the Packets
Look at the Wireshark packet list:
- **Packet 1 (Echo Request):**  
  - Source: Your PC IP (e.g. `192.168.0.103`)  
  - Destination: `8.8.8.8`  
  - Protocol: `ICMP`  
  - Info: `Echo (ping) request  id=0x... seq=1/256, ttl=128`
- **Packet 2 (Echo Reply):**  
  - Source: `8.8.8.8`  
  - Destination: Your PC IP  
  - Protocol: `ICMP`  
  - Info: `Echo (ping) reply    id=0x... seq=1/256, ttl=118`

> **What this demonstrates:** Proof of bidirectional Layer 3 ICMP reachability and round-trip time between your computer and Google Public DNS.

---

## 3. Capture Scenario 2: DNS Query and Response

### Step 1: Apply Display Filter
In the Wireshark filter bar, type:
```text
dns
```
and press **Enter**.

### Step 2: Generate Traffic
In Windows Command Prompt or NetDoctor's **Manual Diagnostics** tab, resolve a domain:
```shell
nslookup cloudflare.com
```

### Step 3: Inspect the Packets
- **Query Packet:**  
  - Source: Your PC IP  
  - Destination: Your configured DNS server or router IP (`192.168.0.1` or `1.1.1.1`)  
  - Info: `Standard query 0x... A cloudflare.com`
- **Response Packet:**  
  - Source: DNS Server IP  
  - Destination: Your PC IP  
  - Info: `Standard query response 0x... A 104.16.132.229 A 104.16.133.229`

> **What this demonstrates:** Shows how Layer 7 Application names are translated to Layer 3 IP addresses via UDP port 53.

---

## 4. Capture Scenario 3: TCP 3-Way Handshake (Port 80/443)

### Step 1: Apply Display Filter
In the Wireshark filter bar, type:
```text
tcp.port == 80 || tcp.port == 443
```
and press **Enter**.

### Step 2: Generate Traffic
In NetDoctor's **Manual Diagnostics** tab, probe `1.1.1.1` on Port `443` (HTTPS), or open a web browser to any website.

### Step 3: Inspect the Handshake Sequence
Look for three consecutive packets between your PC and the remote web server:
1. `[SYN]` — Your PC initiates connection with an initial sequence number.
2. `[SYN, ACK]` — Remote server acknowledges and synchronizes its own sequence number.
3. `[ACK]` — Your PC confirms. The reliable TCP connection is established!

> **What this demonstrates:** Reliable connection-oriented transport protocol operation at Layer 4, proving transport reachability even if ICMP ping is filtered.

---

## 5. Saving Your Evidence (.PCAPNG & Screenshots)

1. **Stop the Capture:** Click the red square icon (Stop) in the top-left corner of Wireshark.
2. **Save Capture File:** Click `File` -> `Save As...`, navigate to your project folder:  
   `C:\Users\annap\.gemini\antigravity\scratch\NetDoctor\captures\`  
   Save as `genuine_traffic_evidence.pcapng`.
3. **Capture Screenshots:** Use `Windows Key + Shift + S` to screenshot the filtered Wireshark window showing the packet details panel for your project report.
