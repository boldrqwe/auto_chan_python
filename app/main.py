from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from service.ChatGPTService import ChatGPTClient  # Убедитесь, что путь правильный

app = FastAPI()

# Инициализация клиента
chat_gpt_client = ChatGPTClient()

# Модель для запроса
class ChatRequest(BaseModel):
    user_input: str

@app.get("/")
async def root():
    return {"message": "FastAPI работает!"}

@app.post("/chat")
async def chat_with_gpt(request: ChatRequest):
    try:
        response = await chat_gpt_client.generate_response(request.user_input)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
