#!/usr/bin/env python3
# ----------------------------- wintunLoader.py --------------------------- #
# This Script is desgined to load the Wintun library dynamically based on   #
# the CPU architecture of the system. It provides a ton of functions to     #
# create, open, close, and manage Wintun adapters and sessions.             #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.2           #
# --------------------------------- s3B-a --------------------------------- #

import ctypes
import ctypes.wintypes as wintypes
import platform

# Define the GUID structure as per the requirements in wintun.h
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", (ctypes.c_ubyte * 8))
    ]

wintun = None

# Return the Wintun library, initalizing it if necessary
def get_wintun():
    global wintun
    if wintun is None:
        init_wintun()
    return wintun

# Initializes the Wintun library by loading the appropriate DLL based on the CPU
def init_wintun():
    global wintun

    cpu = platform.machine().lower()

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