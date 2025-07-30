import torch

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
    
    # Проверка MPS (для Mac)
    mps_available = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    print(f"\nMPS (Metal) available: {mps_available}")

if __name__ == "__main__":
    check_gpu()
