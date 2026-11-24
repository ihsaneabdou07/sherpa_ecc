from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ScenarioInput(BaseModel):
    scenario_name: str = Field(default="Scénario Maroc Base")
    ely_res_ratio: float = Field(default=0.75, ge=0.1, le=1.5)
    electrolyzer_capacity_mw: float = Field(default=100.0, gt=0, le=2000)
    local_lcoe_eur_per_kwh: Optional[float] = Field(default=None, gt=0, le=0.5)
    flh_res_hours: Optional[int] = Field(default=None, ge=500, le=8760)
    storage_duration_hours: float = Field(default=4.0, ge=1.0, le=8.0)
    ev_smart_charging_share: float = Field(default=0.40, ge=0.0, le=1.0)
    water_efficiency_factor: float = Field(default=1.0, ge=0.5, le=1.5)
    desalination_share: float = Field(default=0.70, ge=0.0, le=1.0)
    season: str = Field(default="annual", pattern="^(annual|winter|summer)$")

class TradeoffItem(BaseModel):
    axis: str
    status: str
    summary: str

class ScenarioOutput(BaseModel):
    scenario_name: str
    metrics: Dict[str, float]
    decision_axes: Dict[str, float]
    tradeoffs: List[TradeoffItem]
    assumptions_used: Dict[str, object]