"""
Backend configuration and settings for Flood Evacuation Route Planning.

This module contains configuration constants and settings used throughout
 the backend application. All sensitive values and project-specific settings
 are centralized here for easy management.
"""

import os
from pathlib import Path
from typing import Dict, Set


class Settings:
    """Application settings and configuration constants."""

    # Project information
    PROJECT_NAME = "Flood Evacuation Route Planning"
    VERSION = "1.0.0"
    DESCRIPTION = "Academic flood evacuation route planning simulator around Tezpur University, Assam"

    # Study area configuration
    # Tezpur University coordinates: ~26.1022°N, 92.1986°E (Napaam area, 20km radius)
    STUDY_CENTER_LAT = 26.1022
    STUDY_CENTER_LON = 92.1986
    STUDY_RADIUS_KM = 20.0

    # File paths (relative to backend directory)
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    NETWORKS_DIR = DATA_DIR / "networks"

    # Dataset file paths
    NODES_CSV = DATA_DIR / "nodes.csv"
    ROADS_CSV = DATA_DIR / "roads.csv"
    TRAVEL_TIMES_CSV = DATA_DIR / "travel_times.csv"
    SHELTERS_CSV = DATA_DIR / "shelters.csv"
    FLOOD_SCENARIOS_CSV = DATA_DIR / "flood_scenarios.csv"

    # Network file paths
    DRIVING_NETWORK_GRAPHML = NETWORKS_DIR / "tezu_roads_drive.graphml"
    WALKING_NETWORK_GRAPHML = NETWORKS_DIR / "tezu_roads_walk.graphml"

    # Travel configuration
    DRIVING_SPEED_KMH = 40
    WALKING_SPEED_KMH = 5
    PARTIALLY_FLOODED_MULTIPLIER = 1.5
    SEVERE_FLOOD_MULTIPLIER = 2.5

    # Flood scenario IDs (simulated scenarios)
    SCENARIOS: Set[str] = {"NORMAL", "MODERATE_FLOOD", "SEVERE_FLOOD"}

    # Network types
    NETWORK_TYPES: Set[str] = {"driving", "walking"}

    # Travel modes (used interchangeably with network types)
    TRAVEL_MODES: Set[str] = {"driving", "walking"}

    # Road status values
    ROAD_STATUSES: Dict[str, str] = {
        "AVAILABLE": "normal travel time",
        "PARTIALLY_FLOODED": "apply configurable travel-time penalty",
        "BLOCKED": "exclude the road from routing"
    }

    # Error messages for consistent API responses
    ERROR_MESSAGES = {
        "OUTSIDE_STUDY_AREA": "Starting location is outside the supported study area",
        "NO_VALID_NODE": "No nearby valid road node found at the selected location",
        "INVALID_TRAVEL_MODE": "Invalid travel mode. Must be 'driving' or 'walking'",
        "INVALID_SCENARIO": "Invalid flood scenario",
        "NO_REACHABLE_SHELTER": "No safe route to any shelter is available under the selected flood scenario",
        "MISSING_DATASETS": "Required dataset files are missing or corrupted",
        "FAILED_LOAD_GRAPH": "Failed to load the road network",
        "INVALID_EDGE_ID": "Invalid edge ID provided for manual flood update"
    }

    # API response configurations
    MAX_RESULTS_PER_REQUEST = 100
    MIN_TRAVEL_TIME_MINUTES = 0.1

    # Logging configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # API settings
    HOST = "127.0.0.1"
    PORT = 8000
    WORKERS = 1

    # Processing configuration
    WALKING_PENALTY_FOR_CURVATURE = 1.2

    # Display configuration
    MAX_SEARCH_RESULTS = 10

    @classmethod
    def get_study_area_center(cls) -> tuple[float, float]:
        """Get the study area center coordinates as (latitude, longitude)."""
        return (cls.STUDY_CENTER_LAT, cls.STUDY_CENTER_LON)

    @classmethod
    def get_network_path(cls, network_type: str) -> Path:
        """Get the file path for a specific network type."""
        if network_type == "driving":
            return cls.DRIVING_NETWORK_GRAPHML
        elif network_type == "walking":
            return cls.WALKING_NETWORK_GRAPHML
        else:
            raise ValueError(f"Invalid network type: {network_type}")

    @classmethod
    def validate_scenario_id(cls, scenario_id: str) -> bool:
        """Check if the provided scenario ID is valid."""
        return scenario_id in cls.SCENARIOS

    @classmethod
    def validate_travel_mode(cls, mode: str) -> bool:
        """Check if the provided travel mode is valid."""
        return mode in cls.TRAVEL_MODES

    @classmethod
    def is_demo_shelter(cls, shelter_id: str, shelters_df) -> bool:
        """Check if a shelter is demo data."""
        try:
            shelter_row = shelters_df[shelters_df["shelter_id"] == shelter_id]
            if not shelter_row.empty:
                return shelter_row.iloc[0].get("is_demo", False)
        except Exception:
            pass
        return False

    @classmethod
    def is_demo_shelter_by_name(cls, name: str, shelters_df) -> bool:
        """Check if a shelter is demo data by name."""
        try:
            shelter_row = shelters_df[shelters_df["name"] == name]
            if not shelter_row.empty:
                return shelter_row.iloc[0].get("is_demo", False)
        except Exception:
            pass
        return False

    @classmethod
    def get_flood_penalty(cls, scenario_id: str) -> float:
        """Get the penalty multiplier for a given flood scenario."""
        if scenario_id == "MODERATE_FLOOD":
            return cls.PARTIALLY_FLOODED_MULTIPLIER
        elif scenario_id == "SEVERE_FLOOD":
            return cls.SEVERE_FLOOD_MULTIPLIER
        else:  # NORMAL
            return 1.0

    @classmethod
    def get_scenario_status(cls, scenario_id: str) -> str:
        """Get the status description for a given flood scenario."""
        if scenario_id == "MODERATE_FLOOD":
            return "PARTIALLY_FLOODED"
        elif scenario_id == "SEVERE_FLOOD":
            return "BLOCKED"
        else:  # NORMAL
            return "AVAILABLE"

    @classmethod
    def get_filtered_network_file(cls, network_type: str) -> str:
        """Get the name of a filtered network file for a network type."""
        return f"tezu_roads_{network_type}_filtered.graphml"

    @classmethod
    def get_temp_network_dir(cls) -> Path:
        """Get the directory for temporary network files."""
        return cls.DATA_DIR / "temp_networks"

    @classmethod
    def ensure_directories_exist(cls):
        """Ensure all required directories exist."""
        cls.NETWORKS_DIR.mkdir(parents=True, exist_ok=True)
        cls.get_temp_network_dir().mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)


# Environment variable overrides
def load_env_vars():
    """Load environment variables and override settings if needed."""
    if "FLOOD_EVAC_PORT" in os.environ:
        Settings.PORT = int(os.environ["FLOOD_EVAC_PORT"])

    if "FLOOD_EVAC_STUDY_RADIUS_KM" in os.environ:
        Settings.STUDY_RADIUS_KM = float(os.environ["FLOOD_EVAC_STUDY_RADIUS_KM"])

    if "FLOOD_EVAC_DRIVING_SPEED_KMH" in os.environ:
        Settings.DRIVING_SPEED_KMH = float(os.environ["FLOOD_EVAC_DRIVING_SPEED_KMH"])

    if "FLOOD_EVAC_WALKING_SPEED_KMH" in os.environ:
        Settings.WALKING_SPEED_KMH = float(os.environ["FLOOD_EVAC_WALKING_SPEED_KMH"])


# Load environment variables on module import
load_env_vars()