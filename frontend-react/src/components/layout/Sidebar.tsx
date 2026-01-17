import React from 'react';
import { motion } from 'framer-motion';
import {
    LayoutDashboard,
    Database,
    ShieldAlert,
    CheckCircle2,
    Settings,
    Users,
    History,
    FileSearch,
    LogOut,
    ChevronLeft,
    ChevronRight
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

import { useNavigate, useLocation } from 'react-router-dom';

interface SidebarItemProps {
    icon: React.ElementType;
    label: string;
    path: string;
    collapsed: boolean;
}

const SidebarItem = ({ icon: Icon, label, path, collapsed }: SidebarItemProps) => {
    const navigate = useNavigate();
    const location = useLocation();
    const isActive = location.pathname === path;

    return (
        <button
            onClick={() => navigate(path)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${isActive
                ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
        >
            <Icon size={22} className="flex-shrink-0" />
            {!collapsed && (
                <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="font-medium whitespace-nowrap"
                >
                    {label}
                </motion.span>
            )}
        </button>
    );
};

const Sidebar = () => {
    const [collapsed, setCollapsed] = React.useState(false);
    const { user, logout } = useAuthStore();

    const role = user?.role || 'labeler';

    const menuItems = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard', path: '/', roles: ['admin', 'steward', 'annotator', 'labeler'] },
        { id: 'datasets', icon: Database, label: 'Data Pipeline', path: '/datasets', roles: ['admin', 'steward', 'annotator', 'labeler'] },
        { id: 'pii', icon: ShieldAlert, label: 'PII Detection', path: '/pii', roles: ['admin', 'steward', 'labeler', 'annotator'] },
        { id: 'quality', icon: CheckCircle2, label: 'Quality Hub', path: '/quality', roles: ['admin', 'steward'] },
        { id: 'tasks', icon: FileSearch, label: 'Task Queue', path: '/tasks', roles: ['admin', 'steward', 'annotator', 'labeler'] },
        { id: 'users', icon: Users, label: 'User Control', path: '/users', roles: ['admin'] },
        { id: 'audit', icon: History, label: 'Audit Logs', path: '/audit', roles: ['admin', 'steward'] },
        { id: 'settings', icon: Settings, label: 'Settings', path: '/settings', roles: ['admin', 'steward', 'annotator', 'labeler'] },
    ];

    const filteredItems = menuItems.filter(item => item.roles.includes(role));

    return (
        <motion.aside
            animate={{ width: collapsed ? 80 : 280 }}
            className="h-screen glass sticky top-0 flex flex-col p-4 z-50 overflow-hidden"
        >
            <div className="flex items-center gap-3 mb-10 px-2">
                <img src="/logo.png" alt="Logo" className="w-10 h-10 object-contain" />
                {!collapsed && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                        <h2 className="text-xl font-bold text-white tracking-tight">DataGov</h2>
                        <p className="text-[10px] text-brand-primary font-bold uppercase tracking-widest">{role}</p>
                    </motion.div>
                )}
            </div>

            <nav className="flex-1 space-y-2">
                {filteredItems.map((item) => (
                    <SidebarItem
                        key={item.id}
                        icon={item.icon}
                        label={item.label}
                        path={item.path}
                        collapsed={collapsed}
                    />
                ))}
            </nav>

            <div className="space-y-4 pt-10">
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="w-full flex items-center justify-center p-3 rounded-xl bg-white/5 text-slate-400 hover:text-white transition-colors"
                >
                    {collapsed ? <ChevronRight size={20} /> : <div className="flex items-center gap-3"><ChevronLeft size={20} /> <span className="text-sm font-medium">Collapse</span></div>}
                </button>

                <button
                    onClick={logout}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:text-white hover:bg-red-500/10 transition-all"
                >
                    <LogOut size={22} className="flex-shrink-0" />
                    {!collapsed && <span className="font-medium">Logout</span>}
                </button>
            </div>
        </motion.aside>
    );
};

export default Sidebar;
