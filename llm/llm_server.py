import json

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from llm_wrapper import ChatResponse, GPTCodeGenerator
from pydantic import BaseModel

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

class ChatCompletionRequest(BaseModel):
    user_message: str

@app.options("/chat-completion")
async def options():
    print("OPTIONS request received")
    return Response(content="OK", media_type="text/plain")


@app.post("/chat-completion")
async def chat_completion(request: ChatCompletionRequest) -> ChatResponse:
    user_message = request.user_message

    gpt_interpreter = GPTCodeGenerator()
    return gpt_interpreter.chat(user_message)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
