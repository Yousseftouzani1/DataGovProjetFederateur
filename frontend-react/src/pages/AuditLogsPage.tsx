import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search,
    ArrowDownToLine,
    Info,
    AlertTriangle,
    Zap,
    Clock,
    Terminal
} from 'lucide-react';
import { Button } from '../components/ui/Button';

const AuditLogsPage = () => {
    const [logs, setLogs] = useState<any[]>([]);
    const [severityFilter, setSeverityFilter] = useState('all');

    const fetchLogs = async () => {
        // Simulate logs for now since we haven't centralized the audit service yet
        setTimeout(() => {
            setLogs([
                { id: '1', service: 'AUTH', action: 'LOGIN_SUCCESS', user: 'admin', status: 'INFO', timestamp: new Date().toISOString() },
                { id: '2', service: 'CLEANING', action: 'INGESTION_START', user: 'labeler_1', status: 'INFO', timestamp: new Date().toISOString() },
                { id: '3', service: 'PRESIDIO', action: 'PII_DETECTED', user: 'system', status: 'WARNING', timestamp: new Date().toISOString() },
                { id: '4', service: 'QUALITY', action: 'SCORE_DEGRADATION', user: 'system', status: 'CRITICAL', timestamp: new Date().toISOString() },
                { id: '5', service: 'GATEWAY', action: 'RATE_LIMIT_HIT', user: '192.168.1.1', status: 'WARNING', timestamp: new Date().toISOString() },
            ]);
        }, 800);
    };

    useEffect(() => {
        fetchLogs();
    }, []);

    const filteredLogs = logs.filter(l => severityFilter === 'all' || l.status === severityFilter);

    return (
        <div className="space-y-8">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">System Ledger</h1>
                    <p className="text-slate-400">Forensic audit trail for all cluster interactions and data mutations</p>
                </div>
                <Button variant="ghost">
                    <ArrowDownToLine size={18} />
                    Export forensic PDF
                </Button>
            </header>

            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input
                        type="text"
                        placeholder="Search logs by keyword, user, or IP..."
                        className="input-premium w-full pl-12"
                    />
                </div>
                <div className="flex bg-white/5 p-1.5 rounded-2xl border border-white/5">
                    {['all', 'INFO', 'WARNING', 'CRITICAL'].map((s) => (
                        <button
                            key={s}
                            onClick={() => setSeverityFilter(s as any)}
                            className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${severityFilter === s ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20' : 'text-slate-500 hover:text-white'
                                }`}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            </div>

            <div className="glass rounded-[2.5rem] border border-white/5 overflow-hidden shadow-2xl relative">
                <div className="absolute inset-0 bg-gradient-to-b from-brand-primary/5 to-transparent pointer-events-none" />
                <div className="overflow-x-auto relative">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-white/5 border-b border-white/5">
                                <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Time Vector</th>
                                <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Node ID</th>
                                <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Action Payload</th>
                                <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest">Initiator</th>
                                <th className="px-8 py-5 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Severity</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            <AnimatePresence mode="popLayout">
                                {filteredLogs.map((log, i) => (
                                    <motion.tr
                                        key={log.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="hover:bg-white/5 transition-all group"
                                    >
                                        <td className="px-8 py-6">
                                            <div className="flex items-center gap-3 text-slate-400">
                                                <Clock size={14} className="text-brand-primary" />
                                                <span className="text-xs font-medium">{new Date(log.timestamp).toLocaleTimeString()}</span>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <span className="text-[10px] font-black bg-white/5 px-2 py-1 rounded-lg text-white border border-white/10">
                                                {log.service}:NODE_01
                                            </span>
                                        </td>
                                        <td className="px-8 py-6">
                                            <code className="text-[10px] text-slate-300 font-mono tracking-tight bg-slate-800/50 px-2 py-1 rounded flex items-center gap-2 w-fit">
                                                <Terminal size={10} className="text-brand-primary" />
                                                {log.action}
                                            </code>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 rounded-full bg-brand-primary/20 flex items-center justify-center text-[10px] font-bold text-brand-primary">
                                                    {log.user.charAt(0).toUpperCase()}
                                                </div>
                                                <span className="text-xs text-white font-bold">{log.user}</span>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 text-right">
                                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${log.status === 'INFO' ? 'bg-blue-500/10 text-blue-500' :
                                                    log.status === 'WARNING' ? 'bg-orange-500/10 text-orange-500' :
                                                        'bg-red-500/10 text-red-500'
                                                }`}>
                                                {log.status === 'CRITICAL' && <AlertTriangle size={12} />}
                                                {log.status === 'WARNING' && <Info size={12} />}
                                                {log.status === 'INFO' && <Zap size={12} />}
                                                {log.status}
                                            </span>
                                        </td>
                                    </motion.tr>
                                ))}
                            </AnimatePresence>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AuditLogsPage;
