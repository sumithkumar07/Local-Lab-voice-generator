import torch
import logging
import os
import time
try:
    from styletts2.tts import StyleTTS2 as StyleTTS2Wrapper
    HAS_STYLE_TTS = True
except ImportError:
    HAS_STYLE_TTS = False
    logger.warning("StyleTTS 2 package not found - running in Basic Mode (Kokoro Only).")

logger = logging.getLogger(__name__)

class StyleTTS2:
    """
    Wrapper for StyleTTS 2 Model using the 'styletts2' pip package.
    Includes Dynamic Quantization for memory optimization.
    """
    def __init__(self, config=None, quantized=True):
        self.quantized = quantized
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model_wrapper = None
        self.loaded = False
        
        logger.info(f"Initializing StyleTTS 2 Wrapper (Quantized={quantized}) on {self.device}")

    def load_weights(self, model_path=None):
        logger.info("Loading StyleTTS 2 Model...")
        start_time = time.time()
        
        if not HAS_STYLE_TTS:
            logger.error("Cannot load StyleTTS 2: Package not installed.")
            raise ImportError("StyleTTS 2 package missing. Please use Pro version.")

        try:
            # Initialize the wrapper (this downloads weights on first run)
            # Default model is LibriTTS (High Quality)
            # We don't pass model_name as it's not a valid arg for this class
            self.model_wrapper = StyleTTS2Wrapper() # Uses defaults, downloads if needed
            
            logger.info(f"Base model loaded in {time.time() - start_time:.2f}s")

            # QUANTIZATION (The Magic Trick for Laptops) 🪄
            if self.quantized and self.device == 'cpu':
                logger.info("⚡ Applying PyTorch Dynamic Quantization (Int8)...")
                q_start = time.time()
                
                # Access the internal torch model
                # The 'styletts2' wrapper stores the model in .model usually, or we access parts
                internal_model = self.model_wrapper.model 
                
                try:
                    # We quantize the Linear layers of the generator/bert portions
                    # This reduces their size by ~4x (32-bit float -> 8-bit int)
                    torch.quantization.quantize_dynamic(
                        internal_model, 
                        {torch.nn.Linear, torch.nn.LSTM, torch.nn.GRU}, 
                        dtype=torch.qint8,
                        inplace=True
                    )
                    logger.info(f"✅ Quantization applied in {time.time() - q_start:.2f}s")
                except Exception as qe:
                    logger.warning(f"Quantization warning (partial or failed): {qe}")
            
            self.loaded = True
            logger.info("✅ StyleTTS 2 Ready (Pro Mode)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load StyleTTS 2: {e}")
            raise e

    def inference(self, text, voice=None, speed=1.0):
        if not self.loaded:
            raise RuntimeError("Model not loaded")
        
        logger.info(f"Generating Pro Audio: '{text[:20]}...' Speed={speed}")
        
        try:
            # Support voice cloning path if provided, else default
            target_voice_path = None
            if voice and voice.endswith(".wav") and os.path.exists(voice):
                target_voice_path = voice
            
            # Use the wrapper's inference function (NOT generate)
            # Output is a NumPy array
            audio_array = self.model_wrapper.inference(
                text=text,
                target_voice_path=target_voice_path, # Pass None for default voice
                alpha=0.3, # Controls timbre (default)
                beta=0.7,  # Controls prosody (default)
                diffusion_steps=5, # Reduced steps for speed (5-10 is good for fast inference)
                embedding_scale=1.0
            )
            
            # Speed adjustment (if library doesn't support it directly, we might need post-processing)
            # For now, we return the raw audio.
            
            return audio_array

        except Exception as e:
            logger.error(f"Pro inference failed: {e}")
            return None
