# Cisco Packet Tracer Campus Network Lab Guide

This guide provides step-by-step instructions for building, configuring, and verifying the **NetDoctor Campus Network** in **Cisco Packet Tracer 9.0.1**.

---

## 1. Network Topology Diagram

```
[ PC-Student-1 ] (10.10.10.11) ----\
                                    [ SW-Students ] (VLAN 10) ---\
[ PC-Student-2 ] (10.10.10.12) ----/                              \
                                                                    \  (Trunk Fa0/1-2)
                                                                     [ SW-Core ] ===== (Trunk Gi0/0/0) ===== [ R1-Campus ]
                                                                    /                                             |
[ PC-Faculty-1 ] (10.10.20.11) ----\                              /                                        (WAN: 10.10.99.0/30)
                                    [ SW-Faculty ]  (VLAN 20) ---/                                         (Gi0/0/2 <-> Gi0/0/2)
[ PC-Faculty-2 ] (10.10.20.12) ----/                                                                             |
                                                                                                                  |
[ DNS-Server ] (10.10.30.2) -------\                                                                        [ R2-Branch ]
                                    [ SW-Core ] (VLAN 30)                                                         | (Gi0/0/1)
[ Web-Server ] (10.10.30.3) -------/                                                                              |
                                                                                                            [ SW-Branch ]
                                                                                                                  |
                                                                                                            [ PC-Branch-1 ] (10.20.10.11)
```

---

## 2. Device Inventory

Select these standard devices from the bottom-left palette in Cisco Packet Tracer:

| Device Name | Device Model in Packet Tracer | Role / Purpose |
| :--- | :--- | :--- |
| **R1-Campus** | Router `2911` or `4331` | Main Campus Router & Inter-VLAN Gateway |
| **R2-Branch** | Router `2911` or `4331` | Remote Branch Office Gateway |
| **SW-Core** | Switch `2960` | Central Distribution / Server Farm Switch |
| **SW-Students** | Switch `2960` | Access Switch for Student Department |
| **SW-Faculty** | Switch `2960` | Access Switch for Faculty Department |
| **SW-Branch** | Switch `2960` | Access Switch for Branch Users |
| **PC-Student-1** | PC-PT | Student Lab Workstation 1 |
| **PC-Student-2** | PC-PT | Student Lab Workstation 2 |
| **PC-Faculty-1** | PC-PT | Faculty Office Workstation 1 |
| **PC-Faculty-2** | PC-PT | Faculty Office Workstation 2 |
| **PC-Branch-1** | PC-PT | Remote Branch User Workstation |
| **DNS-Server** | Server-PT | Campus DNS Resolver (`www.campus.local`) |
| **Web-Server** | Server-PT | Campus Intranet Web Portal |

---

## 3. Physical Cabling & Port Connections

Use **Copper Straight-Through Cables** (solid black line icon) for all connections:

| From Device | Port | To Device | Port | Connection Type |
| :--- | :--- | :--- | :--- | :--- |
| **R1-Campus** | GigabitEthernet0/0/0 | **SW-Core** | GigabitEthernet0/1 | 802.1Q Trunk (Router-on-a-Stick) |
| **R1-Campus** | GigabitEthernet0/0/2 | **R2-Branch** | GigabitEthernet0/0/2 | WAN Routed Link (`10.10.99.0/30`) |
| **SW-Core** | FastEthernet0/1 | **SW-Students** | FastEthernet0/24 | 802.1Q Trunk |
| **SW-Core** | FastEthernet0/2 | **SW-Faculty** | FastEthernet0/24 | 802.1Q Trunk |
| **SW-Core** | FastEthernet0/10 | **DNS-Server** | FastEthernet0 | Access Port (VLAN 30) |
| **SW-Core** | FastEthernet0/11 | **Web-Server** | FastEthernet0 | Access Port (VLAN 30) |
| **SW-Students** | FastEthernet0/1 | **PC-Student-1** | FastEthernet0 | Access Port (VLAN 10) |
| **SW-Students** | FastEthernet0/2 | **PC-Student-2** | FastEthernet0 | Access Port (VLAN 10) |
| **SW-Faculty** | FastEthernet0/1 | **PC-Faculty-1** | FastEthernet0 | Access Port (VLAN 20) |
| **SW-Faculty** | FastEthernet0/2 | **PC-Faculty-2** | FastEthernet0 | Access Port (VLAN 20) |
| **R2-Branch** | GigabitEthernet0/0/1 | **SW-Branch** | GigabitEthernet0/1 | LAN Default Gateway |
| **SW-Branch** | FastEthernet0/1 | **PC-Branch-1** | FastEthernet0 | Access Port (VLAN 1) |

---

## 4. IP Addressing Scheme & Subnet Plan

We use non-overlapping Class A/C private subnets:

| Subnet Network | Subnet Mask | Description | Default Gateway IP | Usable Host Range |
| :--- | :--- | :--- | :--- | :--- |
| **10.10.10.0/24** | `255.255.255.0` | VLAN 10 (Students) | `10.10.10.1` | `10.10.10.2` – `10.10.10.254` |
| **10.10.20.0/24** | `255.255.255.0` | VLAN 20 (Faculty) | `10.10.20.1` | `10.10.20.2` – `10.10.20.254` |
| **10.10.30.0/24** | `255.255.255.0` | VLAN 30 (Servers) | `10.10.30.1` | `10.10.30.2` – `10.10.30.254` |
| **10.10.99.0/30** | `255.255.255.252` | WAN Link (R1 <-> R2) | N/A | `10.10.99.1` (R1), `10.10.99.2` (R2) |
| **10.20.10.0/24** | `255.255.255.0` | Branch Office LAN | `10.20.10.1` | `10.20.10.2` – `10.20.10.254` |

---

## 5. Ready-To-Paste Cisco CLI Configurations

To apply these configurations:
1. Click on the device in Packet Tracer.
2. Click the **CLI** tab.
3. Press **Enter**, then paste the code block below.

### 5.1 Main Campus Router (`R1-Campus`)
```cisco
enable
configure terminal
hostname R1-Campus

! Enable physical trunk port
interface GigabitEthernet0/0/0
 no shutdown
exit

! Router-on-a-Stick Subinterfaces
interface GigabitEthernet0/0/0.10
 encapsulation dot1Q 10
 ip address 10.10.10.1 255.255.255.0
exit

interface GigabitEthernet0/0/0.20
 encapsulation dot1Q 20
 ip address 10.10.20.1 255.255.255.0
exit

interface GigabitEthernet0/0/0.30
 encapsulation dot1Q 30
 ip address 10.10.30.1 255.255.255.0
exit

! WAN Link to Branch Router
interface GigabitEthernet0/0/2
 ip address 10.10.99.1 255.255.255.252
 no shutdown
exit

! Static Route to Branch LAN
ip route 10.20.10.0 255.255.255.0 10.10.99.2

end
write memory
```

### 5.2 Branch Router (`R2-Branch`)
```cisco
enable
configure terminal
hostname R2-Branch

! WAN Link to Main Campus
interface GigabitEthernet0/0/2
 ip address 10.10.99.2 255.255.255.252
 no shutdown
exit

! Local Branch Gateway
interface GigabitEthernet0/0/1
 ip address 10.20.10.1 255.255.255.0
 no shutdown
exit

! Static Route to Main Campus Subnets
ip route 10.10.0.0 255.255.0.0 10.10.99.1

end
write memory
```

### 5.3 Campus Core Switch (`SW-Core`)
```cisco
enable
configure terminal
hostname SW-Core

! Create VLANs
vlan 10
 name Students
vlan 20
 name Faculty
vlan 30
 name Servers
exit

! Trunk to R1-Campus
interface GigabitEthernet0/1
 switchport mode trunk
 no shutdown
exit

! Trunks to Access Switches
interface FastEthernet0/1
 switchport mode trunk
 no shutdown
exit

interface FastEthernet0/2
 switchport mode trunk
 no shutdown
exit

! Server Access Ports
interface FastEthernet0/10
 switchport mode access
 switchport access vlan 30
 no shutdown
exit

interface FastEthernet0/11
 switchport mode access
 switchport access vlan 30
 no shutdown
exit

end
write memory
```

### 5.4 Student Access Switch (`SW-Students`)
```cisco
enable
configure terminal
hostname SW-Students

vlan 10
 name Students
exit

! Trunk uplink to SW-Core
interface FastEthernet0/24
 switchport mode trunk
 no shutdown
exit

! Student Access Ports
interface range FastEthernet0/1 - 2
 switchport mode access
 switchport access vlan 10
 no shutdown
exit

end
write memory
```

### 5.5 Faculty Access Switch (`SW-Faculty`)
```cisco
enable
configure terminal
hostname SW-Faculty

vlan 20
 name Faculty
exit

! Trunk uplink to SW-Core
interface FastEthernet0/24
 switchport mode trunk
 no shutdown
exit

! Faculty Access Ports
interface range FastEthernet0/1 - 2
 switchport mode access
 switchport access vlan 20
 no shutdown
exit

end
write memory
```

---

## 6. End-Device Configuration (PCs & Servers)

Click each device in Packet Tracer, go to the **Desktop** tab, and click **IP Configuration**:

| Device | IP Address | Subnet Mask | Default Gateway | DNS Server |
| :--- | :--- | :--- | :--- | :--- |
| **PC-Student-1** | `10.10.10.11` | `255.255.255.0` | `10.10.10.1` | `10.10.30.2` |
| **PC-Student-2** | `10.10.10.12` | `255.255.255.0` | `10.10.10.1` | `10.10.30.2` |
| **PC-Faculty-1** | `10.10.20.11` | `255.255.255.0` | `10.10.20.1` | `10.10.30.2` |
| **PC-Faculty-2** | `10.10.20.12` | `255.255.255.0` | `10.10.20.1` | `10.10.30.2` |
| **PC-Branch-1** | `10.20.10.11` | `255.255.255.0` | `10.20.10.1` | `10.10.30.2` |
| **DNS-Server** | `10.10.30.2` | `255.255.255.0` | `10.10.30.1` | `127.0.0.1` |
| **Web-Server** | `10.10.30.3` | `255.255.255.0` | `10.10.30.1` | `10.10.30.2` |

### Server Services Setup:
1. **DNS-Server:**  
   Click `DNS-Server` -> **Services** tab -> **DNS** -> Turn Service **ON**.  
   - Name: `www.campus.local`  
   - Type: `A Record`  
   - Address: `10.10.30.3`  
   - Click **Add**.
2. **Web-Server:**  
   Click `Web-Server` -> **Services** tab -> **HTTP** -> Ensure HTTP & HTTPS are **ON**. (You can edit `index.html` to say `"Welcome to NetDoctor Campus Portal"`).

---

## 7. Baseline Verification (Proving Everything Works)

On `PC-Student-1`, open **Command Prompt** (in Desktop tab) and test:
```shell
ping 10.10.10.1          # Test local gateway (VLAN 10) -> Should reply!
ping 10.10.20.11         # Test cross-VLAN to Faculty PC -> Should reply!
ping 10.10.30.3          # Test reachability to Web Server -> Should reply!
ping 10.20.10.11         # Test reachability across WAN to Branch PC -> Should reply!
```
Open **Web Browser** on `PC-Student-1`, type `www.campus.local` -> Web page loads!

---

## 8. The 3 Controlled Fault Demonstrations

### Fault 1: Incorrect Default Gateway on PC
1. **Introduce Fault:**  
   On `PC-Student-1`, change Default Gateway from `10.10.10.1` to `10.10.10.99`.
2. **Demonstrate Failure:**  
   Ping `10.10.30.3` (Web Server). Result: `Request timed out (100% loss)`.
3. **Submit to NetDoctor:**  
   Copy the ping output, open NetDoctor's **Packet Tracer Lab Mode**, paste it, and run analysis. NetDoctor diagnoses gateway mismatch.
4. **Fix the Fault:**  
   Change Default Gateway on `PC-Student-1` back to `10.10.10.1`.
5. **Verify Recovery:**  
   Ping `10.10.30.3` again -> `Reply received (0% loss)`. Compare Before & After in NetDoctor!

### Fault 2: Switchport Assigned to Incorrect VLAN
1. **Introduce Fault:**  
   On `SW-Students`, assign port `FastEthernet0/1` to wrong VLAN 20:
   ```cisco
   enable
   configure terminal
   interface FastEthernet0/1
    switchport access vlan 20
   end
   ```
2. **Demonstrate Failure:**  
   `PC-Student-1` (IP `10.10.10.11`) can no longer ping its gateway `10.10.10.1` because it is isolated in VLAN 20.
3. **Submit to NetDoctor:**  
   Run `show vlan brief` on `SW-Students`, copy output into NetDoctor Lab Mode. NetDoctor detects that Fa0/1 is in VLAN 20 instead of 10.
4. **Fix the Fault:**  
   ```cisco
   configure terminal
   interface FastEthernet0/1
    switchport access vlan 10
   end
   ```
5. **Verify Recovery:**  
   Ping `10.10.10.1` -> Success!

### Fault 3: Missing Static Route on Campus Router
1. **Introduce Fault:**  
   On `R1-Campus`, remove the static route to the branch network:
   ```cisco
   enable
   configure terminal
   no ip route 10.20.10.0 255.255.255.0 10.10.99.2
   end
   ```
2. **Demonstrate Failure:**  
   From `PC-Branch-1`, try to ping Web Server `10.10.30.3`. Router responds with `Destination host unreachable`.
3. **Submit to NetDoctor:**  
   Run `show ip route` on `R1-Campus`, paste output into NetDoctor Lab Mode. NetDoctor detects that route `10.20.10.0/24` is missing from the routing table.
4. **Fix the Fault:**  
   ```cisco
   configure terminal
   ip route 10.20.10.0 255.255.255.0 10.10.99.2
   end
   ```
5. **Verify Recovery:**  
   Ping `10.10.30.3` from `PC-Branch-1` -> Success (5/5 replies)!
