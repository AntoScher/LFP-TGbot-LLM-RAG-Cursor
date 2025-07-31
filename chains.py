import os
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline
)
# Импорты для Intel Extension for Transformers
try:
    from intel_extension_for_transformers.transformers import (
        AutoModelForCausalLM as AutoModelForCausalLM_ITREX
    )
    from intel_extension_for_transformers.transformers.llm.quantization.quantization_config import (
        QuantizationConfig,
        RtnConfig
    )
    from intel_extension_for_transformers.transformers.llm.quantization.utils import (
        convert_dtype_str2torch,
        convert_dtype_torch2str,
    )
    ITREX_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Intel Extension for Transformers not available: {e}")
    ITREX_AVAILABLE = False
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import logging

# Глобальные переменные для кэширования
_llm_pipe = None
_qa_chain = None

# Проверка доступности Intel XPU
XPU_AVAILABLE = hasattr(torch, 'xpu') and torch.xpu.is_available()
if XPU_AVAILABLE:
    print(f"XPU is available: {torch.xpu.get_device_name(0)}")
else:
    print("XPU is not available, falling back to CPU")

# Глобальные переменные для кэширования
_llm_pipe = None
_system_prompt = None


def load_system_prompt(path: str = "knowledge_base/system_prompt.txt") -> str:
    global _system_prompt
    if _system_prompt is None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                _system_prompt = f.read().strip()
        except Exception as e:
            logging.error(f"Error loading system prompt: {e}")
            _system_prompt = "Ты — ассистент отдела продаж. Отвечай на вопросы клиентов."
    return _system_prompt


def init_llm_pipeline():
    """Инициализация LLM пайплайна с оптимизациями для Intel Arc."""
    global _llm_pipe
    if _llm_pipe is not None:
        return _llm_pipe

    model_id = os.getenv("MODEL_NAME", "Qwen/Qwen2-1.5B-Instruct")
    device = os.getenv("DEVICE", "xpu" if XPU_AVAILABLE and ITREX_AVAILABLE else "cpu")
    cache_dir = os.getenv("HF_HOME")  # путь к офлайн-кэшу HuggingFace, если задан

    try:
        # Загружаем токенизатор
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            cache_dir=cache_dir,
            trust_remote_code=True
        )

        if ITREX_AVAILABLE and device == "xpu":
            # Настройки квантования для Intel Arc
            quant_config = QuantizationConfig(
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
            
            print(f"Loading model {model_id} on XPU with ITREX optimizations...")
            
            # Загружаем модель с квантованием через ITREX
            model = AutoModelForCausalLM_ITREX.from_pretrained(
                model_id,
                quantization_config=quant_config,
                device_map="auto",
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                cache_dir=cache_dir,
                trust_remote_code=True
            )
            print("Model loaded on XPU with ITREX optimizations")
            
        else:
            # Обычная загрузка модели без ITREX
            if device == "xpu":
                print("ITREX not available, falling back to standard XPU loading")
                device_map = "auto"
                torch_dtype = torch.bfloat16
            else:
                device_map = None
                torch_dtype = torch.float32
            
            print(f"Loading model {model_id} on {device.upper()}...")
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map=device_map,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                cache_dir=cache_dir,
                trust_remote_code=True
            )
            
            if device == "cpu":
                model = model.to('cpu')
                print("Model loaded on CPU")
            else:
                print("Model loaded with standard device mapping")

        # Создаем пайплайн с настройками генерации
        text_generation_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            return_full_text=True,
            device_map="auto" if device == "xpu" and ITREX_AVAILABLE else None,
        )

        # Создаем LangChain пайплайн
        _llm_pipe = HuggingFacePipeline(pipeline=text_generation_pipeline)
        return _llm_pipe

    except Exception as e:
        logging.error(f"Error initializing LLM pipeline: {e}")
        raise


def init_qa_chain(retriever):
    llm_pipe = init_llm_pipeline()
    system_prompt = load_system_prompt()

    # Define the prompt template with proper formatting for the model
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

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["system_prompt", "context", "question"]
    )

    # Create the QA chain with proper configuration
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
        input_key="question",  # Changed from "query" to match the input in handle_message
        output_key="result",
        verbose=True  # Enable verbose for debugging
    )
    
    # Add debug logging
    logging.info("QA chain initialized successfully")
    logging.info(f"Input key: {qa_chain.input_key}")
    logging.info(f"Output key: {qa_chain.output_key}")
    
    # Return both the chain and the system prompt
    return qa_chain, system_prompt
    return qa_chain