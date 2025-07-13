# ------------------------------- bridges.py ------------------------------ #
# This Script is desgined to determine all available relays through the     #
# Tor network csv within the ./servers directory. It allows the the user to #
# choose a country code and returns the fastest and most reliable relay for #
# that country, where it also returns said IP address and port number.      #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.1           #
# --------------------------------- s3B-a --------------------------------- #

import concurrent.futures
import os
import platform
import subprocess
import sys
from time import sleep

choosenCountry = None
country_relays = {}
csv = "./servers/tor_relays_by_country.csv"
fastest = None
list_of_country_codes = ['ad', 'ae', 'af', 'ag', 'ai', 'al', 'am', 'ao', 'ar', 
                         'at', 'au', 'aw', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 
                         'bg', 'bh', 'bi', 'bj', 'bn', 'bo', 'br', 'bs', 'bt', 
                         'bw', 'by', 'bz', 'ca', 'cd', 'cf', 'cg', 'ch', 'ci', 
                         'cl', 'cm', 'cn', 'co', 'cr', 'cu', 'cv', 'cy', 'cz', 
                         'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'ee', 'eg', 
                         'er', 'es', 'et', 'fi', 'fj', 'fm', 'fr', 'ga', 'gb', 
                         'gd', 'ge', 'gh', 'gm', 'gn', 'gq', 'gr', 'gt', 'gw', 
                         'gy', 'hn', 'hr', 'ht', 'hu', 'id', 'ie', 'il', 'in', 
                         'iq', 'ir', 'is', 'it', 'jm', 'jo', 'jp', 'ke', 'kg', 
                         'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'kz', 'la', 
                         'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 
                         'ly', 'ma', 'mc', 'md', 'me', 'mg', 'mh', 'mk', 'ml', 
                         'mm', 'mn', 'mr', 'mt', 'mu', 'mv', 'mw', 'mx', 'my', 
                         'mz', 'na', 'ne', 'ng', 'ni', 'nl', 'no', 'np', 'nr', 
                         'nz', 'om', 'pa', 'pe', 'pg', 'ph', 'pk', 'pl', 'pt', 
                         'pw', 'py', 'qa', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 
                         'sc', 'sd', 'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 
                         'so', 'sr', 'ss', 'st', 'sv', 'sy', 'sz', 'td', 'tg', 
                         'th', 'tj', 'tl', 'tm', 'tn', 'to', 'tr', 'tt', 'tv', 
                         'tz', 'ua', 'ug', 'us', 'uy', 'uz', 'vc', 've', 'vn', 
                         'vu', 'ws', 'ye', 'za', 'zm', 'zw'
]

# Determines the OS of the system
def determineOS():
    os_name = platform.system()
    if os_name not in ["Windows", "Linux", "Darwin"]:
        print(f"Unsupported OS: {os_name}")
        sys.exit(1)
    else:
        return os_name

# Writes to country_relays, a dictionary of all countries and their associated relays
def determineRelays():
    with open(csv, 'r') as file:
        next(file)
        for line in file:
            parts = line.strip().split(",")
            ip = parts[0]
            country = parts[1]
            port = parts[2]
            
            country_relays.setdefault(country, []).append((ip, port))

# Determines the country and returns the dictionary of relays associated with that country
def loadDictionary():
    if not os.path.exists(csv):
        print(f"CSV file not found: {csv}")
        return None
        
    with open(csv, 'r') as file:
        lines = file.readlines()

        if not lines:
            print("CSV file is empty.")
            return None

        relays = determineRelays()
        
        print("Dictionary Loaded!")

# Returns the IP address of the fastest and most reliable relay for a given country code
def returnIP():
    fastest = None
    while(True):
        print("Available countries:")
        for country in list_of_country_codes:
            print(country, end=' ')
        print("\n")

        choosenCountry = input("Enter a country code (e.g., 'ae', 'us', 'fr') or 'exit' or 'q' to quit: ").strip().lower()
        
        if choosenCountry in ['exit', 'q']:
            break
        
        if choosenCountry in country_relays:
            print(f"Relays for {choosenCountry}:")
            for ip in country_relays[choosenCountry]:
                print(ip)
            print("finding fastest and most reliable relay...")
            sleep(2)
            fastest = findFastestRelay(choosenCountry)
        else:
            print(f"No relays found for country code: {choosenCountry}")
        print("Fastest relay found:", fastest if fastest else "No reachable relays found.")
        return [fastest, choosenCountry]

# Returns the port number for the relay
def returnPort(country, ip):
    if country in country_relays:
        for relay in country_relays[country]:
            if relay[0] == ip:
                return relay[1]
    return None

# Iterates through all the diffrent relays and pings them to find the one that responds the fastest
def findFastestRelay(country_code):
    ips = country_relays.get(country_code, [])
    if not ips:
        print("No IPs found for this country.")
        return None

    # Use ThreadPoolExecutor to ping relays concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(relayCheck, ip_port[0]): ip_port for ip_port in ips}

        for future in concurrent.futures.as_completed(futures):
            ip, success = future.result()
            if success:
                print(f"Found working relay: {ip}")
                return ip
    print("No reachable relays found.")
    return None

# Pings the server to check if it's reachable on Windows
def pingServerWindows(ip):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print(result.stdout.decode(errors='ignore'))
        print(f"Relay {ip} is reachable.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout.decode(errors='ignore'))
        print(f"Relay {ip} is not reachable.")
        return False

# Pings the server to check if it's reachable on Linux
def pingServerLinux(ip):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print(result.stdout.decode(errors='ignore'))
        print(f"Relay {ip} is reachable.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout.decode(errors='ignore'))
        print(f"Relay {ip} is not reachable.")
        return False

# Pings the server to check if it's reachable on Mac
def pingServerMac(ip):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print(result.stdout.decode(errors='ignore'))
        print(f"Relay {ip} is reachable.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout.decode(errors='ignore'))
        print(f"Relay {ip} is not reachable.")
        return False

# Checks if a relay is reachable by pinging it
def relayCheck(ip):
    try:
        if platform.system() == "Windows":
            success = pingServerWindows(ip)
        elif platform.system() == "Linux":
            success = pingServerLinux(ip)
        elif platform.system() == "Darwin":
            success = pingServerMac(ip)
        else:
            print(f"Unsupported OS for {ip}")
            return (ip, False)
        return (ip, success)
    except Exception as e:
        print(f"Relay {ip} check failed with error: {e}")
        return (ip, False)

# debugging
if __name__ == "__main__":
    loadDictionary()
    total = returnIP()
    print(total)
    print(returnPort(total[1], total[0]))