from fastapi import FastAPI, HTTPException 
from app.models import QueryRequest, ResponseModel 
from app.config import Config 
from app.utils import (
    is_relevant_to_reu,  # Проверка релевантности запроса к рэу
    process_question_options,  # Обработка вопроса и извлечение вариантов ответа
    process_search_results,  # Получение контента с первых трёх ссылок
    generate_llm_response,  # Генерация ответа с помощью LLM
    summarize_contents  # Суммаризация контента
)

# Создание экземпляра FastAPI 
app = FastAPI()

# Обработка POST-запроса на эндпоинт /api/request
@app.post("/api/request")
async def handle_request(request: QueryRequest) -> ResponseModel:
    # 1. Проверяем, относится ли вопрос к рэу
    relevant, reason = await is_relevant_to_reu(request.query)
    if not relevant:
        return ResponseModel(
            id=request.id,
            answer=None,
            reasoning=reason + f' Ответ сгенерирован моделью {Config.OPENAI_MODEL_NAME}',
            sources=[]
        )
    # 2. Извлекаем варианты ответа из запроса
    processed_query, options = await process_question_options(request.query)
    # 3. Получаем контент с первых трёх ссылок
    context, sources = await process_search_results(processed_query)
    # 4. Если вариантов ответа нет – возвращаем суммаризацию контента
    if len(options) == 0:
        summary = await summarize_contents(context)
        return ResponseModel(
            id=request.id,
            answer=None,
            reasoning=summary + f' Ответ сгенерирован моделью {Config.OPENAI_MODEL_NAME}',
            sources=sources[:3]
        )
    # 5. Если варианты есть – генерируем ответ через LLM
    response = await generate_llm_response(
        query=processed_query,
        context='\n'.join(context),
        options=options
    )
    return ResponseModel(
        id=request.id,
        answer=response['answer'],
        reasoning=response['reasoning'] + f' Ответ сгенерирован моделью {Config.OPENAI_MODEL_NAME}',
        sources=sources[:3]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)