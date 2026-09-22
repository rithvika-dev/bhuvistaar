import { useState, useEffect, useRef } from "react";
import {
  Layers,
  Play,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Activity,
  MapPin,
  SlidersHorizontal,
  Check,
  X,
  Upload,
  Loader2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listProjectDatasets } from "../api/datasets";
import {
  generateHarmonizedFeatures,
  getHarmonizedFeatures,
  reviewHarmonizedFeature,
  getAttributeMappings,
  resolveAttributeMapping,
} from "../api/harmonization";
import { startPipeline, getPipelineStatus } from "../api/pipeline";
import { getProjectMatches } from "../api/matching";

function Harmonization() {
  const { selectedProjectId } = useAuth();
  const [pipelineState, setPipelineState] = useState("idle");
  const [currentStep, setCurrentStep] = useState(0);
  const [activeTab, setActiveTab] = useState("matches");
  const [filterConfidence, setFilterConfidence] = useState("all");
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [matchItems, setMatchItems] = useState([]);
  const [matchResults, setMatchResults] = useState({ match_count: 0, matches: [] });
  const [attributeMappings, setAttributeMappings] = useState([]);
  const [pipelineStatus, setPipelineStatusData] = useState(null);
  const [datasets, setDatasets] = useState([]);

  const stepIntervalRef = useRef(null);

  useEffect(() => {
    if (selectedProjectId) {
      loadAllData();
    } else {
      setMatchItems([]);
      setMatchResults({ match_count: 0, matches: [] });
      setAttributeMappings([]);
      setPipelineStatusData(null);
      setDatasets([]);
    }

    return () => {
      if (stepIntervalRef.current) {
        clearInterval(stepIntervalRef.current);
      }
    };
  }, [selectedProjectId]);

  const loadAllData = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    setError(null);
    try {
      const [dsData, harmonizedData, matchData, statusData, mappingsData] =
        await Promise.allSettled([
          listProjectDatasets(selectedProjectId),
          getHarmonizedFeatures(selectedProjectId),
          getProjectMatches(selectedProjectId),
          getPipelineStatus(selectedProjectId),
          getAttributeMappings(selectedProjectId),
        ]);

      if (dsData.status === "fulfilled") {
        setDatasets(dsData.value || []);
      }
      if (matchData.status === "fulfilled" && matchData.value) {
        setMatchResults(matchData.value);
      }
      if (mappingsData.status === "fulfilled" && mappingsData.value?.mappings) {
        setAttributeMappings(mappingsData.value.mappings);
      } else {
        setAttributeMappings([]);
      }
      if (statusData.status === "fulfilled" && statusData.value) {
        setPipelineStatusData(statusData.value);
        if (statusData.value.status === "completed") {
          setPipelineState("completed");
          setCurrentStep(8);
        } else if (statusData.value.status === "running") {
          setPipelineState("running");
        } else {
          setPipelineState("idle");
          setCurrentStep(0);
        }
      }

      if (
        harmonizedData.status === "fulfilled" &&
        harmonizedData.value &&
        harmonizedData.value.features &&
        harmonizedData.value.features.length > 0
      ) {
        const mapped = harmonizedData.value.features.map((f) => ({
          id: `HF-${f.id}`,
          rawId: f.id,
          featureId: f.feature_id,
          matchId: f.match_id,
          featureType: f.feature_type || "unknown",
          properties: f.properties || {},
          confidence: f.confidence_score,
          aiConfidence:
            f.confidence_score != null
              ? Math.round(f.confidence_score * 100)
              : null,
          conflictType:
            f.review_status === "rejected" ? "Flagged Discrepancy" : "None",
          recommendation: (() => {
            if (f.harmonized_attributes) {
              try {
                const parsed = JSON.parse(f.harmonized_attributes);
                if (typeof parsed === "object") return JSON.stringify(parsed);
              } catch {
                /* not JSON string */
              }
              return f.harmonized_attributes;
            }
            return f.confidence_score != null
              ? `Harmonized feature with ${Math.round(f.confidence_score * 100)}% confidence.`
              : "Harmonized feature generated.";
          })(),
          sourceInfo: f.source_info || null,
          status:
            f.review_status === "approved"
              ? "Accepted"
              : f.review_status === "rejected"
              ? "Rejected"
              : "Pending Review",
        }));
        setMatchItems(mapped);
      } else if (
        matchData.status === "fulfilled" &&
        matchData.value &&
        matchData.value.matches &&
        matchData.value.matches.length > 0
      ) {
        // Fallback to match results when harmonized features haven't been generated yet
        const mappedFromMatches = matchData.value.matches.map((m) => ({
          id: `M-${m.id}`,
          rawId: m.id,
          featureId: m.source_feature_id,
          matchId: m.id,
          featureType: "parcel_match",
          properties: {
            source_feature_id: m.source_feature_id,
            target_feature_id: m.target_feature_id,
            distance: m.distance,
            spatial_score: m.spatial_score,
            attribute_score: m.attribute_score,
          },
          confidence: m.final_confidence_score,
          aiConfidence:
            m.final_confidence_score != null
              ? Math.round(m.final_confidence_score * 100)
              : null,
          conflictType:
            m.match_status === "conflict" || m.match_status === "rejected"
              ? "Flagged Discrepancy"
              : "None",
          recommendation:
            m.explanation ||
            (m.final_confidence_score != null
              ? `Feature match confidence: ${Math.round(m.final_confidence_score * 100)}%.`
              : "Feature match record."),
          sourceInfo: null,
          status:
            m.match_status === "approved"
              ? "Accepted"
              : m.match_status === "rejected"
              ? "Rejected"
              : "Pending Review",
        }));
        setMatchItems(mappedFromMatches);
      } else {
        setMatchItems([]);
      }
    } catch (err) {
      console.error("Failed to load harmonization data:", err);
      setError(err.friendlyMessage || "Failed to load harmonization data.");
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Compute KPIs from real data
  const totalMatches = matchResults.match_count || matchItems.length || 0;
  const highConfMatches = (matchResults.matches || []).filter(
    (m) => m.final_confidence_score != null && m.final_confidence_score >= 0.85
  ).length || matchItems.filter((item) => item.confidence != null && item.confidence >= 0.85).length;

  const flaggedConflicts = matchItems.filter((item) => item.conflictType !== "None").length;
  const avgConfidence =
    totalMatches > 0
      ? (matchResults.matches || []).length > 0
        ? (matchResults.matches || []).reduce(
            (sum, m) => sum + (m.final_confidence_score || 0),
            0
          ) / (matchResults.matches || []).length * 100
        : matchItems.reduce((sum, item) => sum + (item.confidence || 0), 0) /
          matchItems.length *
          100
      : 0;

  const sourceDataset = datasets.length > 0 ? datasets[0] : null;
  const targetDataset = datasets.length > 1 ? datasets[1] : datasets[0] || null;

  const currentPipelineStatusLabel = (() => {
    if (pipelineState === "running") return `Running Step ${currentStep}/8...`;
    if (pipelineStatus?.status === "completed") return "Completed";
    if (pipelineStatus?.status === "running")
      return `Running (${pipelineStatus.progress || 0}%)`;
    if (pipelineStatus?.status === "failed") return "Failed";
    return "Not started";
  })();

  const pipelineSteps = [
    { num: 1, name: "Validation", desc: "Schema check" },
    { num: 2, name: "CRS Transform", desc: "EPSG:4326" },
    { num: 3, name: "Spatial Matching", desc: "Polygon IoU" },
    { num: 4, name: "Attributes", desc: "Schema map" },
    { num: 5, name: "Conflicts", desc: "Flag offsets" },
    { num: 6, name: "Scoring", desc: "Confidence %" },
    { num: 7, name: "Verification", desc: "Officer queue" },
    { num: 8, name: "Harmonized", desc: "Final layer" },
  ];

  const runPipelineSimulation = async () => {
    if (!selectedProjectId) return;
    setPipelineState("running");
    setCurrentStep(1);
    setError(null);

    stepIntervalRef.current = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= 8) {
          if (stepIntervalRef.current) clearInterval(stepIntervalRef.current);
          return 8;
        }
        return prev + 1;
      });
    }, 450);

    try {
      const dsList =
        datasets.length > 0
          ? datasets
          : await listProjectDatasets(selectedProjectId);
      const sourceDatasetId = dsList?.[0]?.id;
      const targetDatasetId = dsList?.[1]?.id ?? sourceDatasetId;

      if (!sourceDatasetId || !targetDatasetId) {
        throw new Error("At least two datasets are required to run the pipeline.");
      }

      if (sourceDatasetId === targetDatasetId) {
        throw new Error(
          "Source and target datasets must be different. Upload at least two datasets in the Datasets page."
        );
      }

      // 1. Run pipeline orchestrator
      await startPipeline(selectedProjectId, sourceDatasetId, targetDatasetId);

      // 2. Generate harmonized features
      try {
        await generateHarmonizedFeatures(selectedProjectId);
      } catch (genErr) {
        console.warn("Harmonized feature generation note:", genErr);
      }

      showToast("Harmonization pipeline executed successfully on server.");
      setPipelineState("completed");
      setCurrentStep(8);
      await loadAllData();
    } catch (err) {
      console.error("Pipeline execution error:", err);
      setError(err.friendlyMessage || err.message || "Pipeline execution failed.");
      showToast("Pipeline execution failed: " + (err.friendlyMessage || err.message || ""));
      setPipelineState("failed");
    } finally {
      if (stepIntervalRef.current) {
        clearInterval(stepIntervalRef.current);
      }
    }
  };

  const handleDecision = async (id, rawId, newStatus) => {
    try {
      if (rawId && id.startsWith("HF-")) {
        await reviewHarmonizedFeature(
          rawId,
          newStatus === "Accepted" ? "approved" : "rejected",
          `Officer decision: ${newStatus}`
        );
      }
      setMatchItems((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, status: newStatus } : item
        )
      );
      showToast(`Parcel ${id} marked as ${newStatus}.`);
    } catch (err) {
      showToast("Failed to save review decision: " + (err.friendlyMessage || ""));
    }
  };

  const handleResolveMapping = async (mappingId, status) => {
    try {
      await resolveAttributeMapping(mappingId, status, `Reviewed as ${status}`);
      setAttributeMappings((prev) =>
        prev.map((m) =>
          m.id === mappingId ? { ...m, mapping_status: status } : m
        )
      );
      showToast(`Mapping #${mappingId} marked as ${status}.`);
    } catch (err) {
      showToast("Failed to update mapping: " + (err.friendlyMessage || ""));
    }
  };

  const filteredMatches = matchItems.filter((item) => {
    if (filterConfidence === "conflicts") return item.conflictType !== "None";
    if (filterConfidence === "pending") return item.status === "Pending Review";
    if (filterConfidence === "accepted") return item.status === "Accepted";
    return true;
  });

  // Dynamic attribute mapping rows
  const attributeMappingRows = (() => {
    if (attributeMappings.length > 0) {
      return attributeMappings.map((m) => ({
        id: m.id,
        sourceField: m.source_field,
        targetField: m.target_field,
        mappingType: m.mapping_type || "similarity",
        confidence:
          m.confidence_score != null
            ? Math.round(m.confidence_score * 100)
            : null,
        status: m.mapping_status,
      }));
    }

    if (matchItems.length === 0) return [];
    const fieldSet = new Map();
    for (const item of matchItems) {
      if (item.properties && typeof item.properties === "object") {
        for (const key of Object.keys(item.properties)) {
          if (!fieldSet.has(key)) {
            fieldSet.set(key, []);
          }
          fieldSet.get(key).push(item.aiConfidence);
        }
      }
    }
    const rows = [];
    for (const [field, confidences] of fieldSet) {
      const avgConf =
        confidences.length > 0
          ? Math.round(
              confidences.reduce((s, v) => s + (v || 0), 0) /
                confidences.length
            )
          : 0;
      rows.push({
        id: `prop-${field}`,
        sourceField: field,
        targetField: field,
        mappingType: "property_schema",
        confidence: avgConf,
        status: "suggested",
      });
    }
    return rows;
  })();

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
            Harmonization Pipeline
          </h1>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Automated spatial polygon matching, attribute alignment, and conflict classification.
          </p>
        </div>

        <button
          onClick={runPipelineSimulation}
          disabled={pipelineState === "running" || loading}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer self-start"
        >
          {pipelineState === "running" ? (
            <>
              <Activity size={14} className="animate-spin" />
              Running Step {currentStep}/8...
            </>
          ) : (
            <>
              <Play size={14} />
              Run Pipeline
            </>
          )}
        </button>
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

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center gap-2 py-8 text-slate-500 text-sm">
          <Loader2 size={18} className="animate-spin" />
          Loading harmonization data...
        </div>
      )}

      {!loading && (
        <>
          {/* Pipeline Config Bar */}
          <div className="bg-white rounded-lg border border-slate-200 p-3.5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Primary Layer
                </span>
                <strong className="text-slate-900 font-medium">
                  {sourceDataset
                    ? `${sourceDataset.name} (${totalMatches} records)`
                    : "No dataset selected"}
                </strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Target CRS
                </span>
                <strong className="font-mono text-[#166534]">
                  {sourceDataset?.crs || "EPSG:4326 (WGS 84)"}
                </strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Matching Threshold
                </span>
                <strong className="text-slate-900 font-medium">
                  IoU ≥ 85% (Buffer 2.5m)
                </strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Pipeline Status
                </span>
                <strong
                  className={`font-semibold ${
                    pipelineStatus?.status === "completed"
                      ? "text-emerald-700"
                      : pipelineStatus?.status === "failed"
                      ? "text-red-600"
                      : pipelineStatus?.status === "running"
                      ? "text-blue-600"
                      : "text-slate-500"
                  }`}
                >
                  {currentPipelineStatusLabel}
                </strong>
              </div>
            </div>
          </div>

          {/* 8-Step Stepper */}
          <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-800">
              <span>Workflow Stages</span>
              <span className="text-[#166534] font-medium">
                {pipelineState === "running"
                  ? `Running Step ${currentStep} of 8...`
                  : currentPipelineStatusLabel}
              </span>
            </div>

            <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
              {pipelineSteps.map((step) => {
                const isDone = currentStep >= step.num;
                const isCurrent =
                  currentStep === step.num && pipelineState === "running";

                return (
                  <div
                    key={step.num}
                    className={`p-2 rounded border text-center transition-colors ${
                      isCurrent
                        ? "bg-blue-50 border-blue-300"
                        : isDone
                        ? "bg-emerald-50 border-emerald-200"
                        : "bg-slate-50 border-slate-200 opacity-50"
                    }`}
                  >
                    <span className="block text-[10px] font-bold text-slate-500">
                      {step.num}
                    </span>
                    <strong className="block text-[11px] font-semibold text-slate-900 truncate">
                      {step.name}
                    </strong>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Results KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-white rounded-lg border border-slate-200 p-3">
              <span className="text-[11px] text-slate-500 block">Total Matches</span>
              <strong className="text-xl font-bold text-slate-900">
                {totalMatches}
              </strong>
            </div>
            <div className="bg-white rounded-lg border border-emerald-200 bg-emerald-50/30 p-3">
              <span className="text-[11px] text-emerald-800 font-medium block">
                High Confidence (≥85%)
              </span>
              <strong className="text-xl font-bold text-[#166534]">
                {highConfMatches}
                {totalMatches > 0
                  ? ` (${Math.round((highConfMatches / totalMatches) * 100)}%)`
                  : ""}
              </strong>
            </div>
            <div className="bg-white rounded-lg border border-amber-200 bg-amber-50/30 p-3">
              <span className="text-[11px] text-amber-800 font-medium block">
                Flagged Conflicts
              </span>
              <strong className="text-xl font-bold text-amber-800">
                {flaggedConflicts}
                {totalMatches > 0
                  ? ` (${Math.round((flaggedConflicts / totalMatches) * 100)}%)`
                  : ""}
              </strong>
            </div>
            <div className="bg-white rounded-lg border border-slate-200 p-3">
              <span className="text-[11px] text-slate-500 block">
                Avg Confidence
              </span>
              <strong className="text-xl font-bold text-slate-900">
                {totalMatches > 0 ? `${avgConfidence.toFixed(1)}%` : "—"}
              </strong>
            </div>
          </div>

          {/* Feature Matches List */}
          <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 text-xs">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab("matches")}
                  className={`px-2.5 py-1 rounded font-semibold cursor-pointer ${
                    activeTab === "matches"
                      ? "bg-slate-100 text-slate-900"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  Matched Features ({filteredMatches.length})
                </button>
                <button
                  onClick={() => setActiveTab("attributes")}
                  className={`px-2.5 py-1 rounded font-semibold cursor-pointer ${
                    activeTab === "attributes"
                      ? "bg-slate-100 text-slate-900"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  Attribute Mapping Matrix ({attributeMappingRows.length})
                </button>
              </div>

              {activeTab === "matches" && (
                <select
                  value={filterConfidence}
                  onChange={(e) => setFilterConfidence(e.target.value)}
                  className="bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs text-slate-700 cursor-pointer"
                >
                  <option value="all">All Parcels</option>
                  <option value="conflicts">Flagged Conflicts</option>
                  <option value="pending">Pending Review</option>
                  <option value="accepted">Accepted</option>
                </select>
              )}
            </div>

            {activeTab === "matches" ? (
              <div className="space-y-3">
                {filteredMatches.length === 0 ? (
                  <div className="py-8 text-center text-sm text-slate-500">
                    {matchItems.length === 0
                      ? "No matching results available yet. Run spatial matching first."
                      : "No results match the selected filter."}
                  </div>
                ) : (
                  filteredMatches.map((item) => (
                    <div
                      key={item.id}
                      className="p-3.5 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors space-y-2.5 text-xs"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <div className="flex items-center gap-2">
                          <strong className="text-slate-900 font-semibold">
                            {item.id} ({item.featureType})
                          </strong>
                          {item.featureId && (
                            <>
                              <span className="text-slate-400">•</span>
                              <span className="text-blue-800 font-medium">
                                Feature #{item.featureId}
                              </span>
                            </>
                          )}
                          {item.matchId && (
                            <>
                              <span className="text-slate-400">•</span>
                              <span className="text-slate-500">
                                Match #{item.matchId}
                              </span>
                            </>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-[#166534]">
                            {item.aiConfidence != null
                              ? `Confidence: ${item.aiConfidence}%`
                              : "Confidence: —"}
                          </span>
                          <span
                            className={`px-2 py-0.2 rounded text-[10px] font-semibold ${
                              item.status === "Accepted"
                                ? "bg-emerald-50 text-[#166534] border border-emerald-200"
                                : item.status === "Rejected"
                                ? "bg-red-50 text-red-700 border border-red-200"
                                : "bg-amber-50 text-amber-800 border border-amber-200"
                            }`}
                          >
                            {item.status}
                          </span>
                        </div>
                      </div>

                      <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-slate-700 leading-relaxed">
                        <strong className="text-slate-900 block mb-0.5">
                          Details:
                        </strong>
                        {item.recommendation}
                      </div>

                      {/* Show properties if available */}
                      {item.properties &&
                        Object.keys(item.properties).length > 0 && (
                          <div className="flex flex-wrap gap-2 text-[11px] text-slate-500">
                            {Object.entries(item.properties)
                              .slice(0, 6)
                              .map(([key, val]) => (
                                <span
                                  key={key}
                                  className="bg-slate-50 px-2 py-0.5 rounded border border-slate-100"
                                >
                                  <strong>{key}:</strong> {String(val)}
                                </span>
                              ))}
                            {Object.keys(item.properties).length > 6 && (
                              <span className="text-slate-400">
                                +{Object.keys(item.properties).length - 6} more
                              </span>
                            )}
                          </div>
                        )}

                      <div className="flex items-center justify-end pt-1">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() =>
                              handleDecision(item.id, item.rawId, "Accepted")
                            }
                            className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-[#166534] border border-emerald-200 rounded text-xs font-semibold transition-colors cursor-pointer"
                          >
                            Accept
                          </button>
                          <button
                            onClick={() =>
                              handleDecision(item.id, item.rawId, "Rejected")
                            }
                            className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 rounded text-xs font-medium transition-colors cursor-pointer"
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                {attributeMappingRows.length === 0 ? (
                  <div className="py-8 text-center text-sm text-slate-500">
                    No attribute mappings available yet. Run the pipeline first.
                  </div>
                ) : (
                  <table className="w-full text-left text-xs text-slate-600">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px]">
                      <tr>
                        <th className="py-2.5 px-3">Source Field</th>
                        <th className="py-2.5 px-3">Target Field</th>
                        <th className="py-2.5 px-3">Mapping Type</th>
                        <th className="py-2.5 px-3">Confidence</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {attributeMappingRows.map((row) => (
                        <tr key={row.id}>
                          <td className="py-2.5 px-3 font-semibold text-slate-900">
                            {row.sourceField}
                          </td>
                          <td className="py-2.5 px-3 font-mono">
                            {row.targetField}
                          </td>
                          <td className="py-2.5 px-3 text-slate-500 capitalize">
                            {row.mappingType.replace(/_/g, " ")}
                          </td>
                          <td className="py-2.5 px-3 font-semibold text-[#166534]">
                            {row.confidence != null
                              ? `${row.confidence}%`
                              : "—"}
                          </td>
                          <td className="py-2.5 px-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                row.status === "approved"
                                  ? "bg-emerald-50 text-[#166534] border border-emerald-200"
                                  : row.status === "rejected"
                                  ? "bg-red-50 text-red-700 border border-red-200"
                                  : "bg-amber-50 text-amber-800 border border-amber-200"
                              }`}
                            >
                              {row.status}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {typeof row.id === "number" && (
                              <div className="inline-flex items-center gap-1">
                                <button
                                  onClick={() =>
                                    handleResolveMapping(row.id, "approved")
                                  }
                                  className="px-2 py-0.5 bg-emerald-50 hover:bg-emerald-100 text-[#166534] border border-emerald-200 rounded text-[11px] font-semibold transition-colors cursor-pointer"
                                >
                                  Approve
                                </button>
                                <button
                                  onClick={() =>
                                    handleResolveMapping(row.id, "rejected")
                                  }
                                  className="px-2 py-0.5 bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 rounded text-[11px] font-medium transition-colors cursor-pointer"
                                >
                                  Reject
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default Harmonization;
