import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Settings,
    Shield,
    Bell,
    Globe,
    Lock,
    Cpu,
    Database,
    Palette,
    RefreshCw,
    X
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useAuthStore } from '../store/authStore';
import { useToast } from '../context/ToastContext';
import apiClient from '../services/api';
import EthiMaskConfig from '../components/EthiMaskConfig';

const SettingsPage = () => {
    const { user } = useAuthStore();
    const { addToast } = useToast();
    const role = user?.role || 'labeler';
    const [isSyncing, setIsSyncing] = useState(false);
    const [showGovernanceModal, setShowGovernanceModal] = useState(false);
    const [showRoadmapModal, setShowRoadmapModal] = useState(false);

    const allSections = [
        { id: 'governance', icon: Shield, title: 'Governance Policy', desc: 'Configure ISO 25012 thresholds and compliance rules.', roles: ['admin', 'steward'] },
        { id: 'alerts', icon: Bell, title: 'Alert Configurations', desc: 'Manage system-wide notification protocols.', roles: ['admin', 'steward'] },
        { id: 'node', icon: Globe, title: 'Node Network', desc: 'Configure cluster endpoints and latency buffers.', roles: ['admin'] },
        { id: 'access', icon: Lock, title: 'Access Control', desc: 'Define granular role permissions and MFA rules.', roles: ['admin'] },
        { id: 'engine', icon: Cpu, title: 'Engine Scaling', desc: 'Modify Presidio and Cleaning service concurrency.', roles: ['admin'] },
        { id: 'storage', icon: Database, title: 'Storage Schema', desc: 'Update MongoDB and Atlas connection pools.', roles: ['admin'] },
        { id: 'roadmap', icon: Cpu, title: 'Neural Roadmap V1', desc: 'V1 Migration plan & PyTorch/Transformer architecture.', roles: ['admin', 'steward'] },
        { id: 'theme', icon: Palette, title: 'Interface Theme', desc: 'Customize platform aesthetics and branding.', roles: ['admin', 'steward', 'annotator', 'labeler'] },
    ];

    const sections = allSections.filter(s => s.roles.includes(role));

    const handleSectionClick = (id: string) => {
        if (id === 'governance') setShowGovernanceModal(true);
        if (id === 'roadmap') setShowRoadmapModal(true);
    };

    const handleSyncAtlas = async () => {
        setIsSyncing(true);
        try {
            const resp = await apiClient.post('/taxonomie/sync-atlas');
            if (resp.data.mock_mode) {
                addToast('⚠️ Atlas is in MOCK mode. Patterns not synced to real cluster.', 'info');
            } else {
                addToast(`✅ Synced ${resp.data.synced} terms to Apache Atlas!`, 'success');
            }
        } catch (err) {
            console.error(err);
            addToast('❌ Failed to sync with Atlas. Check cluster connection.', 'error');
        } finally {
            setIsSyncing(false);
        }
    };

    return (
        <div className="space-y-10">
            <header>
                <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">System Settings</h1>
                <p className="text-slate-400">Configure global environmental parameters and governance logic</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sections.map((s, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        onClick={() => handleSectionClick(s.id)}
                        className="glass p-8 rounded-[2.5rem] border border-white/5 hover:border-brand-primary/30 transition-all group cursor-pointer"
                    >
                        <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center text-slate-400 group-hover:text-brand-primary transition-colors mb-6">
                            <s.icon size={24} />
                        </div>
                        <h3 className="text-lg font-bold text-white mb-2">{s.title}</h3>
                        <p className="text-slate-500 text-sm leading-relaxed mb-6">{s.desc}</p>
                        <Button variant="ghost" size="sm" className="w-full justify-start text-[10px] font-black uppercase tracking-widest px-0">
                            Configure Profile &rarr;
                        </Button>
                    </motion.div>
                ))}
            </div>

            <AnimatePresence>
                {showGovernanceModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
                        onClick={() => setShowGovernanceModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="glass p-8 rounded-[2.5rem] max-w-lg w-full border border-white/10 relative"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button
                                onClick={() => setShowGovernanceModal(false)}
                                className="absolute top-6 right-6 p-2 hover:bg-white/10 rounded-full transition-colors"
                            >
                                <X size={20} className="text-slate-400" />
                            </button>
                            <EthiMaskConfig />
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {showRoadmapModal && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowRoadmapModal(false)}>
                        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="glass p-10 rounded-[2.5rem] max-w-4xl w-full border border-white/10 relative max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                            <button onClick={() => setShowRoadmapModal(false)} className="absolute top-6 right-6 p-2 hover:bg-white/10 rounded-full transition-colors"><X size={20} className="text-slate-400" /></button>

                            <div className="flex items-center gap-4 mb-8">
                                <div className="p-4 bg-brand-primary/20 rounded-3xl text-brand-primary"><Cpu size={32} /></div>
                                <div>
                                    <h3 className="text-2xl font-bold text-white">Migration Plan: V1 Neural (Beta)</h3>
                                    <p className="text-slate-500 font-mono text-xs uppercase tracking-widest">Target Deployment: Q2 2026</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-8 mb-10">
                                <div className="space-y-4">
                                    <h4 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-brand-primary" />
                                        Advanced Loss Function
                                    </h4>
                                    <div className="p-6 bg-slate-950 rounded-2xl border border-white/5 font-mono text-brand-primary italic">
                                        L = α · L_privacy + (1-α) · L_utility
                                    </div>
                                    <p className="text-xs text-slate-500 leading-relaxed">
                                        Our V1 model uses a composite loss function to balance differential privacy constraints with downstream analytic utility.
                                    </p>
                                </div>
                                <div className="space-y-4">
                                    <h4 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                                        Transformer Backbone
                                    </h4>
                                    <div className="p-4 bg-slate-950 rounded-2xl border border-white/5 font-mono text-[10px] text-slate-400">
                                        <pre>
                                            {`class EthiMaskV1(nn.Module):
  def __init__(self):
    self.encoder = TransformerEncoder()
    self.head = nn.Linear(512, 1)
  
  def forward(self, x):
    z = self.encoder(x)
    return torch.sigmoid(self.head(z))`}
                                        </pre>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <h4 className="text-sm font-bold text-white uppercase tracking-widest">Implementation Milestones</h4>
                                <div className="space-y-4">
                                    {[
                                        { date: 'Phase 1', task: 'Switch from Perceptron to RoBERTa-base', status: 'In Progress' },
                                        { date: 'Phase 2', task: 'Implement DP-SGD (Differential Privacy)', status: 'Pending' },
                                        { date: 'Phase 3', task: 'Distributed Training on 4x A100', status: 'Scheduled' },
                                    ].map((m, i) => (
                                        <div key={i} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
                                            <div className="flex items-center gap-4">
                                                <span className="text-[10px] font-black text-brand-primary bg-brand-primary/10 px-2 py-1 rounded">{m.date}</span>
                                                <span className="text-xs text-white font-medium">{m.task}</span>
                                            </div>
                                            <span className="text-[10px] uppercase font-black text-slate-500">{m.status}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="glass p-10 rounded-[3rem] border border-white/5 bg-gradient-to-br from-brand-primary/5 to-transparent flex flex-col items-center text-center">
                <div className="p-4 bg-brand-primary/10 rounded-full mb-6">
                    <Settings className={`text-brand-primary ${isSyncing ? 'animate-spin' : ''}`} size={32} />
                </div>
                <h2 className="text-2xl font-bold text-white mb-4">Governance Sync Required</h2>
                <p className="text-slate-400 max-w-md mb-8">Synchronize local taxonomy definitions with the Apache Atlas governance cluster. Required when updating PI/SPI patterns.</p>
                <div className="flex gap-4">
                    <Button variant="primary" onClick={handleSyncAtlas} isLoading={isSyncing}>
                        <RefreshCw size={18} className="mr-2" />
                        Sync Glossary to Atlas
                    </Button>
                    <Button variant="ghost" onClick={() => window.open('http://100.91.176.196:21000', '_blank')}>
                        Open Atlas UI
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
