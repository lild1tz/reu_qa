from pydantic import BaseModel
from typing import Optional, List

# Модель для запроса
class QueryRequest(BaseModel):
    query: str  # Текстовый запрос пользователя
    id: int     # Уникальный идентификатор запроса

# Модель для ответа
class ResponseModel(BaseModel):
    id: int               # Идентификатор запроса
    answer: Optional[int] # Ответ (число или None)
    reasoning: str        # Обоснование выбора ответа
    sources: List[str]    # Список использованных источников