import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Database, FileText, ArrowRight, Shield, Zap } from 'lucide-react';
import apiClient from '../../services/api';

interface LineageStep {
    id: string;
    label: string;
    icon: React.ReactNode;
    status: 'completed' | 'processing' | 'pending' | 'source' | 'target';
    color: string;
}

interface LineageData {
    atlas_guid?: string;
    steps: { name: string; status: string }[];
}

interface Props {
    datasetId?: string;
}

const LineageVisualizer: React.FC<Props> = ({ datasetId }) => {
    const [lineageData, setLineageData] = useState<LineageData | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!datasetId) return;

        const fetchLineage = async () => {
            setLoading(true);
            try {
                const resp = await apiClient.get(`/cleaning/datasets/${datasetId}/lineage`);
                if (resp.data) {
                    setLineageData(resp.data);
                }
            } catch {
                // Lineage endpoint may not exist yet - show static fallback
                setLineageData(null);
            } finally {
                setLoading(false);
            }
        };

        fetchLineage();
    }, [datasetId]);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-emerald-400 bg-emerald-500/10';
            case 'processing': return 'text-yellow-400 bg-yellow-500/10';
            case 'pending': return 'text-slate-400 bg-slate-500/10';
            default: return 'text-blue-400 bg-blue-500/10';
        }
    };

    const defaultSteps: LineageStep[] = [
        { id: 'upload', label: 'Raw CSV', icon: <FileText size={20} />, status: 'source', color: 'text-blue-400 bg-blue-500/10' },
        { id: 'cleaning', label: 'Airflow Cleaning', icon: <Zap size={20} />, status: 'pending', color: 'text-yellow-400 bg-yellow-500/10' },
        { id: 'masking', label: "EthiMask T'", icon: <Shield size={20} />, status: 'pending', color: 'text-purple-400 bg-purple-500/10' },
        { id: 'target', label: 'Hive Target', icon: <Database size={20} />, status: 'target', color: 'text-emerald-400 bg-emerald-500/10' },
    ];

    // If we have real lineage data, map steps
    const steps: LineageStep[] = lineageData?.steps
        ? lineageData.steps.map((s, i) => ({
            id: `step-${i}`,
            label: s.name,
            icon: i === 0 ? <FileText size={20} /> : i === lineageData.steps.length - 1 ? <Database size={20} /> : <Zap size={20} />,
            status: s.status as LineageStep['status'],
            color: getStatusColor(s.status),
        }))
        : defaultSteps;

    return (
        <div className="p-8 bg-slate-900/50 rounded-3xl border border-white/5 overflow-hidden">
            <h4 className="text-xs font-black uppercase tracking-widest text-slate-500 mb-8 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse" />
                Data Lifecycle (Apache Atlas)
                {loading && <span className="text-[10px] text-slate-600 ml-2">Loading...</span>}
            </h4>

            <div className="flex items-center justify-between relative">
                {/* Connector Line */}
                <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-800 -translate-y-1/2" />

                {steps.map((step, i) => (
                    <React.Fragment key={step.id}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: i * 0.2 }}
                            className="relative z-10 flex flex-col items-center gap-4"
                        >
                            <div className={`p-5 rounded-[2rem] border border-white/10 ${step.color} shadow-xl shadow-black/40 hover:scale-110 transition-transform cursor-pointer group`}>
                                {step.icon}
                                <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1 bg-slate-800 rounded-lg text-[10px] font-black text-white opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                    Status: {step.status.toUpperCase()}
                                </div>
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-tighter text-slate-400">{step.label}</span>
                        </motion.div>
                        {i < steps.length - 1 && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: i * 0.2 + 0.1 }}
                                className="z-10 text-slate-700"
                            >
                                <ArrowRight size={20} />
                            </motion.div>
                        )}
                    </React.Fragment>
                ))}
            </div>

            <div className="mt-12 p-4 bg-brand-primary/5 rounded-2xl border border-brand-primary/10">
                <div className="flex justify-between items-center text-[10px] text-slate-500 font-bold">
                    <span>Active Trace: <span className="text-brand-primary">{lineageData?.atlas_guid || (datasetId ? `Dataset ${datasetId.slice(0, 8)}...` : 'No dataset selected')}</span></span>
                    <span>Provider: <span className="text-white">Atlas Lineage API</span></span>
                </div>
            </div>
        </div>
    );
};

export default LineageVisualizer;
