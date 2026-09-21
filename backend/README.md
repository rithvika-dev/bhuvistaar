# BhuVistaar — Backend Platform

> **Problem Statement 26013 (SIH 2026)**: *Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management*

---

## 🏛️ System Architecture

BhuVistaar provides an end-to-end platform for ingesting, validating, georeferencing, matching, harmonizing, and exporting multi-source urban land record datasets (vector and raster/drone imagery).

```
 ┌────────────────┐     ┌────────────────┐
 │ Vector Datasets│     │ Raster/Drone/  │
 │ (GeoJSON, SHP) │     │ GeoTIFF/DSM    │
 └───────┬────────┘     └───────┬────────┘
         │                      │
         ├──────────────────────┘
         ▼
 ┌────────────────────────────────────────┐
 │ Ingestion, CRS Normalization & GCP     │
 │ Metric Projection (Auto-UTM EPSG)     │
 └───────────────────┬────────────────────┘
                     ▼
 ┌────────────────────────────────────────┐
 │ Intelligent AI Matching Engine         │
 │ (Spatial IoU + Proximity + RF Model)   │
 └───────────────────┬────────────────────┘
                     ▼
 ┌────────────────────────────────────────┐
 │ Conflict Detection & Topology Checks   │
 │ (Attribute, Identity, Overlaps, Gaps)  │
 └───────────────────┬────────────────────┘
                     ▼
 ┌────────────────────────────────────────┐
 │ Human-in-the-Loop Review & Provenance │
 └───────────────────┬────────────────────┘
                     ▼
 ┌────────────────────────────────────────┐
 │ Harmonized Datasets & Export Engine    │
 │ (GeoJSON, GeoPackage, CSV)             │
 └────────────────────────────────────────┘
```

---

## ⚡ Technology Stack

- **Framework**: FastAPI (Python 3.14 / 3.12)
- **Database**: PostgreSQL 18 + PostGIS 3.6 (GeoAlchemy2 + SQLAlchemy)
- **Background Tasks**: Celery + Redis (`redis://localhost:6379/0`)
- **GIS Processing**: GeoPandas, Shapely, PyProj, Rasterio, OpenCV
- **AI/ML Engine**: Random Forest Classifier (`scikit-learn`, `joblib`)
- **Security**: JWT Authentication (bcrypt), input sanitization, max upload protection

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 14+ with PostGIS extension enabled
- Redis server (optional, for Celery background tasks)

### 2. Environment Configuration
Copy `.env.example` to `.env` and configure:
```env
DATABASE_URL=postgresql://postgres:bhuvistaar@localhost:5432/bhuvistaar
SECRET_KEY=bhuvistaar-super-secret-key
REDIS_URL=redis://localhost:6379/0
UPLOAD_DIR=uploads
PROCESSED_DIR=processed
EXPORT_DIR=exports
```

### 3. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate        # On Windows
pip install -r requirements.txt
pip install celery redis opencv-python-headless pytest
```

### 4. Database Setup & Migrations
```bash
# Create PostGIS database 'bhuvistaar' in PostgreSQL
# Run database index & column type migrations
python -c "import sys; sys.path.insert(0, '.'); from app.migrations.add_indexes import run_migrations; run_migrations()"
```

### 5. Start Backend Server
```bash
uvicorn app.main:app --reload
```
API Documentation: `http://localhost:8000/docs`

### 6. Start Celery Worker (Optional)
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

---

## 🧪 Testing

Run full test suite:
```bash
python -m pytest tests/ -v
```

---

## 🚀 Demonstration Flow (30 Steps)

1. **Register User**: `POST /auth/register`
2. **Login**: `POST /auth/login`
3. **Create Project**: `POST /projects/`
4. **Create Source Dataset**: `POST /datasets/`
5. **Create Target Dataset**: `POST /datasets/`
6. **Upload Datasets**: `POST /datasets/{id}/upload`
7. **Inspect Vector**: `POST /gis/datasets/{id}/process`
8. **Inspect Raster**: `POST /raster/{id}/inspect`
9. **GCP Georeferencing**: `POST /georeferencing/{id}/gcps`
10. **Validate GCPs**: `POST /georeferencing/{id}/validate`
11. **Execute Georeferencing**: `POST /georeferencing/{id}/execute`
12. **Extract Raster Features**: `POST /raster/{id}/extract-features`
13. **Auto-Detect UTM CRS**: Metric distance calculation in meters
14. **Run AI Matching**: `POST /matching/run`
15. **Fetch Suggested Matches**: `GET /matching/{project_id}/pending`
16. **Review Match**: `POST /matching/{id}/review`
17. **Retrain ML Model**: `POST /ml/retrain`
18. **Detect Conflicts**: `POST /conflicts/detect`
19. **Resolve Conflicts**: `POST /conflicts/{id}/resolve`
20. **Validate Topology**: `POST /topology/validate`
21. **Suggest Field Mappings**: `POST /harmonization/suggest-mappings`
22. **Approve Mapping**: `POST /harmonization/{id}/resolve`
23. **Detect Version Changes**: `POST /change-detection/detect-versions`
24. **Generate Harmonized Features**: `POST /harmonized-features/generate`
25. **Review Harmonized Feature**: `POST /harmonized-features/{id}/review`
26. **View Lineage & Provenance**: `GET /harmonized-features/{project_id}`
27. **Export GeoJSON**: `POST /exports` (`export_type: "harmonized_features"`, `format: "geojson"`)
28. **Download Export**: `GET /exports/download/{id}`
29. **View Audit Trail**: `GET /audit/{project_id}`
30. **Run Full Pipeline**: `POST /pipeline/start`
