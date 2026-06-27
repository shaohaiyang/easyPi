import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI

from src.web.routes import router

app = FastAPI(title="Travel Assistant")
app.include_router(router)


def main():
    uvicorn.run("src.app:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
