"""Pydantic schemas for Flood Evacuation Route Planning API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Request/Response schemas for routing

class RouteRequest(BaseModel):
    """Request model for finding evacuation routes."""

    latitude: float = Field(
        description="Starting location latitude",
        ge=-90,
        le=90
    )
    longitude: float = Field(
        description="Starting location longitude",
        ge=-180,
        le=180
    )
    mode: str = Field(
        description="Travel mode: driving or walking",
        pattern="^(driving|walking)$"
    )
    scenario_id: str = Field(
        description="Flood scenario: NORMAL, MODERATE_FLOOD, or SEVERE_FLOOD",
        pattern="^(NORMAL|MODERATE_FLOOD|SEVERE_FLOOD)$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 26.1022,
                "longitude": 92.1986,
                "mode": "driving",
                "scenario_id": "NORMAL"
            }
        }


class RouteResponse(BaseModel):
    """Response model for route finding."""

    start_latitude: float = Field(description="Starting latitude")
    start_longitude: float = Field(description="Starting longitude")
    distance_to_start_node_m: float = Field(description="Distance to nearest graph node")
    travel_mode: str = Field(description="Travel mode: driving or walking")
    scenario_id: str = Field(description="Flood scenario")

    # Recommended shelter
    recommended_shelter_id: Optional[str] = Field(
        default=None,
        description="Recommended shelter ID (fastest route)"
    )
    recommended_shelter_name: Optional[str] = Field(
        default=None,
        description="Recommended shelter name"
    )
    recommended_shelter_travel_time_min: Optional[float] = Field(
        default=None,
        description="Estimated travel time to recommended shelter"
    )
    recommended_shelter_distance_km: Optional[float] = Field(
        default=None,
        description="Distance to recommended shelter in km"
    )

    # Alternative shelters
    alternative_shelters: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Other reachable shelters as alternative evacuation options"
    )

    # Unreachable shelters
    unreachable_shelters: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Shelters that cannot be reached under current flood scenario"
    )

    # Route metadata
    total_reachable_shelters: int = Field(
        default=0,
        description="Number of reachable shelters"
    )
    total_unreachable_shelters: int = Field(
        default=0,
        description="Number of unreachable shelters"
    )

    # Route geometry
    recommended_route_geometry: Optional[List[Dict[str, float]]] = Field(
        default=None,
        description="Route geometry as list of {latitude, longitude} points"
    )

    # Response status
    success: bool = Field(default=True, description="Request was successful")
    message: Optional[str] = Field(
        default=None,
        description="Human-readable status message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_latitude": 26.1022,
                "start_longitude": 92.1986,
                "distance_to_start_node_m": 150.5,
                "travel_mode": "driving",
                "scenario_id": "NORMAL",
                "recommended_shelter_id": "Tezpur_University_Main_Campus",
                "recommended_shelter_name": "Tezpur University Main Campus",
                "recommended_shelter_travel_time_min": 12.5,
                "recommended_shelter_distance_km": 5.2,
                "alternative_shelters": [],
                "unreachable_shelters": [],
                "total_reachable_shelters": 2,
                "total_unreachable_shelters": 3,
                "success": True,
                "message": "Route found successfully"
            }
        }


# Flood update request

class FloodUpdateRequest(BaseModel):
    """Request model for manual flood status update."""

    edge_id: str = Field(
        description="Edge ID to update",
    )
    status: str = Field(
        description="New road status: AVAILABLE, PARTIALLY_FLOODED, or BLOCKED",
        pattern="^(AVAILABLE|PARTIALLY_FLOODED|BLOCKED)$"
    )
    penalty_multiplier: Optional[float] = Field(
        default=None,
        description="Travel time penalty multiplier (overrides default for PARTIALLY_FLOODED)",
        gt=0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "edge_id": "Road_0_1_0",
                "status": "PARTIALLY_FLOODED",
                "penalty_multiplier": 1.5
            }
        }


# Flood scenario schema

class ScenarioInfo(BaseModel):
    """Schema for flood scenario information."""

    scenario_id: str = Field(description="Scenario identifier")
    status: str = Field(description="Road status behavior")
    severity: str = Field(description="Severity description")
    penalty_multiplier: float = Field(description="Travel time penalty multiplier")

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "MODERATE_FLOOD",
                "status": "PARTIALLY_FLOODED",
                "severity": "moderate",
                "penalty_multiplier": 1.5
            }
        }


class ScenariosResponse(BaseModel):
    """Response model for flood scenarios."""

    scenarios: List[ScenarioInfo]
    current_scenario: str
    success: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "scenarios": [
                    {"scenario_id": "NORMAL", "status": "AVAILABLE", "severity": "none", "penalty_multiplier": 1.0},
                    {"scenario_id": "MODERATE_FLOOD", "status": "PARTIALLY_FLOODED", "severity": "moderate", "penalty_multiplier": 1.5},
                    {"scenario_id": "SEVERE_FLOOD", "status": "BLOCKED", "severity": "severe", "penalty_multiplier": 2.5}
                ],
                "current_scenario": "NORMAL"
            }
        }


# Shelter schema

class ShelterInfo(BaseModel):
    """Schema for shelter information."""

    shelter_id: str = Field(description="Shelter identifier")
    name: str = Field(description="Shelter name")
    latitude: float = Field(description="Latitude")
    longitude: float = Field(description="Longitude")
    capacity: int = Field(description="Capacity")
    is_demo: bool = Field(description="Whether this is demo/simulated data")

    class Config:
        json_schema_extra = {
            "example": {
                "shelter_id": "Tezpur_University_Main_Campus",
                "name": "Tezpur University Main Campus",
                "latitude": 26.1022,
                "longitude": 92.1986,
                "capacity": 500,
                "is_demo": True
            }
        }


class SheltersResponse(BaseModel):
    """Response model for shelters."""

    shelters: List[ShelterInfo]
    success: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "shelters": [
                    {
                        "shelter_id": "Tezpur_University_Main_Campus",
                        "name": "Tezpur University Main Campus",
                        "latitude": 26.1022,
                        "longitude": 92.1986,
                        "capacity": 500,
                        "is_demo": True
                    }
                ]
            }
        }


# Critical road analysis schema

class CriticalRoad(BaseModel):
    """Schema for a single critical road."""

    source_node: int = Field(description="Source junction node ID")
    target_node: int = Field(description="Target junction node ID")
    length_m: float = Field(description="Road segment length in meters")
    road_type: str = Field(description="Road type classification")
    oneway: bool = Field(description="Whether the road is one-way")
    affected_node_count: int = Field(description="Number of nodes disconnected if blocked")
    impact_score: int = Field(description="Impact ranking score")
    is_bridge: bool = Field(description="Whether this is a bridge edge")
    explanation: str = Field(description="Human-readable explanation of importance")

    class Config:
        json_schema_extra = {
            "example": {
                "source_node": 12345,
                "target_node": 12346,
                "length_m": 250.0,
                "road_type": "residential",
                "oneway": False,
                "affected_node_count": 45,
                "impact_score": 90,
                "is_bridge": True,
                "explanation": "Road segment between nodes 12345 and 12346 is a BRIDGE in the road network. If this road becomes blocked (e.g., by flooding), 45 locations will lose ALL access to evacuation shelters. This makes it a HIGH PRIORITY road for flood monitoring and protection."
            }
        }


class CriticalRoadsResponse(BaseModel):
    """Response model for critical road analysis."""

    critical_roads: List[CriticalRoad]
    analysis_summary: Dict[str, Any]
    success: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "critical_roads": [],
                "analysis_summary": {
                    "graph_nodes": 500,
                    "graph_edges": 800,
                    "shelter_nodes_count": 5,
                    "originally_reachable_nodes": 450,
                    "critical_bridges_count": 0
                }
            }
        }