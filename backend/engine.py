
import os
import torch
import logging
from kokoro import KPipeline
from .model_styletts2 import StyleTTS2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EngineManager:
    """
    Manages the two voice engines:
    1. Kokoro (Lite) - Always loaded (fast)
    2. StyleTTS 2 (Pro) - Lazy loaded (heavy, quantized)
    """
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"EngineManager initialized on {self.device}")
        
        # Engines
        self.kokoro_pipeline = None
        self.styletts_model = None
        
        # Load Lite immediately
        self.load_kokoro()

    def load_kokoro(self):
        """Loads the lightweight Kokoro model"""
        if self.kokoro_pipeline: return
        
        logger.info("Loading Kokoro (Lite)...")
        try:
            # Existing Kokoro logic adapted
            self.kokoro_pipeline = KPipeline(lang_code='a') 
            logger.info("✅ Kokoro Loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load Kokoro: {e}")

    def load_styletts(self):
        """Lazy loads the heavy StyleTTS 2 model"""
        if self.styletts_model: return
        
        logger.info("Loading StyleTTS 2 (Pro)...")
        try:
            self.styletts_model = StyleTTS2(quantized=True)
            self.styletts_model.load_weights()
        except Exception as e:
            logger.error(f"❌ Failed to load StyleTTS 2: {e}")
            raise e

    def generate(self, text, voice, speed, model_type="kokoro"):
        """Unified Generation Interface (Generator)"""
        
        # PRO MODE
        if model_type == "pro":
            # Check hardware
            if self.device == 'cpu':
                logger.warning("⚠️ Pro mode requested on CPU - falling back to Standard")
                # Fallback handled below
            else:
                try:
                    self.load_styletts()
                    result_audio = self.styletts_model.inference(text, voice, speed)
                    if result_audio is not None:
                         # Wrap in a generator format to match Kokoro's signature
                         # (phonemes, tokens, audio)
                         yield (None, None, result_audio)
                         return  # Exit after yielding pro audio
                    
                    # If returned None, log and fallback
                    logger.warning("StyleTTS 2 returned None. Falling back to Kokoro.")
                except Exception as e:
                    logger.error(f"Pro generation failed: {e}")
                    # Fallback to Kokoro below
            
        # STANDARD MODE (or Fallback)
        if not self.kokoro_pipeline: self.load_kokoro()
        
        # Kokoro returns a generator, so we use yield from
        yield from self.kokoro_pipeline(text, voice=voice, speed=speed)

engine_manager = EngineManager()
