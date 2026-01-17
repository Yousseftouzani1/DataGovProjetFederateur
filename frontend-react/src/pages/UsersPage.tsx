import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    UserPlus,
    Search,
    Filter,
    MoreVertical,
    CheckCircle2,
    XCircle,
    Mail
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import apiClient from '../services/api';

const UsersPage = () => {
    const [users, setUsers] = useState<any[]>([]);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchUsers = async () => {
        try {
            const resp = await apiClient.get('/auth/users');
            setUsers(resp.data.users || []);
        } catch (err) {
            console.error('Failed to fetch users', err);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleAction = async (username: string, status: 'active' | 'rejected') => {
        try {
            await apiClient.put(`/auth/users/${username}/status?status=${status}`);
            fetchUsers();
        } catch (err) {
            console.error('Failed to update user status', err);
        }
    };

    const filteredUsers = users.filter(u =>
        u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.role.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const stats = {
        total: users.length,
        active: users.filter(u => u.status === 'active').length,
        pending: users.filter(u => u.status === 'pending').length,
    };

    return (
        <div className="space-y-8">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">User Control</h1>
                    <p className="text-slate-400">Manage identity, access, and role assignments for the ecosystem</p>
                </div>
                <div className="flex gap-4">
                    <div className="glass px-6 py-3 rounded-2xl flex items-center gap-6 border border-white/5">
                        <div className="text-center">
                            <p className="text-[10px] font-black text-slate-500 uppercase">Total</p>
                            <p className="text-xl font-bold text-white">{stats.total}</p>
                        </div>
                        <div className="w-px h-8 bg-white/10" />
                        <div className="text-center">
                            <p className="text-[10px] font-black text-slate-500 uppercase">Active</p>
                            <p className="text-xl font-bold text-green-500">{stats.active}</p>
                        </div>
                        <div className="w-px h-8 bg-white/10" />
                        <div className="text-center">
                            <p className="text-[10px] font-black text-slate-500 uppercase">Pending</p>
                            <p className="text-xl font-bold text-orange-500">{stats.pending}</p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input
                        type="text"
                        placeholder="Search identities by name or role..."
                        className="input-premium w-full pl-12"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex gap-2">
                    <Button variant="ghost"><Filter size={18} /> Filters</Button>
                    <Button variant="primary"><UserPlus size={18} /> Provision User</Button>
                </div>
            </div>

            <div className="glass rounded-[2.5rem] overflow-hidden border border-white/5 shadow-2xl">
                <table className="w-full text-left">
                    <thead>
                        <tr className="bg-white/5 border-b border-white/5">
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Identity</th>
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Authorization Role</th>
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Onboarding Status</th>
                            <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Administrative Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        <AnimatePresence mode="popLayout">
                            {filteredUsers.map((user, i) => (
                                <motion.tr
                                    key={user.username}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: i * 0.05 }}
                                    className="hover:bg-white/5 transition-all group"
                                >
                                    <td className="px-8 py-6">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center text-white font-bold">
                                                {user.username.charAt(0).toUpperCase()}
                                            </div>
                                            <div>
                                                <p className="font-bold text-white">{user.username}</p>
                                                <p className="text-[10px] text-slate-500 flex items-center gap-1 font-black uppercase">
                                                    <Mail size={10} />
                                                    {user.username.toLowerCase()}@datagov.ma
                                                </p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-8 py-6">
                                        <span className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${user.role === 'admin' ? 'bg-purple-500/10 text-purple-500' :
                                                user.role === 'steward' ? 'bg-blue-500/10 text-blue-500' :
                                                    'bg-slate-500/10 text-slate-500'
                                            }`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="px-8 py-6">
                                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${user.status === 'active' ? 'text-green-500' :
                                                user.status === 'rejected' ? 'text-red-500' :
                                                    'text-orange-500 animate-pulse'
                                            }`}>
                                            <div className={`w-1.5 h-1.5 rounded-full ${user.status === 'active' ? 'bg-green-500' :
                                                    user.status === 'rejected' ? 'bg-red-500' :
                                                        'bg-orange-500'
                                                }`} />
                                            {user.status}
                                        </span>
                                    </td>
                                    <td className="px-8 py-6 text-right">
                                        <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            {user.status === 'pending' && (
                                                <>
                                                    <button
                                                        onClick={() => handleAction(user.username, 'active')}
                                                        className="p-2 bg-green-500/10 text-green-500 rounded-xl hover:bg-green-500 hover:text-white transition-all shadow-lg shadow-green-500/10"
                                                    >
                                                        <CheckCircle2 size={18} />
                                                    </button>
                                                    <button
                                                        onClick={() => handleAction(user.username, 'rejected')}
                                                        className="p-2 bg-red-500/10 text-red-500 rounded-xl hover:bg-red-500 hover:text-white transition-all shadow-lg shadow-red-500/10"
                                                    >
                                                        <XCircle size={18} />
                                                    </button>
                                                </>
                                            )}
                                            <button className="p-2 text-slate-500 hover:text-white transition-colors">
                                                <MoreVertical size={18} />
                                            </button>
                                        </div>
                                    </td>
                                </motion.tr>
                            ))}
                        </AnimatePresence>
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default UsersPage;
