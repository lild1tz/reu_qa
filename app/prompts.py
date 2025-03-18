from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser

template_relevant_to_reu = """
Ты — аналитик, оценивающий релевантность вопросов к теме Университета РЭУ.  
Твоя задача — определить, связан ли данный вопрос с Университетом РЭУ, его образовательными программами, мероприятиями или другими аспектами.

## Instructions:
1. Внимательно изучи вопрос в поле Question и попробуй понять его смысл.
2. Изучи примеры в поле Examples релевантных и нерелевантных вопросов.
3. Определи, упоминается ли в вопросе РЭУ напрямую или в целом университетская тематика.
4. Если вопрос не связан с экономическим образованием, университетами или обучением в России, он нерелевантен.
5. Дай четкий бинарный ответ:  
   - **True** (релевантен) — если вопрос явно или косвенно связан с РЭУ.  
   - **False** (нерелевантен) — если вопрос не имеет отношения к РЭУ.
6. В поле Reasoning напиши краткое объяснение своего решения.
7. Верни ответ в формате json с кавычками markdown

## Examples:

question: Какие программы обучения предлагает РЭУ им. Г. В. Плеханова?
reasoning: Вопрос напрямую касается образовательных программ РЭУ.
relevant: True

question: Какая студенческая жизнь в университете?
reasoning: Вопрос касается студенческой жизни в университете. Если он задан в контексте РЭУ, то релевантен.
relevant: True

question: Какой курс доллара прогнозируют на 2025 год?
reasoning: Вопрос относится к экономике в целом, но не связан с образовательными программами РЭУ.
relevant: False

question: Как получить грант на обучение в США?
reasoning: Вопрос касается международного образования, но не затрагивает РЭУ.
relevant: False

## Question: 
{question}

## Answer:
{format_instructions}
"""

reasonig_schema_reu = ResponseSchema(name="reasoning", description="Пояснение, почему вопрос релевантен или нерелевантен.", type="str")
answer_schema_reu = ResponseSchema(name="relevant", description="Бинарный ответ: True (релевантен) или False (нерелевантен).", type='bool')
response_schemas_relevant_to_reu = [reasonig_schema_reu, answer_schema_reu]
output_parser_relevant_to_reu = StructuredOutputParser.from_response_schemas(response_schemas_relevant_to_reu)
format_instructions_relevant_to_reu = output_parser_relevant_to_reu.get_format_instructions()
prompt_template_relevant_to_reu = PromptTemplate(
    input_variables=["question"], 
    template=template_relevant_to_reu,
    partial_variables={"format_instructions": format_instructions_relevant_to_reu}
)

template_general_response = """
Ты — эксперт, который анализирует информацию из интернета и отвечает на вопросы на основе полученных данных.

### Инструкции:
1. Внимательно прочитай вопрос из поля Question.
2. Проанализируй поле Context — он содержит информацию из интернета, релевантную запросу.
3. Если контекста недостаточно для точного ответа, отметь это в объяснении.
4. Раздели ответ на две части:
   - **resoning**: Кратко объясни, что говорит контекст по теме.
   - **answer**: Дай конкретный и обоснованный ответ.

### Question:
{question}

### Context:
{context}

### Answer:
{format_instructions}
"""

reasonig_schema_final = ResponseSchema(name="reasoning", description="Объясни, на основе чего ты дал такой ответ", type="str")
answer_schema_final = ResponseSchema(name="answer", description="Дай конкретный и обоснованный ответ в сжатом виде", type='str')
response_schemas_final = [reasonig_schema_final, answer_schema_final]
output_parser_final = StructuredOutputParser.from_response_schemas(response_schemas_final)
format_instructions_final = output_parser_final.get_format_instructions()
prompt_template_final = PromptTemplate(
    input_variables=["question", "context"], 
    template=template_general_response,
    partial_variables={"format_instructions": format_instructions_final}
)
