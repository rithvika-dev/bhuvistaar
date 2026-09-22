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
  Loader2,
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
  const [resolutionChoice, setResolutionChoice] = useState("accepted_source");
  const [officerNote, setOfficerNote] = useState("");
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState(null);

  const [conflicts, setConflicts] = useState([]);

  useEffect(() => {
    if (selectedProjectId) {
      loadConflicts();
    } else {
      setConflicts([]);
    }
  }, [selectedProjectId]);

  const loadConflicts = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await listConflicts(selectedProjectId);
      if (data && data.conflicts) {
        const mapped = data.conflicts.map((c) => {
          const rawConf = c.confidence_score;
          const pctConf =
            rawConf != null
              ? rawConf <= 1.0
                ? Math.round(rawConf * 100)
                : Math.round(rawConf)
              : 85;

          const rawSev = (c.severity || "medium").toLowerCase();
          const sevDisplay =
            rawSev === "high" ? "High" : rawSev === "low" ? "Low" : "Medium";

          const isResolved =
            c.resolution_status &&
            c.resolution_status !== "pending";

          const statusDisplay =
            c.resolution_status === "rejected"
              ? "Rejected"
              : isResolved
              ? "Resolved"
              : "Pending Review";

          return {
            id: `CNF-${c.id}`,
            rawId: c.id,
            featureId: c.feature_id,
            parcelId: c.feature_id ? `Feature #${c.feature_id}` : `Project #${c.project_id}`,
            khasraNo: c.feature_id ? `${c.feature_id}` : "N/A",
            type: c.conflict_type || "attribute_mismatch",
            severity: sevDisplay,
            confidence: pctConf,
            status: statusDisplay,
            rawStatus: c.resolution_status || "pending",
            detectedDate: c.created_at
              ? new Date(c.created_at).toISOString().split("T")[0]
              : new Date().toISOString().split("T")[0],
            description:
              c.description ||
              "Spatial / Attribute discrepancy detected across multi-source layers.",
            sourceValue: c.source_value != null ? String(c.source_value) : "N/A",
            targetValue: c.target_value != null ? String(c.target_value) : "N/A",
            aiRecommendation:
              c.suggested_resolution ||
              "Reconcile discrepancy using authoritative multi-source validation.",
            resolutionNotes: c.resolution_notes || "",
          };
        });
        setConflicts(mapped);
      } else {
        setConflicts([]);
      }
    } catch (err) {
      console.error("Failed to load conflicts from API:", err);
      setError(err.friendlyMessage || "Failed to load conflicts.");
    } finally {
      setLoading(false);
    }
  };

  const handleRunDetection = async () => {
    if (!selectedProjectId) return;
    setDetecting(true);
    setError(null);
    try {
      const res = await detectConflicts(selectedProjectId);
      const count = res.conflicts_found != null ? res.conflicts_found : res.conflicts?.length || 0;
      showToast(`Conflict detection completed: ${count} active conflicts.`);
      await loadConflicts();
    } catch (err) {
      showToast("Failed to run conflict detection. " + (err.friendlyMessage || ""));
      setError(err.friendlyMessage || "Conflict detection failed.");
    } finally {
      setDetecting(false);
    }
  };

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleOpenModal = (conflict) => {
    setActiveModalConflict(conflict);
    setResolutionChoice("accepted_source");
    setOfficerNote(conflict.resolutionNotes || "");
  };

  const handleResolveSubmit = async () => {
    if (!activeModalConflict) return;

    try {
      await resolveConflict(
        activeModalConflict.rawId,
        resolutionChoice,
        officerNote || `Officer resolved as ${resolutionChoice}`
      );

      const statusText =
        resolutionChoice === "rejected" ? "Rejected" : "Resolved";

      setConflicts((prev) =>
        prev.map((c) =>
          c.id === activeModalConflict.id
            ? {
                ...c,
                status: statusText,
                rawStatus: resolutionChoice,
                resolutionNotes: officerNote,
              }
            : c
        )
      );

      showToast(`Conflict ${activeModalConflict.id} saved as ${resolutionChoice}.`);
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

      const matchesType =
        selectedType === "all" ||
        c.type.toLowerCase() === selectedType.toLowerCase();
      const matchesSeverity =
        selectedSeverity === "all" ||
        c.severity.toLowerCase() === selectedSeverity.toLowerCase();
      const matchesStatus =
        selectedStatus === "all" ||
        c.status.toLowerCase() === selectedStatus.toLowerCase();

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
            disabled={detecting || loading || !selectedProjectId}
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

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-red-50 text-red-800 border border-red-200 rounded-lg text-xs font-medium">
          <AlertTriangle size={14} />
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-500 hover:text-red-700 cursor-pointer"
          >
            <X size={14} />
          </button>
        </div>
      )}

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
            placeholder="Search by Conflict ID (CNF-1024), Feature ID, description..."
            className="w-full bg-slate-50 border border-slate-200 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Conflict Types</option>
            <option value="attribute_mismatch">Attribute Mismatch</option>
            <option value="geometry_conflict">Geometry Conflict</option>
            <option value="identity_conflict">Identity Conflict</option>
            <option value="duplicate_feature">Duplicate Feature</option>
            <option value="crs_inconsistency">CRS Inconsistency</option>
          </select>

          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Severities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="Pending Review">Pending Review</option>
            <option value="Resolved">Resolved</option>
            <option value="Rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center gap-2 py-12 text-slate-500 text-sm bg-white rounded-lg border border-slate-200">
          <Loader2 size={18} className="animate-spin" />
          Loading conflicts from database...
        </div>
      )}

      {/* Conflicts Table */}
      {!loading && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Conflict ID / Feature</th>
                  <th className="py-2.5 px-3">Type & Description</th>
                  <th className="py-2.5 px-3">Values (Source ⟷ Target)</th>
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
                      {conflicts.length === 0
                        ? "No conflicts found in the database. Run feature matching and conflict detection to test."
                        : "No conflicts match the selected search or filter criteria."}
                    </td>
                  </tr>
                ) : (
                  filteredConflicts.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2.5 px-3">
                        <span className="font-mono font-bold text-slate-900 block">{c.id}</span>
                        <span className="text-[10px] text-slate-400 font-mono">{c.parcelId}</span>
                      </td>
                      <td className="py-2.5 px-3 max-w-sm">
                        <strong className="text-slate-900 block font-semibold capitalize">
                          {c.type.replace(/_/g, " ")}
                        </strong>
                        <span className="text-[11px] text-slate-500 leading-tight block">
                          {c.description}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-700">
                        <div className="truncate max-w-xs">
                          <span className="text-slate-500">Src:</span> {c.sourceValue}
                        </div>
                        <div className="truncate max-w-xs">
                          <span className="text-slate-500">Tgt:</span> {c.targetValue}
                        </div>
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            c.severity === "High"
                              ? "bg-red-50 text-red-700 border-red-200"
                              : c.severity === "Low"
                              ? "bg-blue-50 text-blue-700 border-blue-200"
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
                              : c.status === "Rejected"
                              ? "bg-red-50 text-red-700 border-red-200"
                              : "bg-amber-50 text-amber-800 border-amber-200"
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={() => handleOpenModal(c)}
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

          {/* Table Footer */}
          <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing {filteredConflicts.length} of {conflicts.length} entries
            </span>
            <span className="font-mono text-[11px] text-slate-400">
              Authority: Verified Land Records Officer
            </span>
          </div>
        </div>
      )}

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
                  {activeModalConflict.parcelId} • Type: {activeModalConflict.type.replace(/_/g, " ")} • Severity: {activeModalConflict.severity}
                </span>
              </div>
              <button
                onClick={() => setActiveModalConflict(null)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
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
                  <span className="font-semibold text-slate-500 block mb-0.5">Source Value</span>
                  <strong className="text-slate-900 font-mono break-all">
                    {activeModalConflict.sourceValue}
                  </strong>
                </div>
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded">
                  <span className="font-semibold text-slate-500 block mb-0.5">Target Value</span>
                  <strong className="text-slate-900 font-mono break-all">
                    {activeModalConflict.targetValue}
                  </strong>
                </div>
              </div>

              <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded text-[#166534]">
                <strong className="block mb-0.5 font-bold">Algorithmic Suggested Action:</strong>
                {activeModalConflict.aiRecommendation}
              </div>

              <div className="pt-2 space-y-1.5">
                <span className="font-semibold text-slate-700 block">Resolution Action:</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="res"
                    value="accepted_source"
                    checked={resolutionChoice === "accepted_source"}
                    onChange={() => setResolutionChoice("accepted_source")}
                    className="accent-emerald-700"
                  />
                  <span>Accept Source Record (Retain Source Baseline)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="res"
                    value="accepted_target"
                    checked={resolutionChoice === "accepted_target"}
                    onChange={() => setResolutionChoice("accepted_target")}
                    className="accent-emerald-700"
                  />
                  <span>Accept Target Record (Adopt Field/Drone Survey)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="res"
                    value="merged"
                    checked={resolutionChoice === "merged"}
                    onChange={() => setResolutionChoice("merged")}
                    className="accent-emerald-700"
                  />
                  <span>Merge & Reconcile Records</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="res"
                    value="rejected"
                    checked={resolutionChoice === "rejected"}
                    onChange={() => setResolutionChoice("rejected")}
                    className="accent-emerald-700"
                  />
                  <span>Dismiss / Reject Conflict</span>
                </label>
              </div>

              <div className="pt-1">
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                  Officer Review Notes:
                </label>
                <textarea
                  value={officerNote}
                  onChange={(e) => setOfficerNote(e.target.value)}
                  placeholder="Enter adjudication rationale or reference survey report..."
                  rows={2}
                  className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-xs text-slate-800 placeholder-slate-400 focus:bg-white transition-colors"
                />
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