#!/usr/bing/env python3
# ------------------------------ dnsresolve.py ---------------------------- #
# This script is designed to manage anything DNS related, whether that be   #
# The server or the website                                                 #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.3           #
# --------------------------------- s3B-a --------------------------------- #

import random
import socket
import struct
import sys
import time

# minimal root server IPv4 addresses (hints)
ROOT_SERVERS = [
    "198.41.0.4",      # a.root-servers.net
    "199.9.14.201",    # b.root-servers.net
    "192.33.4.12",     # c.root-servers.net
    "199.7.91.13",     # d.root-servers.net
    "192.203.230.10",  # e.root-servers.net
    "192.5.5.241",     # f.root-servers.net
    "192.112.36.4",    # g.root-servers.net
    "198.97.190.53",   # h.root-servers.net
    "192.36.148.17",   # i.root-servers.net
    "192.58.128.30",   # j.root-servers.net
    "193.0.14.129",    # k.root-servers.net
    "199.7.83.42",     # l.root-servers.net
    "202.12.27.33",    # m.root-servers.net
]

UDPTIMEOUT = 2.0

# Internal function: Question section
def encode_domain(name: str) ->  bytes:
    parts = name.split('.')
    encoded = b""
    for part in parts:
        if not part:
            continue
        encoded += struct.pack("B", len(part)) + part.encode("utf-8")
    return encoded + b"\x00" # NULL byte to end QNAME

# Constructs a raw DNS query packet for the given domain
def dns_query(domain: str) -> bytes:
    
    # Transition_ID (random 16bit number)
    id = random.randint(0, 0xFFFF)

    # Flags: standard query and recursion if desired
    flags = 0x0100

    # Questions, Answer RR, Authority RR, Additional RR
    qdcount = 1
    ancount = nscount = arcount = 0

    # 12bytes for the header
    header = struct.pack("!HHHHHH", id, flags, qdcount, ancount, nscount, arcount)
    
    qname = encode_domain(domain)
    qtype = 1   # A record
    qclass = 1  # IN (Internet)
    question = qname + struct.pack("!HH", qtype, qclass)

    return header + question, id

# Parses a raw DNS response and returns an IPv4
def parse_dns(response: bytes, id: int):

    if len(response) < 12:
        raise ValueError("Truncated DNS response")
    

    # Validate Transaction_ID
    txid, flags, qdcount, ancount, nscount, arcount = struct.unpack("!HHHHHH", response[0:12])
    if txid != id:
        raise ValueError("Transaction ID mismatch")
    
    rcode = flags & 0x000F # 

    # Skip header
    offset = 12

    for _ in range(qdcount):
        _, offset = readName(response, offset)
        offset+=4
    
    ips = []

    # parse through the section given
    for _ in range(ancount):
        # Skip NAME (2 bytes/pointer), TYPE, RCLASS, TTL
        _, offset = readName(response, offset)
        rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', response[offset:offset+10])
        offset += 10

        rdata = response[offset:offset+rdlength]
        offset += rdlength

        # Record IPv4
        if rtype == 1 and rclass == 1 and rdlength == 4:
            ip = ".".join(str(b) for b in rdata)
            ips.append(ip)
    
    authorities = []
    for _ in range(nscount):
        ns_name, offset = readName(response, offset)
        # No need for type/class/ttl/rdlength for NS
        offset+=10
        authorities.append(ns_name)

    additionals = {}
    for _ in range(arcount):
        name, offset = readName(response, offset)
        rtype, rclass, ttl, rdlength, = struct.unpack("!HHIH", response[offset:offset+10])
        offset+=10
        rdata = response[offset:offset+rdlength]
        offset+=rdlength
        if rtype == 1 and rclass == 1 and rdlength == 4:
            ip = ".".join(str(b) for b in rdata)
            additionals.setdefault(name, []).append(ip)
    
    return {
        "answers": ips,
        "authorities": authorities,
        "additionals": additionals,
        "rcode": rcode,
    }

# Performs a raw DNS query to resolve a domain to its IPs
def rawDNSLookup(domain: str) -> list[str]:
    return iterativeLookup(domain)

# Iterative lookup for A records of 'domain' starting from root servers
# Returns a list of IPv4s
def iterativeLookup(domain: str, max_depth: int = 6) -> list[str]:
    #if domain in OVERRIDES:
    #    return OVERRIDES[domain][:] # Copy
    nameserver_ips = ROOT_SERVERS[:]
    depth = 0
    while depth < max_depth:
        depth+=1
        for server in nameserver_ips:
            try:
                query_packet, txid = dns_query(domain)
                raw = sendUDPquery(query_packet, server)
                parsed = parse_dns(raw, txid)
            except Exception:
                continue

            if parsed["answers"]:
                return parsed["answers"]
            
            next_ns_ips = []

            for ns_name in parsed["authorities"]:
                glue = parsed["additionals"].get(ns_name)
                if glue:
                    next_ns_ips.extend(glue)
                else:
                    try:
                        ns_ips = iterativeLookup(ns_name, max_depth=max_depth - depth)
                        next_ns_ips.extend(ns_ips)
                    except Exception:
                        continue
            
            if next_ns_ips:
                nameserver_ips = next_ns_ips
                break
        else:
            break
    
    raise RuntimeError(f"Failed to resolve {domain}")

# Send a DNS UDP query to a given server IP and return the raw response
# socket.timeout if no response
def sendUDPquery(packet: bytes, server_ip: str, port: int=53) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(UDPTIMEOUT)
        s.sendto(packet, (server_ip, port))
        data, _ = s.recvfrom(4096)
        return data

# Reads a domain name from response beginning at an offset and compression handling
def readName(response: bytes, offset: int) -> (str, int):
    labels = []
    original_offset = offset
    jumped = False

    while True:
        length = response[offset]
        if length & 0xC0 == 0xC0:
            if not jumped:
                original_offset = offset + 2
                jumped = True
            pointer = struct.unpack("!H", response[offset:offset+2])[0] & 0x3FFF
            offset = pointer
            continue
        if length == 0:
            offset+=1
            break
        offset+=1
        labels.append(response[offset:offset + length].decode("utf-8", errors="ignore"))
        offset+=length
    
    name = ".".join(labels)
    return name, (original_offset if jumped else offset)

if __name__ == "__main__":
    test_domains = ["example.com", "ietf.org", "nonexistent.invalid"]
    for d in test_domains:
        try:
            ips = rawDNSLookup(d)
            print(f"{d} -> {ips}")
        except Exception as e:
            print(f"{d} resolution failed: {e}")