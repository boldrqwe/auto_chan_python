import logging
from fastapi import FastAPI, HTTPException
from service.ChatGPTService import ChatGPTClient, UserInput  # Убедитесь, что путь правильный

app = FastAPI()

# Инициализация клиента
chat_gpt_client = ChatGPTClient()
logger = logging.getLogger()

@app.get("/")
async def root():
    return {"message": "FastAPI работает!"}


# Эндпоинт для общения с ChatGPT
@app.post("/chat")
async def chat_endpoint(user_input: UserInput):
    """
    Эндпоинт для отправки промпта и сообщения игрока в ChatGPT.
    """
    try:
        response = await chat_gpt_client.generate_response(
            player_message=user_input.player_message,
            prompt=user_input.prompt
        )
        return {"response": response}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Необработанная ошибка: {e}")
        raise HTTPException(status_code=500, detail="Произошла ошибка на сервере.")
