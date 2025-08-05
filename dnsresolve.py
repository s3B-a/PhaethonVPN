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

# Constructs a raw DNS query packet for the given domain
def dns_query(domain):
    
    # Transition_ID (random 16bit number)
    id = random.randint(0, 65535)

    # Flags: standard query and recursion if desired
    flags = 0x0100

    # Questions, Answer RR, Authority RR, Additional RR
    qdcount = 1
    ancount = nscount = arcount = 0

    # 12bytes for the header
    header = struct.pack("!HHHHHH", id, flags, qdcount, ancount, nscount, arcount)

    # Internal function: Question section
    def encode_domain(name):
        parts = name.split('.')
        encoded = b""
        for part in parts:
            encoded += struct.pack("B", len(part)) + part.encode()
        return encoded + b"\x00" # NULL byte to end QNAME
    
    qname = encode_domain(domain)
    qtype = 1   # A record
    qclass = 1  # IN (Internet)
    question = qname + struct.pack("!HH", qtype, qclass)

    return header + question, id

# Parses a raw DNS response and returns an IPv4
def parse_dns(response, id):
    # Validate Transaction_ID
    response_id = struct.unpack("!H", response[0:2])[0]
    if response_id != id:
        raise ValueError("ID mismatch.")
    
    # Answer count
    qdcount = struct.unpack("!H", response[4:6])[0]
    ancount = struct.unpack("!H", response[6:8])[0]
    if ancount == 0:
        raise ValueError("ancount is 0, no answers found.")
    
    # Skip header
    offset = 12

    for _ in range(qdcount):
        while response[offset] != 0:
            offset += response[offset] + 1
        offset += 5 # NULL byte + QTYPE(2) + QCLASS(2)
    
    ips = []

    # parse through the section given
    for _ in range(ancount):

        # Skip NAME (2 bytes/pointer), TYPE, RCLASS, TTL
        offset += 2
        rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', response[offset:offset+10])
        offset += 10

        rdata = response[offset:offset+rdlength]
        offset += rdlength

        # Record IPv4
        if rtype == 1 and rclass == 1 and rdlength == 4:
            ip = ".".join(str(b) for b in rdata)
            ips.append(ip)
    
    if not ips:
        raise ValueError("No records found to parse through")
    
    return ips

# Performs a raw DNS query to resolve a domain to its IPs
def rawDNSLookup(domain, dns_server="8.8.8.8"):
    query, txid = dns_query(domain)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.sendto(query, (dns_server, 53))

    try:
        data, _ = sock.recvfrom(512)
        return parse_dns(data, txid)
    except socket.timeout:
        return "DNS query timeout"
    finally:
        sock.close()