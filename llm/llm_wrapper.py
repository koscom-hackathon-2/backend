import base64
import os
import re
from io import BytesIO

import openai
import requests
from decouple import config
from PIL import Image
from termcolor import colored

# Constants
assert os.path.isfile(".env"), ".env file not found!"
openai.api_key = config("OPENAI_API_KEY")

CODE_INTERPRETER_SYSTEM_PROMPT = "You are code-interpreter GPT that can execute code by generation of code in ```python\n(here)```"

def distinguish_and_handle(input_str):
    if hasattr(input_str, 'content'):
        input_str = input_str.content

    base64_pattern = r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"
    
    if re.match(base64_pattern, input_str):
        try:
            decoded_bytes = base64.b64decode(input_str)
            img = Image.open(BytesIO(decoded_bytes))
            return img, input_str
        except Exception:
            return input_str, None
    return input_str, None

class GPTCodeGenerator:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.dialog = [{"role": "system", "content": CODE_INTERPRETER_SYSTEM_PROMPT}]

    def chat_completion(self):
        dialog_stream = openai.ChatCompletion.create(
            model=self.model,
            messages=self.dialog,
            temperature=0.1,
            top_p=1.0,
            stream=True,
        )

        buffer = ""
        stop_condition_met = [False, False]

        for chunk in dialog_stream:
            content = chunk["choices"][0].get("delta", {}).get("content")
            if content:
                buffer += content
                yield from content

                if "```python" in buffer:
                    stop_condition_met[0] = True
                elif stop_condition_met[0] and "```" in buffer:
                    stop_condition_met[1] = True
                
                if len(buffer) > 100:
                    buffer = buffer[-100:]

                if stop_condition_met[1]:
                    break

    @staticmethod
    def execute_code(code: str) -> str:
        # code_exec API의 endpoint
        url = "http://127.0.0.1:8080/execute"
        response = requests.post(url, json={"code": code})
        result = response.json().get("result", "")
        return distinguish_and_handle(result)

    @staticmethod
    def extract_code_blocks(text: str):
        pattern = r"```(?:python\n)?(.*?)```"
        code_blocks = re.findall(pattern, text, re.DOTALL)
        return [block.strip() for block in code_blocks]

    def chat(self, user_message: str, max_try: int = 6):
        print(colored(user_message, "green"), end=" ")
        self.dialog.append({"role": "user", "content": user_message})

        for _ in range(max_try):
            generated_text = ""
            for char in self.chat_completion():
                generated_text += char
                yield char

            code_blocks = self.extract_code_blocks(generated_text)
            if code_blocks:
                code_output, img_raw = self.execute_code(code_blocks[0])

                response_content = f"{generated_text}\n```Execution Result:\n{code_output}\n```"
                yield f"```Execution Result:\n{code_output}\n```"
                self.dialog.append({"role": "assistant", "content": response_content})

                feedback_content = ("Keep going. If you think debugging, tell me where you got wrong and suggest better code. "
                                    "Need conclusion to question only in text (Do not leave result part alone). "
                                    "If no further generation is needed, just say <done>.")
                self.dialog.append({"role": "user", "content": feedback_content})
            else:
                if "<done>" in generated_text:
                    generated_text = generated_text.split("<done>")[0].strip()
                self.dialog.append({"role": "assistant", "content": generated_text})
                break

if __name__ == "__main__":
    gpt_generator = GPTCodeGenerator()
    for char in gpt_generator.chat("what is 555th fibonacci number?"):
        print(char, end="")
