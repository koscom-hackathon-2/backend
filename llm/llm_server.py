import json

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from llm_dto import *
from llm_wrapper import GPTCodeGenerator

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.options("/chat-completion")
async def options():
    print("OPTIONS request received")
    return Response(content="OK", media_type="text/plain")


@app.post("/chat-completion")
async def chat_completion(request: ChatCompletionRequest):
    user_message = request.user_message

    async def generate():
        gpt_interpreter = GPTCodeGenerator()
        for char in gpt_interpreter.chat(user_message):
            print(char, end="")
            response = {
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": char},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(response)}\n\n"  # 서버 전송 이벤트 형식

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
