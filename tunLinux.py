#!/usr/bin/env python3
# ------------------------------- tunLinux.py ----------------------------- #
# This script is designed to create a TUN device, start a session, read and #
# send packets using the UNIX TUN/TAP interface, handle the TUN device,     #
# and manage the adapter lifecycle on a Linux system.                       #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.2           #
# --------------------------------- s3B-a --------------------------------- #

import adapterscan
import bridges
import fcntl
from multiprocessing import Event
import os
import socket
import struct
import subprocess
import threading

TUNSETIFF = 0x400454ca # ioctl to set TUN/TAP interface flags
IFF_TUN   = 0x0001 # TUN device
IFF_NO_PI = 0x1000 # Do not provide packet information in the I/O operations

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
        try:
            packet = os.read(tun, 4096)
            sock.sendto(packet, (server_ip, server_port))
        except Exception as e:
            if not stop_event.is_set():
                print(f"Error reading from TUN device: {e}")
            else:
                print("Stopping read thread due to stop event.")

# Receives packets from the server and injects them into the TUN device
def receiveFromServerAndInject(sock, tun, stop_event):
    while not stop_event.is_set():
        try:
            data, _ = sock.recvfrom(4096)
            os.write(tun, data)
        except Exception as e:
            print(f"Error receiving data: {e}")

# This function runs the main logic of the TUN device management and packet handling
def run():

    # networking setup
    network = chooseNetwork()
    tun_name = 'PhaethonVPN'
    tun_ip = adapterscan.generateNonConflictingIP(skip_first=100)
    server_ip = network[0]
    server_country = network[1]
    server_port = int(bridges.returnPort(server_country, server_ip))
    print(f"Connecting to server {server_ip}:{server_port} with TUN device {tun_name} at IP {tun_ip}")

    tun = create_tun(tun_name)
    configure_tun(tun_name, tun_ip)

    # UDP socket for communication with the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)

    stop_event = Event()

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

# Returns an array with the chosen network's IP and country code
# bridges.returnIP[0] = Choosen Server IP address
# bridges.returnIP[1] = Choosen Server Country Code
def chooseNetwork():
    bridges.loadDictionary()
    return bridges.returnIP()