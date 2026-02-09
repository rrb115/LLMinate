from pydantic import BaseModel


class ScanRequest(BaseModel):
    path: str
    api_key: str | None = None
    api_provider: str | None = None


class GitScanRequest(BaseModel):
    url: str
    api_key: str | None = None
    api_provider: str | None = None


class ScanResponse(BaseModel):
    scan_id: int
    status: str


class StatusResponse(BaseModel):
    scan_id: int
    status: str
    progress: int
    logs: str
