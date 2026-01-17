import { useState, useEffect } from 'react';
import { X, CheckCircle2, AlertTriangle, Edit2, Save, ChevronDown, ChevronRight, Copy } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/Button';
import { useAuthStore } from '../store/authStore';

interface TaskDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    task: any;
    onValidate: (id: string, correctedData?: any) => void;
    onReject: (id: string) => void;
}

const TaskDetailsModal = ({ isOpen, onClose, task, onValidate, onReject }: TaskDetailsModalProps) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedData, setEditedData] = useState<Record<string, any>>({});
    const [isDetectionsOpen, setIsDetectionsOpen] = useState(false);

    useEffect(() => {
        if (task?.data_sample) {
            setEditedData(task.data_sample);
        }
    }, [task]);

    if (!isOpen || !task) return null;

    // Group detections by type to clean up UI
    const groupedDetections = (task.detections || []).reduce((acc: any, det: any) => {
        const type = det.entity_type || 'Unknown';
        if (!acc[type]) acc[type] = [];
        acc[type].push(det);
        return acc;
    }, {});

    const handleSave = () => {
        setIsEditing(false);
        onValidate(task.id, editedData);
    };

    const handleInputChange = (key: string, value: string) => {
        setEditedData(prev => ({ ...prev, [key]: value }));
    };

    const renderContent = (data: any) => {
        if (!data) return <p className="text-slate-500 italic">No data content available</p>;

        let contentToRender = data;

        // Try to parse if it's a string looking like JSON
        if (typeof data === 'string') {
            try {
                contentToRender = JSON.parse(data);
            } catch {
                // Keep as string
            }
        } else if (data.source_text && typeof data.source_text === 'string') {
            // Handle the "Rich Context" wrapper we created
            try {
                contentToRender = JSON.parse(data.source_text);
            } catch {
                // Fallback to wrapper
            }
        }

        // 1. Array of Objects (Table View) - BEST for "Volume Scan"
        if (Array.isArray(contentToRender) && contentToRender.length > 0) {
            const headers = Object.keys(contentToRender[0] || {});
            return (
                <div className="overflow-x-auto rounded-lg border border-slate-800">
                    <table className="w-full text-xs text-left text-slate-400">
                        <thead className="bg-slate-900 uppercase font-bold text-slate-500">
                            <tr>
                                {headers.map(h => (
                                    <th key={h} className="px-3 py-2 border-b border-slate-800 whitespace-nowrap">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {contentToRender.map((row: any, i: number) => (
                                <tr key={i} className={`border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors ${i % 2 === 0 ? 'bg-slate-900/20' : ''}`}>
                                    {headers.map(h => {
                                        const val = row[h];
                                        // Highlight value if it matches detection value?
                                        const isMatch = task.detections?.some((d: any) => d.value === String(val));
                                        return (
                                            <td key={h} className="px-3 py-2 max-w-[200px] truncate" title={String(val)}>
                                                {isMatch ? (
                                                    <span className="bg-red-500/20 text-red-400 px-1 py-0.5 rounded border border-red-500/30 font-bold">{String(val)}</span>
                                                ) : (
                                                    String(val)
                                                )}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            );
        }

        // 2. Single Object (Key-Value View)
        if (typeof contentToRender === 'object' && contentToRender !== null) {
            return (
                <div className="grid grid-cols-1 gap-1">
                    {Object.entries(contentToRender).map(([key, value]) => (
                        <div key={key} className="flex flex-col sm:flex-row sm:gap-4 p-2 rounded hover:bg-white/5 border border-transparent hover:border-white/5 transition-colors">
                            <span className="text-slate-500 uppercase font-bold text-[10px] tracking-wider sm:w-32 flex-shrink-0 pt-1">
                                {key.replace(/_/g, ' ')}
                            </span>
                            <div className="text-slate-300 font-mono text-xs break-all">
                                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </div>
                        </div>
                    ))}
                </div>
            );
        }

        // 3. Raw String
        return (
            <div className="p-3 rounded bg-slate-950/50 border border-slate-800/50 text-slate-300 font-mono text-xs whitespace-pre-wrap">
                {String(contentToRender)}
            </div>
        );
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
                        aria-hidden="true"
                    />

                    <motion.div
                        initial={{ scale: 0.95, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.95, opacity: 0, y: 20 }}
                        className="relative bg-[#0f172a] border border-white/10 rounded-3xl p-8 max-w-2xl w-full shadow-2xl overflow-hidden z-10 flex flex-col max-h-[90vh]"
                    >
                        <div className="flex justify-between items-start mb-6 flex-shrink-0">
                            <div>
                                <h3 className="text-2xl font-bold text-white mb-2">Task Analysis</h3>
                                <p className="text-slate-400 text-sm">Reviewing detection for <span className="text-brand-primary font-mono">{task.id.split('-')[0]}</span></p>
                            </div>
                            <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-slate-400 transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="space-y-6 overflow-y-auto pr-2 custom-scrollbar">
                            {/* Detections Panel - Collapsible */}
                            <div className={`rounded-lg border ${isDetectionsOpen ? 'border-red-500/30 bg-red-500/5' : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'} transition-colors overflow-hidden flex-shrink-0`}>
                                <button
                                    onClick={() => setIsDetectionsOpen(!isDetectionsOpen)}
                                    className="w-full flex items-center justify-between p-4"
                                >
                                    <div className="flex items-center gap-3">
                                        <AlertTriangle className={`w-5 h-5 ${task.detections?.length > 0 ? 'text-red-400' : 'text-slate-400'}`} />
                                        <span className={`font-medium ${task.detections?.length > 0 ? 'text-red-200' : 'text-slate-400'}`}>
                                            DETECTED ISSUES ({task.detections?.length || 0})
                                        </span>
                                    </div>
                                    {isDetectionsOpen ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                                </button>

                                <AnimatePresence>
                                    {isDetectionsOpen && (
                                        <motion.div
                                            initial={{ height: 0 }}
                                            animate={{ height: 'auto' }}
                                            exit={{ height: 0 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="p-4 pt-0 space-y-2 border-t border-red-500/10">
                                                {Object.entries(groupedDetections || {}).map(([type, items]: [string, any]) => (
                                                    <div key={type} className="flex flex-col p-2 bg-slate-950/50 rounded border border-slate-800/50 gap-1">
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-2">
                                                                <span className="font-mono text-xs text-white uppercase bg-slate-800 px-1.5 py-0.5 rounded">{type}</span>
                                                                {items.length > 1 && <span className="text-xs text-slate-500">x{items.length}</span>}
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-xs font-mono text-red-300 bg-red-500/10 px-1.5 py-0.5 rounded">
                                                                    {Math.round(Math.max(...items.map((i: any) => i.score || 0)) * 100)}% Conf.
                                                                </span>
                                                            </div>
                                                        </div>
                                                        {items[0]?.analysis_explanation && (
                                                            <div className="flex items-start gap-1.5 mt-1 border-t border-white/5 pt-1.5">
                                                                <div className="min-w-[4px] h-[4px] rounded-full bg-violet-500 mt-1.5"></div>
                                                                <p className="text-[10px] text-slate-400 italic leading-relaxed">
                                                                    {items[0].analysis_explanation}
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                                {(!task.detections || task.detections.length === 0) && (
                                                    <p className="text-sm text-slate-500 italic p-2">No issues detected automatically.</p>
                                                )}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* Data Content */}
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <h4 className="text-slate-500 font-bold text-xs uppercase tracking-wider">Row Content</h4>
                                    {/* Edit Restriction: Labelers are Read-Only */}
                                    {['admin', 'steward', 'annotator'].includes(useAuthStore.getState().user?.role || '') && (
                                        <button
                                            onClick={() => setIsEditing(!isEditing)}
                                            className={`text-xs flex items-center gap-1.5 ${isEditing ? 'text-brand-primary' : 'text-slate-400 hover:text-white'} transition-colors`}
                                        >
                                            <Edit2 size={12} />
                                            {isEditing ? 'Editing...' : 'Edit Data'}
                                        </button>
                                    )}
                                </div>

                                <div className="bg-black/20 rounded-xl border border-white/5 p-4 max-h-60 overflow-y-auto font-mono text-sm relative group">
                                    {isEditing ? (
                                        <div className="space-y-4">
                                            <div className="p-3 rounded bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs mb-4">
                                                Editing mode allows you to correct the JSON structure directly.
                                            </div>
                                            {Object.entries(editedData || {}).map(([key, value]) => (
                                                <div key={key} className="flex flex-col gap-2">
                                                    <label className="text-xs font-bold text-slate-500 uppercase">{key}</label>
                                                    <textarea
                                                        value={value as string}
                                                        onChange={(e) => handleInputChange(key, e.target.value)}
                                                        className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200 focus:border-brand-primary focus:outline-none min-h-[100px] text-xs font-mono leading-relaxed"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        renderContent(editedData)
                                    )}

                                    {!isEditing && (
                                        <button
                                            className="absolute top-2 right-2 p-1.5 text-slate-500 hover:text-white bg-slate-900/50 hover:bg-slate-800 rounded opacity-0 group-hover:opacity-100 transition-all"
                                            title="Copy as JSON"
                                            onClick={() => navigator.clipboard.writeText(JSON.stringify(editedData, null, 2))}
                                        >
                                            <Copy className="w-3.5 h-3.5" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-4 mt-8 pt-6 border-t border-white/5">
                            <Button
                                variant="ghost"
                                className="flex-1 bg-red-500/10 text-red-500 hover:bg-red-500/20 border-red-500/20"
                                onClick={() => onReject(task.id)}
                            >
                                <X size={18} className="mr-2" />
                                Reject (Not PII)
                            </Button>

                            {isEditing ? (
                                <Button
                                    variant="primary"
                                    className="flex-1 bg-blue-500 hover:bg-blue-600"
                                    onClick={handleSave}
                                >
                                    <Save size={18} className="mr-2" />
                                    Save & Validate
                                </Button>
                            ) : (
                                <Button
                                    variant="primary"
                                    className="flex-1 bg-green-500 hover:bg-green-600 border-green-500"
                                    onClick={() => onValidate(task.id, editedData)}
                                >
                                    <CheckCircle2 size={18} className="mr-2" />
                                    Confirm Valid PII
                                </Button>
                            )}
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
};

export default TaskDetailsModal;
