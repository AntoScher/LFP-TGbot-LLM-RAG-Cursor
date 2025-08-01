"""
Intel Arc GPU Optimization Module
Provides optimized configurations and utilities for Intel Arc GPU acceleration
"""

import os
import torch
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class IntelArcOptimizer:
    """Optimizer for Intel Arc GPU acceleration"""
    
    def __init__(self):
        # Check if we should use CPU mode first
        use_cpu = os.getenv("DEVICE", "").lower() == "cpu"
        
        if use_cpu:
            self.xpu_available = False
            self.ipex_available = False
            self.device = "cpu"
            return
            
        # Only check for XPU if not in CPU mode
        self.xpu_available = hasattr(torch, 'xpu') and torch.xpu.is_available()
        self.ipex_available = self._check_ipex_availability()
        self.device = self._get_optimal_device()
        
    def _check_ipex_availability(self) -> bool:
        """Check if Intel Extension for PyTorch is available"""
        # Skip checking if in CPU mode
        if os.getenv("DEVICE", "").lower() == "cpu":
            return False
            
        try:
            import intel_extension_for_pytorch as ipex
            return ipex.xpu.is_available()
        except ImportError:
            return False
        except Exception as e:
            print(f"Warning: Error checking IPEX availability: {e}")
            return False
    
    def _get_optimal_device(self) -> str:
        """Get optimal device for the current setup"""
        # Check if DEVICE is explicitly set in environment variables
        device = os.getenv("DEVICE", "").lower()
        
        if device == "cpu":
            return "cpu"
        elif device == "xpu" and self.xpu_available and self.ipex_available:
            return "xpu"
        elif device == "cuda" and torch.cuda.is_available():
            return "cuda"
        # Auto-detect if no specific device is requested
        elif self.xpu_available and self.ipex_available:
            return "xpu"
        elif torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def setup_environment(self):
        """Setup environment variables for Intel Arc optimization"""
        if self.device == "xpu":
            # Intel XPU specific environment variables
            os.environ.setdefault("INTEL_EXTENSION_FOR_PYTORCH_VERBOSE", "1")
            os.environ.setdefault("SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS", "1")
            os.environ.setdefault("XPU_DEVICE_ID", "0")
            
            logger.info("Intel Arc GPU environment configured")
        else:
            logger.info(f"Using device: {self.device}")
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get optimized model configuration for Intel Arc
        
        Note: The 'device' parameter is not included in the returned config
        as it's not a valid parameter for AutoModelForCausalLM.from_pretrained().
        Device handling should be done separately.
        """
        config = {
            "torch_dtype": torch.float16 if self.device in ["xpu", "cuda"] else torch.float32,
            "low_cpu_mem_usage": True,
            "trust_remote_code": True,
        }
        
        if self.device == "xpu":
            config.update({
                "attn_implementation": "flash_attention_2",
                "use_cache": True,
            })
        
        return config
    
    def optimize_model(self, model, tokenizer=None):
        """Apply Intel Arc optimizations to model"""
        # Skip optimization if in CPU mode
        if os.getenv("DEVICE", "").lower() == "cpu":
            logger.info("Skipping Intel optimizations in CPU mode")
            return model
            
        if self.device == "xpu" and self.ipex_available:
            try:
                import intel_extension_for_pytorch as ipex
                
                # Move model to XPU
                model = model.to("xpu")
                
                # Apply IPEX optimizations
                model = ipex.optimize(model)
                
                logger.info("Model optimized with Intel Extension for PyTorch")
                return model
                
            except Exception as e:
                logger.warning(f"Failed to apply Intel optimizations: {e}")
                return model
        
        return model
    
    def get_quantization_config(self) -> Optional[Dict[str, Any]]:
        """Get quantization configuration for Intel Arc"""
        if self.device == "xpu" and self.ipex_available:
            try:
                from intel_extension_for_transformers.transformers.llm.quantization.quantization_config import (
                    QuantizationConfig, RtnConfig
                )
                
                return QuantizationConfig(
                    approach="weight_only",
                    op_type_dict={
                        ".*": {
                            "weight": {
                                "dtype": "int4_fullrange",
                                "bits": 4,
                                "group_size": 128,
                                "scheme": "sym",
                                "algorithm": "RTN"
                            }
                        }
                    },
                    recipes={
                        "rtn_args": {"enable_full_range": True, "enable_mse_search": True}
                    }
                )
            except ImportError:
                logger.warning("Intel Extension for Transformers not available for quantization")
                return None
        
        return None

# Global optimizer instance
intel_optimizer = IntelArcOptimizer()

def get_optimized_device() -> str:
    """Get the optimal device for current setup"""
    return intel_optimizer.device

def setup_intel_environment():
    """Setup Intel Arc environment"""
    intel_optimizer.setup_environment()

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get optimized model configuration"""
    return intel_optimizer.get_model_config(model_name)

def optimize_model(model, tokenizer=None):
    """Optimize model for Intel Arc"""
    return intel_optimizer.optimize_model(model, tokenizer)

def get_quantization_config() -> Optional[Dict[str, Any]]:
    """Get quantization configuration"""
    return intel_optimizer.get_quantization_config() 