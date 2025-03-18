from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    """Модель запроса от пользователя."""
    query: str  


class ResponseModel(BaseModel):
    """ Модель ответа сервиса."""
    answer: str = 'Данный вопрос не связан с РЭУ' 
    reasoning: str        
    sources: List[str] = [] 