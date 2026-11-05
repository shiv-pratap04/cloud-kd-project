# Task 5: Subnet allocation for 10.20.0.0/16

Method: smallest prefix with 2^(32-p) - 2 >= hosts needed; allocate largest first, each block placed right after the previous one.

| Subnet     | Hosts needed | Working                                   | Network        | Prefix | Usable range              | Broadcast   | Usable hosts |
|------------|-------------:|-------------------------------------------|----------------|-------:|---------------------------|-------------|-------------:|
| app        | 1000 | /23 = 510 (too few), /22 = 1022 (fits)    | 10.20.0.0      | /22 | 10.20.0.1 - 10.20.3.254   | 10.20.3.255 | 1022 |
| public     | 250  | /25 = 126 (too few), /24 = 254 (fits)     | 10.20.4.0      | /24 | 10.20.4.1 - 10.20.4.254   | 10.20.4.255 | 254  |
| data       | 100  | /26 = 62 (too few), /25 = 126 (fits)      | 10.20.5.0      | /25 | 10.20.5.1 - 10.20.5.126   | 10.20.5.127 | 126  |
| management | 20   | /28 = 14 (too few), /27 = 30 (fits)       | 10.20.5.128    | /27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30   |

Block sizes: /22 = 1024 addresses (10.20.0.0 - 10.20.3.255); next free address is 10.20.4.0.
/24 = 256 (10.20.4.0 - 10.20.4.255); next 10.20.5.0. /25 = 128 (10.20.5.0 - 10.20.5.127); next 10.20.5.128. /27 = 32 (10.20.5.128 - 10.20.5.159).

# NACL explanation (public subnet)

A NACL is stateless: it keeps no record of connections, so every packet is checked on its own. A client's request to port 443 is allowed by an inbound rule, but the reply leaves on an ephemeral port (1024-65535) and is a different packet in the other direction, so it needs its own outbound rule (rule 110). The same applies to replies from the app subnet coming back in (inbound rule 130).

Rules are evaluated from the lowest number upward and the first match decides. The deny for 198.51.100.0/24 is rule 90, below the allow rules 100/110 for ports 80/443 from 0.0.0.0/0. If the deny had a higher number, a packet from 198.51.100.9 to port 443 would match the allow first and the block would never take effect.
