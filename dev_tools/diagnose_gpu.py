import torch
import sys
import platform

print("=== GPU Diagnostic ===")
print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"CUDA Version (Torch): {torch.version.cuda}")

if torch.cuda.is_available():
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
else:
    print("❌ CUDA NOT AVAILABLE")
    print("Possible reasons: Drivers missing, CPU-only PyTorch installed, or hardware incompatible.")
