from pydantic import BaseModel


class ScanRequest(BaseModel):
    path: str


class ScanResponse(BaseModel):
    scan_id: int
    status: str


class StatusResponse(BaseModel):
    scan_id: int
    status: str
    progress: int
    logs: str
