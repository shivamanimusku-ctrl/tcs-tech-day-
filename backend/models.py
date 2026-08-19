"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel
from typing import Optional, List, Any


class MachineOut(BaseModel):
    machine_id: str
    line_id: str
    machine_name: str
    machine_type: str
    status: str
    last_maintenance_date: Optional[str] = None
    maintenance_due_date: Optional[str] = None


class ReadingOut(BaseModel):
    id: int
    machine_id: str
    timestamp: str
    temperature: float
    vibration: float
    normal_temperature: float
    normal_vibration: float


class ProductionLogOut(BaseModel):
    id: int
    line_id: str
    timestamp: str
    production_target: int
    actual_production: int
    downtime_minutes: int


class QualityOut(BaseModel):
    id: int
    line_id: str
    timestamp: str
    defect_rate: float
    defect_count: int
    total_inspected: int
    result: str


class MaterialOut(BaseModel):
    material_id: str
    line_id: str
    name: str
    stock_level: float
    required_quantity: float
    availability_pct: float


class ShiftOut(BaseModel):
    shift_id: str
    line_id: str
    date: str
    shift_name: str
    operators_scheduled: int
    operators_present: int


class IssueNoteOut(BaseModel):
    note_id: str
    line_id: str
    machine_id: Optional[str] = None
    timestamp: str
    author_role: str
    text: str


class ProductionOrderOut(BaseModel):
    order_id: str
    line_id: str
    customer: str
    due_date: str
    priority: str
    units_target: int
    units_completed: int


class AlertOut(BaseModel):
    alert_id: str
    line_id: str
    machine_id: Optional[str] = None
    risk_score: float
    risk_level: str
    contributing_factors: Any  # JSON list
    business_impact: Any  # JSON dict
    ai_explanation: Optional[str] = None
    ai_recommendation: Optional[str] = None
    status: str
    priority_rank: Optional[int] = None
    priority_rationale: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


class DashboardSummary(BaseModel):
    overall_risk_pct: float
    production_health_pct: float
    active_alerts: int
    lines_at_risk: int
    total_lines: int
    total_machines: int
