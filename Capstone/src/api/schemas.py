"""
Pydantic Schemas for API Requests and Responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(..., example="DR_302")


class BreakGlassRequest(BaseModel):
    user_id: str = Field(..., example="DR_302")
    justification: str = Field(..., example="Patient in acute cardiogenic shock; emergency access required.")


class ChatQueryRequest(BaseModel):
    query: str = Field(..., example="What is the diagnosis and phone number for patient P-1042?")
    token: Optional[str] = Field(None, description="Signed JWT Bearer token")


class PolicyApproveRequest(BaseModel):
    approver_id: str = Field(..., example="compliance_director_02")


class SimulateTamperRequest(BaseModel):
    entry_index: int = Field(1, example=1)
