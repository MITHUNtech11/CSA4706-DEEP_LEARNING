"""
Pydantic Schemas for API Requests and Responses (Pydantic v2 Compliant).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(..., json_schema_extra={"example": "DR_302"})
    password: Optional[str] = Field(None, json_schema_extra={"example": "doc@123"})


class BreakGlassRequest(BaseModel):
    user_id: str = Field(..., json_schema_extra={"example": "DR_302"})
    justification: str = Field(
        ..., 
        json_schema_extra={"example": "Patient in acute cardiogenic shock; emergency access required."}
    )


class ChatQueryRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "What is the diagnosis and phone number for patient P-1042?"})
    token: Optional[str] = Field(None, description="Signed JWT Bearer token")


class PolicyApproveRequest(BaseModel):
    approver_id: str = Field(..., json_schema_extra={"example": "compliance_director_02"})


class SimulateTamperRequest(BaseModel):
    entry_index: int = Field(1, json_schema_extra={"example": 1})
