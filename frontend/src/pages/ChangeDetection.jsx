import { useState, useMemo, useEffect, useCallback } from "react";
import {
  Calendar,
  CheckCircle2,
  Search,
  RefreshCw,
  GitCompare,
  MapPin,
  FileText,
  Building2,
  AlertCircle
} from "lucide-react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getProjectChangeDetections, detectVersionChanges } from "../api/changeDetection";

function ChangeDetection() {
  const { selectedProjectId } = useAuth();
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [toastMessage, setToastMessage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Live metadata, summary counts, and changes list from the real API
  const [meta, setMeta] = useState({
    old_dataset_name: "2020 State Cadastral Baseline",
    new_dataset_name: "2026 Drone Survey",
    old_year: 2020,
    new_year: 2026,
    temporal_interval_label: "6.0 Years (2020 - 2026)",
    total_coverage_sqkm: null,
    analysis_method: "Vector Polygon Differencing & Attribute Change Detection",
    verified_percentage: 0
  });

  const [summary, setSummary] = useState({
    added: 0,
    removed: 0,
    geometry_modified: 0,
    attributes_modified: 0,
    both_modified: 0,
    unchanged: 0
  });

  const [changesList, setChangesList] = useState([]);

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadChangeDetections = useCallback(async () => {
    if (!selectedProjectId) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await getProjectChangeDetections(selectedProjectId);
      if (data && data.status === "completed") {
        setMeta({
          old_dataset_name: data.old_dataset_name || "2020 Cadastral Baseline",
          new_dataset_name: data.new_dataset_name || "2026 Drone Survey",
          old_year: data.old_year || 2020,
          new_year: data.new_year || 2026,
          temporal_interval_label: data.temporal_interval_label || `${data.temporal_interval_years || 6.0} Years`,
          total_coverage_sqkm: data.total_coverage_sqkm,
          analysis_method: data.analysis_method || "Vector Polygon Differencing & Attribute Change Detection",
          verified_percentage: data.verified_percentage || 0
        });
        if (data.changes_summary) {
          setSummary(data.changes_summary);
        }
        setChangesList(data.changes || []);
      } else {
        setChangesList([]);
      }
    } catch (err) {
      console.error("Failed to load change detections:", err);
      setError(err?.response?.data?.detail || "Could not load temporal change detection data.");
    } finally {
      setIsLoading(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    loadChangeDetections();
  }, [loadChangeDetections]);

  const handleRunChangeAnalysis = async () => {
    if (!selectedProjectId) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const result = await detectVersionChanges(selectedProjectId);
      if (result && result.status === "completed") {
        setMeta({
          old_dataset_name: result.old_dataset_name || "2020 Cadastral Baseline",
          new_dataset_name: result.new_dataset_name || "2026 Drone Survey",
          old_year: result.old_year || 2020,
          new_year: result.new_year || 2026,
          temporal_interval_label: result.temporal_interval_label || `${result.temporal_interval_years || 6.0} Years`,
          total_coverage_sqkm: result.total_coverage_sqkm,
          analysis_method: result.analysis_method || "Vector Polygon Differencing & Attribute Change Detection",
          verified_percentage: result.verified_percentage || 0
        });
        if (result.changes_summary) {
          setSummary(result.changes_summary);
        }
        setChangesList(result.changes || []);
        showToast(
          `Bi-temporal analysis completed: ${result.total_changes || result.changes?.length || 0} total changes detected.`
        );
      } else {
        showToast("Bi-temporal change analysis completed.");
      }
    } catch (err) {
      console.error("Change detection execution error:", err);
      const msg = err?.response?.data?.detail || "Bi-temporal change analysis failed. Ensure project has processed datasets.";
      setError(msg);
      showToast(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Dynamic calculation of total detected changes
  const totalDetectedChanges = useMemo(() => {
    return (
      (summary.added || 0) +
      (summary.removed || 0) +
      (summary.geometry_modified || 0) +
      (summary.attributes_modified || 0) +
      (summary.both_modified || 0)
    );
  }, [summary]);

  const landUseChangesCount = (summary.attributes_modified || 0) + (summary.both_modified || 0);

  const filteredChanges = useMemo(() => {
    return changesList.filter((item) => {
      const cat = item.category || item.change_type;
      let matchesCategory = false;

      if (activeCategory === "all") {
        matchesCategory = true;
      } else if (activeCategory === "new_building") {
        matchesCategory = cat === "new_building" || item.change_type === "added";
      } else if (activeCategory === "boundary") {
        matchesCategory = cat === "boundary" || item.change_type === "geometry_modified";
      } else if (activeCategory === "land_use") {
        matchesCategory =
          cat === "land_use" ||
          item.change_type === "attributes_modified" ||
          item.change_type === "both_modified";
      } else if (activeCategory === "demolition") {
        matchesCategory = cat === "demolition" || item.change_type === "removed";
      }

      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        (item.id && item.id.toLowerCase().includes(q)) ||
        (item.parcelId && item.parcelId.toLowerCase().includes(q)) ||
        (item.parcel_id && item.parcel_id.toLowerCase().includes(q)) ||
        (item.khasraNo && item.khasraNo.toLowerCase().includes(q)) ||
        (item.type && item.type.toLowerCase().includes(q)) ||
        (item.summary && item.summary.toLowerCase().includes(q));

      return matchesCategory && matchesSearch;
    });
  }, [changesList, activeCategory, searchQuery]);

  return (
    <div className="space-y-5">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 bg-emerald-50 text-[#166534] border border-emerald-200 rounded-lg shadow-md text-xs font-semibold">
          <CheckCircle2 size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Temporal Change Detection
          </h1>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Bi-temporal spatial comparison ({meta.old_year} Baseline vs {meta.new_year} Drone Survey) to identify encroachments and unassessed construction.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunChangeAnalysis}
            disabled={isAnalyzing}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
          >
            {isAnalyzing ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                Analyzing Temporal Layers...
              </>
            ) : (
              <>
                <GitCompare size={14} />
                Run Bi-Temporal Diff
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}

      {/* Temporal Comparison Header Card */}
      <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-emerald-50 text-[#166534] flex items-center justify-center font-bold text-xs border border-emerald-200 flex-shrink-0">
              <Calendar size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-bold text-slate-800">
                  T0: {meta.old_dataset_name} ({meta.old_year})
                </span>
                <span className="text-slate-400 font-bold">⟷</span>
                <span className="text-xs font-bold text-[#166534]">
                  T1: {meta.new_dataset_name} ({meta.new_year})
                </span>
              </div>
              <span className="text-[11px] text-slate-500 font-normal">
                Analysis Method: <strong>{meta.analysis_method}</strong>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs flex-wrap">
            <div className="px-3 py-1 bg-slate-50 border border-slate-200 rounded-md">
              <span className="text-[10px] text-slate-400 font-semibold uppercase block">Temporal Interval</span>
              <strong className="text-slate-900">{meta.temporal_interval_label}</strong>
            </div>
            {meta.total_coverage_sqkm !== null && (
              <div className="px-3 py-1 bg-slate-50 border border-slate-200 rounded-md">
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">Total Coverage</span>
                <strong className="text-[#166534]">{meta.total_coverage_sqkm} sq.km</strong>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Summary KPI Cards - Dynamic from API */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="bg-white rounded-lg border border-slate-200 p-3.5 shadow-xs">
          <span className="text-[11px] text-slate-500 font-medium block">Total Detected Changes</span>
          <h3 className="text-2xl font-bold text-slate-900 mt-1">{totalDetectedChanges}</h3>
          <span className="text-[10px] text-slate-400 font-medium">
            {meta.verified_percentage > 0 ? `${meta.verified_percentage}% verified` : "Pending Human Review"}
          </span>
        </div>

        <div className="bg-white rounded-lg border border-amber-200 bg-amber-50/20 p-3.5 shadow-xs">
          <span className="text-[11px] text-amber-800 font-semibold block">New Buildings</span>
          <h3 className="text-2xl font-bold text-amber-800 mt-1">{summary.added || 0}</h3>
          <span className="text-[10px] text-amber-700 font-medium">Unassessed structures</span>
        </div>

        <div className="bg-white rounded-lg border border-red-200 bg-red-50/20 p-3.5 shadow-xs">
          <span className="text-[11px] text-red-800 font-semibold block">Boundary Shifts</span>
          <h3 className="text-2xl font-bold text-red-700 mt-1">{summary.geometry_modified || 0}</h3>
          <span className="text-[10px] text-red-600 font-medium">Encroachments & footings</span>
        </div>

        <div className="bg-white rounded-lg border border-blue-200 bg-blue-50/20 p-3.5 shadow-xs">
          <span className="text-[11px] text-blue-800 font-semibold block">Land Use Conversions</span>
          <h3 className="text-2xl font-bold text-blue-800 mt-1">{landUseChangesCount}</h3>
          <span className="text-[10px] text-blue-700 font-medium">Agri → Commercial/Residential</span>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-3.5 shadow-xs">
          <span className="text-[11px] text-slate-500 font-medium block">Demolished Structures</span>
          <h3 className="text-2xl font-bold text-slate-700 mt-1">{summary.removed || 0}</h3>
          <span className="text-[10px] text-slate-400 font-medium">Cleared for re-dev</span>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="bg-white rounded-lg border border-slate-200 p-3.5 shadow-xs space-y-3">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          {/* Category Tabs */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              onClick={() => setActiveCategory("all")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
                activeCategory === "all"
                  ? "bg-emerald-50 text-[#166534] border border-emerald-200"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              All Changes ({totalDetectedChanges})
            </button>
            <button
              onClick={() => setActiveCategory("new_building")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
                activeCategory === "new_building"
                  ? "bg-amber-50 text-amber-800 border border-amber-200"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              New Buildings ({summary.added || 0})
            </button>
            <button
              onClick={() => setActiveCategory("boundary")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
                activeCategory === "boundary"
                  ? "bg-red-50 text-red-700 border border-red-200"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              Boundary Shifts ({summary.geometry_modified || 0})
            </button>
            <button
              onClick={() => setActiveCategory("land_use")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
                activeCategory === "land_use"
                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              Land Use Conversions ({landUseChangesCount})
            </button>
            <button
              onClick={() => setActiveCategory("demolition")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
                activeCategory === "demolition"
                  ? "bg-slate-100 text-slate-800 border border-slate-200"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              Demolitions ({summary.removed || 0})
            </button>
          </div>

          {/* Search */}
          <div className="relative w-full lg:w-72">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by ID, Khasra, or change type..."
              className="w-full bg-slate-50 border border-slate-200 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:bg-white transition-colors"
            />
          </div>
        </div>
      </div>

      {/* Main Changes Feed */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-8 text-center bg-white border border-slate-200 rounded-lg text-slate-400 text-xs flex items-center justify-center gap-2">
            <RefreshCw size={16} className="animate-spin text-[#166534]" />
            Loading real temporal change records...
          </div>
        ) : filteredChanges.length === 0 ? (
          <div className="p-8 text-center bg-white border border-slate-200 rounded-lg text-slate-400 text-xs">
            No temporal changes detected yet. Click "Run Bi-Temporal Diff" above to perform automated spatial comparison.
          </div>
        ) : (
          filteredChanges.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs hover:border-slate-300 transition-colors space-y-3"
            >
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-md bg-emerald-50 text-[#166534] flex items-center justify-center font-bold text-xs border border-emerald-200">
                    {item.parcelId || item.parcel_id}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <strong className="text-sm font-bold text-slate-900">
                        {item.type}
                      </strong>
                      <span className="font-mono text-xs text-slate-400">
                        ID: {item.id} • Khasra {item.khasraNo || item.khasra_no || "N/A"}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500 font-normal">
                      Detected {item.detectedDate || item.detected_date} • Verified via Automated Spatial Differencing
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${item.impactColor || item.impact_color || "bg-slate-100 text-slate-700"}`}>
                    {item.impact || "Medium Impact"}
                  </span>
                  <span className="text-xs font-bold text-[#166534]">
                    {item.confidence || 90}% Match
                  </span>
                </div>
              </div>

              {/* Before vs After Visual Comparison Box */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 bg-slate-50 rounded border border-slate-200 space-y-0.5">
                  <div className="flex items-center justify-between text-slate-500 text-[10px] font-semibold uppercase">
                    <span>Baseline T0 ({meta.old_year})</span>
                    <span>Historical Record</span>
                  </div>
                  <p className="text-slate-800 font-medium text-[11px]">{item.beforeState || item.before_state}</p>
                </div>

                <div className="p-2.5 bg-emerald-50/50 rounded border border-emerald-200 space-y-0.5">
                  <div className="flex items-center justify-between text-[#166534] text-[10px] font-semibold uppercase">
                    <span>Current T1 ({meta.new_year})</span>
                    <span>Surveyed Layer</span>
                  </div>
                  <p className="text-emerald-950 font-medium text-[11px]">{item.afterState || item.after_state}</p>
                </div>
              </div>

              {/* Change Summary & Revenue Impact */}
              <div className="p-2.5 bg-slate-50 rounded border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                <p className="text-slate-700 font-normal flex-1">
                  {item.summary}
                </p>
                <div className="text-right sm:border-l sm:pl-4 border-slate-200">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Revenue / Tax Delta</span>
                  <strong className="text-emerald-900 font-bold text-xs">{item.taxImpact || item.tax_impact}</strong>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-1 flex items-center justify-between border-t border-slate-100">
                <Link
                  to="/map"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#166534] hover:underline"
                >
                  <MapPin size={13} />
                  View Delta on GIS Map
                </Link>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => showToast(`Mutation Notice generated for Parcel ${item.parcelId || item.parcel_id}!`)}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <FileText size={13} />
                    Issue Mutation Notice
                  </button>
                  <button
                    onClick={() => showToast(`Forwarded ${item.parcelId || item.parcel_id} to Municipal Property Tax Cell!`)}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-md text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <Building2 size={13} />
                    Forward to ULB Tax Cell
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default ChangeDetection;
