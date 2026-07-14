from pydantic import BaseModel, ConfigDict

class ScrobbleItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    duration_ms: int

class ScrobbleCurrentlyPlaying(BaseModel):
    model_config = ConfigDict(extra="ignore")
    progress_ms: int | None = None
    item: ScrobbleItem | None = None