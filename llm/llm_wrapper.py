import base64
import json
import os
import re
import sys
import time
from collections import deque
from io import BytesIO

import requests
from decouple import config
from openai import OpenAI
from PIL import Image
from pydantic import BaseModel
from termcolor import colored


class CodeExecResult(BaseModel):
    text: str | None
    image: str | None


class ChatResponse(BaseModel):
    generated_code: str
    code_exec_result: CodeExecResult
    news_result: dict


assert os.path.isfile(".env"), ".env file not found!"

with open("code_interpreter_system_prompt.txt", "r") as f:
    CODE_INTERPRETER_SYSTEM_PROMPT = f.read()

IMAGE_DESCRIPTOR_SYSTEM_PROMPT = "너는 그래프 이미지에서 확인할 수 있는 정보를 찾아내는 역할을 할거야. 그래프 이미지를 생성하기 위한 파이썬 코드를 참고하여 그래프 이미지에서 확인할 수 있는 정보에 대해 설명해줘. 답변을 생성할 때는 반드시 한국어로 답변해."

EXTRACT_KEYWORD_SYSTEM_PROMPT = "너는 텍스트에서 하나의 키워드를 추출하는 역할을 할거야. 이 키워드는 구글에서 뉴스를 검색하는 용도로 사용할거야. 예를 들어서 [삼성전자 종가 기준 10년 그래프를 그려줘] 라는 사용자 입력이 있을 때, 여기서 '삼성전자'를 추출해줘야 해. 즉, 기업명을 추출해줘. 또 다른 예시로는 [KOSPI 200 지수 10년 그래프를 그려줘] 라는 사용자 입력이 있을 때, 여기서는 'KOSPI 200'을 추출해줘야 해."


def distinguish_and_handle(input_str):
    if hasattr(input_str, "content"):
        input_str = input_str.content

    base64_pattern = r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"

    if encoded_bytes_group := re.match(base64_pattern, input_str):
        try:
            encoded_bytes = encoded_bytes_group.group(0)
            decoded_bytes = base64.b64decode(encoded_bytes)
            img = Image.open(BytesIO(decoded_bytes))
            return encoded_bytes, img
        except Exception:
            return input_str, None
    return input_str, None


def get_financial_news(search_keyword: str):
    SERPER_API_KEY = config("SERPER_API_KEY")
    SERPER_URL = "https://google.serper.dev/news"

    payload = json.dumps(
        {
            "q": search_keyword,
            "location": "Seoul, Seoul, South Korea",
            "gl": "kr",
            "hl": "ko",
            "num": 5,
        }
    )
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.request("POST", SERPER_URL, headers=headers, data=payload)

    # json 형태로 변환
    return json.loads(response.text)


class GPTAgent:
    def __init__(self, system_message, model="gpt-4"):
        self.client = OpenAI(api_key=config("OPENAI_API_KEY"))
        self.model = model
        self.system_message = system_message
        self.chat_history = deque([])

    def chat(self, user_input):
        messages = [{"role": "system", "content": self.system_message}]
        for chat in self.chat_history:
            messages.append(chat)

        messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )

        assistant_message = response.choices[0].message.content

        self.chat_history.append({"role": "user", "content": user_input})
        self.chat_history.append({"role": "assistant", "content": assistant_message})

        return assistant_message


class GPTNewsGenerator:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.dialog = [{"role": "system", "content": EXTRACT_KEYWORD_SYSTEM_PROMPT}]
        self.client = OpenAI(api_key=config("OPENAI_API_KEY"))

        # 요약 키워드(검색어) 추출

    def extract_keyword(self, user_input: str):
        agent = GPTAgent(system_message=EXTRACT_KEYWORD_SYSTEM_PROMPT)
        keyword = agent.chat(f"[{user_input}]에서 키워드를 추출해주세요.")
        return keyword

    def chat(self, user_message: str):
        print(colored(user_message, "blue"))
        self.dialog.append({"role": "user", "content": user_message})
        total_start_time = time.time()
        search_keyword = ""
        search_keyword = self.extract_keyword(user_message)

        print(" === search_keyword : ", search_keyword)
        news_result = get_financial_news(search_keyword)
        print(" === news_result : ", news_result)
        print(f"=== Total Execution Time: {time.time() - total_start_time} ===")
        code_exec_result = CodeExecResult(text="", image="")

        return ChatResponse(
            generated_code="",
            code_exec_result=code_exec_result,
            news_result=news_result,
        )


class GPTCodeGenerator:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.dialog = [{"role": "system", "content": CODE_INTERPRETER_SYSTEM_PROMPT}]
        self.messages = [{"role": "system", "content": IMAGE_DESCRIPTOR_SYSTEM_PROMPT}]
        self.messages_2 = [{"role": "system", "content": EXTRACT_KEYWORD_SYSTEM_PROMPT}]
        self.client = OpenAI(api_key=config("OPENAI_API_KEY"))

    def chat_completion(self):
        dialog_stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.dialog,
            temperature=0,
            stream=True,
        )

        buffer = ""
        stop_condition_met = [False, False]

        for chunk in dialog_stream:
            content = chunk.choices[0].delta.content
            if content:
                buffer += content

                if "```python" in buffer:
                    stop_condition_met[0] = True
                elif stop_condition_met[0] and "```" in buffer:
                    break
        return buffer

    # 이미지(차트)에 대한 설명
    def descript_image(self, code_block: str, image_result: str):
        query_content = [
            {"type": "text", "text": code_block},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_result}"},
            },
        ]
        self.messages.append({"role": "user", "content": query_content})

        execution_start_time = time.time()

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            temperature=0.2,
        )

        execution_duration = time.time() - execution_start_time
        print(
            f"Generate image description successfully in {execution_duration}seconds."
        )

        return response.choices[0].message.content

    # 요약 키워드(검색어) 추출
    def extract_keyword(self, user_input: str):

        agent = GPTAgent(system_message=EXTRACT_KEYWORD_SYSTEM_PROMPT)
        keyword = agent.chat(f"[{user_input}]에서 키워드를 추출해주세요.")

        return keyword

    @staticmethod
    def execute_code(code: str) -> str:
        # code_exec API의 endpoint
        url = os.getenv("EXECUTOR_URL", "http://localhost:8081/execute")

        response = requests.post(url, json={"code": code})
        result = response.json().get("result", "")
        return distinguish_and_handle(result)

    @staticmethod
    def extract_code_blocks(text: str):
        pattern = r"```(?:python\n)?(.*?)```"
        code_blocks = re.findall(pattern, text, re.DOTALL)
        return [block.strip() for block in code_blocks]

    def chat(self, user_message: str, max_try: int = 1):
        print(colored(user_message, "blue"))
        self.dialog.append({"role": "user", "content": user_message})

        total_start_time = time.time()

        image_result = None
        text_result = None
        code_block = ""
        search_keyword = ""

        search_keyword = self.extract_keyword(user_message)

        print(" === search_keyword : ", search_keyword)

        news_result = get_financial_news(search_keyword)

        print(" === news_result : ", news_result)

        for i in range(max_try):
            generated_text = self.chat_completion()
            print(generated_text)
            print(f"==== {i}번째 generated text : {generated_text}=== \n")

            if "<done>" in generated_text:
                generated_text = generated_text.split("<done>")[0].strip()
                self.dialog.append({"role": "assistant", "content": generated_text})
                break

            if code_blocks := self.extract_code_blocks(generated_text):
                code_block = code_blocks[-1]
                code_output, img_raw = self.execute_code(code_block)

                if img_raw:
                    image_result = code_output
                    code_output = "image"  # TODO
                    text_result = self.descript_image(code_block, image_result)
                else:
                    text_result = code_output

                response_content = (
                    f"{generated_text}\n```Execution Result:\n{code_output}\n```"
                )
                self.dialog.append({"role": "assistant", "content": response_content})

                feedback_content = (
                    "Keep going. If you think debugging, tell me where you got wrong and suggest better code. "
                    "Need conclusion to question only in text (Do not leave result part alone). "
                    "If no further generation is needed, just say <done>."
                )
                self.dialog.append({"role": "user", "content": feedback_content})
            else:
                self.dialog.append({"role": "assistant", "content": generated_text})
                break

        print(f"=== text_result : {text_result} ===")
        code_exec_result = CodeExecResult(text=text_result, image=image_result)

        print(f"=== Total Execution Time: {time.time() - total_start_time} ===")

        return ChatResponse(
            generated_code=code_block,
            code_exec_result=code_exec_result,
            news_result=news_result,
        )


if __name__ == "__main__":
    gpt_generator = GPTCodeGenerator()
    gpt_news_generator = GPTNewsGenerator()
    for char in gpt_generator.chat("what is 10th fibonacci number?"):
        print(char, end="")
