# Backend Status

## Implemented

- FastAPI application with health check and all specified `/api` endpoints.
- Driving/walking GraphML loading, nearest-node lookup, and configurable flood-aware graph copies.
- Dijkstra routing with recommended, alternative, and unreachable shelter results.
- Simulated flood scenarios and manually editable edge status updates.
- Manual updates validated against graph edge IDs and persisted to
  `data/manual_flood_updates.json`.
- Critical bridge/cutset analysis as a separate network-vulnerability feature.
- OSMnx dataset generation for local driving and walking networks, CSV exports,
  demo shelters, and simulated scenario rows.
- Backend setup instructions in `README.md`; focused Dijkstra regression test.

## Setup and Validation

Run from the project root:

```powershell
python -m pip install -r backend/requirements.txt
python -m backend.scripts.generate_dataset
python -m uvicorn backend.app:app --reload
```

Dataset generation requires an internet connection to retrieve OpenStreetMap
data. Generated datasets are not committed and must exist before route requests
can be served. The API does not download data or generate datasets at startup.

Verification performed during implementation:

- Python source compilation.
- Dijkstra predecessor/path reconstruction regression test (requires dependencies).

All shelters and flood scenarios are simulated; the service is not suitable for
real emergency use.
