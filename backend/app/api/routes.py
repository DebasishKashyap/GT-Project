"""API routes for Flood Evacuation Route Planning Backend.

Contains FastAPI endpoint handlers for all required functionality:
- Find evacuation routes
- Get shelters
- Get flood scenarios
- Apply manual flood updates
- Critical road analysis
"""

import logging
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from backend.app.schemas import (
    RouteRequest,
    RouteResponse,
    FloodUpdateRequest,
    ScenarioInfo,
    ScenariosResponse,
    ShelterInfo,
    SheltersResponse,
    CriticalRoad,
    CriticalRoadsResponse,
)
from backend.app.services.graph_service import GraphService
from backend.app.services.routing_service import RoutingService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["flood-evacuation"])


# Initialize services (will be wired with dependency injection in main app)
_graph_service: Optional[GraphService] = None
_routing_service: Optional[RoutingService] = None
_manual_updates: Dict[str, Dict[str, Any]] = {}


def get_graph_service() -> GraphService:
    """Get or initialize graph service."""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service


def get_routing_service() -> RoutingService:
    """Get or initialize routing service."""
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService(get_graph_service())
    return _routing_service


def _persist_manual_updates(graph_svc: GraphService) -> None:
    """Atomically persist manual road statuses for later API processes."""
    path = graph_svc.config.DATA_DIR / "manual_flood_updates.json"
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(_manual_updates, indent=2), encoding="utf-8")
    temporary_path.replace(path)


def _load_manual_updates(graph_svc: GraphService) -> None:
    """Load previously saved road statuses once when the graph service is created."""
    path = graph_svc.config.DATA_DIR / "manual_flood_updates.json"
    if path.exists() and not _manual_updates:
        try:
            updates = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(updates, dict):
                raise ValueError("Manual flood updates must be a JSON object")
            for edge_id, update in updates.items():
                if (
                    not isinstance(edge_id, str)
                    or not isinstance(update, dict)
                    or update.get("status") not in {"AVAILABLE", "PARTIALLY_FLOODED", "BLOCKED"}
                    or (
                        update.get("penalty_multiplier") is not None
                        and float(update["penalty_multiplier"]) <= 0
                    )
                ):
                    raise ValueError(f"Invalid persisted flood update for edge {edge_id}")
            _manual_updates.update(updates)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.error("Could not load persisted manual flood updates: %s", exc)
            raise RuntimeError("Could not load persisted manual flood updates") from exc


# ---- Route: Find Evacuation Routes ----

@router.post("/routes/find", response_model=RouteResponse)
async def find_evacuation_routes(request: RouteRequest):
    """
    Find evacuation routes from a starting location.

    Input:
        latitude: Starting location latitude
        longitude: Starting location longitude
        mode: Travel mode (driving or walking)
        scenario_id: Flood scenario (NORMAL, MODERATE_FLOOD, SEVERE_FLOOD)

    Process:
    1. Validate input parameters
    2. Find nearest graph node to starting location
    3. Select driving or walking graph
    4. Apply flood scenario (remove blocked roads, penalize flooded roads)
    5. Run Dijkstra from start node to all reachable nodes
    6. Calculate paths to all demo shelters
    7. Compare travel times and recommend fastest shelter
    8. Return route details and alternative shelters
    """
    try:
        # Initialize services
        graph_svc = get_graph_service()
        _load_manual_updates(graph_svc)
        routing_svc = get_routing_service()

        # Find evacuation routes
        result = routing_svc.find_evacuation_routes(
            start_lat=request.latitude,
            start_lon=request.longitude,
            travel_mode=request.mode,
            scenario_id=request.scenario_id,
            traffic_data={key: value["status"] for key, value in _manual_updates.items()},
            penalty_overrides={key: value["penalty_multiplier"] for key, value in _manual_updates.items()
                               if value["penalty_multiplier"] is not None},
        )

        # Build response
        response = RouteResponse(
            start_latitude=request.latitude,
            start_longitude=request.longitude,
            distance_to_start_node_m=result["distance_to_start_node_m"],
            travel_mode=result["travel_mode"],
            scenario_id=result["scenario_id"],
            recommended_shelter_id=result["recommended_shelter"]["shelter_id"] if result["recommended_shelter"] else None,
            recommended_shelter_name=result["recommended_shelter"]["name"] if result["recommended_shelter"] else None,
            recommended_shelter_travel_time_min=result["recommended_shelter"]["travel_time_min"] if result["recommended_shelter"] else None,
            recommended_shelter_distance_km=result["recommended_shelter"]["distance_km"] if result["recommended_shelter"] else None,
            alternative_shelters=[
                {
                    "shelter_id": s["shelter_id"],
                    "name": s["name"],
                    "travel_time_min": s["travel_time_min"],
                    "distance_km": s["distance_km"],
                    "is_demo": s["is_demo"],
                }
                for s in result["alternative_shelters"]
            ],
            unreachable_shelters=[
                {
                    "shelter_id": s["shelter_id"],
                    "name": s["name"],
                    "reason": s["reason"],
                    "is_demo": s["is_demo"],
                }
                for s in result["unreachable_shelters"]
            ],
            total_reachable_shelters=result["total_reachable_shelters"],
            total_unreachable_shelters=result["total_unreachable_shelters"],
            recommended_route_geometry=result["recommended_route_geometry"],
            success=True,
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in find_evacuation_routes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during route finding")


# ---- Route: Get Shelters ----

@router.get("/shelters", response_model=SheltersResponse)
async def get_shelters():
    """Get all demo shelters."""
    try:
        graph_svc = get_graph_service()
        routing_svc = get_routing_service()

        shelters = routing_svc._load_shelters()

        shelter_infos = [
            ShelterInfo(
                shelter_id=s.get("shelter_id", ""),
                name=s.get("name", ""),
                latitude=float(s.get("latitude", 0)),
                longitude=float(s.get("longitude", 0)),
                capacity=int(s.get("capacity", 0)),
                is_demo=s.get("is_demo", False),
            )
            for s in shelters
        ]

        return SheltersResponse(
            shelters=shelter_infos,
            success=True,
        )

    except Exception as e:
        logger.error(f"Error loading shelters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while loading shelters")


# ---- Route: Get Flood Scenarios ----

@router.get("/scenarios", response_model=ScenariosResponse)
async def get_scenarios():
    """Get flood scenario information."""
    try:
        scenarios_info = [
            ScenarioInfo(
                scenario_id="NORMAL",
                status="AVAILABLE",
                severity="none",
                penalty_multiplier=1.0,
            ),
            ScenarioInfo(
                scenario_id="MODERATE_FLOOD",
                status="PARTIALLY_FLOODED",
                severity="moderate",
                penalty_multiplier=1.5,
            ),
            ScenarioInfo(
                scenario_id="SEVERE_FLOOD",
                status="BLOCKED",
                severity="severe",
                penalty_multiplier=2.5,
            ),
        ]

        return ScenariosResponse(
            scenarios=scenarios_info,
            current_scenario="NORMAL",
            success=True,
        )

    except Exception as e:
        logger.error(f"Error loading scenarios: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while loading scenarios")


# ---- Route: Apply Manual Flood Update ----

@router.post("/flood/update")
async def apply_flood_update(request: FloodUpdateRequest):
    """
    Apply manual flood status update for a specific road edge.

    Allows demonstration of manual road status updates for flood scenarios.

    Parameters:
        edge_id: Edge ID to update
        status: New road status (AVAILABLE, PARTIALLY_FLOODED, BLOCKED)
        penalty_multiplier: Optional override for travel time penalty

    Returns:
        Success/failure status and confirmation
    """
    try:
        graph_svc = get_graph_service()
        if not graph_svc.is_graph_loaded():
            graph_svc.load_graphs()
        _load_manual_updates(graph_svc)
        if not graph_svc.edge_id_exists(request.edge_id):
            raise HTTPException(status_code=404, detail="Edge ID not found in the road networks")
        previous = _manual_updates.get(request.edge_id)
        _manual_updates[request.edge_id] = {
            "status": request.status,
            "penalty_multiplier": request.penalty_multiplier,
        }
        try:
            _persist_manual_updates(graph_svc)
        except OSError as exc:
            if previous is None:
                _manual_updates.pop(request.edge_id, None)
            else:
                _manual_updates[request.edge_id] = previous
            logger.error("Could not save manual flood update: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Could not persist manual flood update") from exc

        return {
            "success": True,
            "message": f"Flood update applied: edge {request.edge_id} status set to {request.status}",
            "edge_id": request.edge_id,
            "status": request.status,
            "penalty_multiplier": request.penalty_multiplier,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying flood update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while applying flood update")


# ---- Route: Critical Road Analysis ----

@router.get("/critical-roads", response_model=CriticalRoadsResponse)
async def get_critical_roads():
    """
    Perform critical road / cutset analysis on the road network.

    Identifies important roads whose removal may disconnect areas from
    evacuation shelters. This is a separate feature from the main routing
    algorithm and does not replace Dijkstra for route calculation.
    """
    try:
        graph_svc = get_graph_service()
        routing_svc = get_routing_service()

        # Load shelters CSV
        import pandas as pd
        shelters_path = graph_svc.config.SHELTERS_CSV

        if not shelters_path.exists():
            # Return empty results if no shelters loaded
            return CriticalRoadsResponse(
                critical_roads=[],
                analysis_summary={
                    "graph_nodes": 0,
                    "graph_edges": 0,
                    "shelter_nodes_count": 0,
                    "originally_reachable_nodes": 0,
                    "critical_bridges_count": 0,
                },
                success=True,
            )

        shelters_df = pd.read_csv(shelters_path)
        shelters = shelters_df.to_dict("records")

        # Load the driving graph
        if not graph_svc.is_graph_loaded():
            graph_svc.load_graphs()

        # Get shelter nodes from the graph (nearest graph nodes to shelter coordinates)
        shelter_nodes = []
        for shelter in shelters:
            try:
                lat = float(shelter.get("latitude", 0))
                lon = float(shelter.get("longitude", 0))
                # Find nearest node
                nearest_node, _ = graph_svc.find_nearest_node(lat, lon, "driving")
                shelter_nodes.append(nearest_node)
            except Exception:
                continue

        # Analyze critical roads
        from backend.app.algorithms.critical_roads import analyze_critical_roads
        result = analyze_critical_roads(
            graph_svc.get_graph("driving"),
            shelter_nodes=shelter_nodes,
            max_bridges_to_analyze=50
        )

        return CriticalRoadsResponse(
            critical_roads=result["critical_roads"],
            analysis_summary=result["analysis_summary"],
            success=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in critical road analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during critical road analysis")


# Attach router to app will happen in main.py