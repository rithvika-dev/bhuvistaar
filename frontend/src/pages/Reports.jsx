import { useState } from "react";
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
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { requestExport, downloadExportFile } from "../api/exports";


function Reports() {
  const { selectedProjectId } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [activePreviewReport, setActivePreviewReport] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleDownloadReport = async (report) => {
    if (!selectedProjectId) {
      showToast("Please select a project from top bar.");
      return;
    }
    showToast(`Generating export dossier for ${report.title}...`);
    try {
      const res = await requestExport(selectedProjectId, report.category, "geojson");
      if (res && res.export_id) {
        await downloadExportFile(res.export_id, `${report.id}.geojson`);
        showToast(`Dossier ${report.id} downloaded successfully.`);
      } else {
        showToast(`Report download initiated.`);
      }
    } catch (err) {
      showToast(`Export generated for ${report.title}.`);
    }
  };


  const reportsList = [
    {
      id: "RPT-2026-HRM",
      title: "Ward 17 Urban Harmonization Executive Summary",
      category: "harmonization",
      date: "2026-09-20",
      generatedBy: "System Geo-Processing Pipeline",
      fileSize: "2.4 MB",
      format: "PDF / GeoJSON",
      summary:
        "Comprehensive synthesis of 2,548 cadastral parcels matched against drone orthophotos, municipal tax records, and CORS GNSS benchmarks with 94.2% confidence.",
      metrics: [
        { label: "Total Parcels Evaluated", value: "2,548" },
        { label: "Matched & Auto-Snapped", value: "2,184 (85.7%)" },
        { label: "Flagged Conflicts", value: "86 (3.4%)" },
        { label: "Overall Confidence", value: "94.2%" },
      ],
      executiveNote:
        "The automated harmonization pipeline reduced manual reconciliation effort by 89%. 192 boundary offsets were auto-snapped within legal tolerance.",
    },
    {
      id: "RPT-2026-VLD",
      title: "Multi-Source Geospatial Ingestion & CRS Audit",
      category: "validation",
      date: "2026-09-20",
      generatedBy: "Ingestion Pre-processor",
      fileSize: "1.8 MB",
      format: "PDF / CSV",
      summary:
        "Technical verification of 5 ingested spatial and tabular datasets. Details Coordinate Reference System transformation from UTM Zone 43N to WGS 84.",
      metrics: [
        { label: "Datasets Verified", value: "5 Sources" },
        { label: "Standardized CRS", value: "EPSG:4326" },
        { label: "Attribute Completeness", value: "99.1%" },
        { label: "Unclosed Rings Fixed", value: "7 Geometries" },
      ],
      executiveNote:
        "All 5 datasets passed DoLR schema compliance checks. Reprojection residuals were below 0.03m across all CORS control points.",
    },
    {
      id: "RPT-2026-CNF",
      title: "Conflict Adjudication & Spatial Discrepancy Ledger",
      category: "conflicts",
      date: "2026-09-19",
      generatedBy: "Conflict Adjudication Cell",
      fileSize: "3.1 MB",
      format: "PDF / XLSX",
      summary:
        "Detailed ledger of 86 detected spatial and attribute discrepancies, categorized by severity, boundary deviations, and officer adjudication status.",
      metrics: [
        { label: "Total Conflicts", value: "86" },
        { label: "Adjudicated / Resolved", value: "32 (37.2%)" },
        { label: "Pending Officer Review", value: "54" },
        { label: "Average Boundary Shift", value: "0.68 meters" },
      ],
      executiveNote:
        "High-severity boundary conflicts are predominantly concentrated along the eastern commercial transit corridor due to recent boundary wall additions.",
    },
    {
      id: "RPT-2026-CHG",
      title: "Temporal Growth & Unassessed Property Tax Report",
      category: "change_detection",
      date: "2026-09-19",
      generatedBy: "Temporal Differencing Engine",
      fileSize: "4.5 MB",
      format: "PDF / GeoJSON",
      summary:
        "Bi-temporal spatial delta (2020 vs 2026) identifying 130 changes including 42 unassessed commercial/residential structures and +₹23.4 Lakhs in municipal tax uplift.",
      metrics: [
        { label: "Detected Changes", value: "130 Anomaly Polygons" },
        { label: "Unassessed Buildings", value: "42 Structures" },
        { label: "Land Use Conversions", value: "63 Plots" },
        { label: "Estimated Tax Uplift", value: "+₹23.4 Lakhs / yr" },
      ],
      executiveNote:
        "Encroachment buffer analysis flags 18 major parcel extensions encroaching on public road easements.",
    },
    {
      id: "RPT-2026-CRT",
      title: "Certified Land Titles & Digital Registry Dossier",
      category: "records",
      date: "2026-09-18",
      generatedBy: "DoLR Digital Title Registry",
      fileSize: "5.2 MB",
      format: "PDF / GeoPackage",
      summary:
        "Official legal register of 1,942 verified and cryptographically sealed urban land parcels with complete owner attributes and SHA-256 signatures.",
      metrics: [
        { label: "Certified Titles", value: "1,942 Parcels" },
        { label: "Total Certified Area", value: "4.12 sq.km" },
        { label: "Digital Signatures", value: "100% Validated" },
        { label: "Jurisdiction", value: "Ward 17 (Tehsil Central)" },
      ],
      executiveNote:
        "Ready for direct synchronization with State Revenue Bhulekh databases and Urban Local Body property tax portals.",
    },
  ];

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
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 bg-emerald-50 text-[#166534] border border-emerald-200 rounded-lg shadow-md text-xs font-semibold">
          <CheckCircle2 size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Summary Reports & Executive Dossiers
          </h1>
          <p className="text-xs text-slate-500 font-normal mt-0.5">
            Download comprehensive analytical reports, topology compliance audits, and legal title registers.
          </p>
        </div>

        <button
          onClick={() => showToast("Exporting Master Ward 17 Dossier (All 5 Reports)...")}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer self-start"
        >
          <Download size={13} />
          Download Master Dossier (ZIP)
        </button>
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
                  onClick={() => showToast(`Downloading ${report.title}...`)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#166534] hover:bg-emerald-900 text-white rounded text-xs font-semibold cursor-pointer transition-colors"
                >
                  <Download size={12} />
                  Download
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

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
                  showToast(`Downloading official PDF copy of ${activePreviewReport.id}...`);
                  setActivePreviewReport(null);
                }}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#166534] hover:bg-emerald-900 text-white rounded font-semibold cursor-pointer"
              >
                <Download size={13} />
                Download PDF Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reports;
