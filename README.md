# Write a TextService Module. It handles CRUD and dynamic processing for text type.
from __future__ import annotations

from typing import Any

import uvicorn
import pandas as pd
import sqlalchemy as sa
import uuid
import fastapi


class TextService:
    create_text: str = "INSERT INTO Text.content (id, text) VALUES (:id, :text);"
    read_text: str = "SELECT * FROM Text.content WHERE id = %(id)s;"
    update_text: str = "UPDATE Text.content SET text = :text WHERE id = :id;"
    delete_text: str = "DELETE FROM Text.content WHERE id = :id;"

    def __init__(self, hostname: str, port: int, username: str, password: str, database: str):
        # build a sql alchmey engine
        self.engine = sa.create_engine(f"mysql+mysqlconnector://{username}:{password}@{hostname}:{port}/{database}")
        self.db_connection = self.engine.connect()

    def create(self, text: str) -> str:
        global_id = str(uuid.uuid4())
        with self.db_connection.begin():
            self.db_connection.execute(sa.text(self.create_text), {"id": global_id, "text": text})
            return global_id

    def read(self, global_id: str) -> pd.DataFrame:
        return pd.read_sql(self.read_text, con=self.db_connection.connection, params={"id": global_id})

    def update(self, global_id: str, text: str) -> None:
        with self.db_connection.begin():
            self.db_connection.execute(sa.text(self.update_text), {"id": global_id, "text": text})

    def delete(self, global_id: str) -> None:
        with self.db_connection.begin():
            self.db_connection.execute(sa.text(self.delete_text), {"id": global_id})

    def process(self) -> str:
        # TODO: return text of different language, or text with different format e.g. font, color, ...
        pass


app = fastapi.FastAPI()
text_service: TextService | None = None


@app.post("/texts/init")
def init_text_service(hostname: str, port: int, username: str, password: str, database: str):
    global text_service
    text_service = TextService(hostname, port, username, password, database)
    return "Text Service Created"


@app.post("/texts/create")
def create_text(text: str) -> str:
    return text_service.create(text)


@app.get("/texts/{global_id}")
def read_text(global_id: str) -> dict[str, Any]:
    result: pd.DataFrame = text_service.read(global_id)
    # convert into dict
    return result.to_dict()


@app.put("/texts/{global_id}")
def update_text(global_id: str, text: str) -> None:
    text_service.update(global_id, text)


@app.delete("/texts/{global_id}")
def delete_text(global_id: str) -> None:
    text_service.delete(global_id)


# start the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9999)
