# BHUVISTAAR (भू-विस्तार)
### AI-Powered Multi-Source Urban Land Data Harmonization Platform
**Smart India Hackathon 2026 • Problem Statement SIH26013**  
*Department of Land Resources (DoLR) • Ministry of Rural Development, Government of India*

---

## 📌 Overview

**BHUVISTAAR** is an enterprise geospatial platform engineered to resolve land record fragmentation across urban jurisdictions in India. It harmonizes disparate spatial and tabular land data sources—including revenue cadastral maps, high-resolution drone orthophotos, municipal property tax registries, Jamabandi (Record of Rights / RoR), and high-precision GNSS/CORS control benchmarks—into a unified, topologically valid, and cryptographically verified canonical land record.

---

## 🏛️ Key Capabilities & Modules

| Module | Route | Description |
|---|---|---|
| **Dashboard Overview** | `/` | Real-time KPI metrics, harmonization pipeline progress, connected data sources, and quick-access conflict queue. |
| **Data Ingestion** | `/ingestion` | Multi-source drag-and-drop ingestion supporting 8 spatial/tabular formats (GeoTIFF, Shapefile, GeoJSON, GPKG, CSV, XLSX) with automated CRS detection and schema validation. Includes one-click demo dataset loader (Ward 17). |
| **Dataset Repository** | `/datasets` | Searchable spatial dataset catalog with metadata inspector, extent boundaries, CRS tags, and Grid/Table view toggles. |
| **Harmonization Pipeline** | `/harmonization` | 8-step automated spatial matching engine (CRS transformation, polygon IoU matching, attribute crosswalk matrix, and confidence scoring). |
| **Topology Validation** | `/topology` | Automated spatial geometry audit against 5 core DoLR rules (*Must Not Overlap, Must Not Have Gaps, No Self-Intersection, Sliver Tolerance, Closed Linear Rings*) with automated Shapely geometric healing. |
| **Interactive GIS Map** | `/map` | Multi-layer Leaflet GIS viewer supporting Satellite, Light, and OSM basemaps, vector overlays (Cadastral, Drone Footprints, GNSS Control Points, Conflict Markers), search fly-to, and parcel feature inspector drawer. |
| **Conflict Center** | `/conflicts` | Multi-source discrepancy adjudication center with side-by-side Source A vs. Source B comparison, area deltas, and officer resolution workflows. |
| **Change Detection** | `/changes` | Bi-temporal comparison (2020 Cadastral Baseline vs 2026 Drone Survey) identifying new unassessed buildings (42), boundary shifts (18), land-use conversions (63), and municipal property tax uplift (+₹23.4L/yr). |
| **Review Queue** | `/review` | Human-in-the-loop review interface for officers to inspect evidence, accept & ratify titles, reject anomalies, or dispatch ground-truth field surveys. |
| **Certified Records** | `/verified` | Registry of ratified land titles equipped with SHA-256 digital seals and printable **Harmonized Urban Land Title Certificates**. |
| **Executive Reports** | `/reports` | Downloadable executive dossiers covering harmonization summaries, CRS audits, conflict ledgers, and property tax impact reports. |
| **Audit Trail** | `/audit` | Immutable chronological event ledger recording all spatial mutations, CRS re-projections, and officer actions with SHA-256 hashes. |
| **System Settings** | `/settings` | Spatial matching tolerances (IoU threshold, vertex snapping buffer, Levenshtein fuzzy match ratio), CRS defaults (`EPSG:4326`), and custodian node configuration. |

---

## 🛠️ Technology Stack

- **Framework**: React 19 (JavaScript ES6+ / JSX)
- **Bundler & Build Tool**: Vite 8 with `@tailwindcss/vite`
- **Styling**: Tailwind CSS v4 (Pure utility styling, clean enterprise aesthetics)
- **Routing**: React Router DOM v7 (`BrowserRouter`, `Routes`, `Route`, `NavLink`)
- **Mapping & GIS**: Leaflet & React-Leaflet with Esri World Imagery, Carto Positron, and OSM vector layers
- **Icons**: Lucide React
- **Design System**: Government of India / DoLR Enterprise Theme — Forest Green (`#166534`), Emerald (`#22c55e`), Crisp White (`#ffffff`), and Slate neutrals

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the local development server:
   ```bash
   npm run dev
   ```
   The application will be available at `http://localhost:5173`.

### Production Build

To compile and optimize the application for production:
```bash
npm run build
```

To preview the production build locally:
```bash
npm run preview
```

---

## 📁 Directory Structure

```
frontend/
├── public/                     # Static assets
├── src/
│   ├── components/
│   │   └── layout/             # Sidebar, Header, and Main Layout shell
│   ├── pages/
│   │   ├── Dashboard.jsx       # Overview & KPI metrics
│   │   ├── DataIngestion.jsx   # Drag-and-drop multi-source upload & validation
│   │   ├── Datasets.jsx        # Spatial dataset repository
│   │   ├── Harmonization.jsx   # 8-step spatial matching & attribute crosswalk
│   │   ├── TopologyValidation.jsx # 5 DoLR topology rules & auto-repair
│   │   ├── GISMap.jsx          # Interactive multi-layer Leaflet GIS viewer
│   │   ├── Conflicts.jsx       # Discrepancy adjudication & side-by-side comparison
│   │   ├── ChangeDetection.jsx # Bi-temporal diff & tax uplift calculation
│   │   ├── Verification.jsx    # Human-in-the-loop officer review queue
│   │   ├── VerifiedRecords.jsx # Certified records & digital title certificate
│   │   ├── Reports.jsx         # Executive analytical dossiers & export
│   │   ├── AuditTrail.jsx      # Immutable SHA-256 event ledger
│   │   └── Settings.jsx        # CRS configuration & Geo-AI thresholds
│   ├── App.jsx                 # Route definitions (13 connected pages)
│   ├── index.css               # Tailwind CSS v4 import & typography resets
│   └── main.jsx                # Application entry point
├── package.json                # Project dependencies & scripts
├── vite.config.js              # Vite configuration with Tailwind plugin
└── README.md                   # Project documentation
```

---

## 🛡️ Standards & Compliance

- **DILRMP**: Fully compliant with the *Digital India Land Records Modernization Programme* data standards.
- **OGC Compliant**: Built around Open Geospatial Consortium (OGC) Simple Feature Access standards and WGS 84 (`EPSG:4326`) canonical projection.
- **Offline-First Architecture**: Client-side data storage and processing ensures operational continuity even in remote field conditions without active internet connectivity.
