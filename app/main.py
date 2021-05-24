import uvicorn
from fastapi import FastAPI

from .api import api_router
from .database import create_db_schema


create_db_schema()
app = FastAPI(title='fastapi-microblog')


app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
