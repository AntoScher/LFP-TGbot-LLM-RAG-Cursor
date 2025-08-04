import os
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline
)
from langchain_community.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import logging

# Глобальные переменные для кэширования
_llm_pipe = None
_system_prompt = None

# Проверка доступности Intel XPU
XPU_AVAILABLE = hasattr(torch, 'xpu') and torch.xpu.is_available()
if XPU_AVAILABLE:
    print(f"XPU is available: {torch.xpu.get_device_name(0)}")
else:
    print("XPU is not available, falling back to CPU")


def load_system_prompt(path: str = "system_prompt.txt") -> str:
    """Загружает системный промпт из файла"""
    global _system_prompt
    if _system_prompt is None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                _system_prompt = f.read().strip()
            logging.info(f"System prompt loaded from {path}")
        except Exception as e:
            logging.error(f"Error loading system prompt: {e}")
            _system_prompt = "Ты — ассистент отдела продаж. Отвечай на вопросы клиентов."
    return _system_prompt


def init_llm_pipeline():
    """Инициализация LLM пайплайна с оптимизациями для Intel Arc."""
    global _llm_pipe
    if _llm_pipe is not None:
        return _llm_pipe

    # Определяем устройство
    device = os.getenv("DEVICE", "cpu").lower()
    
    # Проверяем доступность устройств
    if device == "xpu" and not XPU_AVAILABLE:
        logging.warning("XPU requested but not available, falling back to CPU")
        device = "cpu"
    elif device == "cuda" and not torch.cuda.is_available():
        logging.warning("CUDA requested but not available, falling back to CPU")
        device = "cpu"
    
    model_id = os.getenv("MODEL_NAME", "Qwen/Qwen2-1.5B-Instruct")
    cache_dir = os.getenv("HF_HOME")

    try:
        logging.info(f"Loading model {model_id} on {device.upper()}")
        
        # Загружаем токенизатор
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            cache_dir=cache_dir,
            trust_remote_code=True
        )

        # Настройки модели в зависимости от устройства
        model_kwargs = {
            "cache_dir": cache_dir,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
        
        if device == "xpu":
            # Intel XPU оптимизации
            try:
                import intel_extension_for_pytorch as ipex
                model_kwargs.update({
                    "torch_dtype": torch.bfloat16,
                    "attn_implementation": "flash_attention_2",
                })
            except ImportError:
                logging.warning("Intel Extension for PyTorch not available")
                device = "cpu"
                model_kwargs["torch_dtype"] = torch.float32
        elif device == "cuda":
            model_kwargs["torch_dtype"] = torch.float16
        else:
            model_kwargs["torch_dtype"] = torch.float32

        # Загружаем модель
        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
        
        # Перемещаем модель на нужное устройство
        if device == "xpu":
            model = model.to("xpu")
            # Применяем Intel оптимизации
            try:
                import intel_extension_for_pytorch as ipex
                model = ipex.optimize(model)
                logging.info("Model optimized with Intel Extension for PyTorch")
            except ImportError:
                logging.warning("Intel optimizations not applied")
        elif device == "cuda":
            model = model.to("cuda")
        else:
            model = model.to("cpu")

        # Создаем пайплайн
        text_generation_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            return_full_text=True,
        )

        # Создаем LangChain пайплайн
        _llm_pipe = HuggingFacePipeline(pipeline=text_generation_pipeline)
        logging.info(f"LLM pipeline initialized successfully on {device.upper()}")
        return _llm_pipe

    except Exception as e:
        logging.error(f"Error initializing LLM pipeline: {e}")
        raise


def init_qa_chain(retriever):
    """Инициализация QA цепи"""
    llm_pipe = init_llm_pipeline()
    system_prompt = load_system_prompt()

    # Определяем шаблон промпта
    prompt_template = """<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
Context:
{context}

Question: {question}
<|im_end|>
<|im_start|>assistant
"""

    # Создаем промпт
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
        partial_variables={"system_prompt": system_prompt}
    )

    # Создаем QA цепь
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm_pipe,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={
            "prompt": prompt,
            "document_prompt": PromptTemplate(
                input_variables=["page_content"],
                template="{page_content}"
            ),
            "document_variable_name": "context",
            "verbose": True
        },
        return_source_documents=True,
        input_key="question",
        output_key="result",
        verbose=True
    )
    
    logging.info("QA chain initialized successfully")
    logging.info(f"Input key: {qa_chain.input_key}")
    logging.info(f"Output key: {qa_chain.output_key}")
    
    return qa_chain, system_prompt 