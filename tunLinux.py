# ------------------------------- tunLinux.py ----------------------------- #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.1           #
# --------------------------------- s3B-a --------------------------------- #

import adapterscan
import bridges
import fcntl
import os
import socket
import struct
import subprocess
import threading

TUNSETIFF = 0x400454ca
IFF_TUN   = 0x0001
IFF_NO_PI = 0x1000

# Creates a TUN device on a Linux system and returns the file descriptor
def create_tun(name=''):
    tun = os.open('/dev/net/tun', os.O_RDWR)
    ifr = struct.pack('16sH', name.encode(), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)
    return tun

# Configures the TUN device with the given specifications
def configure_tun(name, ip):
    subprocess.run(['ip', 'addr', 'add', ip, 'dev', name])
    subprocess.run(['ip', 'link', 'set', name, 'up'])

# Reads packets from the TUN session
def readPackets(tun, sock, server_ip, server_port, stop_event):
    while not stop_event.is_set():
        packet = os.read(tun, 4096)
        sock.sendto(packet, (server_ip, server_port))

# Receives packets from the server and injects them into the TUN device
def receiveFromServerAndInject(sock, tun, stop_event):
    while not stop_event.is_set():
        data, _ = sock.recvfrom(4096)
        os.write(tun, data)

def run():
    network = chooseNetwork()
    
    tun_name = 'PhaethonVPN'
    tun_ip = adapterscan.generateNonConflictingIP(skip_first=100)
    server_ip = network[0]
    server_country = network[1]
    server_port = int(bridges.returnPort(server_country, server_ip))
    print(f"Connecting to server {server_ip}:{server_port} with TUN device {tun_name} at IP {tun_ip}")

    tun = create_tun(tun_name)
    configure_tun(tun_name, tun_ip)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)

    stop_event = threading.Event()

    reader_thread = threading.Thread(target=readPackets, args=(tun, sock, server_ip, server_port, stop_event))
    injector_thread = threading.Thread(target=receiveFromServerAndInject, args=(sock, tun, stop_event))

    reader_thread.start()
    injector_thread.start()

    try:
        reader_thread.join()
        injector_thread.join()
    except KeyboardInterrupt:
        stop_event.set()
        reader_thread.join()
        injector_thread.join()
    finally:
        os.close(tun)
        sock.close()

def chooseNetwork():
    bridges.loadDictionary()
    return bridges.returnIP()