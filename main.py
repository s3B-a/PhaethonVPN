# -------------------------------- main.py -------------------------------- #
# This script is designed to determine the users platform and import the    #
# appropriate TUN/TAP adapter module based on the platform. It then runs    #
# the main function of the imported module by calling 'tun.run()'.          #
#                                                                           #
# Requires Python 3.10 or higher to run.                                    #
#                                                                           #
# This script is part of the PhaethonVPN project.          v0.0.2           #
# --------------------------------- s3B-a --------------------------------- #

import ctypes
import os
import platform
import shutil
import sys

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
    system = platform.system()

    if system == "Windows":
        # Admin check for Windows
        if not administratorCheck():
            print("Launching with administrator privileges (Windows)...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join([os.path.abspath(__file__)] + sys.argv[1:]), None, 1
            )
            sys.exit()
    elif system == "Darwin":
        if os.geteuid() != 0:
            print("Launching with administrator privileges (Mac)...")
            script = f'''osascript -e 'do script "sudo python3 {os.path.abspath(__file__)} {' '.join(sys.argv[1:])}"' '''
            os.system(script)
            sys.exit()
    elif system == "Linux":
        if os.geteuid() != 0:
            print("Launching with administrator privileges (Linux)...")
            term_cmd = None
            script_path = os.path.abspath(__file__)
            args = ' '.join(sys.argv[1:])

            if shutil.which("gnome-terminal"):
                term_cmd = f'gnome-terminal -- bash -c "sudo python3 {script_path} + {args}; exec bash"'
            elif shutil.which("xterm"):
                term_cmd = f'xterm -e "sudo python3 {script_path} + {args}; bash"'
            else:
                term_cmd = f'sudo python3 {script_path} + {args}'
            
            os.system(term_cmd)
            sys.exit()

    if sys.version_info < (3, 10):
        print("This script requires Python 3.10 or higher.")
        sys.exit(1)
    main()
