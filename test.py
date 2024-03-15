import os
import sys
import platform

def create_shortcut():
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    script_path = os.path.expanduser('/home/maxat/Projects/Agrarka/feeder-installer/submod/scripts/gui/config_gui.py')

    os_name = platform.system()

    if os_name == 'Windows':
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(os.path.join(desktop_path, 'Config GUI.lnk'))
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{script_path}"'
        shortcut.WorkingDirectory = os.path.dirname(script_path)
        shortcut.IconLocation = sys.executable
        shortcut.save()

    elif os_name == 'Linux':
        desktop_file = os.path.join(desktop_path, 'config_gui.desktop')
        with open(desktop_file, 'w') as f:
            if os.path.exists("/home/maxat/Projects/Agrarka/feeder-installer/venv"):
                f.write(f"""[Desktop Entry]
Type=Application
Name=Config GUI
Exec=bash -c 'source /home/maxat/Projects/Agrarka/feeder-installer/venv/bin/activate && python3 "{script_path}"'
Icon=/home/maxat/Projects/Agrarka/feeder-installer/submod/scripts/gui/feeder_shortcut.png
Terminal=false
""")
            else:
                f.write(f"""[Desktop Entry]
Type=Application
Name=Config GUI
Exec=bash -c 'python3 "{script_path}"'
Icon=/home/maxat/Projects/Agrarka/feeder-installer/submod/scripts/gui/feeder_shortcut.png
Terminal=false
""")
        os.chmod(desktop_file, 0o755)


if __name__ == '__main__':
    create_shortcut()
