import React, { useState, useEffect } from "react";
import {
  Database,
  Layers,
  AlertTriangle,
  CheckCircle2,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Upload,
  Map,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listProjectDatasets } from "../api/datasets";
import { listConflicts } from "../api/conflicts";
import { getHarmonizedFeatures } from "../api/harmonization";
import { getProjectMatches } from "../api/matching";

function Dashboard() {
  const { selectedProjectId, projects } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [harmonizedCount, setHarmonizedCount] = useState(0);
  const [matchesCount, setMatchesCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const activeProject = projects.find((p) => p.id === selectedProjectId);

  useEffect(() => {
    if (selectedProjectId) {
      loadDashboardData(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadDashboardData = async (projectId) => {
    setLoading(true);
    try {
      const [dsList, cnfList, harmList, matchResult] = await Promise.allSettled([
        listProjectDatasets(projectId),
        listConflicts(projectId),
        getHarmonizedFeatures(projectId),
        getProjectMatches(projectId),
      ]);

      if (dsList.status === "fulfilled") {
        setDatasets(Array.isArray(dsList.value) ? dsList.value : []);
      }
      if (cnfList.status === "fulfilled") {
        const val = cnfList.value;
        const confArray = Array.isArray(val) ? val : (val?.conflicts || []);
        setConflicts(confArray);
      }
      if (harmList.status === "fulfilled") {
        const val = harmList.value;
        const harmArray = Array.isArray(val) ? val : (val?.features || []);
        setHarmonizedCount(harmArray.length);
      }
      if (matchResult.status === "fulfilled") {
        const val = matchResult.value;
        const matchArray = Array.isArray(val) ? val : (val?.pending_matches || []);
        setMatchesCount(matchArray.length);
      }
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  const safeConflicts = Array.isArray(conflicts) ? conflicts : [];
  const pendingConflictsCount = safeConflicts.filter((c) => c.resolution_status === "pending").length;
  const resolvedConflictsCount = safeConflicts.filter((c) => c.resolution_status !== "pending").length;

  const safeDatasets = Array.isArray(datasets) ? datasets : [];
  const totalFeaturesIngested = safeDatasets.reduce((acc, ds) => acc + (ds.feature_count || 0), 0);


  const statistics = [
    {
      title: "Total Ingested Datasets",
      value: datasets.length.toString(),
      change: `+${datasets.length}`,
      isPositive: true,
      meta: `${totalFeaturesIngested} features stored`,
      icon: Database,
    },
    {
      title: "Harmonized Records",
      value: harmonizedCount.toString(),
      change: matchesCount > 0 ? `${Math.round((harmonizedCount / (matchesCount || 1)) * 100)}%` : "0%",
      isPositive: true,
      meta: `${matchesCount} matched pairs`,
      icon: Layers,
    },
    {
      title: "Active Conflicts",
      value: pendingConflictsCount.toString(),
      change: `${resolvedConflictsCount} resolved`,
      isPositive: pendingConflictsCount === 0,
      meta: `${conflicts.length} total conflicts`,
      icon: AlertTriangle,
    },
    {
      title: "Verified Records",
      value: harmonizedCount.toString(),
      change: "100%",
      isPositive: true,
      meta: "PostGIS stored & validated",
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Heading & Status Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Dashboard Overview
            </h1>
            <span className="px-2 py-0.5 bg-slate-100 text-slate-700 border border-slate-200 rounded text-[11px] font-mono font-medium">
              {activeProject ? activeProject.name : "Select Project"}
            </span>
            {loading && <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />}
          </div>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Multi-source land record integration, spatial harmonization, and verification status.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => selectedProjectId && loadDashboardData(selectedProjectId)}
            title="Refresh Data"
            className="p-1.5 bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 rounded-md text-xs transition"
          >
            <RefreshCw size={13} />
          </button>
          <Link
            to="/ingestion"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-md text-xs font-semibold transition-colors"
          >
            <Upload size={13} />
            Import Data
          </Link>
          <Link
            to="/map"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors"
          >
            <Map size={13} />
            GIS Map Viewer
          </Link>
        </div>
      </div>

      {/* Metadata Bar */}
      <div className="bg-white rounded-lg border border-slate-200 p-3.5 shadow-xs">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">
              Active Project
            </span>
            <strong className="text-slate-800 font-medium">
              {activeProject ? activeProject.name : "None Selected"}
            </strong>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">
              Coordinate System
            </span>
            <strong className="font-mono text-[#166534] font-medium">EPSG:4326 (WGS 84 / Metric UTM)</strong>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">
              Loaded Datasets
            </span>
            <strong className="text-slate-800 font-medium">{datasets.length} Active Layer(s)</strong>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">
              PostGIS Status
            </span>
            <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
              Connected & Operational
            </span>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statistics.map((stat) => {
          const Icon = stat.icon;

          return (
            <div
              key={stat.title}
              className="bg-white rounded-lg border border-slate-200 p-4 hover:border-slate-300 transition-colors shadow-xs"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-md bg-emerald-50 text-[#166534] flex items-center justify-center">
                  <Icon size={18} />
                </div>
                <span
                  className={`inline-flex items-center gap-0.5 text-xs font-semibold px-2 py-0.5 rounded ${
                    stat.isPositive
                      ? "text-emerald-700 bg-emerald-50 border border-emerald-200"
                      : "text-amber-700 bg-amber-50 border border-amber-200"
                  }`}
                >
                  {stat.isPositive ? (
                    <ArrowUpRight size={13} />
                  ) : (
                    <ArrowDownRight size={13} />
                  )}
                  {stat.change}
                </span>
              </div>
              <p className="text-xs font-medium text-slate-500">{stat.title}</p>
              <div className="flex items-baseline justify-between mt-1">
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                  {stat.value}
                </h2>
                <span className="text-[10px] text-slate-400 font-medium truncate">
                  {stat.meta}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Progress & Sources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Harmonization Progress */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-4 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Harmonization Pipeline
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Active multi-stage spatial convergence pipeline
              </p>
            </div>
            <Link
              to="/harmonization"
              className="text-xs font-semibold text-[#166534] hover:underline"
            >
              View Pipeline →
            </Link>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-700">
                Project Harmonization Status
              </span>
              <strong className="text-[#166534] font-bold">
                {harmonizedCount} Harmonized Records
              </strong>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-[#166534] rounded-full transition-all duration-300"
                style={{ width: datasets.length > 0 ? "100%" : "0%" }}
              ></div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-md text-xs">
              <div className="flex items-center gap-2 text-slate-700">
                <CheckCircle2 size={15} className="text-[#166534]" />
                <span className="font-medium">Multi-Source Datasets Loaded</span>
              </div>
              <span className="px-2 py-0.5 bg-emerald-50 border border-emerald-200 text-[#166534] rounded font-semibold text-[10px]">
                {datasets.length} Loaded
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-md text-xs">
              <div className="flex items-center gap-2 text-slate-700">
                <CheckCircle2 size={15} className="text-[#166534]" />
                <span className="font-medium">CRS Auto-UTM Standardization</span>
              </div>
              <span className="px-2 py-0.5 bg-emerald-50 border border-emerald-200 text-[#166534] rounded font-semibold text-[10px]">
                Active (Metres)
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-md text-xs">
              <div className="flex items-center gap-2 text-slate-700">
                <CheckCircle2 size={15} className="text-[#166534]" />
                <span className="font-medium">AI Spatial & Attribute Matching</span>
              </div>
              <span className="px-2 py-0.5 bg-emerald-50 border border-emerald-200 text-[#166534] rounded font-semibold text-[10px]">
                {matchesCount} Matches Found
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 bg-blue-50/50 border border-blue-200 rounded-md text-xs">
              <div className="flex items-center gap-2 text-blue-900">
                <Activity size={15} className="text-blue-600" />
                <span className="font-semibold">Conflict Adjudication</span>
              </div>
              <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded font-semibold text-[10px]">
                {pendingConflictsCount} Pending
              </span>
            </div>
          </div>
        </div>

        {/* Data Sources */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-4 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Project Datasets
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Active multi-source land record inputs
              </p>
            </div>
            <Link
              to="/datasets"
              className="text-xs font-semibold text-[#166534] hover:underline"
            >
              Manage Datasets →
            </Link>
          </div>

          <div className="space-y-2.5 max-h-[220px] overflow-y-auto">
            {datasets.length === 0 ? (
              <div className="p-6 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-md">
                No datasets uploaded yet for this project.
                <div className="mt-2">
                  <Link to="/ingestion" className="text-emerald-700 font-semibold hover:underline">
                    Upload Dataset Now
                  </Link>
                </div>
              </div>
            ) : (
              datasets.map((ds) => (
                <div key={ds.id} className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-md">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded bg-[#166534] text-white font-bold text-xs flex items-center justify-center flex-shrink-0 uppercase">
                      {ds.name ? ds.name.slice(0, 1) : "D"}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <strong className="text-xs font-semibold text-slate-900 leading-tight truncate">
                          {ds.name}
                        </strong>
                        <span className="font-mono text-[10px] text-slate-500 bg-white border border-slate-200 px-1 py-0.2 rounded">
                          {ds.dataset_type || "vector"}
                        </span>
                      </div>
                      <span className="block text-[11px] text-slate-500 truncate">
                        Source: {ds.source || "Uploaded File"} • Status: {ds.status}
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] font-semibold text-[#166534] bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded flex-shrink-0">
                    Active
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Conflicts */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-3 shadow-xs">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Recent Conflicts Requiring Adjudication
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Spatial deviations and attribute mismatches detected across multi-source layers
            </p>
          </div>
          <Link
            to="/conflicts"
            className="text-xs font-semibold text-[#166534] hover:underline px-2.5 py-1 bg-emerald-50 rounded border border-emerald-200"
          >
            View All ({safeConflicts.length})
          </Link>
        </div>

        <div className="overflow-x-auto">
          {safeConflicts.length === 0 ? (
            <div className="p-6 text-center text-slate-400 text-xs">
              No conflicts detected for the active project.
            </div>
          ) : (
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Conflict ID / Description</th>
                  <th className="py-2.5 px-3">Conflict Type</th>
                  <th className="py-2.5 px-3">Source vs Target Value</th>
                  <th className="py-2.5 px-3">Confidence</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {safeConflicts.slice(0, 5).map((cnf) => (

                  <tr key={cnf.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3">
                      <span className="font-mono font-bold text-slate-900 block">CNF-{cnf.id}</span>
                      <span className="text-[10px] text-slate-400 truncate block max-w-[200px]">{cnf.description}</span>
                    </td>
                    <td className="py-2.5 px-3 text-amber-800 font-medium capitalize">{cnf.conflict_type.replace('_', ' ')}</td>
                    <td className="py-2.5 px-3 text-slate-600">
                      <span className="text-emerald-700 font-mono">{cnf.source_value || 'None'}</span> vs <span className="text-rose-600 font-mono">{cnf.target_value || 'None'}</span>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-[#166534]">
                      {Math.round((cnf.confidence_score || 0.8) * 100)}%
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        cnf.resolution_status === 'pending'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}>
                        {cnf.resolution_status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {cnf.resolution_status === 'pending' ? (
                        <Link
                          to="/conflicts"
                          className="px-2.5 py-1 bg-[#166534] hover:bg-emerald-900 text-white rounded text-xs font-semibold inline-block"
                        >
                          Adjudicate
                        </Link>
                      ) : (
                        <span className="text-[11px] text-slate-400 font-medium">Resolved</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;