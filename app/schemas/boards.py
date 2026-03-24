from pydantic import BaseModel

class CreateBoard(BaseModel):
    id: str
    password: str
    title: str
    content: str
