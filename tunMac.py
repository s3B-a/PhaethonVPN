#!/usr/bin/env python3
# -------------------------------- tunMac.py ------------------------------ #
# This script is designed to create a TUN device, start a session, read and #
# send packets using the macOS utun interface, handle the tun device,       #
# and manage the adapter lifecycle on a Darwin system                       #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.3           #
# --------------------------------- s3B-a --------------------------------- #

# Major work in progress as it has been discovered development must continue
# on a Darwin system to complete this script

import adapterscan
import bridges
from multiprocessing import Event
import os
import socket
import struct
import subprocess
import threading

IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

# Creates a utun device on a Darwin system and returns the file descripter and tun name
def create_tun(name='utun'):
    TUN_PREFIX = 'utun'
    for i in range(0, 255):
        try:
            tun_name = f'{TUN_PREFIX}{i}'
            fd = socket.socket(socket.AF_SYSTEM, socket.SOCK_DGRAM, 2)
            fd.setsockopt(socket.SYSPROTO_CONTROL, 2, struct.pack('256s', tun_name.encode()))
            return fd.fileno(), tun_name
        except Exception:
            continue
    raise OSError("No utun interfaces available.")

# Configures the utun device witht eh given specifications
def configure_tun(name, ip):
    subprocess.run(['ifconfig', name, ip, ip, 'up'])

# Reads packets from the TUN session
# Uncertian if this currently works
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
# Uncertian if this currnetly works
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