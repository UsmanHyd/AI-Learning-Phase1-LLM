from pydantic import BaseModel, Field


class EchoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    repeat: int = Field(default=1, ge=1, le=5)


class EchoResponse(BaseModel):
    echoed: str
    length: int
