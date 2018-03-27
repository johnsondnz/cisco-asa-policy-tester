# Cisco ASA Policy Tester

## Description
This python3 tool will log into a Cisco ASA and perform a series of packet-tracer commands to test a security policy.

The tool will create a report in `reports/html_report.html` which is overwritten with each run.

At this time the tool requires a privilege-level 15 user.  It is untested with lower levels or passing into enable mode.

## Requirements
- netmiko
- scp>=0.10.0
- pyyaml
- pyserial
- textfsm
- logzero
- getpass3
- jinja2

## New to Version 0.5
- Added support for mutli-destination IP per test, see YAML examples below.

## New to Version 0.4
- Major Code cleanup for easier management.

## New to Version 0.3
- Added ability to use named hosts for source and destination IP.
- Support for hostfile (custom) and DNS resolution.
- Error reporting for skipped items where names could not resolve to IP.

## New to Version 0.2
- Added NAT detection and report output.
- Fixed issue with ICMP type and code not appearing in report.

## ToDo
- Implement a retest.yml file from a test to allow for easy rerun on failed items without the need to retest all items.
- Test and implement enable password.
- Implement expected NAT resolution.

## Usage
- `python3 tester.py -i <IP> -u <USERNAME> -p -y <yml_definition> -hf <path/to/hostfile>`
- `python3 tester.py -i 192.168.1.1 -u admin -p -y firewall_test.yml -hf /tmp/hosts`

The tool uses getpass3 to securely obtain the users passwords.

## YAML Structure
Store in `tests/` folder.

### Mutli Destination IP
```
---
INSIDE: # One dictionary per interface
  allow: # rules you expect to be allowed by the firewall
    - {
        protocol: tcp, 
        icmp_type: , icmp_code: ,
        source_ip: 192.168.1.1, source_port: 12345, 
        destination_ip: [host1, host2, host3], destination_port: 1443
    }
```

### Allow and Drop
```
---
INSIDE: # One dictionary per interface
  allow: # rules you expect to be allowed by the firewall
   - {
        protocol: tcp, 
        icmp_type: , icmp_code: ,
        source_ip: 192.168.1.1, source_port: 12345, 
        destination_ip: [host1, host2, host3], destination_port: 1443
    }
    - {
        protocol: tcp, 
        icmp_type: , icmp_code: ,
        source_ip: 192.168.1.1, source_port: 12345, 
        destination_ip: 192.168.1.2, destination_port: 1443
    }
    - {
        protocol: tcp, 
        icmp_type: , icmp_code: ,
        source_ip: 192.168.1.1, source_port: 12345, 
        destination_ip: 192.168.1.2, destination_port: 137
    }
    - {
        protocol: icmp, 
        icmp_type: 8,
        icmp_code: 0,
        source_ip: 192.168.1.1,
        source_port: , 
        destination_ip: 192.168.1.2, 
        destination_port: 
    }
    - {
        protocol: tcp, 
        icmp_type: ,
        icmp_code: ,
        source_ip: 192.168.1.1,
        source_port: 12345, 
        destination_ip: 192.168.1.1, 
        destination_port: 14452
    }

  drop: # rules you expect to be blocked by the firewall
    - {
        protocol: udp, 
        icmp_type: ,
        icmp_code: ,
        source_ip: 192.168.1.1,
        source_port: 12345, 
        destination_ip: 192.168.1.2, 
        destination_port: 14143
    }
    - {
        protocol: tcp, 
        icmp_type: ,
        icmp_code: ,
        source_ip: 192.168.1.1,
        source_port: 12345, 
        destination_ip: 192.168.1.2, 
        destination_port: 15632
    }

OUTSIDE: # One dictionary per interface
  allow: # rules you expect to be allowed by the firewall
    - {
        protocol: udp, 
        icmp_type: ,
        icmp_code: ,
        source_ip: 192.168.1.1,
        source_port: 12345, 
        destination_ip: 192.168.1.2, 
        destination_port: 53
    }
    - {
        protocol: tcp, 
        icmp_type: ,
        icmp_code: ,
        source_ip: 192.168.1.1,
        source_port: 12345, 
        destination_ip: 192.168.1.2, 
        destination_port: 53
    }

  drop: # rules you expect to be blocked by the firewall
   - {
        protocol: tcp, 
        icmp_type: , icmp_code: ,
        source_ip: 192.168.1.1, source_port: 12345, 
        destination_ip: [host1, host2, host3], destination_port: 1443
    }
    - {
        protocol: tcp, 
        icmp_type: ,
        icmp_code: ,
        source_ip: 192.168.1.1,
        source_port: 12345, 
        destination_ip: 192.168.1.2, 
        destination_port: 53
    }
    - {
        protocol: tcp, 
        icmp_type: ,
        icmp_code: ,
        source_ip: 192.168.1.1,
        source_port: 12345, 
        destination_ip: 192.168.1.2, 
        destination_port: 8080
    }
    
```

## Hostfile format
Currently cause I'm lazy and didn't recode a preprepared file.
I'll get around to remove the first item 'name' at some point and flip the IP and hostname to be more like a true hostfile
```
name 192.168.1.1 device1
name 192.168.1.2 device2
```

## Running the tool
### Full Run-through
```
 clear; ./tester.py -i 192.168.1.1 -u admin -y test.yml -p -hf /tmp/names
Password:
[I 180327 18:15:14 tester:54] Hostfile "/tmp/names" found and loaded
[I 180327 18:15:14 tester:67] ! ---------- CONSTRUCTING TESTS ---------- !

[D 180327 18:15:14 testcontrol:22] Context data loaded
[D 180327 18:15:14 testcontrol:40] Dictionary for "INSIDE" created.
[I 180327 18:15:14 testcontrol:180] Constructing "INSIDE", "allow" tests
[I 180327 18:15:14 testcontrol:186] Processing tcp protocol policy
[D 180327 18:15:14 testcontrol:61] List detect in destination_ip
[I 180327 18:15:14 resolve:89] Source IP "10.1.1.1" is a valid IP, further resolution not required

[E 180327 18:15:14 resolve:94] Source IP "host1" is not a valid IP, further resolution required
[I 180327 18:15:14 resolve:116] Looking up "host1" in hostfile
[E 180327 18:15:14 resolve:44] Object: host1, IP: not found
[I 180327 18:15:14 resolve:124] Attemping to resolve "host1" via DNS
[I 180327 18:15:14 resolve:62] DNS resovled object "host1" to "192.168.1.1"
[I 180327 18:15:14 resolve:89] Source IP "192.168.1.1" is a valid IP, further resolution not required

[E 180327 18:15:14 resolve:94] Source IP "host2" is not a valid IP, further resolution required
[I 180327 18:15:14 resolve:116] Looking up "host2" in hostfile
[I 180327 18:15:14 resolve:35] Found: name 192.168.1.2 host2, on line 143
[I 180327 18:15:14 resolve:41] Object: host2, IP: 192.168.1.2
[I 180327 18:15:14 resolve:89] Source IP "192.168.1.2" is a valid IP, further resolution not required

[E 180327 18:15:14 resolve:94] Source IP "host3" is not a valid IP, further resolution required
[I 180327 18:15:14 resolve:116] Looking up "host3" in hostfile
[I 180327 18:15:14 resolve:35] Found: name 192.168.1.3 host3, on line 136
[I 180327 18:15:14 resolve:41] Object: host3, IP: 192.168.1.3
[I 180327 18:15:14 resolve:89] Source IP "192.168.1.3" is a valid IP, further resolution not required

[E 180327 18:15:14 resolve:94] Source IP "host4" is not a valid IP, further resolution required
[I 180327 18:15:14 resolve:116] Looking up "host4" in hostfile
[I 180327 18:15:14 resolve:35] Found: name 192.168.1.4 host4, on line 150
[I 180327 18:15:14 resolve:41] Object: host4, IP: 192.168.1.4
[I 180327 18:15:14 resolve:89] Source IP "192.168.1.4" is a valid IP, further resolution not required
[I 180327 18:15:14 testcontrol:186] Processing tcp protocol policy
[I 180327 18:15:14 resolve:89] Source IP "10.1.1.1" is a valid IP, further resolution not required

[E 180327 18:15:14 resolve:94] Source IP "host5" is not a valid IP, further resolution required
[I 180327 18:15:14 resolve:116] Looking up "host5" in hostfile
[I 180327 18:15:14 resolve:35] Found: name 192.168.1.5 host5, on line 93
[I 180327 18:15:14 resolve:41] Object: host5, IP: 192.168.1.5
[I 180327 18:15:14 resolve:89] Source IP "192.168.1.5" is a valid IP, further resolution not required


[I 180327 18:15:14 tester:73] ! ----------   EXECUTING TESTS  ---------- !

[I 180327 18:15:14 tester:74] Attempting connection to 192.168.1.1
[I 180327 18:15:19 testcontrol:323] Excuting interface INSIDE test record, "0"
[I 180327 18:15:19 testcontrol:324] Command: packet-tracer input INSIDE tcp 10.1.1.1 12345 192.168.1.1 3389 detail
[I 180327 18:15:20 testcontrol:332] Expecting: allow
[I 180327 18:15:20 testcontrol:334] ASA reports: drop
[I 180327 18:15:20 testcontrol:346] Drop reason: (no-route) No route to host
[E 180327 18:15:20 testcontrol:353] Test failed!

[I 180327 18:15:20 testcontrol:323] Excuting interface INSIDE test record, "0"
[I 180327 18:15:20 testcontrol:324] Command: packet-tracer input INSIDE tcp 10.1.1.1 12345 192.168.1.2 3389 detail
[I 180327 18:15:20 testcontrol:332] Expecting: allow
[I 180327 18:15:20 testcontrol:334] ASA reports: allow
[I 180327 18:15:20 testcontrol:350] Test passed!

[I 180327 18:15:20 testcontrol:323] Excuting interface INSIDE test record, "0"
[I 180327 18:15:20 testcontrol:324] Command: packet-tracer input INSIDE tcp 10.1.1.1 12345 192.168.1.3 3389 detail
[I 180327 18:15:21 testcontrol:332] Expecting: allow
[I 180327 18:15:21 testcontrol:334] ASA reports: allow
[I 180327 18:15:21 testcontrol:350] Test passed!

[I 180327 18:15:21 testcontrol:323] Excuting interface INSIDE test record, "0"
[I 180327 18:15:21 testcontrol:324] Command: packet-tracer input INSIDE tcp 10.1.1.1 12345 192.168.1.4 3389 detail
[I 180327 18:15:22 testcontrol:332] Expecting: allow
[I 180327 18:15:22 testcontrol:334] ASA reports: allow
[I 180327 18:15:22 testcontrol:350] Test passed!

[I 180327 18:15:22 testcontrol:323] Excuting interface INSIDE test record, "1"
[I 180327 18:15:22 testcontrol:324] Command: packet-tracer input INSIDE tcp 10.1.1.1 12345 192.168.1.5 80 detail
[I 180327 18:15:22 testcontrol:332] Expecting: allow
[I 180327 18:15:22 testcontrol:334] ASA reports: allow
[I 180327 18:15:22 testcontrol:350] Test passed!

[D 180327 18:15:22 report:19] HTML report output to "/Coding/GitHub/cisco-asa-policy-tester/reports/html_report.html"
```

### Example of Failed IP resolution
```
$ clear; ./tester.py -i 192.168.1.1 -u admin -y test.yml -p -hf /tmp/names
Password:
[I 180327 18:26:52 tester:54] Hostfile "/tmp/names" found and loaded
[I 180327 18:26:52 tester:66] ! ---------- CONSTRUCTING TESTS ---------- !

[D 180327 18:26:52 testcontrol:22] Context data loaded
[D 180327 18:26:52 testcontrol:40] Dictionary for "INSIDE" created.
[I 180327 18:26:52 testcontrol:180] Constructing "INSIDE", "allow" tests
[I 180327 18:26:52 testcontrol:186] Processing tcp protocol policy
[D 180327 18:26:52 testcontrol:61] List detect in destination_ip
[I 180327 18:26:52 resolve:89] Source IP "10.1.1.1" is a valid IP, further resolution not required

[E 180327 18:26:52 resolve:94] Source IP "host1" is not a valid IP, further resolution required
[I 180327 18:26:52 resolve:116] Looking up "host1" in hostfile
[E 180327 18:26:52 resolve:44] Object: host1, IP: not found
[I 180327 18:26:52 resolve:124] Attemping to resolve "host1" via DNS
[I 180327 18:26:53 resolve:66] DNS resolution failed for object "host1"
[E 180327 18:26:53 resolve:97] Unable to resolve "host1" to an IP Address
```

### Example of hostfile resolution with DNS fallback
```
 clear; ./tester.py -i 192.168.1.1 -u admin -y test.yml -p -hf /tmp/names
Password:
[I 180327 18:15:14 tester:54] Hostfile "/tmp/names" found and loaded
[I 180327 18:15:14 tester:67] ! ---------- CONSTRUCTING TESTS ---------- !

[D 180327 18:15:14 testcontrol:22] Context data loaded
[D 180327 18:15:14 testcontrol:40] Dictionary for "INSIDE" created.
[I 180327 18:15:14 testcontrol:180] Constructing "INSIDE", "allow" tests
[I 180327 18:15:14 testcontrol:186] Processing tcp protocol policy
[D 180327 18:15:14 testcontrol:61] List detect in destination_ip
[I 180327 18:15:14 resolve:89] Source IP "10.1.1.1" is a valid IP, further resolution not required

[E 180327 18:15:14 resolve:94] Source IP "host1" is not a valid IP, further resolution required
[I 180327 18:15:14 resolve:116] Looking up "host1" in hostfile
[E 180327 18:15:14 resolve:44] Object: host1, IP: not found
[I 180327 18:15:14 resolve:124] Attemping to resolve "host1" via DNS
[I 180327 18:15:14 resolve:62] DNS resovled object "host1" to "192.168.1.1"
[I 180327 18:15:14 resolve:89] Source IP "192.168.1.1" is a valid IP, further resolution not required
```

## Report Output
### Fail and Pass Tests
![alt text](https://i.imgur.com/WAByh3g.png "Report Output")

### NAT Detection
![alt text](https://i.imgur.com/Nqhr8EH.png "NAT Detection")

### Skipped Tests
![alt text](https://i.imgur.com/7SryMhT.png "Skipped Test")
