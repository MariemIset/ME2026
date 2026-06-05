import { Outlet, Navigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LayoutDashboard, Users, HeartPulse, BarChart3, TrendingUp, MessageSquare, LogOut } from 'lucide-react';

const DashboardLayout = () => {
  const { role, logout } = useAuth();
  const location = useLocation();

  if (!role) {
    return <Navigate to="/login" replace />;
  }

  if (role === "Client") {
    return <Navigate to="/feedback" replace />;
  }

  const allNavItems = [
    { path: "/ceo-overview", label: "Executive Overview", icon: BarChart3 },
    { path: "/churn-risk", label: "Churn & Behavior", icon: LayoutDashboard },
    { path: "/loyalty-economics", label: "Loyalty Economics", icon: Users },
    { path: "/satisfaction-drivers", label: "Satisfaction & NLP", icon: HeartPulse },
    { path: "/marketing-loyalty", label: "Marketing Loyalty", icon: TrendingUp },
    { path: "/process-management", label: "Process Management", icon: MessageSquare },
  ];

  let navItems = allNavItems;
  if (role === "Marketing") {
    navItems = allNavItems.filter(item => ["/loyalty-economics", "/marketing-loyalty"].includes(item.path));
  } else if (role === "Process") {
    navItems = allNavItems.filter(item => ["/satisfaction-drivers", "/process-management"].includes(item.path));
  }

  if (location.pathname !== "/" && !navItems.some(item => item.path === location.pathname)) {
    return <Navigate to={navItems[0].path} replace />;
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200 selection:bg-rose-500/30">
      <aside className="w-72 bg-slate-900/50 backdrop-blur-xl border-r border-slate-800/50 flex flex-col shrink-0 transition-all duration-300">
        <div className="h-20 flex items-center px-8 border-b border-slate-800/50">
          <div className="flex items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 124.4 64" className="w-10 h-6">
              <path fill="#d81e05" fill-rule="evenodd" clip-rule="evenodd" d="M13.6,53c16.5-13.3,28.2-24.8,31.7-31c1.5-2.4,2-4.7,1.1-6.5c-1.5-3.5-7-4.5-13.6-3.2C62.7,5.5,93.2,1.4,123.8,0c0.3,0,0.6,0.2,0.6,0.5c0,0.2-0.1,0.5-0.4,0.5c-38.8,12.6-74.1,33-104,59.4c0,0-0.1,0.1-0.1,0.1L0.3,64c-0.3,0-0.4-0.3-0.2-0.5C4.7,60.1,9.2,56.6,13.6,53"/>
              <path fill="#93282c" fill-rule="evenodd" clip-rule="evenodd" d="M11,17.4c-0.4,0.1-0.9,0.2-1.3,0.4c-0.3,0.1-0.2,0.4,0,0.5l7.4,1.1L30,21.2c0.1,0,0.1,0,0.1,0c9.1-4.3,15.1-6,16.5-4.1c0.4,0.6,0.3,1.5-0.1,2.6c-0.2,0.4-0.4,0.8-0.6,1.3c1.4-2.3,1.9-4.4,1.1-6.2c-1.5-3.3-6.6-4.3-13.1-3C26.2,13.5,18.6,15.4,11,17.4"/>
            </svg>
            <span className="text-xl font-black text-white tracking-tighter">ALI</span>
          </div>
        </div>

        <div className="px-8 py-6">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-4">Dashboards</p>
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (location.pathname === "/" && item.path === "/ceo-overview");
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden ${
                    isActive
                      ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent"
                  }`}
                >
                  {isActive && <div className="absolute left-0 top-0 bottom-0 w-1 bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.8)]"></div>}
                  <Icon className={`mr-3 h-5 w-5 transition-transform duration-300 ${isActive ? "scale-110" : "group-hover:scale-110"}`} />
                  <span className="font-medium text-sm">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="mt-auto p-8 border-t border-slate-800/50">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs text-slate-500">Logged in as</span>
              <span className="text-sm font-semibold text-slate-300">{role}</span>
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all shadow-sm hover:shadow-[0_0_10px_rgba(244,63,94,0.2)]"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-rose-500/5 blur-[120px] rounded-full pointer-events-none"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/5 blur-[120px] rounded-full pointer-events-none"></div>

        <header className="h-20 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/50 flex items-center px-10 justify-between shrink-0 z-10">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              {navItems.find(i => i.path === location.pathname)?.label || "Executive Overview"}
            </h1>
            <p className="text-xs text-slate-400 mt-1">Real-time dynamic insights</p>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-10 z-10 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
