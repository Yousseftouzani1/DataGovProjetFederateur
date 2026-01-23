import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload,
    File,
    X,
    CheckCircle2,
    Database,
    ArrowRight,
    Search,
    RefreshCw,
    ExternalLink,
    Eye,
    ShieldCheck,
    Copy,
    Columns,
    Lock,
    Trash2,
    Activity
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import apiClient from '../services/api';
import { useAuthStore } from '../store/authStore';
import { useToast } from '../context/ToastContext';
import ExportsList from '../components/ExportsList';
import LineageVisualizer from '../components/ui/LineageVisualizer';

// Roles that can see actual data preview
const ROLES_CAN_VIEW_DATA = ['admin', 'steward'];
const ROLES_CAN_DELETE = ['admin', 'steward'];

const DataPipelinePage = () => {
    const navigate = useNavigate();
    const { addToast } = useToast();

    const user = useAuthStore((state) => state.user);
    const userRole = user?.role || 'labeler';

    const canViewData = ROLES_CAN_VIEW_DATA.includes(userRole);
    const canDelete = ROLES_CAN_DELETE.includes(userRole);

    const [file, setFile] = useState<File | null>(null);
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
    const [datasets, setDatasets] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedDataset, setSelectedDataset] = useState<any | null>(null);
    const [datasetPreview, setDatasetPreview] = useState<any>(null);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);
    const [uploadedFilename, setUploadedFilename] = useState('');
    const [activeModalTab, setActiveModalTab] = useState<'preview' | 'lineage'>('preview');

    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const droppedFiles = e.dataTransfer.files;
        if (droppedFiles && droppedFiles.length > 0) {
            const droppedFile = droppedFiles[0];
            const fileExt = droppedFile.name.split('.').pop()?.toLowerCase();
            if (['csv', 'json', 'xlsx', 'xls'].includes(fileExt || '')) {
                setFile(droppedFile);
            } else {
                addToast('❌ Invalid file type. Use CSV, JSON, or Excel.', 'error');
            }
        }
    };

    const fetchDatasets = async () => {
        setIsLoading(true);
        try {
            const resp = await apiClient.get('/cleaning/datasets');
            setDatasets(resp.data.datasets || resp.data); // Support both formats
        } catch (err) {
            console.error('Failed to fetch datasets', err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchDatasets();
    }, []);

    const handleDeleteDataset = async (datasetId: string, e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent row click
        if (!confirm('Are you sure you want to delete this dataset? This action cannot be undone.')) {
            return;
        }
        try {
            await apiClient.delete(`/cleaning/datasets/${datasetId}`);
            addToast('✅ Dataset deleted successfully', 'success');
            fetchDatasets();
        } catch (err) {
            console.error('Failed to delete dataset', err);
            addToast('❌ Failed to delete dataset', 'error');
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setStatus('uploading');
        setProgress(0);
        setUploadedFilename(file.name);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await apiClient.post('/cleaning/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
                    setProgress(percentCompleted);
                }
            });

            setStatus('processing');

            // Mandatory Task: Trigger Airflow Pipeline
            try {
                await apiClient.post(`/cleaning/trigger-pipeline?dataset_id=${response.data.dataset_id}`);
                console.log("Airflow Pipeline Triggered");
            } catch (triggerErr) {
                console.error("Failed to trigger pipeline", triggerErr);
                addToast('Warning: Uploaded but Pipeline start failed', 'error');
            }

            setTimeout(() => {
                setStatus('success');
                fetchDatasets();
                // Show Atlas registration notification
                addToast(`✅ Dataset registered in Apache Atlas (ID: ${response.data.dataset_id.substring(0, 8)}...)`, 'success');
                addToast(`🚀 Airflow DAG Started: cleaning_pipeline_v1`, 'success');
            }, 1000);

        } catch (err) {
            console.error('Upload failed', err);
            setStatus('error');
            addToast('❌ Upload failed. Please try again.', 'error');
        }
    };

    const handleDatasetClick = async (dataset: any) => {
        setSelectedDataset(dataset);
        setIsLoadingPreview(true);
        try {
            const resp = await apiClient.get(`/cleaning/dataset/${dataset.id}/json?sample=true`);
            setDatasetPreview({ preview: resp.data.data.slice(0, 5) });
        } catch (err) {
            console.error('Failed to load preview', err);
            setDatasetPreview(null);
        } finally {
            setIsLoadingPreview(false);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        addToast('ID Copied', 'info');
    };

    const filteredDatasets = datasets.filter(d =>
        (d.name || d.id).toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-10 max-w-6xl mx-auto">
            <header className="text-center">
                <h1 className="text-4xl font-bold text-white mb-4">Ingestion Engine</h1>
                <p className="text-slate-400">Securely upload and register datasets into the DataGov ecosystem</p>
            </header>

            {/* Upload Section */}
            {userRole === 'annotator' ? (
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => !file && document.getElementById('fileInput')?.click()}
                    className={`glass p-10 rounded-[2.5rem] border transition-all relative overflow-hidden group cursor-pointer ${isDragging
                        ? 'border-brand-primary bg-brand-primary/10 shadow-[0_0_40px_rgba(99,102,241,0.2)]'
                        : 'border-white/5 hover:border-brand-primary/20'
                        }`}
                >
                    {!file ? (
                        <div className="text-center py-12">
                            <div className="w-20 h-20 bg-brand-primary/10 rounded-3xl flex items-center justify-center mx-auto mb-8 border border-brand-primary/20 group-hover:scale-110 transition-transform">
                                <Upload size={32} className={`${isDragging ? 'animate-bounce' : ''} text-brand-primary`} />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">Drag & Drop or Click to Ingest</h3>
                            <p className="text-slate-500 mb-8 font-medium">Supports CSV, JSON, and Excel (Max 500MB)</p>

                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-slate-400 group-hover:text-brand-primary group-hover:border-brand-primary/30 transition-all">
                                <span>Browse Secondary Storage</span>
                                <ArrowRight size={14} />
                            </div>

                            <input
                                id="fileInput"
                                type="file"
                                className="hidden"
                                accept=".csv,.json,.xlsx,.xls"
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                                onClick={(e) => e.stopPropagation()} // Prevent double trigger
                            />
                        </div>
                    ) : (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-between p-6 bg-white/5 rounded-3xl border border-white/10 max-w-xl mx-auto">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-brand-primary rounded-2xl text-white">
                                        <File size={24} />
                                    </div>
                                    <div className="text-left">
                                        <p className="font-bold text-white truncate max-w-[200px]">{file.name}</p>
                                        <p className="text-xs text-slate-500 uppercase font-black">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                    </div>
                                </div>
                                {status === 'idle' && (
                                    <button onClick={() => setFile(null)} className="p-2 hover:bg-white/10 rounded-full text-slate-400 transition-colors">
                                        <X size={20} />
                                    </button>
                                )}
                            </div>

                            {status === 'idle' && (
                                <div className="flex justify-center">
                                    <Button className="w-full max-w-sm" onClick={handleUpload}>
                                        Begin High-Speed Ingestion
                                        <ArrowRight size={18} />
                                    </Button>
                                </div>
                            )}

                            {(status === 'uploading' || status === 'processing') && (
                                <div className="max-w-md mx-auto space-y-4">
                                    <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                                        <span className="text-brand-primary">{status === 'uploading' ? 'Streaming to Cluster' : 'Indexing Taxonomy'}</span>
                                        <span className="text-white">{progress}%</span>
                                    </div>
                                    <div className="h-2.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                                        <motion.div initial={{ width: 0 }} animate={{ width: `${progress}%` }} className="h-full bg-brand-primary shadow-[0_0_15px_rgba(99,102,241,0.5)]" />
                                    </div>
                                </div>
                            )}

                            {status === 'success' && (
                                <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="space-y-6 text-center">
                                    <div className="w-16 h-16 bg-green-500/20 border border-green-500/30 rounded-full flex items-center justify-center mx-auto text-green-500">
                                        <CheckCircle2 size={32} />
                                    </div>
                                    <h4 className="text-2xl font-bold text-white tracking-tight">Ingestion Complete</h4>
                                    <p className="text-slate-400">File: <span className="text-brand-primary font-mono">{uploadedFilename}</span></p>
                                    <div className="flex justify-center gap-4">
                                        <Button variant="ghost" onClick={() => { setFile(null); setStatus('idle'); }}>Upload Another</Button>
                                        <Button variant="primary" onClick={() => navigate('/pii')}>Scan for PII</Button>
                                    </div>
                                </motion.div>
                            )}

                            {status === 'error' && (
                                <div className="text-center space-y-6">
                                    <div className="w-16 h-16 bg-red-500/20 border border-red-500/30 rounded-full flex items-center justify-center mx-auto text-red-500">
                                        <X size={32} />
                                    </div>
                                    <h4 className="text-2xl font-bold text-white">Ingestion Failed</h4>
                                    <Button variant="ghost" onClick={() => setStatus('idle')}>Try Again</Button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            ) : (
                <div className="p-12 glass rounded-[2.5rem] border border-red-500/10 bg-red-500/5 text-center">
                    <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 text-red-500/50">
                        <Lock size={32} />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">Restricted Access</h3>
                    <p className="text-slate-500">Only the <span className="text-brand-primary font-bold">Data Annotator</span> role is authorized to ingest raw datasets.</p>
                </div>
            )}

            {/* Recent Uploads Table */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-2xl font-bold text-white">Repository Log</h3>
                        <p className="text-slate-500 text-sm">Click a dataset to view details and actions</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                            <input
                                type="text"
                                placeholder="Search repository..."
                                className="bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-brand-primary/50"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <button onClick={fetchDatasets} className="p-2 bg-white/5 rounded-xl text-slate-400 hover:text-white transition-colors">
                            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
                        </button>
                    </div>
                </div>

                <div className="glass rounded-[2rem] overflow-hidden">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-white/5 bg-white/5">
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Dataset Name</th>
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500">System ID</th>
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Accession Date</th>
                                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Status</th>
                                <th className="px-6 py-4 text-right"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {isLoading && datasets.length === 0 ? (
                                <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-500 italic">Synchronizing with node cluster...</td></tr>
                            ) : filteredDatasets.length === 0 ? (
                                <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-500 italic">No datasets found in primary storage.</td></tr>
                            ) : (
                                filteredDatasets.map((d, i) => (
                                    <motion.tr key={d.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }} onClick={() => handleDatasetClick(d)} className="hover:bg-white/5 transition-colors group cursor-pointer">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 bg-brand-primary/10 rounded-lg text-brand-primary"><Database size={16} /></div>
                                                <span className="font-bold text-white group-hover:text-brand-primary transition-colors">{d.name || 'Unnamed Dataset'}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4"><code className="text-[10px] text-slate-500 bg-slate-800/50 px-2 py-1 rounded">{d.id.substring(0, 8)}...</code></td>
                                        <td className="px-6 py-4 text-xs font-medium text-slate-400">{d.date ? new Date(d.date).toLocaleDateString() : 'N/A'}</td>
                                        <td className="px-6 py-4">
                                            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg bg-green-500/10 text-green-500 text-[10px] font-black uppercase tracking-tighter">
                                                <CheckCircle2 size={10} />{d.status || 'Ready'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right flex items-center justify-end gap-2">
                                            <Eye size={16} className="text-slate-500 group-hover:text-brand-primary transition-colors" />
                                            {canDelete && (
                                                <button
                                                    onClick={(e) => handleDeleteDataset(d.id, e)}
                                                    className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors"
                                                    title="Delete dataset"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            )}
                                        </td>
                                    </motion.tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Exports Hub Section */}
            <ExportsList />

            {/* Dataset Detail Modal */}
            <AnimatePresence>
                {selectedDataset && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => { setSelectedDataset(null); setDatasetPreview(null); }}>
                        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="glass p-8 rounded-3xl max-w-2xl w-full mx-4 border border-white/10 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                            <div className="flex justify-between items-start mb-6">
                                <div>
                                    <h3 className="text-2xl font-bold text-white mb-1">{selectedDataset.name || 'Dataset Details'}</h3>
                                    <div className="flex items-center gap-2">
                                        <code className="text-xs text-slate-400 bg-slate-800 px-2 py-1 rounded">{selectedDataset.id}</code>
                                        <button onClick={() => copyToClipboard(selectedDataset.id)} className="text-slate-500 hover:text-brand-primary transition-colors"><Copy size={14} /></button>
                                    </div>
                                </div>
                                <button onClick={() => { setSelectedDataset(null); setDatasetPreview(null); }} className="p-2 hover:bg-white/10 rounded-full transition-colors"><X size={20} className="text-slate-400" /></button>
                            </div>

                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Status</p>
                                    <p className="text-green-500 font-bold">{selectedDataset.status || 'Ready'}</p>
                                </div>
                                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Type</p>
                                    <p className="text-white font-bold">{selectedDataset.type || 'Raw'}</p>
                                </div>
                                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                    <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Date</p>
                                    <p className="text-white font-bold text-sm">{selectedDataset.date ? new Date(selectedDataset.date).toLocaleDateString() : 'N/A'}</p>
                                </div>
                            </div>

                            {/* Tab Switcher */}
                            <div className="flex bg-white/5 p-1 rounded-xl mb-6">
                                <button
                                    onClick={() => setActiveModalTab('preview')}
                                    className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${activeModalTab === 'preview' ? 'bg-brand-primary text-white' : 'text-slate-500'}`}
                                >
                                    Data Preview
                                </button>
                                <button
                                    onClick={() => setActiveModalTab('lineage')}
                                    className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${activeModalTab === 'lineage' ? 'bg-brand-primary text-white' : 'text-slate-500'}`}
                                >
                                    Lineage Trace
                                </button>
                            </div>

                            {activeModalTab === 'preview' ? (
                                <div className="mb-6">
                                    <div className="flex items-center gap-2 mb-3">
                                        <Columns size={16} className="text-brand-primary" />
                                        <p className="text-[10px] text-slate-500 uppercase font-bold">Data Preview (First 5 Rows)</p>
                                    </div>
                                    {!canViewData ? (
                                        <div className="p-8 text-center bg-red-500/5 rounded-xl border border-red-500/20">
                                            <Lock size={24} className="mx-auto text-red-400 mb-2" />
                                            <p className="text-red-400 font-bold text-sm">Access Restricted</p>
                                            <p className="text-slate-500 text-xs">Only Admin and Steward can view raw data</p>
                                        </div>
                                    ) : isLoadingPreview ? (
                                        <div className="p-8 text-center text-slate-500">Loading preview...</div>
                                    ) : datasetPreview?.preview && datasetPreview.preview.length > 0 ? (
                                        <div className="overflow-x-auto rounded-xl border border-white/10">
                                            <table className="w-full text-xs">
                                                <thead>
                                                    <tr className="bg-white/5">
                                                        {Object.keys(datasetPreview.preview[0]).map((col: string) => (
                                                            <th key={col} className="px-3 py-2 text-left text-slate-400 font-mono">{col}</th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {datasetPreview.preview.map((row: any, i: number) => (
                                                        <tr key={i} className="border-t border-white/5">
                                                            {Object.values(row).map((val: any, j: number) => (
                                                                <td key={j} className="px-3 py-2 text-white font-mono truncate max-w-[150px]">{String(val)}</td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    ) : (
                                        <div className="p-8 text-center text-slate-500 bg-slate-900/50 rounded-xl">No preview available</div>
                                    )}
                                </div>
                            ) : (
                                <div className="mb-6 animate-in fade-in slide-in-from-right-4">
                                    <LineageVisualizer />
                                </div>
                            )}

                            {/* Quick Actions */}
                            <div className="flex gap-3">
                                <Button variant="primary" className="flex-1" onClick={() => { setSelectedDataset(null); navigate('/pii'); }}>
                                    <ShieldCheck size={16} />
                                    Scan for PII
                                </Button>
                                {canViewData && (
                                    <>
                                        <Button variant="ghost" className="flex-1" onClick={() => { setSelectedDataset(null); navigate('/quality'); }}>
                                            <ExternalLink size={16} />
                                            Quality Audit
                                        </Button>
                                        <Button variant="ghost" className="flex-1" onClick={() => window.open(`/api/cleaning/datasets/${selectedDataset.id}/lineage`, '_blank')}>
                                            <Activity size={16} />
                                            Lineage Graph
                                        </Button>
                                    </>
                                )}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default DataPipelinePage;
