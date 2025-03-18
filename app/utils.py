import json
import ssl
import aiohttp
import asyncio
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import ChatOpenAI
from typing import List, Tuple
from bs4 import BeautifulSoup
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

async def fetch_url_content(session: aiohttp.ClientSession, url: str) -> Tuple[str, str]:
    """Асинхронное получение HTML-содержимого страницы."""
    try:
        async with session.get(url, timeout=10, ssl=ssl_ctx) as response:
            if response.status != 200:
                return url, ""

            if "text/html" not in response.content_type.lower() and "text/plain" not in response.content_type.lower():
                return url, ""

            try:
                return url, await response.text()
            except UnicodeDecodeError:
                return url, await response.text(encoding="latin-1")

    except (aiohttp.ClientError, UnicodeDecodeError, TimeoutError):
        return url, ""

def parse_content(html: str, word_limit: int = 1000) -> str:
    """Извлечение и обрезка текстового содержимого страницы."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        [tag.decompose() for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'form', 'iframe', 'img', 'audio', 'video'])]

        text = ' '.join(soup.stripped_strings)
        return ' '.join(text.split()[:word_limit])
    except Exception:
        return "" 


async def relevant_to_reu(llm: ChatOpenAI, question: str, promt_template: PromptTemplate, output_parser: StructuredOutputParser) -> Tuple[bool, str]:
    """Проверка релевантности запроса об унивесритете РЭУ"""

    prompt = promt_template.format_prompt(question=question)
    response = await llm.ainvoke(prompt, max_tokens=100)
    output_dict = output_parser.parse(response.content)

    return (output_dict['relevant'], output_dict['reasoning'])

async def general_output(llm: ChatOpenAI, question: str, context:str, promt_template: PromptTemplate, output_parser: StructuredOutputParser) -> Tuple[bool, str]:
    """Общий ответ модели на вопрос"""
    prompt = promt_template.format_prompt(question=question, context=context)
    response = await llm.ainvoke(prompt, max_tokens=500)
    output_dict = output_parser.parse(response.content)

    return (output_dict['answer'], output_dict['reasoning'])

async def search_info(search: GoogleSerperAPIWrapper, question: str, top_sites: int = 5) -> Tuple[List[str], List[str]]:
    """Поиск информации по запросу"""
    query = f"{question.rstrip('?')} Университет РЭУ им. Плеханова"
    search_results = await asyncio.to_thread(search.results, query)
    links = list({res['link'] for res in search_results.get('organic', [])[:top_sites] if 'link' in res})

    if not links:
        return [], []

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5)) as session:
        results = await asyncio.gather(*(fetch_url_content(session, url) for url in links))

    parsed_data = [(parse_content(html), url) for url, html in results if html]
    
    if not parsed_data:
        return [], []

    contents, sources = zip(*parsed_data)
    return list(contents), list(sources)
