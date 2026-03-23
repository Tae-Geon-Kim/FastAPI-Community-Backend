from pydantic import BaseModel

class CreateBoard(BaseModel):
    name: str
    pw: str
    title: str
    content: str
