import torch
import sys
import os

def check_gpu():
    print("=== PyTorch GPU/CPU Info ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    
    # Проверка поддержки XPU (Intel)
    xpu_available = hasattr(torch, 'xpu') and torch.xpu.is_available()
    print(f"\nXPU available: {xpu_available}")
    if xpu_available:
        print(f"Number of XPU devices: {torch.xpu.device_count()}")
        for i in range(torch.xpu.device_count()):
            print(f"  XPU Device {i}: {torch.xpu.get_device_name(i)}")
            print(f"  XPU Device {i} properties: {torch.xpu.get_device_properties(i)}")
    
    # Проверка MPS (для Mac)
    mps_available = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    print(f"\nMPS (Metal) available: {mps_available}")
    
    # Проверка Intel Extension for PyTorch
    print(f"\n=== Intel Extension for PyTorch ===")
    try:
        import intel_extension_for_pytorch as ipex
        print(f"IPEX version: {ipex.__version__}")
        print(f"IPEX XPU available: {ipex.xpu.is_available()}")
        if ipex.xpu.is_available():
            print(f"IPEX XPU device count: {ipex.xpu.device_count()}")
            for i in range(ipex.xpu.device_count()):
                print(f"  IPEX XPU Device {i}: {ipex.xpu.get_device_name(i)}")
    except ImportError as e:
        print(f"Intel Extension for PyTorch not available: {e}")
    
    # Проверка Intel Extension for Transformers
    print(f"\n=== Intel Extension for Transformers ===")
    try:
        import intel_extension_for_transformers as itrex
        print(f"ITREX version: {itrex.__version__}")
    except ImportError as e:
        print(f"Intel Extension for Transformers not available: {e}")
    
    # Проверка переменных окружения
    print(f"\n=== Environment Variables ===")
    env_vars = [
        'DEVICE', 'XPU_DEVICE_ID', 'INTEL_EXTENSION_FOR_PYTORCH_VERBOSE',
        'SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS'
    ]
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        print(f"{var}: {value}")
    
    # Рекомендации
    print(f"\n=== Recommendations ===")
    if not xpu_available:
        print("❌ Intel XPU not available. Please:")
        print("   1. Install Intel Arc drivers")
        print("   2. Install Intel Extension for PyTorch")
        print("   3. Set DEVICE=xpu in .env file")
    else:
        print("✅ Intel XPU is available and ready to use!")
        print("   Set DEVICE=xpu in your .env file to use Intel Arc GPU")

if __name__ == "__main__":
    check_gpu()
