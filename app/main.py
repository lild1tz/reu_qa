import os
import threading
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import ChatOpenAI
from app.models import QueryRequest, ResponseModel
from app.config import Config
from app.prompts import (
    prompt_template_relevant_to_reu, output_parser_relevant_to_reu,
    prompt_template_final, output_parser_final
    )
from app.utils import (
    relevant_to_reu, 
    general_output,
    search_info
)

search = GoogleSerperAPIWrapper(serper_api_key=Config.SERPER_API_KEY)
llm = ChatOpenAI(
    temperature=0.0,
    model=Config.OPENAI_MODEL_NAME,
    openai_api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL
)

app = FastAPI()

def run_streamlit():
    os.system("streamlit run frontend/frontend.py --server.port 8501 --server.headless true")

threading.Thread(target=run_streamlit, daemon=True).start()

@app.get("/")
async def redirect_to_frontend():
    """ Перенаправляем пользователя сразу в Streamlit-интерфейс """
    return RedirectResponse(url="http://localhost:8501")

@app.post("/api/request")
async def handle_request(request: QueryRequest) -> ResponseModel:
    question = request.query
    relevant, reasoning = await relevant_to_reu(
        llm=llm, 
        question=question,
        promt_template=prompt_template_relevant_to_reu,
        output_parser=output_parser_relevant_to_reu
    )

    if not relevant:
        return ResponseModel(
            answer="Данный вопрос не связан с РЭУ",
            reasoning=reasoning,
            sources=[]
        )

    search_results = await search_info(search=search, question=question, top_sites=5)
    context = '\n'.join(search_results[0]) if search_results[0] else "Контекст отсутствует."
    links = search_results[1] if search_results[1] else []

    answer, reasoning = await general_output(
        llm=llm,
        question=question,
        context=context,
        promt_template=prompt_template_final,
        output_parser=output_parser_final
    )

    return ResponseModel(
        answer=answer,
        reasoning=reasoning,
        sources=links
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)