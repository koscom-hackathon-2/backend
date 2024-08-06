import logging
import os
import time

from codeboxapi import CodeBox
from decouple import config
from fastapi import FastAPI, HTTPException, Request

assert os.path.isfile(".env"), ".env file not found!"
os.environ["CODEBOX_API_KEY"] = config("CODEBOX_API_KEY")

session_id = None

app = FastAPI()

@app.on_event("startup")
def startup_event():
    global session_id

    codebox = CodeBox()
    codebox.start()

    with open("./fetch/LSFetcher.py", "r") as f:
        raw_python_file = f.read()
    codebox.upload("LSFetcher.py", raw_python_file)

    with open("./fetch/BaseFetcher.py", "r") as f:
        raw_base_file = f.read()
    codebox.upload("BaseFetcher.py", raw_base_file)

    with open("./fetch/.env", "r") as f:
        env_file = f.read()
    codebox.upload(".env", env_file)

    codebox.install("httpx")
    codebox.install("python-decouple")

    session_id = codebox.session_id

@app.post("/execute")
async def execute_code(request: Request):
    try:
        start_time = time.time()

        body = await request.json()
        code = body.get("code", "")
        
        print("Deserialization Time:", time.time() - start_time)
        print("Code extracted successfully")

        # Restore session
        codebox = CodeBox.from_id(session_id)
        logging.warning(codebox.list_files())

        execution_start_time = time.time()
        print("Executing code with CodeBox")
        result = codebox.run(code)
        execution_duration = time.time() - execution_start_time
        print("Code executed successfully in", execution_duration, "seconds")

        total_time = time.time() - start_time
        print("Total time taken to process the request:", total_time, "seconds")

        return {"result": result.content}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
