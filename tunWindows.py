#!/usr/bin/env python3
# ----------------------------- tunWindows.py ----------------------------- #
# This script is designed to create a wintun adapter, start a session,      #
# read and send packets using the Wintun library, handle the Wintun driver  #
# and manage the adapter lifecycle on a Windows system.                     #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.2           #
# --------------------------------- s3B-a --------------------------------- #

import adapterscan as adaptScan
import bridges
import ctypes
import ctypes.wintypes as wintypes
from multiprocessing import Event
import socket
import subprocess
import time
import threading
import os
import uuid
import wintunLoader

INFINITE = 0xFFFFFFFF

wintun = wintunLoader.get_wintun()

# Converts a string of a GUID into the GUID structure
def string_to_guid(s):
    u = uuid.UUID(s)
    d = u.bytes_le
    return wintun.GUID(
        Data1=int.from_bytes(d[0:4], 'little'),
        Data2=int.from_bytes(d[4:6], 'little'),
        Data3=int.from_bytes(d[6:8], 'little'),
        Data4=(ctypes.c_ubyte * 8).from_buffer_copy(d[8:])
    )

# Starts a Wintun session with the specified adapter and MTU
# Returns a session handle if successful, otherwise None
def startWintunSession(adapter, mtu):
    print(f"Starting Wintun session with MTU {mtu}")
    session = wintun.WintunStartSession(adapter, mtu)
    if not session:
        print("Failed to start session. Adapter handle:", adapter)
        return None
    return session

# Reads packets from the Wintun session
def readPackets(session, sock, server_ip, server_port, stop_event):
    read_event = wintun.WintunGetReadWaitEvent(session)
    if not read_event:
        print("Failed to get read wait event.")
        return

    while not stop_event.is_set():
        result = ctypes.windll.kernel32.WaitForSingleObject(read_event, 1000)  # 1s timeout to check stop_event
        if result == 0:
            packet_size = wintypes.DWORD(0)
            packet = wintun.WintunReceivePacket(session, ctypes.byref(packet_size))
            print(f"Received packet of size {packet_size.value} bytes.")
            if packet:
                packet_bytes = ctypes.string_at(packet, packet_size.value)
                wintun.WintunReleaseReceivePacket(session, packet)

                # Send
                try:
                    sock.sendto(packet_bytes, (server_ip, server_port))
                    time.sleep(0.01)
                except Exception as e:
                    print(f"Send error: {e}")
        else:
            continue

# Closes the Wintun adapter and any resources associated with it
def closeAdapter(adapter):
    if adapter:
        wintun.WintunCloseAdapter(adapter)
        print("Adapter at", adapter, "closed successfully.")
    else:
        print("No adapter to close.")

# Receives packets from the server and injects them into the Wintun session
def receiveFromServerAndInject(sock, session, stop_event):
    while not stop_event.is_set():
        try:
            data, _ = sock.recvfrom(65535)
            if data:
                packet = wintun.WintunAllocateSendPacket(session, len(data))
                print(f"Received {len(data)} bytes from server, injecting into Wintun session.")
                if packet:
                    ctypes.memmove(packet, data, len(data))
                    wintun.WintunSendPacket(session, packet)
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Receive error: {e}")
            break

# This helper function runs the packet reader
def packetReader(session, sock, server_ip, server_port, stop_event):
    while not stop_event.is_set():
        readPackets(session, sock, server_ip, server_port, stop_event)

# This helper function runs the packet injector
def packetInjector(sock, session, stop_event):
    while not stop_event.is_set():
        receiveFromServerAndInject(sock, session, stop_event)

# This function initializes the Wintun library, creates an adapter, and starts a session
# Receives packets from the server and injects them into the Wintun session
def receiveFromServerAndInject(sock, session, stop_event):
    while not stop_event.is_set():
        try:
            data, _ = sock.recvfrom(65535)
            if data:
                packet = wintun.WintunAllocateSendPacket(session, len(data))
                print(f"Received {len(data)} bytes from server, injecting into Wintun session.")
                if packet:
                    ctypes.memmove(packet, data, len(data))
                    wintun.WintunSendPacket(session, packet)
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Receive error: {e}")
            break

# This helper function runs the packet reader
def packetReader(session, sock, server_ip, server_port, stop_event):
    while not stop_event.is_set():
        readPackets(session, sock, server_ip, server_port, stop_event)

# This helper function runs the packet injector
def packetInjector(sock, session, stop_event):
    while not stop_event.is_set():
        receiveFromServerAndInject(sock, session, stop_event)

# This function initializes the Wintun library, creates an adapter, and starts a session
def run():
    # Wintun Adapter name and tunnel type
    adapter_name = "PhaethonVPN"
    tunnel_type = "PhaethonVPN"
    guidStr = None  # Use None for random GUID, or a valid UUID string

    if guidStr:
        guid = string_to_guid(guidStr)
        guid_ptr = ctypes.byref(guid)
    else:
        guid_ptr = None

    # defines the adapter itself
    adapter = wintun.WintunCreateAdapter(
        ctypes.create_unicode_buffer(adapter_name),
        ctypes.create_unicode_buffer(tunnel_type),
        guid_ptr
    )

    # Checks if the adapter was created successfully
    if not adapter:
        print("Failed to create adapter... Check if the Wintun driver is installed and running.")
    else:
        print("Adapter created successfully:", adapter)
        print("Current process PID:", os.getpid())

    # Give the adapter a random IP address and set it to the created adapter
    random_ip = adaptScan.generateNonConflictingIP()
    subprocess.run([
        "netsh", "interface", "ip", "set", "address",
        "name=PhaethonVPN",
        "static", random_ip, "255.0.0.0", random_ip
    ])
    print("Adapter IP set to:", random_ip)

    # Enable traffic to be routed through the adapter
    subprocess.run([
        "powershell", "-Command",
        "Get-NetAdapter | Where-Object { $_.InterfaceAlias -like '*PhaethonVPN*' }"
    ])

    # Add a default route to the adapter
    subprocess.run([
        "route", "add", "0.0.0.0", "mask", "0.0.0.0", random_ip
    ])

    # network setup
    choosenNetwork = chooseNetwork()
    server_ip = choosenNetwork[0]
    print("\nThe IP is: ", server_ip)
    server_country = choosenNetwork[1]
    server_port = int(bridges.returnPort(server_country, server_ip))

    # UDP socket for communication with the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)

    # Checks if the driver is running and then starts a session
    if wintun.WintunOpenAdapter(adapter_name):
        print("Adapter is open, proceeding with session creation...")
        session = startWintunSession(adapter, 0x400000)
        if session:
            print("Session created successfully:", session)
            print("Beginning packet reading and injection...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024*1024)

            stop_event = Event()

            reader_thread = threading.Thread(
                target=readPackets,
                args=(session, sock, server_ip, server_port, stop_event),
                daemon=True
            )
            injector_thread = threading.Thread(
                target=receiveFromServerAndInject,
                args=(sock, session, stop_event),
                daemon=True
            )
            
            reader_thread.start()
            injector_thread.start()

            try:
                reader_thread.join()
                injector_thread.join()
            except KeyboardInterrupt:
                print("\nReceived interrupt, stopping threads...")
                stop_event.set()
                reader_thread.join()
                injector_thread.join()
            finally:
                print("Cleaning up...")
                wintun.WintunEndSession(session)
                closeAdapter(adapter)
                sock.close()
        else:
            print("Failed to start session.")
    else:
        print("Adapter is not open, exiting...")

    
    input("press enter to close the adapter and exit...")
    closeAdapter(adapter)

# This function allows the user to choose what country to connect to
# bridges.returnIP[0] = Server IP
# bridges.returnIP[1] = Country Code
def chooseNetwork():
    bridges.loadDictionary()
    return bridges.returnIP()
