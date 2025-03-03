import re
import json
from bs4 import BeautifulSoup
import aiohttp
import ssl
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import ChatOpenAI
from app.config import Config
import asyncio
from typing import Optional, List, Tuple, Dict
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация объектов для поиска и генерации ответов
search = GoogleSerperAPIWrapper(serper_api_key=Config.SERPER_API_KEY)
llm = ChatOpenAI(
    temperature=0.3,
    openai_api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL
)

# Создаем SSL-контекст один раз
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


async def fetch_url_content(session: aiohttp.ClientSession, url: str) -> Tuple[str, str]:
    """Получение и парсинг содержимого URL"""
    try:
        async with session.get(url, timeout=10, ssl=ssl_ctx) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type or 'text/plain' in content_type:
                    charset = response.charset if response.charset else 'utf-8'
                    try:
                        text = await response.text(encoding=charset)
                    except UnicodeDecodeError:
                        text = await response.text(encoding='latin-1')
                    return url, text
                return url, ""
            else:
                logger.warning(f"Failed to retrieve content from {url}, status code: {response.status}")
                return url, ""
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return url, ""

def parse_content(html: str, word_limit: int = 350) -> str:
    """Парсинг и обрезка содержимого страницы"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'form', 'iframe', 'img', 'audio', 'video']):
            element.decompose()
        text = ' '.join(soup.stripped_strings)
        words = text.split()
        return ' '.join(words[:word_limit])
    except Exception as e:
        logger.error(f"Error parsing content: {str(e)}")
        return ""

async def is_relevant_to_reu(question: str) -> Tuple[bool, str]:
    prompt = f"""Проанализируй вопрос и определи его отношение к Университету РЭУ. Ответь строго в JSON:
{{
 "relevant": boolean,
 "reason": "краткое объяснение на русском языке"
}}
Вопрос: {question}"""
    try:
        response = await llm.ainvoke(prompt)
        result = json.loads(response.content)
        return result.get('relevant', False), result.get('reason', '')
    except Exception as e:
        logger.error(f"Ошибка проверки релевантности: {str(e)}")
        return False, f"Ошибка проверки релевантности: {str(e)}"

async def process_question_options(query: str) -> Tuple[str, List[str]]:
    """Извлечение вариантов ответов из запроса"""
    options = re.findall(r'\n\d+\.\s*(.+?)(?=\n\d+\.|\Z)', query, flags=re.DOTALL)
    if len(options) > 10:
        options = options[:10]
    if options:
        parts = re.split(r'\n\d+\.', query)
        new_query = parts[0] + '\n' + '\n'.join(f"{i+1}. {opt.strip()}" for i, opt in enumerate(options))
        return new_query, options
    return query, options

async def generate_llm_response(query: str, context: str, options: List[str]) -> dict:
    """Генерация ответа с учетом вариантов"""
    answer_instruction = (
        "answer: номер варианта (1-10) или 1, если варианты ответа есть ВСЕГДА ВОЗВРАЩАЙ ЧИСЛО И ТОЛЬКО ЕГО"
        if options
        else "answer: всегда null"
    )
    prompt = f"""Отвечай строго в JSON. Вопрос: {query}
Контекст: {context}
Требования:
- {answer_instruction}
- reasoning: краткое обоснование на русском
- если нет вариантов ответа - СТРОГО NULL
- если варианты ответа есть, ВСЕГДА возвращай число в поле answer
- если информации недостаточно, выбери наиболее вероятный вариант
"""
    try:
        response = await llm.ainvoke(prompt)
        result = json.loads(response.content)
        if options:
            answer = result.get('answer')
            if answer is None:
                answer = 1
            else:
                answer = max(1, min(int(answer), len(options)))
        else:
            answer = None
        return {
            "answer": answer,
            "reasoning": result.get('reasoning', 'Обоснование отсутствует'),
            "sources": []
        }
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {str(e)}")
        return {
            "answer": 1 if options else None,
            "reasoning": f"Ошибка генерации ответа: {str(e)}",
            "sources": []
        }

async def process_search_results(question: str) -> Tuple[List[str], List[str]]:
    """Обработка результатов поиска с парсингом контента"""
    try:
        search_results = await asyncio.to_thread(search.results, question)
        organic_results = search_results.get('organic', [])[:3]
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_url_content(session, res['link']) for res in organic_results if 'link' in res]
            results = await asyncio.gather(*tasks)
        parsed_contents = []
        sources = []
        for url, html in results:
            if html:
                content = parse_content(html)
                if content:
                    parsed_contents.append(content)
                    sources.append(url)
        return parsed_contents, sources
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return [], []

async def summarize_contents(contexts: List[str]) -> str:
    """Суммирование контента из нескольких источников с помощью LLM"""
    combined_text = "\n".join(contexts)
    prompt = f"""Проанализируй следующий текст, состоящий из нескольких частей, и кратко суммируй его на русском языке:
---
{combined_text}
---
Сформулируй 3-4 предложения, отражающие суть прочитанного, без потери важных деталей.
Ответ дай в свободной форме (просто текст).
"""
    try:
        response = await llm.ainvoke(prompt)
        return response.content.strip()
    except Exception as e:
        logger.error(f"Ошибка при суммировании контента: {str(e)}")
        return "Ошибка при суммировании контента"