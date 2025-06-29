# ----------------------------- adapterscan.py ---------------------------- #
# This script is designed to scan the system for all network adapters,      #
# Where we can get the IP addresses and input them into a list to prevent   #
# duplicates, where we can then create a random IP address without          #
# overriding the existing adapters.                                         #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.1           #
# --------------------------------- s3B-a --------------------------------- #

import psutil
import ipaddress
import random

# Retrieves all local networks by scanning the system's network adapters
def getLocalNetworks():
    networks = set()
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name.startswith("AF_INET") and addr.address != '127.0.0.1':
                try:
                    net = ipaddress.ip_network(f"{addr.address}/{addr.netmask}", strict=False)
                    networks.add(net)
                except ValueError:
                    continue
    return networks

# Generates a random IP address that doesn't conflict with existing local networks
def generateNonConflictingIP(skip_first=100):
    local_networks = getLocalNetworks()

    while True:
        a, b, c = random.randint(0, 255), random.randint(0, 255), random.randint(1, 254)
        ip_str = f"10.{a}.{b}.{c}"
        ip_obj = ipaddress.IPv4Address(ip_str)
        if not any(ip_obj in net for net in local_networks):
            return ip_str