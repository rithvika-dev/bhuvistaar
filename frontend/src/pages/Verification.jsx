import React, { useState, useEffect } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Check,
  X,
  Search,
  MapPin,
  FileCheck,
  Cpu,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getPendingMatches, reviewMatch, runMatching } from "../api/matching";

function Verification() {
  const { selectedProjectId, projects } = useAuth();
  const [pendingMatches, setPendingMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");
  const [toastMessage, setToastMessage] = useState(null);
  const [matchingRunning, setMatchingRunning] = useState(false);

  useEffect(() => {
    if (selectedProjectId) {
      loadPendingMatches(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadPendingMatches = async (projectId) => {
    setLoading(true);
    try {
      const data = await getPendingMatches(projectId);
      // API returns { matches: [...] } with match_id field
      const matchList = (data?.matches || data || []).map((m) => ({
        ...m,
        id: m.match_id || m.id,
      }));
      setPendingMatches(matchList);
    } catch (err) {
      console.error("Failed to load pending matches:", err);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = "success") => {
    setToastMessage({ text: message, type });
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleReview = async (matchId, status) => {
    try {
      await reviewMatch(matchId, status, reviewNotes || `Reviewed as ${status} by user`);
      showToast(`Match #${matchId} set to '${status}'. Saved to PostgreSQL database.`);
      setPendingMatches((prev) => prev.filter((m) => m.id !== matchId));
      setReviewNotes("");
    } catch (err) {
      showToast(err.friendlyMessage || "Failed to update match status.", "error");
    }
  };

  const handleTriggerMatching = async () => {
    if (!selectedProjectId) return;
    setMatchingRunning(true);
    try {
      // Auto-resolve source & target datasets on backend
      const result = await runMatching(selectedProjectId);
      showToast(`Matching complete: ${result.matches_found || 0} matches found!`);
      loadPendingMatches(selectedProjectId);
    } catch (err) {
      showToast(err.friendlyMessage || "Matching failed. Check datasets exist and are processed.", "error");
    } finally {
      setMatchingRunning(false);
    }
  };

  const filteredMatches = pendingMatches.filter((m) => {
    const sId = (m.source_feature_id || "").toString();
    const tId = (m.target_feature_id || "").toString();
    return sId.includes(searchQuery) || tId.includes(searchQuery);
  });

  return (
    <div className="space-y-5">
      {/* Toast */}
      {toastMessage && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-lg border shadow-md text-xs font-semibold ${
          toastMessage.type === "error" ? "bg-red-50 text-red-800 border-red-200" : "bg-emerald-50 text-[#166534] border-emerald-200"
        }`}>
          {toastMessage.type === "error" ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Human-in-the-Loop Review Queue</h1>
            {loading && <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />}
          </div>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Adjudicate AI-suggested feature matches, review spatial confidence, and ratify titles.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleTriggerMatching}
            disabled={matchingRunning}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold cursor-pointer disabled:opacity-50"
          >
            {matchingRunning ? <Loader2 size={13} className="animate-spin" /> : <Cpu size={13} />}
            Run AI Matching
          </button>
          <button onClick={() => selectedProjectId && loadPendingMatches(selectedProjectId)} className="p-1.5 bg-white border border-slate-200 rounded text-slate-600">
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg border border-slate-200 p-3.5 flex items-center justify-between gap-3 shadow-xs">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Feature ID..."
            className="w-full bg-slate-50 border border-slate-200 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:bg-white"
          />
        </div>
      </div>

      {/* Review Cards */}
      <div className="space-y-3">
        {filteredMatches.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-lg border border-slate-200 text-slate-400 text-xs">
            No pending AI feature matches to review for this project.
            <div className="mt-2">
              <button onClick={handleTriggerMatching} className="text-emerald-700 font-semibold hover:underline">
                Run AI Feature Matching Engine
              </button>
            </div>
          </div>
        ) : (
          filteredMatches.map((match) => (
            <div key={match.id} className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-md bg-emerald-50 text-[#166534] flex items-center justify-center font-bold text-xs border border-emerald-200">
                    #{match.id}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">
                      Source Feature #{match.source_feature_id} ⟷ Target Feature #{match.target_feature_id}
                    </h3>
                    <span className="text-[11px] text-slate-500">
                      Distance: <strong>{match.distance != null ? `${match.distance.toFixed(2)} m` : "N/A"}</strong> • Scoring: <strong>{match.explanation ? JSON.parse(match.explanation || "{}").scoring_method || "Weighted" : "Weighted"}</strong>
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#166534]">
                    {Math.round((match.final_confidence_score || 0) * 100)}% Confidence
                  </span>
                </div>
              </div>

              {/* Match Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs bg-slate-50 p-2.5 rounded border border-slate-200">
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Spatial Score</span>
                  <strong>{Math.round((match.spatial_score || 0) * 100)}%</strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Attribute Score</span>
                  <strong>{Math.round((match.attribute_score || 0) * 100)}%</strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Geometry Similarity</span>
                  <strong>{Math.round((match.geometry_similarity || 0) * 100)}%</strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Proximity Score</span>
                  <strong>{Math.round((match.proximity_score || 0) * 100)}%</strong>
                </div>
              </div>

              {/* Review Actions */}
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-2 border-t border-slate-100">
                <input
                  type="text"
                  placeholder="Optional review notes..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full sm:w-80 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded text-xs"
                />

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleReview(match.id, "rejected")}
                    className="px-3 py-1.5 bg-white hover:bg-red-50 text-red-700 border border-red-200 rounded text-xs font-semibold"
                  >
                    Reject Match
                  </button>
                  <button
                    onClick={() => handleReview(match.id, "approved")}
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded text-xs font-semibold"
                  >
                    <Check size={13} /> Approve Match
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

export default Verification;
