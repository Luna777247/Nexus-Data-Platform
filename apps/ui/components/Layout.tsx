
import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useStore } from '../store';
import { 
  LayoutDashboard, 
  Database, 
  BarChart3, 
  Search, 
  ShieldCheck, 
  Activity, 
  Users, 
  Settings, 
  Menu, 
  X, 
  LogOut,
  Bell,
  Sun,
  Moon,
  ChevronRight
} from 'lucide-react';
import { UserRole } from '../types';

const SidebarItem: React.FC<{ 
  to: string; 
  icon: React.ReactNode; 
  label: string; 
  collapsed: boolean;
  allowedRoles?: UserRole[];
}> = ({ to, icon, label, collapsed, allowedRoles }) => {
  const { user } = useStore();
  
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return null;
  }

  return (
    <NavLink 
      to={to} 
      className={({ isActive }) => `
        flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
        ${isActive 
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-200' 
          : 'text-slate-600 hover:bg-blue-50 hover:text-blue-600 dark:text-slate-400 dark:hover:bg-slate-800'
        }
      `}
    >
      <div className="flex-shrink-0">{icon}</div>
      {!collapsed && (
        <span className="font-medium whitespace-nowrap overflow-hidden text-ellipsis">
          {label}
        </span>
      )}
      {!collapsed && (
        <div className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
          <ChevronRight size={16} />
        </div>
      )}
    </NavLink>
  );
};

const Layout: React.FC = () => {
  const { sidebarOpen, toggleSidebar, user, logout, theme, toggleTheme } = useStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { to: '/explorer', icon: <Database size={20} />, label: 'Data Explorer' },
    { to: '/analytics', icon: <BarChart3 size={20} />, label: 'Analytics & BI' },
    { to: '/logs', icon: <Search size={20} />, label: 'Log & Search' },
    { to: '/quality', icon: <ShieldCheck size={20} />, label: 'Quality & Lineage' },
    { to: '/monitoring', icon: <Activity size={20} />, label: 'Monitoring' },
    { to: '/users', icon: <Users size={20} />, label: 'User Management', roles: [UserRole.ADMIN] },
    { to: '/settings', icon: <Settings size={20} />, label: 'Settings' },
  ];

  return (
    <div className={`flex h-screen overflow-hidden ${theme === 'dark' ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      {/* Sidebar */}
      <aside 
        className={`
          ${sidebarOpen ? 'w-64' : 'w-20'} 
          bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 
          transition-all duration-300 ease-in-out flex flex-col z-20
        `}
      >
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold shadow-md">N</div>
            {sidebarOpen && <span className="text-xl font-bold tracking-tight text-slate-800 dark:text-white">Nexus</span>}
          </div>
          <button onClick={toggleSidebar} className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
          {navItems.map((item) => (
            <SidebarItem 
              key={item.to} 
              {...item} 
              collapsed={!sidebarOpen} 
              allowedRoles={item.roles}
            />
          ))}
        </nav>

        <div className="p-4 border-t border-slate-100 dark:border-slate-800">
          <button 
            onClick={handleLogout}
            className={`flex items-center gap-3 w-full px-4 py-3 text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-xl transition-colors ${!sidebarOpen && 'justify-center'}`}
          >
            <LogOut size={20} />
            {sidebarOpen && <span className="font-medium">Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Navbar */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-8 z-10 sticky top-0">
          <h1 className="text-lg font-semibold capitalize">
            {window.location.hash.split('/')[1] || 'Dashboard'}
          </h1>

          <div className="flex items-center gap-4">
            <button 
              onClick={toggleTheme}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
            >
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>
            <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors relative">
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-slate-900"></span>
            </button>
            <div className="h-8 w-px bg-slate-200 dark:bg-slate-800 mx-1"></div>
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-semibold">{user?.username}</p>
                <p className="text-xs text-slate-500">{user?.role}</p>
              </div>
              <img 
                src={`https://picsum.photos/seed/${user?.id}/32/32`} 
                alt="Avatar" 
                className="w-8 h-8 rounded-full border border-slate-200"
              />
            </div>
          </div>
        </header>

        {/* Page Area */}
        <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950 p-6 md:p-8 custom-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
