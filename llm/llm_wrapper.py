import base64
import os
import re
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

assert os.path.isfile(".env"), ".env file not found!"

CODE_INTERPRETER_SYSTEM_PROMPT = "You are code-interpreter GPT that can execute code by generation of code in ```python\n(here)```. You can access real-time stock data through y-finance library."

def distinguish_and_handle(input_str):
    if hasattr(input_str, 'content'):
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

class GPTCodeGenerator:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.dialog = [{"role": "system", "content": CODE_INTERPRETER_SYSTEM_PROMPT}]
        self.client = OpenAI(api_key=config("OPENAI_API_KEY"))

    def chat_completion(self):
        dialog_stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.dialog,
            temperature=0,
            top_p=1.0,
            stream=True,
        )

        buffer = ""
        stop_condition_met = [False, False]

        for chunk in dialog_stream:
            content = chunk.choices[0].delta.content
            if content:
                buffer += content
                # yield from content

                if "```python" in buffer:
                    stop_condition_met[0] = True
                elif stop_condition_met[0] and "```" in buffer:
                    # stop_condition_met[1] = True
                    break
                
                # TODO
                # if len(buffer) > 100:
                #     buffer = buffer[-100:]

                # if stop_condition_met[1]:
                #     break
        return buffer

    @staticmethod
    def execute_code(code: str) -> str:
        # code_exec API의 endpoint
        url = "http://127.0.0.1:8081/execute"
        response = requests.post(url, json={"code": code})
        result = response.json().get("result", "")
        return distinguish_and_handle(result)

    @staticmethod
    def extract_code_blocks(text: str):
        pattern = r"```(?:python\n)?(.*?)```"
        code_blocks = re.findall(pattern, text, re.DOTALL)
        return [block.strip() for block in code_blocks]

    def chat(self, user_message: str, max_try: int = 6):
        print(colored(user_message, "blue"))
        self.dialog.append({"role": "user", "content": user_message})

        for _ in range(max_try):
            generated_text = self.chat_completion()
            print(generated_text) # TODO
            # TODO
            # for char in self.chat_completion():
            #     generated_text += char
            #     yield char

            if "<done>" in generated_text:
                generated_text = generated_text.split("<done>")[0].strip()
                self.dialog.append({"role": "assistant", "content": generated_text})
                break

            if code_blocks := self.extract_code_blocks(generated_text):
                code_block = code_blocks[0]
                code_output, img_raw = self.execute_code(code_block)

                # yield f"```Execution Result:\n{code_output}\n```" TODO

                image_result = None
                text_result = None

                if img_raw:
                    img_raw.save("temp.png") # code for test
                    image_result = code_output
                    code_output = "image" # TODO
                else:
                    text_result = code_output

                response_content = f"{generated_text}\n```Execution Result:\n{code_output}\n```"
                self.dialog.append({"role": "assistant", "content": response_content})

                feedback_content = ("Keep going. If you think debugging, tell me where you got wrong and suggest better code. "
                                    "Need conclusion to question only in text (Do not leave result part alone). "
                                    "If no further generation is needed, just say <done>.")
                self.dialog.append({"role": "user", "content": feedback_content})
            else:
                self.dialog.append({"role": "assistant", "content": generated_text})
                break

        print(f"{text_result=}  {image_result}") # TODO
        code_exec_result = CodeExecResult(text= text_result, image=image_result)
        return ChatResponse(generated_code=code_block, code_exec_result=code_exec_result)

if __name__ == "__main__":
    gpt_generator = GPTCodeGenerator()
    for char in gpt_generator.chat("what is 555th fibonacci number?"):
        print(char, end="")
