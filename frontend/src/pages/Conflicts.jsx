import { useState, useMemo, useEffect } from "react";
import {
  AlertTriangle,
  Search,
  CheckCircle2,
  Clock,
  Eye,
  Check,
  X,
  MapPin,
  Filter,
  Download,
  ShieldAlert,
  GitMerge,
  RefreshCw,
  Play,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listConflicts, detectConflicts, resolveConflict } from "../api/conflicts";


function Conflicts() {
  const { selectedProjectId } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedSeverity, setSelectedSeverity] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [activeModalConflict, setActiveModalConflict] = useState(null);
  const [resolutionChoice, setResolutionChoice] = useState("resolved");
  const [officerNote, setOfficerNote] = useState("");
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);

  const [conflicts, setConflicts] = useState([]);

  useEffect(() => {
    if (selectedProjectId) {
      loadConflicts();
    }
  }, [selectedProjectId]);

  const loadConflicts = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    try {
      const data = await listConflicts(selectedProjectId);
      if (data && data.conflicts) {
        const mapped = data.conflicts.map((c) => ({
          id: `CNF-${c.id}`,
          rawId: c.id,
          parcelId: `Feature #${c.feature_id || c.id}`,
          khasraNo: c.feature_id ? `${c.feature_id}/1` : "N/A",
          type: c.conflict_type || "Attribute Conflict",
          sourceA: "Source A",
          sourceB: "Source B",
          severity: c.confidence_score < 70 ? "High" : "Medium",
          confidence: Math.round(c.confidence_score || 85),
          status: c.resolution_status === "resolved" || c.resolution_status === "approved" ? "Resolved" : "Pending Review",
          detectedDate: c.created_at ? new Date(c.created_at).toISOString().split("T")[0] : "2026-09-21",
          description: c.description || "Spatial / Attribute discrepancy detected across multi-source layers.",
          sourceAData: { area: "Source A Record", value: String(c.source_value || "N/A") },
          sourceBData: { area: "Source B Record", value: String(c.target_value || "N/A") },
          aiRecommendation: "Reconcile discrepancy using highest confidence source layer.",
          differenceSummary: `Source: ${c.source_value || "N/A"} vs Target: ${c.target_value || "N/A"}`,
        }));
        setConflicts(mapped);
      }
    } catch (err) {
      console.error("Failed to load conflicts from API:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunDetection = async () => {
    if (!selectedProjectId) return;
    setDetecting(true);
    try {
      await detectConflicts(selectedProjectId);
      showToast("Conflict detection completed for project.");
      await loadConflicts();
    } catch (err) {
      showToast("Failed to run conflict detection. " + (err.friendlyMessage || ""));
    } finally {
      setDetecting(false);
    }
  };

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleResolveSubmit = async () => {
    if (!activeModalConflict) return;

    try {
      const statusText = resolutionChoice === "rejected" ? "rejected" : "resolved";
      await resolveConflict(activeModalConflict.rawId, statusText, officerNote);

      setConflicts((prev) =>
        prev.map((c) =>
          c.id === activeModalConflict.id
            ? {
                ...c,
                status: statusText === "resolved" ? "Resolved" : "Rejected",
              }
            : c
        )
      );

      showToast(`Conflict ${activeModalConflict.id} marked as ${statusText}.`);
      setActiveModalConflict(null);
      setOfficerNote("");
    } catch (err) {
      showToast("Resolution failed: " + (err.friendlyMessage || ""));
    }
  };

  const filteredConflicts = useMemo(() => {
    return conflicts.filter((c) => {
      const matchesSearch =
        c.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.parcelId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType = selectedType === "all" || c.type.toLowerCase().includes(selectedType.toLowerCase());
      const matchesSeverity = selectedSeverity === "all" || c.severity.toLowerCase() === selectedSeverity.toLowerCase();
      const matchesStatus = selectedStatus === "all" || c.status.toLowerCase() === selectedStatus.toLowerCase();

      return matchesSearch && matchesType && matchesSeverity && matchesStatus;
    });
  }, [conflicts, searchQuery, selectedType, selectedSeverity, selectedStatus]);


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
            Conflict Resolution Center
          </h1>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Review spatial, coordinate, and attribute discrepancies flagged across multi-source datasets.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunDetection}
            disabled={detecting || !selectedProjectId}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
          >
            {detecting ? (
              <>
                <RefreshCw size={13} className="animate-spin" />
                Detecting Conflicts...
              </>
            ) : (
              <>
                <Play size={13} />
                Detect Conflicts
              </>
            )}
          </button>
          <Link
            to="/map"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded-md text-xs font-semibold transition-colors"
          >
            <MapPin size={13} />
            View on GIS Map
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-xs">
          <span className="text-[11px] text-slate-500 block">Total Conflicts</span>
          <strong className="text-xl font-bold text-slate-900">{conflicts.length}</strong>
        </div>
        <div className="bg-white rounded-lg border border-red-200 bg-red-50/20 p-3 shadow-xs">
          <span className="text-[11px] text-red-700 font-medium block">High Severity</span>
          <strong className="text-xl font-bold text-red-700">
            {conflicts.filter((c) => c.severity === "High").length}
          </strong>
        </div>
        <div className="bg-white rounded-lg border border-amber-200 bg-amber-50/20 p-3 shadow-xs">
          <span className="text-[11px] text-amber-700 font-medium block">Pending Review</span>
          <strong className="text-xl font-bold text-amber-800">
            {conflicts.filter((c) => c.status === "Pending Review").length}
          </strong>
        </div>
        <div className="bg-white rounded-lg border border-emerald-200 bg-emerald-50/20 p-3 shadow-xs">
          <span className="text-[11px] text-emerald-700 font-medium block">Resolved</span>
          <strong className="text-xl font-bold text-[#166534]">
            {conflicts.filter((c) => c.status === "Resolved").length}
          </strong>
        </div>
      </div>


      {/* Search & Filter Bar */}
      <div className="bg-white rounded-lg border border-slate-200 p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
        <div className="relative flex-1 w-full">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Conflict ID (CNF-1024), Parcel ID..."
            className="w-full bg-slate-50 border border-slate-200 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Severities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="Pending Review">Pending Review</option>
            <option value="Resolved">Resolved</option>
          </select>
        </div>
      </div>

      {/* Conflicts Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Conflict ID / Parcel</th>
                <th className="py-2.5 px-3">Type & Description</th>
                <th className="py-2.5 px-3">Sources Involved</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredConflicts.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-400 text-xs">
                    No conflicts found in the database. Upload datasets and run conflict detection to test.
                  </td>
                </tr>
              ) : (
                filteredConflicts.map((c) => (

                <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-2.5 px-3">
                    <span className="font-mono font-bold text-slate-900 block">{c.id}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{c.parcelId} (Khasra {c.khasraNo})</span>
                  </td>
                  <td className="py-2.5 px-3">
                    <strong className="text-slate-900 block font-semibold">{c.type}</strong>
                    <span className="text-[11px] text-slate-500 truncate max-w-xs block">{c.description}</span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-700">{c.sourceA} ⟷ {c.sourceB}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        c.severity === "High"
                          ? "bg-red-50 text-red-700 border-red-200"
                          : "bg-amber-50 text-amber-800 border-amber-200"
                      }`}
                    >
                      {c.severity}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-semibold text-[#166534]">{c.confidence}%</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        c.status === "Resolved"
                          ? "bg-emerald-50 text-[#166534] border-emerald-200"
                          : "bg-amber-50 text-amber-800 border-amber-200"
                      }`}
                    >
                      {c.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => setActiveModalConflict(c)}
                      className="px-2.5 py-1 bg-[#166534] hover:bg-emerald-900 text-white rounded text-xs font-semibold cursor-pointer transition-colors"
                    >
                      Adjudicate
                    </button>
                  </td>
                </tr>
              ))
              )}
            </tbody>

          </table>
        </div>

        {/* Table Pagination / Summary */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing {filteredConflicts.length} of {conflicts.length} entries (86 total in database)
          </span>
          <span className="font-mono text-[11px] text-slate-400">
            Adjudication Authority: Officer in Charge, Ward 17 GIS Cell
          </span>
        </div>
      </div>

      {/* Adjudication Modal */}
      {activeModalConflict && (
        <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg border border-slate-200 max-w-lg w-full p-5 shadow-xl space-y-4 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div>
                <h4 className="font-bold text-slate-900 text-sm">
                  Adjudicate {activeModalConflict.id}
                </h4>
                <span className="font-mono text-[10px] text-slate-400">
                  Parcel: {activeModalConflict.parcelId} • Khasra: {activeModalConflict.khasraNo}
                </span>
              </div>
              <button
                onClick={() => setActiveModalConflict(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3 text-slate-700">
              <p className="p-2.5 bg-slate-50 border border-slate-200 rounded leading-relaxed">
                {activeModalConflict.description}
              </p>

              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded">
                  <span className="font-semibold text-slate-500 block mb-0.5">{activeModalConflict.sourceA}</span>
                  <strong className="text-slate-900">{activeModalConflict.sourceAData.area}</strong>
                </div>
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded">
                  <span className="font-semibold text-slate-500 block mb-0.5">{activeModalConflict.sourceB}</span>
                  <strong className="text-slate-900">{activeModalConflict.sourceBData.area}</strong>
                </div>
              </div>

              <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded text-[#166534]">
                <strong className="block mb-0.5 font-bold">Algorithmic Recommendation:</strong>
                {activeModalConflict.aiRecommendation}
              </div>

              <div className="pt-2 space-y-1.5">
                <span className="font-semibold text-slate-700 block">Resolution Action:</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="res"
                    checked={resolutionChoice === "ai"}
                    onChange={() => setResolutionChoice("ai")}
                    className="accent-emerald-700"
                  />
                  <span>Adopt Recommendation (Auto-snap to GNSS / Drone GCP)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="res"
                    checked={resolutionChoice === "sourceA"}
                    onChange={() => setResolutionChoice("sourceA")}
                    className="accent-emerald-700"
                  />
                  <span>Retain Legal Baseline (Cadastral RoR)</span>
                </label>
              </div>
            </div>

            <div className="pt-3 flex justify-end gap-2 border-t border-slate-100">
              <button
                onClick={() => setActiveModalConflict(null)}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded font-medium cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleResolveSubmit}
                className="px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded font-semibold cursor-pointer"
              >
                Confirm Resolution
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Conflicts;