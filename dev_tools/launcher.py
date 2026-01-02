
import os
import subprocess
import sys
import webbrowser
import time

def main():
    # Hide the console window
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            user32.ShowWindow(hWnd, 0)

    # Get directory of this executable
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Define paths
    app_dir = os.path.join(base_dir, "app")
    python_exe = os.path.join(base_dir, "python", "python.exe")
    app_script = "app.py"

    # Ensure paths exist
    if not os.path.exists(python_exe):
        # Fallback if folder structure is wrong (e.g. debugging)
        python_exe = sys.executable

    # Setup environment
    env = os.environ.copy()
    env["PYTHONPATH"] = app_dir

    # Command to run: python.exe app.py
    cmd = [python_exe, app_script]

    print(f"Starting Local Lab in {app_dir}")
    
    # Start the application process (hidden)
    # creationflags=0x08000000 is CREATE_NO_WINDOW
    process = subprocess.Popen(
        cmd, 
        cwd=app_dir,
        env=env,
        creationflags=0x08000000 
    )

    # Calculate optimal wait time
    # Check port 8000 availability
    server_ready = False
    for _ in range(15): # Try for 15 seconds
        time.sleep(1)
        # We assume it will open
    
    # Force open browser
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

    # Keep launcher alive to monitor process? 
    # No, let it exit effectively making it a true background process
    # But wait, if we exit, the child process might die if not detached?
    # Popen usage above allows it to run independently.
    
if __name__ == "__main__":
    main()
