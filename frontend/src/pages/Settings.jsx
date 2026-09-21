import { useState } from "react";
import {
  Settings as SettingsIcon,
  ShieldCheck,
  Save,
  Globe2,
  Sliders,
  Database,
  Smartphone,
  CheckCircle2,
  Lock,
  RefreshCw,
} from "lucide-react";

function Settings() {
  const [crsDefault, setCrsDefault] = useState("EPSG:4326");
  const [activeZone, setActiveZone] = useState("EPSG:32643");
  const [iouThreshold, setIouThreshold] = useState(85);
  const [bufferDistance, setBufferDistance] = useState(2.5);
  const [fuzzyThreshold, setFuzzyThreshold] = useState(80);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleSave = (e) => {
    e.preventDefault();
    showToast("System configuration & Geo-Processing parameters saved successfully.");
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-2.5 bg-emerald-50 text-[#166534] border border-emerald-200 rounded-lg shadow-md text-xs font-semibold">
          <CheckCircle2 size={16} className="text-[#166534]" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            System Configuration & Parameters
          </h1>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Configure spatial reference systems, Geo-AI harmonization thresholds, and administrative security parameters.
          </p>
        </div>

        <button
          onClick={handleSave}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer self-start"
        >
          <Save size={13} />
          Save Configuration
        </button>
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
                disabled
                value="Ministry of Rural Development"
                className="w-full bg-slate-100 border border-slate-200 rounded-md p-2 text-slate-800 font-medium"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Department
              </label>
              <input
                type="text"
                disabled
                value="Department of Land Resources (DoLR)"
                className="w-full bg-slate-100 border border-slate-200 rounded-md p-2 text-slate-800 font-medium"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Platform Node Identifier
              </label>
              <input
                type="text"
                disabled
                value="NODE-SIH26013-W17 (Urban Pilot)"
                className="w-full bg-slate-100 border border-slate-200 rounded-md p-2 text-slate-800 font-mono"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Operational Status
              </label>
              <div className="flex items-center gap-2 p-2 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 font-semibold text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
                <span>Active • Connected to CORS Base DL-04</span>
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
            <span>Local Storage & Cryptographic Signature Settings</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
              <span className="text-[10px] font-semibold text-slate-400 uppercase block">
                Local Storage Engine
              </span>
              <strong className="text-slate-900 font-bold block">IndexedDB / Browser Local DB</strong>
              <p className="text-[11px] text-slate-500">
                100% offline-first architecture. Records persist securely without cloud dependency.
              </p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
              <span className="text-[10px] font-semibold text-slate-400 uppercase block">
                Hashing Algorithm
              </span>
              <strong className="text-slate-900 font-bold block">SHA-256 (256-bit Digest)</strong>
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