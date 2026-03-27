from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser



class FinanceAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model="qwen3-vl:8b"
        )
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位專業的財務分析師，請根據提供的報表進行分析。")
        ])
    
    def chat_ollama(self, data:dict, scoring:bool=False, history:list=[]):
        llm = ChatOpenAI(
            api_key="ollama",
            base_url=settings.OLLAMA_V1_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.9
        )
        system_content = settings.PATIENT_SYSTEM_PROMPT
        user_content = settings.PATIENT_USER_PROMPT
        if scoring:
            system_content = settings.SCORING_SYSTEM_PROMPT
            user_content = settings.SCORING_USER_PROMPT
        prompt = [
            ("system", system_content),
            ("human", user_content),
        ]
        if history:
            prompt.extend(history)
        prompt = ChatPromptTemplate.from_messages(prompt)

        if scoring:
            chain = prompt | llm | JsonOutputParser()
        else:
            chain = prompt | llm.bind(
                stop=["。", "\n", "！"], 
                max_tokens=20
            )
        response = chain.invoke(data)
        return response
        