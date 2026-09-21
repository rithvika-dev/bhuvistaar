import React, { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Popup,
  useMap,
  Tooltip,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  Layers,
  Search,
  CheckCircle2,
  AlertTriangle,
  Download,
  X,
  Loader2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listProjectDatasets } from "../api/datasets";
import { getDatasetFeatures } from "../api/gis";

function MapFlyController({ center, zoom }) {
  const map = useMap();
  if (center) {
    map.flyTo(center, zoom || 16, { duration: 1.0 });
  }
  return null;
}

function GISMap() {
  const { selectedProjectId } = useAuth();
  const [baseMap, setBaseMap] = useState("satellite");
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [flyToCoords, setFlyToCoords] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const defaultCenter = [12.9716, 77.5946]; // Bangalore / Default India coordinates

  const baseMapTiles = {
    satellite: {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      attribution: "&copy; Esri World Imagery",
    },
    positron: {
      url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
      attribution: "&copy; CARTO Positron",
    },
    osm: {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution: "&copy; OpenStreetMap",
    },
  };

  useEffect(() => {
    if (selectedProjectId) {
      loadProjectDatasets(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadProjectDatasets = async (projectId) => {
    try {
      const list = await listProjectDatasets(projectId);
      setDatasets(list || []);
      if (list && list.length > 0) {
        setSelectedDatasetId(list[0].id.toString());
        loadFeatures(list[0].id);
      }
    } catch (err) {
      console.error("Failed to load project datasets:", err);
    }
  };

  const loadFeatures = async (datasetId) => {
    setLoading(true);
    setGeoJsonData(null);
    try {
      const data = await getDatasetFeatures(datasetId);
      if (data && data.features && data.features.length > 0) {
        setGeoJsonData(data);
        // Fly map to first feature coordinates if available
        const firstGeom = data.features[0].geometry;
        if (firstGeom && firstGeom.coordinates) {
          let coords = null;
          if (firstGeom.type === "Point") coords = [firstGeom.coordinates[1], firstGeom.coordinates[0]];
          else if (firstGeom.type === "Polygon") coords = [firstGeom.coordinates[0][0][1], firstGeom.coordinates[0][0][0]];
          if (coords) setFlyToCoords(coords);
        }
      }
    } catch (err) {
      console.error("Failed to load dataset features:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDatasetChange = (id) => {
    setSelectedDatasetId(id);
    if (id) loadFeatures(id);
  };

  const featureStyle = (feature) => {
    const isSelected = selectedFeature?.id === feature.id;
    return {
      fillColor: isSelected ? "#2563eb" : "#7dd3fc",
      weight: isSelected ? 3 : 2.5,
      opacity: 1,
      color: isSelected ? "#f8fafc" : "#facc15",
      fillOpacity: isSelected ? 0.38 : 0.18,
      dashArray: isSelected ? "0" : "5 6",
      lineJoin: "round",
      lineCap: "round",
    };
  };

  const onEachFeature = (feature, layer) => {
    layer.on({
      click: () => setSelectedFeature(feature),
    });
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">GIS Map Viewer</h1>
            {loading && <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />}
          </div>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Interactive spatial viewer displaying live PostGIS layers.
          </p>
        </div>

        {/* Dataset selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Active Layer:</label>
          <select
            value={selectedDatasetId}
            onChange={(e) => handleDatasetChange(e.target.value)}
            className="bg-white border border-slate-200 rounded px-2.5 py-1 text-xs font-medium text-slate-800 focus:outline-none"
          >
            {datasets.length === 0 ? (
              <option value="">No Datasets Uploaded</option>
            ) : (
              datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name} (DS-{ds.id})
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      {/* Map Area */}
      <div className="relative bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden h-[74vh] flex">
        <div className="flex-1 h-full z-10 relative">
          <MapContainer center={defaultCenter} zoom={15} style={{ height: "100%", width: "100%" }} zoomControl={false}>
            <MapFlyController center={flyToCoords} zoom={16} />

            <TileLayer url={baseMapTiles[baseMap].url} attribution={baseMapTiles[baseMap].attribution} maxZoom={20} />

            {geoJsonData && <GeoJSON data={geoJsonData} style={featureStyle} onEachFeature={onEachFeature} />}
          </MapContainer>

          {/* Base Map Switcher */}
          <div className="absolute top-3 right-3 z-20 bg-white/95 p-1 rounded-md border border-slate-200 shadow text-xs flex items-center gap-1">
            <button
              onClick={() => setBaseMap("satellite")}
              className={`px-2 py-0.5 rounded text-[11px] font-medium ${baseMap === "satellite" ? "bg-[#166534] text-white" : "text-slate-600 hover:bg-slate-100"}`}
            >
              Satellite
            </button>
            <button
              onClick={() => setBaseMap("positron")}
              className={`px-2 py-0.5 rounded text-[11px] font-medium ${baseMap === "positron" ? "bg-[#166534] text-white" : "text-slate-600 hover:bg-slate-100"}`}
            >
              Light
            </button>
            <button
              onClick={() => setBaseMap("osm")}
              className={`px-2 py-0.5 rounded text-[11px] font-medium ${baseMap === "osm" ? "bg-[#166534] text-white" : "text-slate-600 hover:bg-slate-100"}`}
            >
              OSM
            </button>
          </div>
        </div>

        {/* Drawer */}
        {selectedFeature ? (
          <div className="w-80 h-full bg-white border-l border-slate-200 p-4 overflow-y-auto z-20 flex flex-col justify-between text-xs space-y-3">
            <div className="space-y-3">
              <div className="flex items-start justify-between pb-2 border-b border-slate-100">
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Feature ID: {selectedFeature.id || "N/A"}</h3>
                  <span className="text-[11px] text-slate-500 font-mono">Code: {selectedFeature.properties?.feature_code || selectedFeature.properties?.khasra_no || "N/A"}</span>
                </div>
                <button onClick={() => setSelectedFeature(null)} className="text-slate-400 hover:text-slate-600">
                  <X size={16} />
                </button>
              </div>

              <div className="space-y-1.5 text-slate-700">
                {selectedFeature.properties &&
                  Object.entries(selectedFeature.properties).map(([k, v]) => (
                    <div key={k} className="flex justify-between py-0.5 border-b border-slate-100">
                      <span className="text-slate-500 capitalize">{k.replace("_", " ")}:</span>
                      <strong className="truncate max-w-[150px]">{String(v)}</strong>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="hidden lg:flex w-64 h-full bg-slate-50 border-l border-slate-200 p-4 flex-col justify-center text-center text-xs text-slate-400">
            Click any polygon on the map to inspect PostGIS attributes.
          </div>
        )}
      </div>
    </div>
  );
}

export default GISMap;
