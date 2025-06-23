# ----------------------------- tunWindows.py ------------------------------#
# This script is designed to create a wintun adapter, start a session,      #
# read and send packets using the Wintun library, handle the Wintun driver  #
# and manage the adapter lifecycle on a Windows system.                     #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.1           #
# --------------------------------- s3B-a ----------------------------------#

import ctypes
import ctypes.wintypes as wintypes
import platform
import sys
import os
import uuid

INFINITE = 0xFFFFFFFF

# Determines CPU architecture
cpu = platform.machine().lower()

wintun = None

# Define the GUID structure as per the requirements in wintun.h
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", (ctypes.c_ubyte * 8))
    ]

# Converts a string of a GUID into the GUID structure
def string_to_guid(s):
    u = uuid.UUID(s)
    d = u.bytes_le
    return GUID(
        Data1=int.from_bytes(d[0:4], 'little'),
        Data2=int.from_bytes(d[4:6], 'little'),
        Data3=int.from_bytes(d[6:8], 'little'),
        Data4=(ctypes.c_ubyte * 8).from_buffer_copy(d[8:])
    )

# Starts a Wintun session with the specified adapter and MTU
# Returns a session handle if successful, otherwise None
def startWintunSession(adapter, mtu):
    session = wintun.WintunStartSession(adapter, mtu)
    if not session:
        print("Failed to start session.")
        return None
    print("Session started successfully.")
    return session

# Reads packets from the Wintun session
def readPackets(session):
    read_event = wintun.WintunGetReadWaitEvent(session)
    if not read_event:
        print("Failed to get read wait event.")
        return

    # Wait for packets to be available in the session
    while True:
        ctypes.windll.kernel32.WaitForSingleObject(read_event, INFINITE)

        packet_size = wintypes.DWORD(0)
        packet = wintun.WintunReceivePacket(session, ctypes.byref(packet_size))

        if packet:
            print(f"Received packet of size {packet_size.value} bytes.")
            packet_bytes = ctypes.string_at(packet, packet_size.value)

            print(f"Packet data (hex): {packet_bytes[:min(32, packet_size.value)].hex()}")

            wintun.WintunReleaseReceivePacket(session, packet)
        else:
            print("No packet received.")

# Sends packets through the Wintun session
def sendPackets(session, data):
    packetSize = len(data)
    packet = wintun.WintunAllocateSendPacket(session, packetSize)
    if not packet:
        print("Failed to allocate send packet.")
        return
    ctypes.memmove(packet, data, packetSize)
    wintun.WintunSendPacket(session, packet)
    print(f"Sent packet of size {packetSize} bytes.")

# Closes the Wintun adapter and any resources associated with it
def closeAdapter(adapter):
    if adapter:
        wintun.WintunCloseAdapter(adapter)
        print("Adapter at", adapter, "closed successfully.")
    else:
        print("No adapter to close.")

def run():

    global wintun

    # Determine users CPU architecture and load the appropriate .dll
    if cpu.startswith('amd64'):
        print(cpu)
        wintun = ctypes.WinDLL(r"./dlls/amd64/wintun.dll")
        
    elif cpu.startswith('arm'):
        print(cpu)
        wintun = ctypes.WinDLL(r"./dlls/arm/wintun.dll")
    elif cpu.startswith('arm64'):
        print(cpu)
        wintun = ctypes.WinDLL(r"./dlls/arm64/wintun.dll")
    elif cpu.startswith('x86'):
        print(cpu)
        wintun = ctypes.WinDLL(r"./dlls/x86/wintun.dll")
    else:
        raise ImportError("Unsupported architecture for windows: " + cpu)
    print(wintun)

    # Basic types for Wintun
    WINTUN_ADAPTER_HANDLE = wintypes.HANDLE
    WINTUN_SESSION_HANDLE = wintypes.HANDLE

    # Define the Wintun Adapter
    wintun.WintunCreateAdapter.argtypes = [
        wintypes.LPCWSTR,       # Name
        wintypes.LPCWSTR,       # Tunnel Type
        ctypes.POINTER(GUID)    # Requested GUID
    ]
    wintun.WintunCreateAdapter.restype = WINTUN_ADAPTER_HANDLE

    # WintunOpenAdapter
    wintun.WintunOpenAdapter.argtypes = [wintypes.LPCWSTR]
    wintun.WintunOpenAdapter.restype = WINTUN_ADAPTER_HANDLE

    # WintunCloseAdapter
    wintun.WintunCloseAdapter.argtypes = [WINTUN_ADAPTER_HANDLE]
    wintun.WintunCloseAdapter.restype = None

    # WintunDeleteDriver
    wintun.WintunDeleteDriver.argtypes = []
    wintun.WintunDeleteDriver.restype = wintypes.BOOL

    # NET_LUID struct
    class NET_LUID(ctypes.Structure):
        _fields_ = [("Value", ctypes.c_ulonglong)]

    # WintunGetAdapterLUID
    wintun.WintunGetAdapterLUID.argtypes = [WINTUN_ADAPTER_HANDLE, ctypes.POINTER(NET_LUID)]
    wintun.WintunGetAdapterLUID.restype = None

    # WintunGetRunningDriverVersion
    wintun.WintunGetRunningDriverVersion.argtypes = []
    wintun.WintunGetRunningDriverVersion.restype = wintypes.DWORD

    # WintunStartSession
    wintun.WintunStartSession.argtypes = [WINTUN_ADAPTER_HANDLE, wintypes.DWORD]
    wintun.WintunStartSession.restype = WINTUN_SESSION_HANDLE

    # WintunEndSession
    wintun.WintunEndSession.argtypes = [WINTUN_SESSION_HANDLE]
    wintun.WintunEndSession.restype = None

    # WintunGetReadWaitEvent
    wintun.WintunGetReadWaitEvent.argtypes = [WINTUN_SESSION_HANDLE]
    wintun.WintunGetReadWaitEvent.restype = wintypes.HANDLE

    # WintunReceivePacket
    wintun.WintunReceivePacket.argtypes = [WINTUN_SESSION_HANDLE, ctypes.POINTER(wintypes.DWORD)]
    wintun.WintunReceivePacket.restype = ctypes.POINTER(ctypes.c_ubyte)

    # WintunReleaseReceivePacket
    wintun.WintunReleaseReceivePacket.argtypes = [WINTUN_SESSION_HANDLE, ctypes.POINTER(ctypes.c_ubyte)]
    wintun.WintunReleaseReceivePacket.restype = None

    # WintunAllocateSendPacket
    wintun.WintunAllocateSendPacket.argtypes = [WINTUN_SESSION_HANDLE, wintypes.DWORD]
    wintun.WintunAllocateSendPacket.restype = ctypes.POINTER(ctypes.c_ubyte)

    # WintunSendPacket
    wintun.WintunSendPacket.argtypes = [WINTUN_SESSION_HANDLE, ctypes.POINTER(ctypes.c_ubyte)]
    wintun.WintunSendPacket.restype = None
    
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
    
    # Checks if the driver is running and then starts a session
    while True:
        try:
            if wintun.WintunOpenAdapter(adapter_name):
                print("Adapter is open, proceeding with session creation...")
                session = startWintunSession(adapter, 0x400000) # MTU set to 4MB, increase in the future
                if session:
                    print("Session created successfully:", session)
                    readPackets(session)

                    data = b"Hello, Wintun!"
                    sendPackets(session, data)
                    break
            else:
                print("Adapter is not open, retrying...")
                break
        except Exception as e:
            print(f"Error checking adapter: {e}")
            break

    input("Press Enter to exit...")
    closeAdapter(adapter)
    input("enter")