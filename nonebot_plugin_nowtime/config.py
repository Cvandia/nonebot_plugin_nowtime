from pydantic import BaseModel, Field


class Config(BaseModel):
    start_time: int = Field(default=0, ge=0, le=23)
    end_time: int = Field(default=24, ge=1, le=24)
