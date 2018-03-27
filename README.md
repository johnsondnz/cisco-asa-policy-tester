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
```
$ clear; python3 tester.py -i 192.168.1.1 -u admin -p -y test.yml
Password:
[I 180315 18:11:48 tester:163] Attempting connection to 192.168.1.1
[I 180315 18:11:54 tester:167] Connected to 192.168.1.1

[I 180315 18:11:54 tester:172] Processing INSIDE tests
[I 180315 18:11:54 tester:81] Starting tests that should [PASS] block
[I 180315 18:11:54 tester:88] Processing tcp protocol policy
[I 180315 18:11:54 tester:102] Processing: allow test, "packet-tracer input INSIDE tcp 192.168.1.1 12345 192.168.1.2 80 detail"
[I 180315 18:11:55 tester:110] ASA reports: allow
[I 180315 18:11:55 tester:116] Test passed!

[I 180315 18:11:55 tester:88] Processing udp protocol policy
[I 180315 18:11:55 tester:102] Processing: allow test, "packet-tracer input INSIDE udp 192.168.1.1 12345 192.168.1.2 8080 detail"
[I 180315 18:11:55 tester:110] ASA reports: drop
[I 180315 18:11:55 tester:113] Drop reason: (acl-drop) Flow is denied by configured rule
[E 180315 18:11:55 tester:119] Test failed!

[I 180315 18:11:55 tester:88] Processing icmp protocol policy
[I 180315 18:11:55 tester:102] Processing: allow test, "packet-tracer input INSIDE icmp 192.168.1.1 8 0 192.168.1.2 detail"
[I 180315 18:11:56 tester:110] ASA reports: allow
[I 180315 18:11:56 tester:116] Test passed!

[I 180315 18:11:56 tester:83] Starting tests that should [FAIL] block
[I 180315 18:11:56 tester:88] Processing tcp protocol policy
[I 180315 18:11:56 tester:102] Processing: drop test, "packet-tracer input INSIDE tcp 192.168.1.1 12345 192.168.1.2 12345 detail"
[I 180315 18:11:56 tester:110] ASA reports: drop
[I 180315 18:11:56 tester:113] Drop reason: (acl-drop) Flow is denied by configured rule
[I 180315 18:11:56 tester:116] Test passed!

[I 180315 18:11:56 tester:88] Processing tcp protocol policy
[I 180315 18:11:56 tester:102] Processing: drop test, "packet-tracer input INSIDE tcp 192.168.1.1 12345 192.168.1.2 443 detail"
[I 180315 18:11:57 tester:110] ASA reports: allow
[E 180315 18:11:57 tester:119] Test failed!

[D 180315 18:11:57 report:19] HTML report output to "/Coding/GitHub/cisco-asa-policy-tester/reports/html_report.html"
```

## Report Output
![alt text](https://i.imgur.com/83lz6Ov.png "Report Output")

### NAT Detection
![alt text](https://i.imgur.com/Nqhr8EH.png "NAT Detection")
