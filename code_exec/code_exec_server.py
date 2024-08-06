import base64
import io
import os
import time

import matplotlib.pyplot as plt
from codeboxapi import CodeBox
from decouple import config
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

assert os.path.isfile(".env"), ".env file not found!"
os.environ["CODEBOX_API_KEY"] = config("CODEBOX_API_KEY")

app = FastAPI()


@app.post("/execute")
async def execute_code(request: Request):
    try:
        start_time = time.time()

        body = await request.json()
        code = body.get("code", "")

        print("Deserialization Time:", time.time() - start_time)
        print("Code extracted successfully")

        print(" === Code === ")
        print(code)

        """codebox 실행"""

        with CodeBox() as codebox:
            execution_start_time = time.time()
            print("Executing code with CodeBox")
            result = codebox.run(code)
            execution_duration = time.time() - execution_start_time
            print("Code executed successfully in", execution_duration, "seconds")

        total_time = time.time() - start_time
        print("Total time taken to process the request:", total_time, "seconds")

        return {"result": result.content}

        """로컬실행"""

        # # 그래프를 저장할 경로
        # graph_path = "graph.png"

        # # 코드 실행
        # local_vars = {}
        # exec(code, {}, local_vars)

        # # Prepare a BytesIO object to save the plot
        # buffer = io.BytesIO()

        # # 그래프를 저장하는 부분
        # if "plt" in local_vars:
        #     plt.savefig(buffer, format="png")
        #     plt.close()
        #     buffer.seek(0)

        #     # Base64 인코딩
        #     img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        #     # Total execution time
        #     total_time = time.time() - start_time
        #     print("Total time taken to process the request:", total_time, "seconds")

        #     # Return the base64-encoded image
        #     return {"image": img_base64}
        # else:
        #     raise HTTPException(
        #         status_code=400, detail="No matplotlib plot found in the provided code."
        #     )

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
