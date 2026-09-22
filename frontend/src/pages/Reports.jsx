import { useState, useEffect, useMemo } from "react";
import {
  FileText,
  Download,
  Eye,
  Calendar,
  Layers,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Search,
  Filter,
  X,
  Printer,
  Share2,
  Building2,
  FileCheck,
  Clock,
  ArrowRight,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { requestExport, downloadExportFile } from "../api/exports";
import { getProjectSummary } from "../api/reports";


function Reports() {
  const { selectedProjectId, projects } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [activePreviewReport, setActivePreviewReport] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summaryData, setSummaryData] = useState(null);
  const [downloadingReport, setDownloadingReport] = useState(null);

  const activeProject = projects.find((p) => p.id === selectedProjectId);

  useEffect(() => {
    if (selectedProjectId) {
      loadReportData();
    }
  }, [selectedProjectId]);

  const loadReportData = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    try {
      const data = await getProjectSummary(selectedProjectId);
      setSummaryData(data);
    } catch (err) {
      console.error("Failed to load project summary report:", err);
      showToast(err.friendlyMessage || "Failed to load dynamic report statistics.", "error");
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = "success") => {
    setToastMessage({ text: message, type });
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleDownloadMasterDossier = async () => {
    if (!selectedProjectId) {
      showToast("Please select a project first.", "error");
      return;
    }
    showToast("Compiling Master Project Dossier ZIP (all artifacts)...");
    try {
      const res = await requestExport(selectedProjectId, "master_dossier", "zip");
      const exportId = res?.export_id || res?.id;
      if (exportId) {
        await downloadExportFile(exportId, `Master_Dossier_p${selectedProjectId}.zip`);
        showToast("Master Dossier ZIP downloaded successfully.");
      } else {
        showToast("Dossier generation completed.");
      }
    } catch (err) {
      showToast(err.friendlyMessage || "Failed to generate Master Dossier ZIP.", "error");
    }
  };

  const handleDownloadReport = async (report) => {
    if (!selectedProjectId) {
      showToast("Please select a project first.", "error");
      return;
    }
    setDownloadingReport(report.id);
    showToast(`Generating export for ${report.title}...`);
    try {
      let exportType = "harmonized_features";
      let format = "csv";

      if (report.category === "harmonization") {
        exportType = "harmonized_features";
        format = "geojson";
      } else if (report.category === "validation") {
        exportType = "validation_results";
        format = "csv";
      } else if (report.category === "conflicts") {
        exportType = "conflicts";
        format = "csv";
      } else if (report.category === "change_detection") {
        exportType = "change_detection";
        format = "csv";
      } else if (report.category === "records") {
        exportType = "title_ledger";
        format = "csv";
      }

      const res = await requestExport(selectedProjectId, exportType, format);
      const exportId = res?.export_id || res?.id;
      if (exportId) {
        const ext = format === "geopackage" ? "gpkg" : (format === "geojson" ? "geojson" : "csv");
        await downloadExportFile(exportId, `${report.id}_p${selectedProjectId}.${ext}`);
        showToast(`Report ${report.id} downloaded successfully.`);
      } else {
        showToast(`Report export completed.`);
      }
    } catch (err) {
      showToast(err.friendlyMessage || `Failed to download ${report.title}.`, "error");
    } finally {
      setDownloadingReport(null);
    }
  };

  const reportsList = useMemo(() => {
    if (summaryData && summaryData.reports && summaryData.reports.length > 0) {
      return summaryData.reports;
    }
    return [];
  }, [summaryData]);

  const filteredReports = reportsList.filter((item) => {
    const matchesCategory =
      selectedCategory === "all" || item.category === selectedCategory;
    const matchesSearch =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-5">
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-lg shadow-md text-xs font-semibold border ${
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
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Summary Reports & Executive Dossiers
            </h1>
            {loading && <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />}
          </div>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Download comprehensive analytical reports, topology compliance audits, and legal title registers for {activeProject?.name ? `Project: ${activeProject.name}` : "selected project"}.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadMasterDossier}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer self-start shadow-xs"
          >
            <Download size={13} />
            Download Master Dossier (ZIP)
          </button>
          <button
            onClick={loadReportData}
            className="p-1.5 bg-white border border-slate-200 rounded text-slate-600 hover:bg-slate-50 cursor-pointer"
            title="Refresh Report Data"
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
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
            placeholder="Search reports by title, ID, or keywords..."
            className="w-full bg-slate-50 border border-slate-200 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 text-xs text-slate-700 cursor-pointer"
          >
            <option value="all">All Report Types</option>
            <option value="harmonization">Harmonization</option>
            <option value="validation">Ingestion & CRS</option>
            <option value="conflicts">Conflicts</option>
            <option value="change_detection">Change Detection</option>
            <option value="records">Certified Records</option>
          </select>
        </div>
      </div>

      {/* Reports Grid */}
      {loading && reportsList.length === 0 ? (
        <div className="bg-white rounded-lg border border-slate-200 p-12 text-center text-slate-500">
          <Loader2 className="h-6 w-6 animate-spin text-emerald-600 mx-auto mb-2" />
          <p className="text-xs font-medium">Computing live project reports from PostgreSQL...</p>
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="bg-white rounded-lg border border-slate-200 p-12 text-center text-slate-400">
          <FileText className="h-8 w-8 mx-auto mb-2 text-slate-300" />
          <p className="text-xs font-medium text-slate-600">No reports found for this query.</p>
          <p className="text-[11px] text-slate-400 mt-1">Upload datasets and execute matching to generate project reports.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredReports.map((report) => (
            <div
              key={report.id}
              className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs hover:border-slate-300 transition-colors flex flex-col justify-between space-y-3"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-md bg-emerald-50 text-[#166534] flex items-center justify-center font-bold text-xs border border-emerald-200 flex-shrink-0">
                      <FileText size={16} />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 leading-tight">
                        {report.title}
                      </h3>
                      <span className="font-mono text-[10px] text-slate-400">
                        ID: {report.id} • {report.date}
                      </span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 bg-slate-100 text-slate-700 border border-slate-200 rounded text-[10px] font-mono">
                    {report.format}
                  </span>
                </div>

                <p className="text-xs text-slate-600 font-normal leading-relaxed">
                  {report.summary}
                </p>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 gap-2 pt-1">
                  {report.metrics.map((m, idx) => (
                    <div
                      key={idx}
                      className="p-2 bg-slate-50 rounded border border-slate-200 text-xs"
                    >
                      <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                        {m.label}
                      </span>
                      <strong className="text-slate-900 font-bold text-xs">{m.value}</strong>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between border-t border-slate-100 text-xs">
                <span className="text-[11px] text-slate-400">
                  Size: {report.fileSize} • By: {report.generatedBy}
                </span>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setActivePreviewReport(report)}
                    className="px-2.5 py-1 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded text-xs font-semibold cursor-pointer transition-colors"
                  >
                    Preview
                  </button>
                  <button
                    onClick={() => handleDownloadReport(report)}
                    disabled={downloadingReport === report.id}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#166534] hover:bg-emerald-900 text-white rounded text-xs font-semibold cursor-pointer transition-colors disabled:opacity-50"
                  >
                    {downloadingReport === report.id ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <Download size={12} />
                    )}
                    Download
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Report Preview Modal */}
      {activePreviewReport && (
        <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg border border-slate-200 max-w-xl w-full p-6 shadow-xl space-y-4 text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <FileText size={18} className="text-[#166534]" />
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">
                    {activePreviewReport.title}
                  </h4>
                  <span className="font-mono text-[10px] text-slate-400">
                    {activePreviewReport.id} • {activePreviewReport.date}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setActivePreviewReport(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={16} />
              </button>
            </div>

            <div className="space-y-3 text-slate-700">
              <div className="p-3 bg-slate-50 rounded border border-slate-200 space-y-1">
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Executive Abstract
                </span>
                <p className="leading-relaxed">{activePreviewReport.summary}</p>
              </div>

              <div className="p-3 bg-emerald-50 rounded border border-emerald-200 text-[#166534] space-y-1">
                <span className="text-[10px] font-semibold uppercase block">
                  Analytical Conclusion
                </span>
                <p className="text-emerald-950 font-medium">{activePreviewReport.executiveNote}</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {activePreviewReport.metrics.map((m, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-slate-50 rounded border border-slate-200"
                  >
                    <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                      {m.label}
                    </span>
                    <strong className="text-slate-900 font-bold text-xs">{m.value}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-2 border-t border-slate-100">
              <button
                onClick={() => setActivePreviewReport(null)}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded font-medium cursor-pointer"
              >
                Close
              </button>
              <button
                onClick={() => {
                  handleDownloadReport(activePreviewReport);
                  setActivePreviewReport(null);
                }}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded font-semibold cursor-pointer"
              >
                <Download size={13} />
                Download Dossier File
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reports;
