from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    product_name: str
    mode: str
    version: str
