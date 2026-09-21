import React, { useState, useEffect, useMemo } from "react";
import {
  Database,
  Search,
  Upload,
  Trash2,
  Eye,
  CheckCircle2,
  X,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listProjectDatasets } from "../api/datasets";

function Datasets() {
  const { selectedProjectId } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSource, setSelectedSource] = useState("all");
  const [activeModalDataset, setActiveModalDataset] = useState(null);

  useEffect(() => {
    if (selectedProjectId) {
      loadDatasets(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadDatasets = async (projectId) => {
    setLoading(true);
    try {
      const data = await listProjectDatasets(projectId);
      setDatasets(data || []);
    } catch (err) {
      console.error("Failed to load datasets:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredDatasets = useMemo(() => {
    return datasets.filter((d) => {
      const nameMatch = (d.name || "").toLowerCase().includes(searchQuery.toLowerCase());
      const sourceMatch = (d.source || "").toLowerCase().includes(searchQuery.toLowerCase());
      const typeMatch = (d.dataset_type || "").toLowerCase().includes(searchQuery.toLowerCase());

      const matchesSource =
        selectedSource === "all" || (d.source || "").toLowerCase() === selectedSource.toLowerCase();

      return (nameMatch || sourceMatch || typeMatch) && matchesSource;
    });
  }, [datasets, searchQuery, selectedSource]);

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Dataset Repository</h1>
            {loading && <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />}
          </div>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Registered PostgreSQL/PostGIS spatial and tabular land records repository.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => selectedProjectId && loadDatasets(selectedProjectId)}
            className="p-1.5 bg-white hover:bg-slate-50 border border-slate-200 rounded text-slate-600"
            title="Refresh Datasets"
          >
            <RefreshCw size={14} />
          </button>
          <Link
            to="/ingestion"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors self-start"
          >
            <Upload size={14} />
            + Import Dataset
          </Link>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white rounded-lg border border-slate-200 p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by dataset name, source, or type..."
            className="w-full bg-slate-50 border border-slate-200 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Sources</option>
            <option value="cadastral">Cadastral</option>
            <option value="drone">Drone Survey</option>
            <option value="municipal">Municipal GIS</option>
            <option value="revenue">Revenue Records</option>
            <option value="gnss">GNSS / CORS</option>
          </select>
        </div>
      </div>

      {/* Main Table View */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          {filteredDatasets.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              No datasets found in PostgreSQL for this project.
              <div className="mt-2">
                <Link to="/ingestion" className="text-emerald-700 font-semibold hover:underline">
                  Upload a dataset now
                </Link>
              </div>
            </div>
          ) : (
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Dataset ID</th>
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Source</th>
                  <th className="py-2.5 px-3">File Name</th>
                  <th className="py-2.5 px-3">Features</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDatasets.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-semibold text-slate-900">DS-{d.id}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-900">{d.name}</td>
                    <td className="py-2.5 px-3 font-mono text-[11px] uppercase">{d.dataset_type || "vector"}</td>
                    <td className="py-2.5 px-3 text-slate-700">{d.source || "Uploaded File"}</td>
                    <td className="py-2.5 px-3 font-mono text-[10px] text-slate-500 truncate max-w-[150px]" title={d.file_name}>
                      {d.file_name || "N/A"}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">{d.feature_count || 0}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 bg-emerald-50 text-[#166534] border border-emerald-200 rounded text-[10px] font-semibold capitalize">
                        {d.status || "uploaded"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right space-x-1">
                      <button
                        onClick={() => setActiveModalDataset(d)}
                        className="p-1 text-slate-500 hover:text-slate-900 rounded"
                        title="Inspect"
                      >
                        <Eye size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Dataset Details Modal */}
      {activeModalDataset && (
        <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg border border-slate-200 max-w-lg w-full p-6 shadow-xl space-y-4 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div>
                <h4 className="font-bold text-slate-900 text-sm">{activeModalDataset.name}</h4>
                <span className="text-[11px] text-slate-500">
                  ID: DS-{activeModalDataset.id} • Type: {activeModalDataset.dataset_type}
                </span>
              </div>
              <button onClick={() => setActiveModalDataset(null)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
              </button>
            </div>

            <div className="space-y-2 text-slate-700">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">File Name:</span>
                <span className="font-mono text-right max-w-xs">{activeModalDataset.file_name || "N/A"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">File Path:</span>
                <span className="font-mono text-[10px] text-right max-w-xs truncate">{activeModalDataset.file_path || "N/A"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Features Count:</span>
                <strong>{activeModalDataset.feature_count || 0}</strong>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Processing Status:</span>
                <strong className="text-[#166534] capitalize">{activeModalDataset.status}</strong>
              </div>
            </div>

            <div className="pt-3 flex justify-end">
              <button
                onClick={() => setActiveModalDataset(null)}
                className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Datasets;
