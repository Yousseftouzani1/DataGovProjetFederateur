import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ShieldAlert,
    FileText,
    Database,
    Search,
    Eye,
    EyeOff,
    AlertCircle,
    CheckCircle2,
    ChevronDown,
    Activity,
    X,
    Download,
    AlertTriangle,
    Info,
    Send
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useToast } from '../context/ToastContext';
import apiClient from '../services/api';
import { useAuthStore } from '../store/authStore';

interface Detection {
    entity_type: string;
    start: number;
    end: number;
    score: number;
    value: string;
}

// Entity type descriptions for Moroccan context
const ENTITY_INFO: Record<string, { name: string; desc: string; risk: string }> = {
    'CIN_MAROC': { name: 'Moroccan National ID', desc: 'Carte d\'Identite Nationale - Primary identity document', risk: 'critical' },
    'PHONE_MA': { name: 'Moroccan Phone', desc: 'Mobile or landline number starting with +212 or 0[5-7]', risk: 'high' },
    'IBAN_MA': { name: 'Moroccan IBAN', desc: 'International Bank Account Number for Morocco', risk: 'critical' },
    'EMAIL': { name: 'Email Address', desc: 'Electronic mail address', risk: 'medium' },
    'PERSON': { name: 'Person Name', desc: 'Full name of an individual', risk: 'medium' },
    'LOCATION': { name: 'Location', desc: 'Geographic location or address', risk: 'low' },
    'DATE_TIME': { name: 'Date/Time', desc: 'Date or timestamp information', risk: 'low' },
    'CNSS': { name: 'CNSS Number', desc: 'Moroccan Social Security Number', risk: 'critical' },
    'PASSPORT_MA': { name: 'Moroccan Passport', desc: 'Passport number issued by Morocco', risk: 'critical' },
    'PERMIS_MA': { name: 'Driving License', desc: 'Moroccan driving permit number', risk: 'high' },
};

const getRiskColor = (risk: string) => {
    switch (risk) {
        case 'critical': return 'text-red-500 bg-red-500/10 border-red-500/20';
        case 'high': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
        case 'medium': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
        default: return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
    }
};

// Roles that can see actual PII values
const ROLES_CAN_VIEW_PII = ['admin', 'steward'];

const PIIDetectionPage = () => {
    const user = useAuthStore((state) => state.user);
    const userRole = user?.role || 'labeler';

    const canViewPII = ROLES_CAN_VIEW_PII.includes(userRole);

    const [activeTab, setActiveTab] = useState<'text' | 'dataset'>('text');
    const [text, setText] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [results, setResults] = useState<Detection[]>([]);
    const [error, setError] = useState('');
    const [showValues, setShowValues] = useState(false);
    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedDatasetId, setSelectedDatasetId] = useState('');
    const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);
    const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Entity Filtering (US-PII-02)
    const [selectedEntity, setSelectedEntity] = useState<string>('ALL');
    const [supportedEntities, setSupportedEntities] = useState<string[]>([]);

    useEffect(() => {
        const fetchEntities = async () => {
            try {
                const resp = await apiClient.get('/presidio/entities');
                setSupportedEntities(resp.data.entities || []);
            } catch (err) {
                setSupportedEntities(["CIN", "PHONE_NUMBER", "SENSITIVE_DATA", "EMAIL", "IBAN"]);
            }
        };
        fetchEntities();
    }, []);

    useEffect(() => {
        const fetchDatasets = async () => {
            setIsLoadingDatasets(true);
            try {
                const resp = await apiClient.get('/cleaning/datasets');
                setDatasets(resp.data);
                if (resp.data.length > 0) setSelectedDatasetId(resp.data[0].id);
            } catch (err) {
                console.error('Failed to load datasets', err);
            } finally {
                setIsLoadingDatasets(false);
            }
        };
        fetchDatasets();
    }, []);

    const [lastScannedText, setLastScannedText] = useState('');

    const handleAnalyze = async () => {
        setIsAnalyzing(true);
        setError('');
        setResults([]);

        try {
            let scanText = text;

            if (activeTab === 'dataset' && selectedDatasetId) {
                const previewResp = await apiClient.get(`/cleaning/datasets/${selectedDatasetId}/preview?rows=5`);
                scanText = JSON.stringify(previewResp.data.preview, null, 2);
            }

            if (!scanText) {
                setError('No content available to scan');
                setIsAnalyzing(false);
                return;
            }

            setLastScannedText(scanText); // Store for submission context

            const resp = await apiClient.post('/presidio/analyze', {
                text: scanText,
                language: 'fr',
                score_threshold: 0.3,
                entities: selectedEntity === 'ALL' ? undefined : [selectedEntity]
            });

            setResults(resp.data.detections);
        } catch (err: any) {
            setError('Detection service (Presidio) unavailable or timed out');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleExportCSV = () => {
        const csv = ['Entity Type,Value,Confidence,Start,End'];
        results.forEach((r, i) => {
            // Redact actual values for restricted roles
            const displayValue = canViewPII ? r.value : `[REDACTED_${i + 1}]`;
            csv.push(`${r.entity_type},"${displayValue}",${(r.score * 100).toFixed(0)}%,${r.start},${r.end}`);
        });
        const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pii_report_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
    };

    const { addToast } = useToast();

    // ... existing content ...

    const handleSubmitToProcessing = async () => {
        if (results.length === 0) {
            addToast('No detections to submit. Please run a scan first.', 'info');
            return;
        }

        setIsSubmitting(true);
        try {
            const selectedDataset = datasets.find(d => d.id === selectedDatasetId);

            // Enrich detections with context and column name
            // Enrich detections with context and column name
            const enrichedDetections = results.map(d => {
                const item = d as any;

                return {
                    ...d,
                    column: item.field || "unknown",
                    context: {
                        source_text: lastScannedText,
                        snippet: lastScannedText.substring(Math.max(0, d.start - 100), Math.min(lastScannedText.length, d.end + 100)),
                        full_structure: activeTab === 'dataset' ? "JSON Row" : "Raw Text"
                    }
                };
            });

            const response = await apiClient.post('/cleaning/trigger-pipeline', {
                dataset_id: selectedDatasetId || 'unknown',
                detections: enrichedDetections,
                dataset_name: selectedDataset?.name || 'Dataset'
            });

            if (response.data.success) {
                addToast('Pipeline triggered! Tasks created for Annotator.', 'success');
                setResults([]); // Clear results after submission
            }
        } catch (err: any) {
            console.error('Pipeline trigger failed:', err);
            addToast('Failed to submit to processing. Please try again.', 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    // Calculate statistics
    const entityCounts = results.reduce((acc, r) => {
        acc[r.entity_type] = (acc[r.entity_type] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const criticalCount = results.filter(r => {
        const info = ENTITY_INFO[r.entity_type];
        return info?.risk === 'critical';
    }).length;

    return (
        <div className="space-y-8 max-w-6xl">
            <header>
                <div className="flex items-center gap-2 text-brand-primary mb-2">
                    <ShieldAlert size={20} />
                    <span className="text-xs font-black uppercase tracking-widest">Security Layer</span>
                </div>
                <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">PII Sentinel</h1>
                <p className="text-slate-400">Deep scanning for Moroccan sensitive personal information (CIN, Phone, RIB)</p>
            </header>

            {/* Statistics Panel */}
            {results.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="glass p-4 rounded-2xl border border-white/5 group relative cursor-help">
                        <p className="text-[10px] font-black text-slate-500 uppercase mb-1">Total Detections</p>
                        <p className="text-2xl font-bold text-white">{results.length}</p>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 rounded-lg text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                            Total PII items found in the dataset
                        </div>
                    </div>
                    <div className="glass p-4 rounded-2xl border border-red-500/20 bg-red-500/5 group relative cursor-help">
                        <p className="text-[10px] font-black text-red-400 uppercase mb-1">Critical Risk</p>
                        <p className="text-2xl font-bold text-red-500">{criticalCount}</p>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 rounded-lg text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                            High-risk PII: CIN, IBAN, Passport (requires immediate attention)
                        </div>
                    </div>
                    <div className="glass p-4 rounded-2xl border border-white/5 group relative cursor-help">
                        <p className="text-[10px] font-black text-slate-500 uppercase mb-1">Entity Types</p>
                        <p className="text-2xl font-bold text-white">{Object.keys(entityCounts).length}</p>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 rounded-lg text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none min-w-[200px]">
                            <p className="font-bold mb-1">Types found:</p>
                            {Object.entries(entityCounts).map(([type, count]) => (
                                <div key={type} className="flex justify-between">
                                    <span>{type}:</span>
                                    <span className="font-bold text-white">{count}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="glass p-4 rounded-2xl border border-white/5 group relative cursor-help">
                        <p className="text-[10px] font-black text-slate-500 uppercase mb-1">Avg Confidence</p>
                        <p className="text-2xl font-bold text-brand-primary">
                            {results.length > 0 ? Math.round(results.reduce((a, r) => a + r.score, 0) / results.length * 100) : 0}%
                        </p>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 rounded-lg text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                            How confident the AI is (70%+ = reliable, 50-70% = review needed)
                        </div>
                    </div>
                </div>
            )}

            {/* Entity Filter */}
            <div className="flex flex-wrap gap-2">
                <button
                    onClick={() => setSelectedEntity('ALL')}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${selectedEntity === 'ALL' ? 'bg-brand-primary text-white' : 'bg-white/5 text-slate-500 hover:text-white'
                        }`}
                >
                    ALL
                </button>
                {supportedEntities.map(entity => (
                    <button
                        key={entity}
                        onClick={() => setSelectedEntity(entity)}
                        className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${selectedEntity === entity ? 'bg-brand-primary text-white' : 'bg-white/5 text-slate-500 hover:text-white'
                            }`}
                    >
                        {entity}
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Input area */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="glass rounded-[2rem] p-8 border border-white/5">
                        <div className="flex bg-white/5 p-1.5 rounded-2xl mb-8">
                            <button
                                onClick={() => setActiveTab('text')}
                                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all ${activeTab === 'text' ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20' : 'text-slate-500 hover:text-white'}`}
                            >
                                <FileText size={18} />
                                <span className="text-sm font-bold">Text Inspector</span>
                            </button>
                            <button
                                onClick={() => setActiveTab('dataset')}
                                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl transition-all ${activeTab === 'dataset' ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20' : 'text-slate-500 hover:text-white'}`}
                            >
                                <Database size={18} />
                                <span className="text-sm font-bold">Volume Scan</span>
                            </button>
                        </div>

                        <AnimatePresence mode="wait">
                            {activeTab === 'text' ? (
                                <motion.div key="text" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1 mb-3 block">
                                        RAW DATA INPUT
                                    </label>
                                    <textarea
                                        className="input-premium w-full !h-56 resize-none text-sm leading-relaxed p-4"
                                        placeholder="Paste content containing potential sensitive data for sub-second inspection..."
                                        value={text}
                                        onChange={(e) => setText(e.target.value)}
                                    />
                                </motion.div>
                            ) : (
                                <motion.div key="dataset" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="py-6 space-y-6">
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1 block">
                                            SELECT TARGET REPOSITORY
                                        </label>
                                        <div className="relative group">
                                            <select
                                                className="input-premium w-full appearance-none pr-10 cursor-pointer"
                                                value={selectedDatasetId}
                                                onChange={(e) => setSelectedDatasetId(e.target.value)}
                                                disabled={isLoadingDatasets}
                                            >
                                                {datasets.map(d => (
                                                    <option key={d.id} value={d.id} className="bg-slate-900 border-none">{d.name || d.id}</option>
                                                ))}
                                                {datasets.length === 0 && <option value="">No datasets available</option>}
                                            </select>
                                            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 group-hover:text-brand-primary transition-colors pointer-events-none" size={20} />
                                        </div>
                                    </div>

                                    {selectedDatasetId && (
                                        <div className="p-6 bg-brand-primary/5 rounded-[1.5rem] border border-brand-primary/10 flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className="w-12 h-12 bg-brand-primary/10 rounded-2xl flex items-center justify-center text-brand-primary">
                                                    <Database size={24} />
                                                </div>
                                                <div>
                                                    <p className="text-white font-bold text-sm tracking-tight">Ready for Compliance Scan</p>
                                                    <p className="text-slate-500 text-[10px] font-black uppercase tracking-widest">Metadata Indexed</p>
                                                </div>
                                            </div>
                                            <CheckCircle2 size={24} className="text-green-500/50" />
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <Button
                            className="w-full mt-10 h-14 rounded-2xl text-lg font-bold"
                            onClick={handleAnalyze}
                            isLoading={isAnalyzing}
                            variant="primary"
                            disabled={activeTab === 'text' && !text || activeTab === 'dataset' && !selectedDatasetId}
                        >
                            <Search size={22} />
                            {activeTab === 'text' ? 'Scan Buffer' : 'Full Volume Audit'}
                        </Button>
                    </div>

                    {error && (
                        <div className="p-4 rounded-[1.5rem] bg-red-500/10 border border-red-500/20 flex items-center gap-3 text-red-500 animate-in fade-in slide-in-from-left-4">
                            <AlertCircle size={20} />
                            <span className="text-sm font-medium">{error}</span>
                        </div>
                    )}
                </div>

                {/* Results area */}
                <div className="space-y-6">
                    <div className="glass rounded-[2.5rem] p-8 min-h-[500px] flex flex-col border border-white/5">
                        <div className="flex items-center justify-between mb-8">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <Activity size={20} className="text-brand-primary" />
                                Audit Results
                                {results.length > 0 && (
                                    <span className="ml-2 px-2 py-0.5 rounded-full bg-brand-primary/20 text-brand-primary text-[10px] font-black">
                                        {results.length}
                                    </span>
                                )}
                            </h3>
                            {results.length > 0 && canViewPII && (
                                <button
                                    onClick={() => setShowValues(!showValues)}
                                    className="p-2.5 rounded-xl bg-white/5 text-slate-400 hover:text-white transition-all border border-white/5"
                                    title="Toggle PII visibility (Admin/Steward only)"
                                >
                                    {showValues ? <Eye size={18} /> : <EyeOff size={18} />}
                                </button>
                            )}
                            {results.length > 0 && !canViewPII && (
                                <span className="text-[10px] text-red-400 uppercase font-black">Values Restricted</span>
                            )}
                        </div>

                        <div className="flex-1 space-y-4 overflow-y-auto max-h-[400px]">
                            {results.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-slate-900/40 rounded-[2rem] border border-dashed border-white/10">
                                    <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mb-6">
                                        <Search size={32} className="text-slate-600" />
                                    </div>
                                    <p className="text-slate-400 font-bold mb-2">No Detections Found</p>
                                    <p className="text-slate-600 text-[10px] font-black uppercase tracking-widest max-w-[160px]">Run a scan to analyze system integrity</p>
                                </div>
                            ) : (
                                results.map((res, i) => {
                                    const info = ENTITY_INFO[res.entity_type] || { name: res.entity_type, desc: 'Unknown entity type', risk: 'medium' };
                                    return (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, x: 20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.03 }}
                                            onClick={() => setSelectedDetection(res)}
                                            className={`p-4 rounded-2xl border cursor-pointer transition-all shadow-xl shadow-black/20 hover:scale-[1.02] ${getRiskColor(info.risk)}`}
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-[10px] font-black uppercase tracking-widest">
                                                    {info.name}
                                                </span>
                                                <span className="text-[10px] font-black">{(res.score * 100).toFixed(0)}%</span>
                                            </div>
                                            <code className="text-sm font-mono font-medium tracking-tight text-white">
                                                {showValues ? res.value : `[REDACTED_${i + 1}]`}
                                            </code>
                                        </motion.div>
                                    );
                                })
                            )}
                        </div>

                        {results.length > 0 && (
                            <div className="mt-8 space-y-3">
                                <Button className="w-full" variant="primary" onClick={handleExportCSV}>
                                    <Download size={18} />
                                    Export Report (CSV)
                                </Button>
                                <Button
                                    className="w-full bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700"
                                    variant="primary"
                                    onClick={handleSubmitToProcessing}
                                    isLoading={isSubmitting}
                                >
                                    <Send size={18} />
                                    Submit to Processing
                                </Button>
                                <Button variant="ghost" className="w-full text-xs font-black" onClick={() => setResults([])}>
                                    PURGE AUDIT BUFFER
                                </Button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Detection Detail Modal */}
            <AnimatePresence>
                {selectedDetection && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
                        onClick={() => setSelectedDetection(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="glass p-8 rounded-3xl max-w-lg w-full mx-4 border border-white/10"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {(() => {
                                const info = ENTITY_INFO[selectedDetection.entity_type] || { name: selectedDetection.entity_type, desc: 'Unknown entity type', risk: 'medium' };
                                return (
                                    <>
                                        <div className="flex justify-between items-start mb-6">
                                            <div>
                                                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-black uppercase mb-3 ${getRiskColor(info.risk)}`}>
                                                    <AlertTriangle size={14} />
                                                    {info.risk} Risk
                                                </div>
                                                <h3 className="text-2xl font-bold text-white">{info.name}</h3>
                                                <p className="text-slate-400 text-sm">{selectedDetection.entity_type}</p>
                                            </div>
                                            <button onClick={() => setSelectedDetection(null)} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                                                <X size={20} className="text-slate-400" />
                                            </button>
                                        </div>

                                        <div className="space-y-4 mb-6">
                                            <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                                <p className="text-[10px] text-slate-500 uppercase font-bold mb-2">Detected Value</p>
                                                {canViewPII ? (
                                                    <code className="text-lg font-mono text-brand-primary break-all">{selectedDetection.value}</code>
                                                ) : (
                                                    <div className="text-red-400 text-sm font-bold">
                                                        [RESTRICTED - Admin/Steward access required]
                                                    </div>
                                                )}
                                            </div>

                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Confidence</p>
                                                    <div className="flex items-center gap-2">
                                                        <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                                                            <div className="h-full bg-brand-primary rounded-full" style={{ width: `${selectedDetection.score * 100}%` }} />
                                                        </div>
                                                        <span className="text-white font-bold">{(selectedDetection.score * 100).toFixed(0)}%</span>
                                                    </div>
                                                </div>
                                                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Position</p>
                                                    <p className="text-white font-mono">Char {selectedDetection.start}-{selectedDetection.end}</p>
                                                </div>
                                            </div>

                                            <div className="p-4 rounded-2xl bg-blue-500/5 border border-blue-500/20">
                                                <div className="flex items-start gap-3">
                                                    <Info size={18} className="text-blue-400 mt-0.5" />
                                                    <div>
                                                        <p className="text-blue-400 font-bold text-sm mb-1">About this Entity</p>
                                                        <p className="text-slate-400 text-sm">{info.desc}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex gap-3">
                                            <Button variant="primary" className="flex-1" onClick={() => setSelectedDetection(null)}>
                                                Close
                                            </Button>
                                        </div>
                                    </>
                                );
                            })()}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default PIIDetectionPage;

