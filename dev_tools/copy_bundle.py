import shutil
import os
import sys

# Define source and destination
# Using raw strings to handle backslashes properly
SRC = r"c:\Users\sumit\OneDrive\Desktop\code project\voice"
DEST = r"c:\Users\sumit\OneDrive\Desktop\code project\LocalLab-Portable\app"

# Handle existing destination
if os.path.exists(DEST):
    print(f"Backing up previous app bundle at {DEST}...")
    try:
        backup_path = DEST + "_backup_" + str(sys.version_info.major)
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        os.rename(DEST, backup_path)
        print("Renamed old app to backup.")
    except Exception as e:
        print(f"Error renaming: {e}")
        # If rename fails, try to continue (might be empty or we write over)
        pass

# Copy function
def copy_project():
    print(f"Copying from {SRC} to {DEST}...")
    try:
        shutil.copytree(SRC, DEST, ignore=shutil.ignore_patterns(
            "venv", 
            ".git", 
            "__pycache__", 
            "*.pyc",
            "audio_output", 
            "dist", 
            "build", 
            ".vscode",
            "LocalLab.spec",
            "copy_bundle.py"
        ), dirs_exist_ok=True)
        print("Success! Bundle updated.")
    except Exception as e:
        print(f"Copy failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    copy_project()
