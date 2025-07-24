import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline
)
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import logging

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

    # Конфиг для 4-bit квантования
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True
    )

    model_id = "mistralai/Mistral-7B-v0.1"

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
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