from pydantic import BaseModel
from typing import List

# Модель для запроса
class QueryRequest(BaseModel):
    query: str  # Текстовый запрос пользователя


# Модель для ответа
class ResponseModel(BaseModel):
    answer: str = 'Данный вопрос не связан с РЭУ' # Ответ
    reasoning: str        # Обоснование выбора ответа
    sources: List[str] = []   # Список использованных источников