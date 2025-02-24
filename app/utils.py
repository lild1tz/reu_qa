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
