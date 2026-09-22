import { useState, useEffect } from "react";
import {
  Settings as SettingsIcon,
  ShieldCheck,
  Save,
  Globe2,
  Sliders,
  Database,
  Smartphone,
  CheckCircle2,
  AlertTriangle,
  Lock,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getSettings, updateSettings } from "../api/settings";

function Settings() {
  const { selectedProjectId, projects } = useAuth();
  const [crsDefault, setCrsDefault] = useState("EPSG:4326");
  const [activeZone, setActiveZone] = useState("EPSG:32643");
  const [iouThreshold, setIouThreshold] = useState(85);
  const [bufferDistance, setBufferDistance] = useState(2.5);
  const [fuzzyThreshold, setFuzzyThreshold] = useState(80);
  const [organization, setOrganization] = useState("Ministry of Rural Development");
  const [department, setDepartment] = useState("Department of Land Resources (DoLR)");
  const [nodeIdentifier, setNodeIdentifier] = useState("");
  const [storageEngine, setStorageEngine] = useState("PostgreSQL / PostGIS");
  const [hashingAlgorithm, setHashingAlgorithm] = useState("SHA-256");
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const activeProject = projects.find((p) => p.id === selectedProjectId);

  useEffect(() => {
    if (selectedProjectId) {
      loadSettings();
    }
  }, [selectedProjectId]);

  const loadSettings = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    try {
      const data = await getSettings(selectedProjectId);
      if (data && data.settings) {
        const s = data.settings;
        if (s.crs_default) setCrsDefault(s.crs_default);
        if (s.active_zone) setActiveZone(s.active_zone);
        if (s.iou_threshold != null) setIouThreshold(Number(s.iou_threshold));
        if (s.buffer_distance != null) setBufferDistance(Number(s.buffer_distance));
        if (s.fuzzy_threshold != null) setFuzzyThreshold(Number(s.fuzzy_threshold));
        if (s.organization) setOrganization(s.organization);
        if (s.department) setDepartment(s.department);
        if (s.node_identifier) setNodeIdentifier(s.node_identifier);
        else setNodeIdentifier(`NODE-SIH26013-P${selectedProjectId}`);
        if (s.storage_engine) setStorageEngine(s.storage_engine);
        if (s.hashing_algorithm) setHashingAlgorithm(s.hashing_algorithm);
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
      showToast(err.friendlyMessage || "Failed to load project settings.", "error");
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = "success") => {
    setToastMessage({ text: message, type });
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleSave = async (e) => {
    if (e) e.preventDefault();
    if (!selectedProjectId) {
      showToast("Please select a project from the top header.", "error");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        crs_default: crsDefault,
        active_zone: activeZone,
        iou_threshold: iouThreshold,
        buffer_distance: bufferDistance,
        fuzzy_threshold: fuzzyThreshold,
        organization: organization,
        department: department,
        node_identifier: nodeIdentifier,
        storage_engine: storageEngine,
        hashing_algorithm: hashingAlgorithm,
      };
      await updateSettings(selectedProjectId, payload);
      showToast("System configuration & Geo-Processing parameters saved successfully.");
    } catch (err) {
      console.error("Failed to save settings:", err);
      showToast(err.friendlyMessage || "Failed to save configuration.", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-lg shadow-md text-xs font-semibold border ${
          toastMessage.type === "error" ? "bg-red-50 text-red-800 border-red-200" : "bg-emerald-50 text-[#166534] border-emerald-200"
        }`}>
          {toastMessage.type === "error" ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} className="text-[#166534]" />}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              System Configuration & Parameters
            </h1>
            {loading && <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />}
          </div>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Configure spatial reference systems, Geo-AI harmonization thresholds, and administrative security parameters for {activeProject?.name ? `Project: ${activeProject.name}` : "selected project"}.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer self-start disabled:opacity-50"
          >
            {saving ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
            Save Configuration
          </button>
          <button
            onClick={loadSettings}
            className="p-1.5 bg-white border border-slate-200 rounded text-slate-600 hover:bg-slate-50"
            title="Reload Settings"
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        {/* Node & Organization Information */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100 text-xs font-bold text-slate-900">
            <ShieldCheck size={16} className="text-[#166534]" />
            <span>Organization & Custodian Node Details</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Parent Ministry
              </label>
              <input
                type="text"
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                placeholder="e.g. Ministry of Rural Development"
                className="w-full bg-white border border-slate-200 rounded-md p-2 text-slate-800 font-medium focus:ring-1 focus:ring-emerald-600 focus:border-emerald-600"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Department / Authority
              </label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="e.g. Department of Land Resources (DoLR)"
                className="w-full bg-white border border-slate-200 rounded-md p-2 text-slate-800 font-medium focus:ring-1 focus:ring-emerald-600 focus:border-emerald-600"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Platform Node Identifier
              </label>
              <input
                type="text"
                value={nodeIdentifier}
                onChange={(e) => setNodeIdentifier(e.target.value)}
                placeholder="e.g. NODE-SIH26013-P4"
                className="w-full bg-white border border-slate-200 rounded-md p-2 text-slate-800 font-mono focus:ring-1 focus:ring-emerald-600 focus:border-emerald-600"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Operational Node Status
              </label>
              <div className="flex items-center gap-2 p-2 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 font-semibold text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
                <span>Active • Project ID #{selectedProjectId || "None"} ({activeProject?.name || "Ready"})</span>
              </div>
            </div>
          </div>
        </div>

        {/* Geospatial Coordinate Reference Systems (CRS) */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100 text-xs font-bold text-slate-900">
            <Globe2 size={16} className="text-[#166534]" />
            <span>Coordinate Reference System (CRS) Standards</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Canonical Output CRS
              </label>
              <select
                value={crsDefault}
                onChange={(e) => setCrsDefault(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-md p-2 text-slate-800 font-mono cursor-pointer"
              >
                <option value="EPSG:4326">EPSG:4326 - WGS 84 (Geographic Lat/Lon)</option>
                <option value="EPSG:3857">EPSG:3857 - WGS 84 / Pseudo-Mercator</option>
              </select>
              <span className="text-[10px] text-slate-400 block mt-1">
                Standard format for all verified and exported Title Registers.
              </span>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Local UTM Projected Zone
              </label>
              <select
                value={activeZone}
                onChange={(e) => setActiveZone(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-md p-2 text-slate-800 font-mono cursor-pointer"
              >
                <option value="EPSG:32643">EPSG:32643 - WGS 84 / UTM Zone 43N (Delhi/NCR)</option>
                <option value="EPSG:32644">EPSG:32644 - WGS 84 / UTM Zone 44N</option>
                <option value="EPSG:32642">EPSG:32642 - WGS 84 / UTM Zone 42N</option>
              </select>
              <span className="text-[10px] text-slate-400 block mt-1">
                Used for sub-meter high-precision metric area & distance calculations.
              </span>
            </div>
          </div>
        </div>

        {/* Geo-AI & Harmonization Processing Thresholds */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100 text-xs font-bold text-slate-900">
            <Sliders size={16} className="text-[#166534]" />
            <span>Spatial Matching & Reconciliation Thresholds</span>
          </div>

          <div className="space-y-4 text-xs">
            {/* IoU Threshold Slider */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-semibold text-slate-700">
                  Minimum Polygon IoU Overlap Conformance
                </label>
                <span className="font-mono font-bold text-[#166534] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-xs">
                  {iouThreshold}%
                </span>
              </div>
              <input
                type="range"
                min="60"
                max="98"
                value={iouThreshold}
                onChange={(e) => setIouThreshold(Number(e.target.value))}
                className="w-full accent-[#166534] cursor-pointer"
              />
              <span className="text-[10px] text-slate-400 block">
                Parcels with geometric overlap above this threshold are classified as high-confidence matches.
              </span>
            </div>

            {/* Snapping Buffer Distance */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-semibold text-slate-700">
                  Vertex Snapping Tolerance Buffer
                </label>
                <span className="font-mono font-bold text-[#166534] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-xs">
                  {bufferDistance} meters
                </span>
              </div>
              <input
                type="range"
                min="0.5"
                max="5.0"
                step="0.5"
                value={bufferDistance}
                onChange={(e) => setBufferDistance(Number(e.target.value))}
                className="w-full accent-[#166534] cursor-pointer"
              />
              <span className="text-[10px] text-slate-400 block">
                Maximum allowable geometric offset for automated vertex snapping to CORS control points.
              </span>
            </div>

            {/* Fuzzy Attribute Match */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-semibold text-slate-700">
                  Fuzzy String Matching (Levenshtein Distance)
                </label>
                <span className="font-mono font-bold text-[#166534] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-xs">
                  {fuzzyThreshold}%
                </span>
              </div>
              <input
                type="range"
                min="60"
                max="95"
                value={fuzzyThreshold}
                onChange={(e) => setFuzzyThreshold(Number(e.target.value))}
                className="w-full accent-[#166534] cursor-pointer"
              />
              <span className="text-[10px] text-slate-400 block">
                Tolerance for phonetic and typographical variations in landholder names.
              </span>
            </div>
          </div>
        </div>

        {/* Local Storage & Security */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100 text-xs font-bold text-slate-900">
            <Lock size={16} className="text-[#166534]" />
            <span>Storage & Cryptographic Signature Settings</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-2">
              <label className="text-[10px] font-semibold text-slate-600 uppercase block">
                Storage Engine
              </label>
              <select
                value={storageEngine}
                onChange={(e) => setStorageEngine(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-md p-1.5 text-xs text-slate-800"
              >
                <option value="PostgreSQL / PostGIS">PostgreSQL / PostGIS (Primary Spatial Store)</option>
                <option value="IndexedDB / Browser Local DB">IndexedDB / Browser Local DB (Offline Cache)</option>
              </select>
              <p className="text-[11px] text-slate-500">
                Spatial relational database with PostGIS geometry engine.
              </p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-2">
              <label className="text-[10px] font-semibold text-slate-600 uppercase block">
                Hashing Algorithm
              </label>
              <select
                value={hashingAlgorithm}
                onChange={(e) => setHashingAlgorithm(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-md p-1.5 text-xs text-slate-800 font-mono"
              >
                <option value="SHA-256">SHA-256 (256-bit Digest)</option>
                <option value="SHA-512">SHA-512 (512-bit Digest)</option>
              </select>
              <p className="text-[11px] text-slate-500">
                Tamper-evident cryptographic sealing applied on all verified land record mutations.
              </p>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

export default Settings;