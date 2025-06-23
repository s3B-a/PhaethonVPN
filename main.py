# -------------------------------- tunMac.py -------------------------------#
# This script is designed to determine the users platform and import the    #
# appropriate TUN/TAP adapter module based on the platform. It then runs    #
# the main function of the imported module by calling 'tun.run()'.          #
#                                                                           #
# Requires Python 3.10 or higher to run.                                    #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.1           #
# --------------------------------- s3B-a ----------------------------------#

import sys
import os
import ctypes

def main():
    platform = sys.platform
    
    if platform.startswith('linux'):    
        import tunLinux as tun
    elif platform.startswith('win32'):
        import tunWindows as tun
    elif platform.startswith('darwin'):
        import tunMac as tun
    else:
        raise ImportError("Unsupported platform: " + platform)
    
    tun.run()

def administratorCheck():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":

    # Admin check
    if not administratorCheck():
        print("Launching with administrator privileges...")

        # Relaunch script in a new terminal after requesting administrator permissions
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join([os.path.abspath(__file__)] + sys.argv[1:]), None, 1
        )
        sys.exit()  

    if sys.version_info < (3, 10):
        print("This script requires Python 3.10 or higher.")
        sys.exit(1)
    main()