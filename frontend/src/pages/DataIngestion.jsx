import React, { useState, useRef } from "react";
import {
  Upload,
  Map,
  Building2,
  FileText,
  Navigation,
  Satellite,
  Mountain,
  Database,
  CheckCircle2,
  AlertCircle,
  Trash2,
  ArrowRight,
  RefreshCw,
  Eye,
  X,
  Loader2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { createDataset, uploadDatasetFile, listProjectDatasets } from "../api/datasets";
import { processVectorDataset, processRaster } from "../api/gis";

function DataIngestion() {
  const { selectedProjectId } = useAuth();
  const fileInputRef = useRef(null);
  const [selectedSourceForUpload, setSelectedSourceForUpload] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);
  const [uploadQueue, setUploadQueue] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const dataSources = [
    { id: "drone", name: "Drone Survey", description: "Orthophoto, point clouds & aerial building footprints", icon: Upload, formats: "GeoTIFF, SHP, GeoJSON", acceptedMime: ".tif,.tiff,.shp,.geojson,.zip,.kml" },
    { id: "ori", name: "ORI", description: "High-resolution orthorectified satellite/aerial imagery", icon: Satellite, formats: "GeoTIFF, JPEG, PNG", acceptedMime: ".tif,.tiff,.jpg,.jpeg,.png" },
    { id: "cadastral", name: "Cadastral", description: "Revenue parcel boundaries and village map sheets", icon: Map, formats: "SHP, GeoJSON, GPKG", acceptedMime: ".shp,.geojson,.gpkg,.zip,.kml,.json" },
    { id: "municipal", name: "Municipal GIS", description: "Property tax polygons, building IDs & civic attributes", icon: Building2, formats: "SHP, GeoJSON, CSV", acceptedMime: ".shp,.geojson,.csv,.json,.zip" },
    { id: "revenue", name: "Revenue Records", description: "Ownership register, RoR / Jamabandi & mutation data", icon: FileText, formats: "CSV, XLSX, PDF", acceptedMime: ".csv,.xlsx,.xls,.pdf" },
    { id: "gnss", name: "GNSS / CORS", description: "High-precision rover survey coordinates & GCP benchmarks", icon: Navigation, formats: "CSV, TXT, GPKG", acceptedMime: ".csv,.txt,.gpkg,.dat" },
    { id: "ground_truth", name: "Ground Truth", description: "Field survey ground-truthing & physical verification logs", icon: Database, formats: "CSV, GeoJSON", acceptedMime: ".csv,.geojson,.json" },
    { id: "dsm", name: "DSM / DTM", description: "Digital Surface Model & elevation contours", icon: Mountain, formats: "GeoTIFF, DEM", acceptedMime: ".tif,.tiff,.dem,.img" },
  ];

  const showToast = (message, type = "success") => {
    setToastMessage({ text: message, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleUploadFiles = async (files, forcedSource = null) => {
    if (!files || files.length === 0) return;
    if (!selectedProjectId) {
      showToast("Please select or create a project first from the top header.", "error");
      return;
    }

    setIsUploading(true);
    const fileList = Array.from(files);

    for (const file of fileList) {
      const ext = file.name.split(".").pop().toLowerCase();
      const sourceType = forcedSource ? forcedSource.id : (["tif", "tiff"].includes(ext) ? "drone" : "cadastral");
      const datasetType = ["tif", "tiff", "dem", "img"].includes(ext) ? "raster" : "vector";

      const queueId = "temp-" + Date.now();
      const queueItem = {
        id: queueId,
        name: file.name,
        size: formatFileSize(file.size),
        source: forcedSource ? forcedSource.name : "Uploaded Data",
        status: "Uploading...",
        progress: 0,
        crs: "Auto-detecting...",
      };

      setUploadQueue((prev) => [queueItem, ...prev]);

      try {
        // 1. Create dataset record in backend DB
        const dataset = await createDataset(selectedProjectId, file.name, datasetType, sourceType);

        // 2. Upload file to backend server
        await uploadDatasetFile(dataset.id, file, (percent) => {
          setUploadQueue((prev) =>
            prev.map((item) => (item.id === queueId ? { ...item, progress: percent, status: `Uploading ${percent}%` } : item))
          );
        });

        // 3. Trigger GIS processing / inspection
        setUploadQueue((prev) =>
          prev.map((item) => (item.id === queueId ? { ...item, status: "Processing GIS features..." } : item))
        );

        let processRes = null;
        if (datasetType === "vector") {
          processRes = await processVectorDataset(dataset.id);
        } else {
          processRes = await processRaster(dataset.id);
        }

        setUploadQueue((prev) =>
          prev.map((item) =>
            item.id === queueId
              ? {
                  ...item,
                  id: dataset.id,
                  status: "Completed",
                  crs: processRes?.crs || "EPSG:4326",
                  featuresCount: processRes?.feature_count ? `${processRes.feature_count} features` : "Processed",
                }
              : item
          )
        );

        showToast(`Dataset "${file.name}" uploaded and processed successfully!`);
      } catch (err) {
        setUploadQueue((prev) =>
          prev.map((item) => (item.id === queueId ? { ...item, status: "Failed", error: err.friendlyMessage } : item))
        );
        showToast(`Failed to process "${file.name}": ${err.friendlyMessage}`, "error");
      }
    }
    setIsUploading(false);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files) {
      handleUploadFiles(e.dataTransfer.files, selectedSourceForUpload);
    }
  };

  const triggerGenericUpload = () => {
    setSelectedSourceForUpload(null);
    if (fileInputRef.current) {
      fileInputRef.current.accept = "*";
      fileInputRef.current.click();
    }
  };

  const triggerSourceUpload = (source) => {
    setSelectedSourceForUpload(source);
    if (fileInputRef.current) {
      fileInputRef.current.accept = source.acceptedMime;
      fileInputRef.current.click();
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toastMessage && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-lg border shadow-md text-xs font-semibold ${
          toastMessage.type === "error" ? "bg-red-50 text-red-800 border-red-200" : "bg-emerald-50 text-[#166534] border-emerald-200"
        }`}>
          {toastMessage.type === "error" ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
          <span>{toastMessage.text}</span>
        </div>
      )}

      <input type="file" ref={fileInputRef} onChange={(e) => handleUploadFiles(e.target.files, selectedSourceForUpload)} multiple className="hidden" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Data Ingestion</h1>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Upload real multi-source geospatial files directly to PostgreSQL/PostGIS.
          </p>
        </div>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragActive ? "border-[#166534] bg-emerald-50/50" : "border-slate-300 bg-white hover:border-slate-400"
        }`}
      >
        <div className="w-10 h-10 mx-auto rounded-lg bg-emerald-50 text-[#166534] flex items-center justify-center mb-3">
          {isUploading ? <Loader2 size={20} className="animate-spin text-emerald-600" /> : <Upload size={20} />}
        </div>

        <h2 className="text-sm font-bold text-slate-900">Upload Real Geospatial Land Records</h2>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          Select GeoJSON, Shapefile (.shp / .zip), GeoTIFF, GeoPackage (.gpkg), or CSV. Uploaded files are processed into PostGIS.
        </p>

        <div className="mt-4 flex items-center justify-center gap-3">
          <button
            onClick={triggerGenericUpload}
            disabled={isUploading}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
          >
            <Upload size={14} />
            {isUploading ? "Uploading..." : "Select Files"}
          </button>
        </div>

        <span className="mt-3 block text-[11px] text-slate-400">
          Max file size: 500 MB • Automatic UTM CRS Detection & PostGIS Processing
        </span>
      </div>

      {/* Queue */}
      {uploadQueue.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900">Recent Ingestion Stream</h3>
            <button onClick={() => setUploadQueue([])} className="text-xs text-red-600 hover:underline">Clear List</button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">File Name</th>
                  <th className="py-2.5 px-3">Source</th>
                  <th className="py-2.5 px-3">Size</th>
                  <th className="py-2.5 px-3">Detected CRS</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {uploadQueue.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-medium text-slate-900">{item.name}</td>
                    <td className="py-2.5 px-3">{item.source}</td>
                    <td className="py-2.5 px-3">{item.size}</td>
                    <td className="py-2.5 px-3 font-mono text-[11px]">{item.crs}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        item.status === "Completed" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" :
                        item.status === "Failed" ? "bg-red-50 text-red-800 border border-red-200" :
                        "bg-blue-50 text-blue-800 border border-blue-200"
                      }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Categories */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-slate-900">Supported Ingestion Categories</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {dataSources.map((source) => {
            const Icon = source.icon;
            return (
              <div key={source.id} className="bg-white rounded-lg border border-slate-200 p-4 flex flex-col justify-between hover:border-slate-300">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="w-8 h-8 rounded bg-emerald-50 text-[#166534] flex items-center justify-center">
                      <Icon size={16} />
                    </div>
                  </div>
                  <h3 className="text-xs font-bold text-slate-900">{source.name}</h3>
                  <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2 min-h-[30px]">{source.description}</p>
                </div>
                <button
                  onClick={() => triggerSourceUpload(source)}
                  className="mt-3 w-full py-1.5 px-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded text-xs font-medium flex items-center justify-center gap-1"
                >
                  <Upload size={12} /> Upload
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default DataIngestion;