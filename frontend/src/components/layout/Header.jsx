import React, { useState } from "react";
import { Search, Bell, FolderPlus, LogOut, Plus, X } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { createProject } from "../../api/projects";

function Header() {
  const location = useLocation();
  const { user, projects, selectedProjectId, changeSelectedProject, refreshProjects, logout } = useAuth();

  const [showModal, setShowModal] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [projectDesc, setProjectDesc] = useState("");
  const [creating, setCreating] = useState(false);

  const getPageTitle = () => {
    switch (location.pathname) {
      case "/ingestion":
        return { title: "Data Ingestion", section: "Data / Import" };
      case "/datasets":
        return { title: "Dataset Repository", section: "Data / Datasets" };
      case "/harmonization":
        return { title: "Harmonization Pipeline", section: "Processing / Harmonization" };
      case "/topology":
        return { title: "Topology Validation", section: "Processing / Topology" };
      case "/map":
        return { title: "GIS Map Viewer", section: "Analysis / Map" };
      case "/conflicts":
        return { title: "Conflict Resolution Center", section: "Analysis / Conflicts" };
      case "/changes":
        return { title: "Change Detection", section: "Analysis / Change Detection" };
      case "/review":
        return { title: "Pending Verification", section: "Verification / Review" };
      case "/verified":
        return { title: "Verified Land Records", section: "Verification / Records" };
      case "/reports":
        return { title: "Summary Reports", section: "Reporting / Reports" };
      case "/audit":
        return { title: "Audit Trail", section: "Reporting / Audit Trail" };
      case "/settings":
        return { title: "System Settings", section: "System / Settings" };
      case "/":
      default:
        return { title: "Dashboard Overview", section: "Overview / Dashboard" };
    }
  };

  const { title, section } = getPageTitle();

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!projectName.trim()) return;
    setCreating(true);
    try {
      const newProj = await createProject(projectName, projectDesc);
      await refreshProjects();
      changeSelectedProject(newProj.id);
      setShowModal(false);
      setProjectName("");
      setProjectDesc("");
    } catch (err) {
      alert(err.friendlyMessage || "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Page Title & Breadcrumb */}
      <div>
        <h2 className="text-sm font-bold text-slate-900 leading-tight">
          {title}
        </h2>
        <span className="text-[11px] text-slate-500 font-medium">
          {section}
        </span>
      </div>

      {/* Header Actions & Project Selector */}
      <div className="flex items-center gap-3">
        {/* Project Selector */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-md px-2 py-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase">Project:</span>
          <select
            value={selectedProjectId || ""}
            onChange={(e) => changeSelectedProject(e.target.value)}
            className="bg-transparent text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer"
          >
            {projects.length === 0 ? (
              <option value="">No Projects Available</option>
            ) : (
              projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (ID: {p.id})
                </option>
              ))
            )}
          </select>

          <button
            onClick={() => setShowModal(true)}
            title="Create New Project"
            className="p-1 text-emerald-700 hover:bg-emerald-50 rounded transition"
          >
            <Plus size={14} />
          </button>
        </div>

        {/* Divider */}
        <div className="h-6 w-[1px] bg-slate-200"></div>

        {/* User Info & Logout */}
        <div className="flex items-center gap-2 pl-1">
          <div className="w-8 h-8 rounded-md bg-[#166534] text-white flex items-center justify-center text-xs font-bold uppercase">
            {user?.name ? user.name.slice(0, 2) : "US"}
          </div>
          <div className="text-left hidden sm:block">
            <span className="text-xs font-semibold text-slate-800 block leading-tight">
              {user?.name || user?.email || "User"}
            </span>
            <span className="text-[10px] text-slate-500 font-medium leading-tight">
              GIS Officer
            </span>
          </div>

          <button
            onClick={logout}
            title="Sign Out"
            className="ml-2 p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-md transition"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>

      {/* New Project Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <FolderPlus className="h-4 w-4 text-emerald-600" />
                Create New Land Record Project
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="e.g. Bangalore Urban Cadastral 2026"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:border-emerald-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Description</label>
                <textarea
                  rows={3}
                  value={projectDesc}
                  onChange={(e) => setProjectDesc(e.target.value)}
                  placeholder="e.g. Multi-source parcel boundary harmonization and ULPIN integration."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:border-emerald-600"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-lg shadow disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
}

export default Header;