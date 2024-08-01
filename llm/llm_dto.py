from pydantic import BaseModel


class ChatCompletionRequest(BaseModel):
    user_message: str
