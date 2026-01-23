import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
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
import apiClient from '../services/api';
import { useToast } from '../context/ToastContext';

const AuditLogsPage = () => {
    const { addToast } = useToast();
    const [logs, setLogs] = useState<any[]>([]);
    const [selectedLog, setSelectedLog] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'general' | 'masking'>('general');
    const [maskingFilters, setMaskingFilters] = useState({ role: '', entity_type: '' });
    const [isLoading, setIsLoading] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const fetchLogs = async () => {
        setIsLoading(true);
        try {
            const queryParams = new URLSearchParams({
                role: maskingFilters.role,
                entity_type: maskingFilters.entity_type,
                start_date: startDate,
                end_date: endDate
            }).toString();

            const endpoint = activeTab === 'general'
                ? `/cleaning/audit-logs?${queryParams}`
                : `/ethimask/audit?${queryParams}`;
            const resp = await apiClient.get(endpoint);
            setLogs(resp.data.logs || resp.data); // Handle different response structures
        } catch (err) {
            console.error('Failed to fetch audit logs', err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, [activeTab, maskingFilters, startDate, endDate]);

    const handleExportPDF = () => {
        setIsExporting(true);
        try {
            const doc = new jsPDF();

            // Header
            doc.setFillColor(15, 23, 42); // slate-900
            doc.rect(0, 0, 210, 40, 'F');

            doc.setFontSize(22);
            doc.setTextColor(255, 255, 255);
            doc.text("System Forensic Ledger", 14, 20);

            doc.setFontSize(10);
            doc.setTextColor(148, 163, 184); // slate-400
            doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);
            doc.text(`Total Records: ${logs.length}`, 150, 30);

            const tableData = logs.map(log => [
                new Date(log.timestamp).toLocaleString(),
                log.service || log.entity_type || 'UNKNOWN',
                log.action || 'MASK_EXEC',
                log.user || 'system',
                log.status || log.sensitivity || 'INFO'
            ]);

            autoTable(doc, {
                startY: 45,
                head: [['Timestamp', 'Service/Node', 'Action Payload', 'Initiator', 'Status']],
                body: tableData,
                styles: { fontSize: 8, font: "helvetica" },
                headStyles: { fillColor: [99, 102, 241], textColor: 255 }, // brand-primary
                alternateRowStyles: { fillColor: [241, 245, 249] },
            });

            doc.save(`forensic_audit_log_${new Date().toISOString().slice(0, 10)}.pdf`);
        } catch (err) {
            console.error("PDF generation failed", err);
        } finally {
            setIsExporting(false);
        }
    };

    const filteredLogs = logs;

    const handleRetrain = async () => {
        setIsLoading(true);
        try {
            await apiClient.post('/ethimask/retrain');
            addToast('EthiMask retraining initiated based on forensic audit logs.', 'success');
        } catch (err) {
            console.error(err);
            addToast('Failed to trigger retraining. Check service connectivity.', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">System Ledger</h1>
                    <p className="text-slate-400">Forensic audit trail for all cluster interactions and data mutations</p>
                </div>
                <div className="flex gap-4">
                    <Button variant="ghost" onClick={handleRetrain} isLoading={isLoading}>
                        <Zap size={18} className="text-brand-primary" />
                        Retrain Pattern
                    </Button>
                    <Button variant="ghost" onClick={fetchLogs}>
                        Refresh
                    </Button>
                    <Button variant="ghost" onClick={handleExportPDF} isLoading={isExporting}>
                        <ArrowDownToLine size={18} />
                        Export forensic PDF
                    </Button>
                </div>
            </header>

            <div className="flex flex-col md:flex-row gap-4">
                <div className="flex bg-white/5 p-1 rounded-2xl border border-white/5 self-start">
                    <button
                        onClick={() => setActiveTab('general')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeTab === 'general' ? 'bg-brand-primary text-white' : 'text-slate-500'}`}
                    >
                        General Ledger
                    </button>
                    <button
                        onClick={() => setActiveTab('masking')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeTab === 'masking' ? 'bg-brand-primary text-white' : 'text-slate-500'}`}
                    >
                        Masking Forensics
                    </button>
                </div>

                {activeTab === 'masking' && (
                    <div className="flex gap-2">
                        <select
                            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-slate-300 focus:outline-none"
                            value={maskingFilters.role}
                            onChange={(e) => setMaskingFilters(prev => ({ ...prev, role: e.target.value }))}
                        >
                            <option value="">All Roles</option>
                            <option value="admin">Admin</option>
                            <option value="steward">Steward</option>
                            <option value="annotator">Annotator</option>
                            <option value="labeler">Labeler</option>
                        </select>

                        <select
                            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-slate-300 focus:outline-none"
                            value={maskingFilters.entity_type}
                            onChange={(e) => setMaskingFilters(prev => ({ ...prev, entity_type: e.target.value }))}
                        >
                            <option value="">All Entities</option>
                            <option value="CIN">CIN</option>
                            <option value="PHONE">PHONE</option>
                            <option value="EMAIL">EMAIL</option>
                            <option value="IBAN">IBAN</option>
                        </select>
                    </div>
                )}

                <div className="flex gap-2">
                    <div className="relative group">
                        <input
                            type="date"
                            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-slate-300 focus:outline-none focus:border-brand-primary"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                        <span className="absolute -top-2 left-3 px-1 bg-bg-deep text-[8px] font-black text-slate-500 uppercase tracking-widest">Start Date</span>
                    </div>
                    <div className="relative group">
                        <input
                            type="date"
                            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-slate-300 focus:outline-none focus:border-brand-primary"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                        />
                        <span className="absolute -top-2 left-3 px-1 bg-bg-deep text-[8px] font-black text-slate-500 uppercase tracking-widest">End Date</span>
                    </div>
                    {(startDate || endDate) && (
                        <Button variant="ghost" size="sm" onClick={() => { setStartDate(''); setEndDate(''); }} className="text-red-400 hover:text-red-300">
                            Clear
                        </Button>
                    )}
                </div>

                <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input
                        type="text"
                        placeholder="Search logs by keyword, user, or IP..."
                        className="input-premium w-full pl-12"
                    />
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
                                {filteredLogs.length === 0 && !isLoading && (
                                    <tr>
                                        <td colSpan={5} className="px-8 py-10 text-center text-slate-500 text-sm">
                                            No logs found in persistent storage...
                                        </td>
                                    </tr>
                                )}
                                {filteredLogs.map((log, i) => {
                                    // Map masking log fields to audit display format
                                    const service = log.service || log.entity_type?.toUpperCase() || 'ETHIMASK';
                                    const action = log.action || `MASK_${log.field?.toUpperCase()}` || 'UNKNOWN';
                                    const user = log.user || log.role || 'system';
                                    const status = log.status ||
                                        (log.sensitivity === 'critical' ? 'CRITICAL' :
                                            log.sensitivity === 'high' ? 'WARNING' : 'INFO');
                                    const details = log.details || {
                                        field: log.field,
                                        sensitivity: log.sensitivity,
                                        technique: log.technique,
                                        masking_level: log.masking_level
                                    };

                                    return (
                                        <motion.tr
                                            key={log.id || i}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.05 }}
                                            onClick={() => setSelectedLog({ ...log, service, action, user, status, details })}
                                            className="hover:bg-white/5 transition-all group cursor-pointer"
                                        >
                                            <td className="px-8 py-6">
                                                <div className="flex items-center gap-3 text-slate-400">
                                                    <Clock size={14} className="text-brand-primary" />
                                                    <span className="text-xs font-medium">{new Date(log.timestamp).toLocaleTimeString()}</span>
                                                </div>
                                            </td>
                                            <td className="px-8 py-6">
                                                <span className="text-[10px] font-black bg-white/5 px-2 py-1 rounded-lg text-white border border-white/10">
                                                    {service}:NODE_01
                                                </span>
                                            </td>
                                            <td className="px-8 py-6">
                                                <code className="text-[10px] text-slate-300 font-mono tracking-tight bg-slate-800/50 px-2 py-1 rounded flex items-center gap-2 w-fit">
                                                    <Terminal size={10} className="text-brand-primary" />
                                                    {action}
                                                </code>
                                            </td>
                                            <td className="px-8 py-6">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-6 h-6 rounded-full bg-brand-primary/20 flex items-center justify-center text-[10px] font-bold text-brand-primary">
                                                        {(user || '?').charAt(0).toUpperCase()}
                                                    </div>
                                                    <span className="text-xs text-white font-bold">{user}</span>
                                                </div>
                                            </td>
                                            <td className="px-8 py-6 text-right">
                                                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${status === 'INFO' ? 'bg-blue-500/10 text-blue-500' :
                                                    status === 'WARNING' ? 'bg-orange-500/10 text-orange-500' :
                                                        'bg-red-500/10 text-red-500'
                                                    }`}>
                                                    {status === 'CRITICAL' && <AlertTriangle size={12} />}
                                                    {status === 'WARNING' && <Info size={12} />}
                                                    {status === 'INFO' && <Zap size={12} />}
                                                    {status}
                                                </span>
                                            </td>
                                        </motion.tr>
                                    );
                                })}
                            </AnimatePresence>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Log Details Modal */}
            <AnimatePresence>
                {selectedLog && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
                        onClick={() => setSelectedLog(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-[#0f172a] border border-white/10 rounded-2xl p-8 max-w-2xl w-full shadow-2xl relative overflow-hidden"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-primary to-purple-500" />
                            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                                <Terminal className="text-brand-primary" size={24} />
                                Forensic Detail Record
                            </h3>

                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 bg-white/5 rounded-xl">
                                        <p className="text-[10px] uppercase text-slate-500 font-bold mb-1">Service Entity</p>
                                        <p className="text-white font-mono">{selectedLog.service}</p>
                                    </div>
                                    <div className="p-4 bg-white/5 rounded-xl">
                                        <p className="text-[10px] uppercase text-slate-500 font-bold mb-1">Initiator</p>
                                        <p className="text-white font-mono">{selectedLog.user}</p>
                                    </div>
                                </div>

                                <div className="p-6 bg-slate-950 rounded-xl border border-white/5 font-mono text-xs text-slate-300 overflow-x-auto max-h-64 overflow-y-auto">
                                    <pre>{JSON.stringify(selectedLog.details || {}, null, 2)}</pre>
                                </div>

                                <div className="flex justify-end pt-4 gap-3">
                                    <Button variant="ghost" onClick={() => setSelectedLog(null)}>
                                        Close Case File
                                    </Button>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default AuditLogsPage;
