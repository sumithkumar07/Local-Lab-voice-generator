
import os
import shutil
import subprocess
import time

# ================= Configuration =================
PROJECT_ROOT = r"c:\Users\sumit\OneDrive\Desktop\code project"
VOICE_SRC = os.path.join(PROJECT_ROOT, "voice")
PORTABLE_SRC = os.path.join(PROJECT_ROOT, "LocalLab-Portable")

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Builds")
BASIC_DIR = os.path.join(OUTPUT_DIR, "LocalLab_Basic")
PRO_DIR = os.path.join(OUTPUT_DIR, "LocalLab_Pro")

# Embedded Python Executable Path (Relative to portable root)
PYTHON_REL = r"python\python.exe"

def run_pip(env_root, args):
    """Runs pip inside the specific environment"""
    python_exe = os.path.join(env_root, PYTHON_REL)
    if not os.path.exists(python_exe):
        print(f"❌ Error: Python not found at {python_exe}")
        return False
    
    cmd = [python_exe, "-m", "pip"] + args
    print(f"   > Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError:
        print("   ❌ Command Failed")
        return False

def build_variant(variant_name, dest_dir, pip_commands):
    print(f"\n========================================")
    print(f"🏗️  Building Variant: {variant_name}")
    print(f"========================================")
    
    # 1. Clean & Copy Portable Base
    if os.path.exists(dest_dir):
        print(f"   Deleting old build at {dest_dir}...")
        shutil.rmtree(dest_dir)
    
    print(f"   Copying Portable Enviroment...")
    shutil.copytree(PORTABLE_SRC, dest_dir)
    
    # 2. Update Source Code (App Folder)
    app_dest = os.path.join(dest_dir, "app")
    if os.path.exists(app_dest):
        shutil.rmtree(app_dest)
    
    print(f"   Overlaying Voice App Code...")
    shutil.copytree(VOICE_SRC, app_dest, ignore=shutil.ignore_patterns(
        "venv", ".git", "__pycache__", "build", "dist", ".vscode", "dev_tools"
    ))
    
    # 3. Modify Dependencies (The Magic Step)
    print(f"   🔧 Installing Dependencies for {variant_name}...")
    for args in pip_commands:
        if not run_pip(dest_dir, args):
            print(f"CRITICAL FAIL: Could not install dependencies for {variant_name}")
            return False

    # 4. Zip It
    print(f"   📦 Zipping {variant_name}...")
    shutil.make_archive(dest_dir, 'zip', dest_dir)
    print(f"   ✅ {variant_name} Build Complete!")
    return True

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # --- BUILD BASIC (CPU) ---
    # Strategy: Uninstall heavy GPU stuff, force CPU torch
    basic_cmds = [
        ["uninstall", "-y", "torch", "torchvision", "torchaudio", "styletts2"],
        ["install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"],
        ["install", "kokoro", "scipy", "soundfile", "fastapi", "uvicorn", "python-multipart"]
    ]
    build_variant("LocalLab_Basic", BASIC_DIR, basic_cmds)

    # --- BUILD PRO (GPU) ---
    # Strategy: Force CUDA torch, ensure Styletts2
    # Note: Assuming portable base MIGHT have random stuff, we ensure state
    pro_cmds = [
        ["uninstall", "-y", "torch", "torchvision", "torchaudio"],
        ["install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu121"],
        ["install", "styletts2", "kokoro", "scipy", "soundfile", "fastapi", "uvicorn", "python-multipart"]
    ]
    build_variant("LocalLab_Pro", PRO_DIR, pro_cmds)

    print("\n🎉 ALL BUILDS COMPLETE.")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
