import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline
)
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import logging

# Intel XPU optimisation
from ipex_llm import optimize as ipex_opt
import intel_extension_for_pytorch as ipex

# Глобальные переменные для кэширования
_llm_pipe = None
_system_prompt = None


def load_system_prompt(path: str = "system_prompt.txt") -> str:
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
    global _llm_pipe
    if _llm_pipe is not None:
        return _llm_pipe

    # Читаем идентификатор модели из переменной окружения, по умолчанию берём компактную 1.5-2B-модель
    model_id = os.getenv("LLM_ID", "Qwen/Qwen2-1.5B-Instruct")

    cache_dir = os.getenv("HF_HOME")  # путь к офлайн-кэшу HuggingFace, если задан

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)

        # Загружаем модель на XPU и отдаём под оптимизацию IPEX-LLM
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="xpu",
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            cache_dir=cache_dir,
            trust_remote_code=True
        )

        # int4 / bf16 оптимизация под Intel Arc
        model = ipex_opt(
            model,
            dtype=torch.bfloat16,
            quantize="int4",
            inplace=True,
            level="O1",
        )

        # Создаем пайплайн с настройками генерации
        text_generation_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.3,
            top_p=0.9,
            repetition_penalty=1.1,
            return_full_text=False
        )

        _llm_pipe = HuggingFacePipeline(pipeline=text_generation_pipeline)
        return _llm_pipe

    except Exception as e:
        logging.error(f"Error initializing LLM pipeline: {e}")
        raise


def init_qa_chain(retriever):
    llm_pipe = init_llm_pipeline()
    system_prompt = load_system_prompt()

    prompt_template = (
            system_prompt + "\n\nContext:\n{context}\n\nUser Query:\n{query}"
    )

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "query"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm_pipe,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=False
    )