import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Database,
  Layers,
  Map,
  AlertTriangle,
  Settings,
  Upload,
  CheckSquare,
  FileCheck,
  TrendingUp,
  Shapes,
  FileText,
  Clock,
} from "lucide-react";

function Sidebar() {
  const navigation = [
    {
      group: "Overview",
      items: [
        { name: "Dashboard", href: "/", icon: LayoutDashboard },
      ],
    },
    {
      group: "Data Ingestion",
      items: [
        { name: "Import Datasets", href: "/ingestion", icon: Upload },
        { name: "Dataset Repository", href: "/datasets", icon: Database },
      ],
    },
    {
      group: "Processing",
      items: [
        { name: "Harmonization", href: "/harmonization", icon: Layers },
        { name: "Topology Validation", href: "/topology", icon: Shapes },
      ],
    },
    {
      group: "Spatial Analysis",
      items: [
        { name: "GIS Map Viewer", href: "/map", icon: Map },
        { name: "Conflict Center", href: "/conflicts", icon: AlertTriangle },
        { name: "Change Detection", href: "/changes", icon: TrendingUp },
      ],
    },
    {
      group: "Verification",
      items: [
        { name: "Pending Review", href: "/review", icon: CheckSquare },
        { name: "Verified Records", href: "/verified", icon: FileCheck },
      ],
    },
    {
      group: "Reports & Audit",
      items: [
        { name: "Summary Reports", href: "/reports", icon: FileText },
        { name: "Audit Trail", href: "/audit", icon: Clock },
      ],
    },
    {
      group: "System",
      items: [
        { name: "Settings", href: "/settings", icon: Settings },
      ],
    },
  ];

  return (
    <aside className="w-60 h-screen fixed left-0 top-0 bg-white border-r border-slate-200 flex flex-col z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-200">
        <div className="w-8 h-8 rounded-lg bg-[#166534] flex items-center justify-center text-white flex-shrink-0">
          <Map size={18} />
        </div>
        <div className="min-w-0">
          <h1 className="text-sm font-bold text-slate-900 tracking-tight leading-none">
            BHUVISTAAR
          </h1>
          <span className="block text-[10px] font-medium text-slate-500 tracking-wide mt-1">
            DoLR • Land Records
          </span>
        </div>
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 px-3 py-3 overflow-y-auto space-y-4">
        {navigation.map((section) => (
          <div key={section.group}>
            <p className="px-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              {section.group}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    end={item.href === "/"}
                    className={({ isActive }) =>
                      `flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-xs transition-colors ${
                        isActive
                          ? "bg-emerald-50 text-[#166534] font-semibold"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 font-medium"
                      }`
                    }
                  >
                    <Icon size={16} className="flex-shrink-0" />
                    <span className="truncate">{item.name}</span>
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Node Status Footer */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/50">
        <div className="flex items-center gap-2 px-1">
          <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
          <div className="min-w-0">
            <span className="text-[11px] font-semibold text-slate-800 block leading-tight">
              Node Operational
            </span>
            <span className="text-[10px] text-slate-500 font-normal truncate block">
              SIH26013 • Urban Ward 17
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;