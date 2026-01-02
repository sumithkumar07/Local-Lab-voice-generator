
import subprocess
import json
import logging
import platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HardwareDetector:
    """
    Detects available hardware (GPU) using a 2-Layer approach:
    1. Physical Layer (WMIC): Checks if an NVIDIA card is physically present.
    2. Functional Layer (Torch): Checks if CUDA drivers are installed and usable.
    """

    @staticmethod
    def get_physical_gpu():
        """
        Layer 1: Ask Windows 'Do I have an NVIDIA card?'
        Returns the name of the card if found, else None.
        """
        if platform.system() != "Windows":
            return None
            
        try:
            # Run PowerShell command to get video controller names (Cleaner & Modern)
            cmd = 'powershell -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"'
            result = subprocess.check_output(cmd, shell=True).decode()
            
            # Check for NVIDIA
            for line in result.split('\n'):
                if "NVIDIA" in line.upper():
                    return line.strip()
            return None
            
        except Exception as e:
            logger.error(f"Physical GPU check failed: {e}")
            return None

    @staticmethod
    def get_functional_gpu():
        """
        Layer 2: Ask PyTorch 'Can I use the GPU?'
        Runs in a subprocess to avoid hanging the main app if drivers are stuck.
        """
        import sys
        try:
            # Run a mini-script to check Torch
            script = "import torch; print(f'{torch.cuda.is_available()}|{torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
            cmd = [sys.executable, "-c", script]
            
            # Run in subprocess to avoid main process freeze
            # 10s timeout should be enough for even slow HDDs/GPUs
            result = subprocess.check_output(
                cmd, 
                timeout=10,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            available, name = result.split('|')
            
            return {
                "available": available == "True",
                "name": name,
                "count": 1 if available == "True" else 0
            }
        except subprocess.TimeoutExpired:
            return {"available": False, "error": "Detection timed out (Drivers might be hanging)"}
        except Exception as e:
            return {"available": False, "error": f"Check failed: {str(e)}"}

    @classmethod
    def analyze_system(cls):
        """
        Combines both layers to give a final verdict.
        Returns a Status Dictionary.
        """
        physical_card = cls.get_physical_gpu()
        functional_status = cls.get_functional_gpu()
        
        status = {
            "platform": "Unknown",
            "message": "",
            "can_run_pro": False,
            "details": {}
        }

        # Case 1: Functional GPU is working! 🚀
        if functional_status["available"]:
            status["platform"] = "GPU_READY"
            status["message"] = f"🚀 Pro Mode Ready ({functional_status['name']})"
            status["can_run_pro"] = True
            status["details"] = functional_status
            
        # Case 2: Physical GPU exists, but Functional failed ⚠️
        elif physical_card:
            status["platform"] = "GPU_DRIVER_MISSING"
            status["message"] = f"⚠️ NVIDIA GPU Detected ({physical_card}), but CUDA drivers are missing."
            status["can_run_pro"] = False
            status["details"] = {"physical_card": physical_card, "error": functional_status.get("error")}
            
        # Case 3: No GPU found🥔
        else:
            status["platform"] = "CPU_ONLY"
            status["message"] = "🥔 Standard Mode (CPU Only)"
            status["can_run_pro"] = False
            
        return status

if __name__ == "__main__":
    # Test run
    print(json.dumps(HardwareDetector.analyze_system(), indent=2))
