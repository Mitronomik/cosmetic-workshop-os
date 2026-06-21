from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HealthResponse:
    status: str
    app: str
    product_name: str
    mode: str
    version: str

    def model_dump(self) -> dict[str, str]:
        return asdict(self)
