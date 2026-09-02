import uuid
import logging
from fastapi import FastAPI, HTTPException 

from pydantic import BaseModel
from typing import List , Optional

from Backend.src.api.telemetry import setup_telemetry
setup_telemetry()

from Backend.src.graph.workflow import graph


from dotenv import load_dotenv
load_dotenv(override = True)

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("brand-video-server")

app = FastAPI(
    title = "Brand Video Compliance API",
    description = "This API checks the compliance of brand videos based on various criteria.",
    version = "1.0.0",
)

class AuditRequest(BaseModel):
    video_url :str

class ComplianceResult(BaseModel):
    severity : str
    category : str
    description : str

class AuditResponse(BaseModel):
    video_id : str
    session_id : str
    status : str
    compliance_results : List[ComplianceResult]
    final_report : str

@app.post("/audit", response_model = AuditResponse)

async def audit_video(request = AuditRequest):
    session_id = str(uuid.uuid4())
    video_id = f"vid_{session_id[:8]}"

    initial_input = {
        "video_url" : request.video_url,
        "video_id" : video_id,
        "compliance_results" : [],
        "error" : [],
    }

    try:
        final_state = graph.invoke(initial_input)
        return AuditResponse(
            video_id  = final_state.get("video_id"),
            session_id = session_id,
            status = final_state.get("status"),
            compliance_results = final_state.get("compliance_results" , []),
            final_report = final_state.get("final_report"),
        )
    except Exception as e:
        logger.error(f"Error in Backend  for fetching AuditResponse due to {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed : {str(e)}",
        )

@app.get("/health")

def health():
    return {
        "status" : "healthy " , "servies" : "brand-video-compliance"
    }