# Flood Evacuation Route Planning Using Graph Theory

## Project Development Specification

This document is the single source of instructions for building the project. Follow it step by step. Keep the implementation simple, correct, modular, and easy to explain in a college evaluation.

---

## 1. Project Goal

Build a web application that helps simulate flood evacuation route planning around **Tezpur University, Assam**.

The system must:

- Use a real road network from OpenStreetMap for the study area.
- Support both **driving** and **walking** modes.
- Allow the user to choose a starting location by **clicking the map or searching for a place**.
- Use simulated flood conditions for demonstration.
- Exclude blocked roads from routing.
- Apply additional travel-time penalties to partially flooded roads.
- Use **Dijkstra's Algorithm** as the main routing algorithm.
- Find the shortest safe route from the starting point to each reachable shelter.
- Recommend the shelter with the lowest estimated travel time.
- Show other reachable shelters as alternative evacuation options.
- Include a simple **critical road / cutset analysis** feature as an additional graph-theory concept.

Do not present the application as a real emergency system. Flood conditions and demo shelters must be clearly labelled as simulated unless verified data is later added.

---

## 2. Scope and Study Area

- Study area: approximately **20 km around Tezpur University, Napaam, Assam**.
- Road data: OpenStreetMap.
- Travel modes: Driving and Walking.
- Flood system:
  - Predefined simulated scenarios.
  - Manual road-status updates for demonstration.
- Shelters: Demo shelters clearly marked as demo data.

Important: do not download the road network on every user request. Generate and save the local dataset during setup.

---

## 3. Core Graph Model

Represent the road network as a weighted graph:

`G = (V, E)`

Where:

- `V` represents road junctions, locations, and shelter access points.
- `E` represents road segments.
- Edge weight represents estimated travel time.
- Driving graphs should preserve road direction and one-way restrictions.
- Walking graphs should use pedestrian-accessible connections.

Road status rules:

| Status | Routing behaviour |
|---|---|
| AVAILABLE | Use normal travel time |
| PARTIALLY_FLOODED | Use travel-time penalty |
| BLOCKED | Remove edge from routing |

Keep the flood penalty configurable, for example:

`PARTIALLY_FLOODED_MULTIPLIER = 1.5`

Do not hard-code this value throughout the project.

---

## 4. Algorithms

### Main Algorithm: Dijkstra's Algorithm

Use Dijkstra's Algorithm because travel-time weights are non-negative.

Workflow:

1. Receive the user's starting location.
2. Find the nearest valid node in the selected road graph.
3. Select the driving or walking graph.
4. Apply the selected flood scenario.
5. Remove BLOCKED roads.
6. Increase the effective weight of PARTIALLY_FLOODED roads.
7. Run Dijkstra from the starting node.
8. Calculate the shortest safe path to every reachable shelter.
9. Compare the final travel times.
10. Recommend the shelter with the lowest travel time.
11. Return route geometry, distance, travel time, and shelter information.

Do not use Yen's K-Shortest Paths or other advanced routing algorithms unless explicitly requested.

### Alternative Evacuation Options

Alternative options do not mean multiple paths to the same shelter.

Instead, use Dijkstra's result to show:

- Recommended shelter: lowest estimated travel time.
- Other reachable shelters: additional evacuation options.

This keeps the project simple and based on the algorithm taught in class.

### Additional Feature: Critical Road / Cutset Analysis

Add this only after the main routing system works.

Purpose:

Identify important road connections whose removal may disconnect parts of the network from evacuation shelters.

Suggested implementation:

1. Work with an undirected analysis view of the relevant road network.
2. Identify bridge edges or graph cuts that disconnect components.
3. For each critical road, test whether its removal makes one or more areas unable to reach a shelter.
4. Display critical roads separately on the map.

Important: clearly explain that this feature is for network vulnerability analysis. It does not replace Dijkstra's Algorithm for route calculation.

---

## 5. Recommended Technology Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Leaflet for the interactive map

### Backend

- Python
- FastAPI
- Pydantic for request and response validation

### Graph and Data Processing

- OSMnx for obtaining and processing OpenStreetMap road networks
- NetworkX for graph operations and Dijkstra's Algorithm
- Pandas for CSV data processing
- GeoPandas only if needed for geographic data processing

### Data Storage

Start with local files:

- GraphML for saved road graphs
- CSV for editable project datasets
- JSON or CSV for flood scenarios

Do not add PostgreSQL unless persistent user data or scenario history is actually needed.

---

## 6. Dataset Design

Use separate files to keep the project organized.

### `nodes.csv`

Suggested fields:

```text
node_id
latitude
longitude
```

### `roads.csv`

Suggested fields:

```text
edge_id
source_node
target_node
length_m
road_type
oneway
```

### `travel_times.csv`

Suggested fields:

```text
edge_id
mode
base_speed_kmh
travel_time_min
```

### `shelters.csv`

Suggested fields:

```text
shelter_id
name
latitude
longitude
capacity
is_demo
```

### `flood_scenarios.csv`

Suggested fields:

```text
scenario_id
edge_id
status
severity
penalty_multiplier
```

Required scenario examples:

- NORMAL
- MODERATE_FLOOD
- SEVERE_FLOOD

Do not claim simulated flood statuses are real-time flood information.

---

## 7. Dataset Generation Pipeline

Create a setup script that runs once or whenever the dataset needs to be regenerated.

Workflow:

```text
Define Tezpur University study area
        ↓
Download driving network
        ↓
Download walking network
        ↓
Clean and simplify graphs
        ↓
Assign stable edge identifiers
        ↓
Calculate length and travel-time attributes
        ↓
Save GraphML files
        ↓
Export required CSV files
        ↓
Create demo shelters
        ↓
Create simulated flood scenarios
```

Requirements:

- Store the generated graphs locally.
- Validate that all generated shelter points can connect to the relevant graph.
- Do not place demo shelters in impossible or inaccessible locations.
- Keep the dataset-generation script separate from the running API.

---

## 8. Backend Architecture

Recommended structure:

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── routes.py
│   │   ├── shelters.py
│   │   ├── scenarios.py
│   │   └── critical_roads.py
│   ├── services/
│   │   ├── graph_service.py
│   │   ├── routing_service.py
│   │   ├── flood_service.py
│   │   └── shelter_service.py
│   ├── algorithms/
│   │   ├── dijkstra.py
│   │   └── critical_roads.py
│   ├── schemas/
│   │   ├── route.py
│   │   └── scenario.py
│   └── utils/
│       └── geo.py
├── data/
│   ├── networks/
│   ├── nodes.csv
│   ├── roads.csv
│   ├── shelters.csv
│   └── flood_scenarios.csv
├── scripts/
│   └── generate_dataset.py
├── requirements.txt
└── README.md
```

Keep business logic out of API route files.

---

## 9. API Requirements

### Find evacuation routes

`POST /api/routes/find`

Input:

```json
{
  "latitude": 26.0,
  "longitude": 92.0,
  "mode": "driving",
  "scenario_id": "NORMAL"
}
```

Do not use these coordinates as fixed project data. They are only an API structure example.

Response should include:

- Recommended shelter.
- Travel time.
- Distance.
- Route geometry.
- Other reachable shelters.
- Unreachable shelters.

### Get shelters

`GET /api/shelters`

Return demo shelter data.

### Get flood scenarios

`GET /api/scenarios`

### Apply manual flood update

`POST /api/flood/update`

Allow status changes only for valid edge IDs.

### Critical road analysis

`GET /api/critical-roads`

Return critical roads and a simple explanation of their importance.

---

## 10. Frontend Requirements

The interface should be clean and simple.

### Main controls

- Travel mode selector: Driving / Walking.
- Starting location search.
- Click-to-select location on the map.
- Flood scenario selector.
- Find Safe Route button.

### Map

Show:

- Starting location marker.
- Demo shelter markers.
- Recommended route.
- Other reachable shelter routes only when selected.
- Flooded or blocked roads when relevant.
- Critical roads when the analysis layer is enabled.

### Results Panel

Show:

1. Recommended shelter.
2. Estimated travel time.
3. Total distance.
4. Route status.
5. Other reachable shelters.

Clearly label all simulated data.

---

## 11. Frontend Structure

```text
frontend/
├── app/
│   ├── page.tsx
│   └── layout.tsx
├── components/
│   ├── map/
│   │   ├── EvacuationMap.tsx
│   │   └── MapControls.tsx
│   ├── controls/
│   │   ├── LocationSearch.tsx
│   │   ├── TravelMode.tsx
│   │   └── ScenarioSelector.tsx
│   └── results/
│       └── RouteResults.tsx
├── services/
│   └── api.ts
├── types/
│   └── index.ts
└── lib/
    └── constants.ts
```

Avoid putting all map and routing logic into one component.

---

## 12. Development Order

Build the project in this exact order.

### Phase 1: Dataset

- Set up Python environment.
- Generate and save local driving and walking graphs.
- Generate CSV datasets.
- Create demo shelters.
- Create flood scenarios.
- Validate the dataset.

### Phase 2: Routing Engine

- Load saved graphs.
- Implement flood filtering.
- Implement travel-time penalties.
- Implement Dijkstra routing.
- Test routes to every shelter.
- Handle unreachable shelters correctly.

### Phase 3: API

- Build FastAPI application.
- Add request validation.
- Add route endpoints.
- Add clear error responses.
- Test API independently before frontend integration.

### Phase 4: Frontend

- Build the map.
- Add location selection.
- Add place search.
- Add travel mode and scenario controls.
- Connect the API.
- Display routing results.

### Phase 5: Critical Road Analysis

- Implement after routing is stable.
- Add a separate map layer.
- Keep this feature independent of the main route flow.

---

## 13. Error Handling Requirements

The project must handle these cases:

- Starting point is outside the supported study area.
- No nearby valid road node is found.
- Invalid travel mode.
- Invalid flood scenario.
- Invalid edge ID during manual updates.
- No shelter is reachable.
- Missing or corrupted dataset files.
- Road graph fails to load.

Never return an unhandled server exception to the user.

Use clear messages such as:

`No safe route to any shelter is available under the selected flood scenario.`

---

## 14. Testing Requirements

Before considering a feature complete, test:

### Routing

- Normal scenario.
- Partially flooded road.
- Blocked road.
- No reachable shelter.
- Driving mode.
- Walking mode.

### Data

- Every shelter has valid coordinates.
- Edge IDs are unique.
- Flood scenarios reference valid edges.
- Travel times are non-negative.

### API

- Valid request.
- Invalid request.
- Missing data.
- Unreachable route.

Do not skip tests just because the application appears to work visually.

---

## 15. Performance Rules

- Load graphs once during application startup where practical.
- Do not download OpenStreetMap data during route requests.
- Do not run expensive full-network analysis on every map interaction.
- Cache static data when appropriate.
- Keep API responses limited to data needed by the frontend.
- Start with correctness before optimization.

For a college-scale project, correctness and clear architecture are more important than unnecessary micro-optimizations.

---

## 16. Code Quality Rules

- Use TypeScript strict mode.
- Add Python type hints.
- Keep functions focused on one responsibility.
- Use environment variables for configuration.
- Do not hard-code API URLs, study-area values, or flood penalties in multiple files.
- Add short comments only where logic is not obvious.
- Avoid duplicate code.
- Format and lint code before finalizing.
- Do not introduce libraries unless they solve a real requirement.

---

## 17. UI and Presentation Rules

- Keep the design simple and professional.
- Prioritize map readability.
- Avoid excessive animations.
- Clearly distinguish:
  - Available roads.
  - Partially flooded roads.
  - Blocked roads.
  - Recommended route.
  - Demo shelters.
- Include a visible disclaimer that the project is an academic simulation.

---

## 18. Definition of Done

The project is complete when:

- A user can select a location by map click or search.
- A user can choose driving or walking.
- A user can select a flood scenario.
- The backend applies flood conditions correctly.
- Dijkstra finds the shortest safe route to each reachable shelter.
- The application recommends the best reachable shelter.
- Other reachable shelters are displayed as alternatives.
- No-route situations are handled properly.
- Demo shelters and simulated flood information are clearly labelled.
- The critical-road analysis works as a separate optional feature.
- The project can be explained clearly in a college presentation.

---

## Final Instruction to Development Agents

Do not attempt to build everything at once.

First inspect the existing repository and project structure. Then implement the project phase by phase. After each phase:

1. Run the relevant tests.
2. Fix errors before moving forward.
3. Avoid rewriting working code unnecessarily.
4. Keep changes small and logically grouped.
5. Reuse existing project conventions where possible.
6. Ask for clarification only when a decision cannot be safely inferred.

The core academic focus of this project is:

**Graph representation + flood-aware edge filtering + Dijkstra's shortest-path algorithm + evacuation shelter selection.**

Keep this focus clear throughout development.
