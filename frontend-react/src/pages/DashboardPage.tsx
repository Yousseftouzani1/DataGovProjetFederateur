import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ShieldCheck,
    Activity,
    Zap,
    Server,
    Database,
    RefreshCw,
    X,
    ExternalLink,
    Upload,
    Search,
    FileCheck,
    Users,
    Settings,
    Tag,
    History,
    ClipboardList
} from 'lucide-react';
import apiClient from '../services/api';
import { Button } from '../components/ui/Button';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useToast } from '../context/ToastContext';

// Service metadata for detailed view
const SERVICE_INFO: Record<string, { port: number; description: string; docs: string }> = {
    auth: { port: 8001, description: 'User authentication, JWT tokens, role management', docs: '/api/auth/docs' },
    cleaning: { port: 8004, description: 'Data upload, profiling, cleaning, and transformation', docs: '/api/cleaning/docs' },
    quality: { port: 8008, description: 'ISO 25012 quality metrics and reporting', docs: '/api/quality/docs' },
    presidio: { port: 8003, description: 'PII detection with Microsoft Presidio + Moroccan recognizers', docs: '/api/presidio/docs' },
    taxonomie: { port: 8002, description: 'Moroccan PII/SPI taxonomy with 47+ patterns', docs: '/api/taxonomie/docs' },
    ethimask: { port: 8009, description: 'Contextual data masking with perceptron decision logic', docs: '/api/ethimask/docs' },
    correction: { port: 8006, description: 'Automated data correction using ML regression & rules', docs: '/api/correction/docs' },
    classification: { port: 8005, description: 'Data sensitivity classification using ensemble models', docs: '/api/classification/docs' },
    annotation: { port: 8007, description: 'Human-in-the-loop validation workflow management', docs: '/api/annotation/docs' },
};

// Role-specific configuration
const ROLE_CONFIG: Record<string, {
    title: string;
    description: string;
    color: string;
    image: string;
    tasks: { icon: any; title: string; desc: string; path: string }[]
}> = {
    labeler: {
        title: 'Data Labeler',
        description: 'Primary Focus: Restricted, high-volume manual tagging of sensitive entities.',
        color: 'from-cyan-400 to-teal-600',
        image: '/role_labeler.png',
        tasks: [
            { icon: ClipboardList, title: 'My Tasks', desc: 'Open the first record in your personal queue', path: '/tasks' },
        ]
    },
    annotator: {
        title: 'Data Annotator',
        description: 'Primary Focus: Data ingestion, profiling, and AI-assisted correction.',
        color: 'from-purple-400 to-pink-600',
        image: '/role_annotator.png',
        tasks: [
            { icon: Upload, title: 'Upload Dataset', desc: 'Securely upload new datasets for analysis', path: '/datasets' },
            { icon: Tag, title: 'Validate Detections', desc: 'Confirm or correct PII labels', path: '/tasks' },
        ]
    },
    steward: {
        title: 'Data Steward',
        description: 'Primary Focus: Quality standards, compliance auditing, and metadata cataloging.',
        color: 'from-emerald-400 to-green-600',
        image: '/role_steward.png',
        tasks: [
            { icon: RefreshCw, title: 'Sync Taxonomy', desc: 'Push PII/SPI tags to Apache Atlas', path: '/dashboard' },
            { icon: Zap, title: 'Quality Audit', desc: 'Run evaluations on new datasets', path: '/quality' },
            { icon: History, title: 'Forensic Review', desc: 'View masked data audit reports', path: '/audit' },
        ]
    },
    admin: {
        title: 'Administrator',
        description: 'Primary Focus: Infrastructure, Identity Access Management (IAM), and math foundations.',
        color: 'from-red-500 to-orange-600',
        image: '/role_admin.png',
        tasks: [
            { icon: Users, title: 'User Management', desc: 'Management of account approvals and roles', path: '/users' },
            { icon: Settings, title: 'System Settings', desc: 'Configure weights and alpha tuning', path: '/settings' },
            { icon: Activity, title: 'Operational Status', desc: 'Health pulse of HBase, Solr, and Kafka', path: '/dashboard' },
        ]
    },
};

const DashboardPage = () => {
    const navigate = useNavigate();
    const { addToast } = useToast();

    // Get user from auth store directly (reactive)
    const user = useAuthStore((state) => state.user);
    const userInfo = {
        name: user?.username || 'User',
        role: user?.role || 'labeler'
    };
    const roleConfig = ROLE_CONFIG[userInfo.role] || ROLE_CONFIG.labeler;

    const [stats, setStats] = useState([
        { label: 'Total Records', value: '...', trend: 'LOADING', icon: Database, color: 'text-blue-500' },
        { label: 'Total Datasets', value: '...', trend: 'LOADING', icon: ShieldCheck, color: 'text-brand-primary' },
        { label: 'Quality Score', value: '...', trend: 'LOADING', icon: Zap, color: 'text-green-500' },
        { label: 'System Nodes', value: '6/6', trend: 'STABLE', icon: Server, color: 'text-purple-500' },
    ]);

    const [services, setServices] = useState([
        { id: 'auth', name: 'Auth Service', path: '/auth/health', status: 'Checking...', latency: '0ms' },
        { id: 'cleaning', name: 'Cleaning Engine', path: '/cleaning/health', status: 'Checking...', latency: '0ms' },
        { id: 'quality', name: 'Quality Hub', path: '/quality/health', status: 'Checking...', latency: '0ms' },
        { id: 'presidio', name: 'Presidio ML', path: '/presidio/health', status: 'Checking...', latency: '0ms' },
        { id: 'taxonomie', name: 'Taxonomy', path: '/taxonomie/health', status: 'Checking...', latency: '0ms' },
        { id: 'ethimask', name: 'EthiMask', path: '/ethimask/health', status: 'Checking...', latency: '0ms' },
        { id: 'correction', name: 'Correction ML', path: '/correction/health', status: 'Checking...', latency: '0ms' },
        { id: 'classification', name: 'Classification', path: '/classification/health', status: 'Checking...', latency: '0ms' },
        { id: 'annotation', name: 'Annotation', path: '/annotation/health', status: 'Checking...', latency: '0ms' },
    ]);

    const [isRefreshing, setIsRefreshing] = useState(false);
    const [selectedService, setSelectedService] = useState<string | null>(null);
    const [showWelcome, setShowWelcome] = useState(true);

    const fetchData = async () => {
        setIsRefreshing(true);
        try {
            const cleanResp = await apiClient.get('/cleaning/stats');
            const qualityResp = await apiClient.get('/quality/stats');

            // Check health for each service
            const updatedServices = await Promise.all(services.map(async (s) => {
                const startTime = Date.now();
                try {
                    await apiClient.get(s.path);
                    return { ...s, status: 'Healthy', latency: `${Date.now() - startTime}ms` };
                } catch {
                    return { ...s, status: 'Offline', latency: '--' };
                }
            }));
            setServices(updatedServices);

            setStats([
                { label: 'Total Records', value: cleanResp.data.total_rows?.toLocaleString() || '0', trend: '+0.0%', icon: Database, color: 'text-blue-500' },
                { label: 'Total Datasets', value: cleanResp.data.total_datasets?.toLocaleString() || '0', trend: 'STABLE', icon: ShieldCheck, color: 'text-brand-primary' },
                { label: 'Quality Score', value: `${qualityResp.data.average_score || 0}%`, trend: 'ISO-25012', icon: Zap, color: 'text-green-500' },
                { label: 'System Nodes', value: `${updatedServices.filter(s => s.status === 'Healthy').length}/9`, trend: 'ACTIVE', icon: Server, color: 'text-purple-500' },
            ]);


        } catch (err) {
            console.error('Failed to fetch dashboard data', err);
        } finally {
            setIsRefreshing(false);
        }
    };

    const handleSyncAtlas = async () => {
        addToast('Syncing Taxonomy with Apache Atlas...', 'info');
        try {
            await apiClient.post('/taxonomie/sync-atlas');
            addToast('✅ Taxonomy successfully synced to Atlas!', 'success');
        } catch (err) {
            console.error('Atlas sync failed', err);
            addToast('❌ Failed to sync with Atlas. Check logs.', 'error');
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const isGovernanceRole = userInfo.role === 'admin' || userInfo.role === 'steward';

    return (
        <div className="space-y-10">
            {/* Welcome Hero Section */}
            {showWelcome && (
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`relative glass p-8 rounded-[2.5rem] overflow-hidden border border-white/10`}
                >
                    {/* Gradient overlay */}
                    <div className={`absolute inset-0 bg-gradient-to-r ${roleConfig.color} opacity-10`} />

                    {/* Role image background on the right */}
                    <div
                        className="absolute right-0 top-0 bottom-0 w-1/3 opacity-30"
                        style={{
                            backgroundImage: `url(${roleConfig.image})`,
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                            maskImage: 'linear-gradient(to left, rgba(0,0,0,0.8), transparent)',
                            WebkitMaskImage: 'linear-gradient(to left, rgba(0,0,0,0.8), transparent)'
                        }}
                    />

                    <div className="relative z-10">
                        <div className="flex justify-between items-start mb-6">
                            <div className="flex items-center gap-6">
                                {/* Role avatar */}
                                <div
                                    className={`w-20 h-20 rounded-2xl border-2 border-white/20 shadow-2xl overflow-hidden`}
                                    style={{
                                        backgroundImage: `url(${roleConfig.image})`,
                                        backgroundSize: 'cover',
                                        backgroundPosition: 'center'
                                    }}
                                />
                                <div>
                                    <p className="text-slate-400 text-sm mb-1">Welcome back,</p>
                                    <h1 className="text-3xl font-bold text-white mb-2">{userInfo.name}</h1>
                                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-black uppercase bg-gradient-to-r ${roleConfig.color} text-white`}>
                                        {roleConfig.title}
                                    </span>
                                </div>
                            </div>
                            <button onClick={() => setShowWelcome(false)} className="p-2 hover:bg-white/10 rounded-full">
                                <X size={20} className="text-slate-400" />
                            </button>
                        </div>
                        <p className="text-slate-300 mb-8 max-w-2xl">{roleConfig.description}</p>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {roleConfig.tasks.map((task, i) => (
                                <motion.button
                                    key={i}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    onClick={() => navigate(task.path)}
                                    className="p-4 bg-white/5 hover:bg-white/10 rounded-2xl border border-white/5 hover:border-brand-primary/30 transition-all text-left group"
                                >
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="p-2 bg-brand-primary/20 rounded-xl text-brand-primary group-hover:scale-110 transition-transform">
                                            <task.icon size={18} />
                                        </div>
                                        <span className="font-bold text-white">{task.title}</span>
                                    </div>
                                    <p className="text-slate-500 text-xs">{task.desc}</p>
                                </motion.button>
                            ))}
                        </div>
                    </div>
                </motion.div>
            )}

            {/* Project Info Section */}
            <div className="glass p-6 rounded-3xl border border-white/5">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <ShieldCheck className="text-brand-primary" size={24} />
                    DataGov - Data Governance Platform
                </h2>
                <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                        <h3 className="text-sm font-bold text-slate-400 uppercase">What is DataGov?</h3>
                        <p className="text-slate-300 text-sm leading-relaxed">
                            DataGov is a comprehensive data governance platform designed for Moroccan enterprises.
                            It provides automated PII detection, data quality assessment (ISO 25012), and secure data handling workflows.
                        </p>
                    </div>
                    <div className="space-y-3">
                        <h3 className="text-sm font-bold text-slate-400 uppercase">Key Features</h3>
                        <div className="grid grid-cols-2 gap-2">
                            {[
                                { icon: Search, text: 'PII Detection (CIN, Phone, IBAN)' },
                                { icon: Zap, text: 'ISO 25012 Quality Metrics' },
                                { icon: ShieldCheck, text: 'Role-Based Access Control' },
                                { icon: Database, text: 'Secure Data Pipeline' },
                            ].map((f, i) => (
                                <div key={i} className="flex items-center gap-2 text-xs text-slate-400">
                                    <f.icon size={14} className="text-brand-primary" />
                                    {f.text}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Role-Specific Insights (Day 4 Requirement) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {userInfo.role === 'admin' && (
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass p-8 rounded-[2.5rem] border border-brand-primary/20 bg-gradient-to-br from-brand-primary/5 to-transparent">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <Activity className="text-brand-primary" size={20} />
                                System Benchmarks
                            </h3>
                            <span className="text-[10px] font-black text-brand-primary bg-brand-primary/10 px-2 py-1 rounded-lg">LIVE: 124 req/s</span>
                        </div>
                        <div className="h-24 flex items-end gap-1 px-2">
                            {[40, 60, 45, 90, 65, 80, 50, 70, 85, 100, 95, 110].map((h, i) => (
                                <motion.div key={i} initial={{ height: 0 }} animate={{ height: `${h}%` }} transition={{ delay: i * 0.05 }} className="flex-1 bg-brand-primary/30 rounded-t-sm border-t border-brand-primary/50" />
                            ))}
                        </div>
                        <p className="text-[10px] text-slate-500 mt-4 text-center font-bold uppercase tracking-widest">Throughput Stability: 99.98%</p>
                    </motion.div>
                )}

                {userInfo.role === 'steward' && (
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass p-8 rounded-[2.5rem] border border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-transparent">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <Zap className="text-emerald-500" size={20} />
                                Compliance Trend (ISO 25012)
                            </h3>
                            <span className="text-[10px] font-black text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded-lg">+12% This Week</span>
                        </div>
                        <div className="h-24 flex items-end gap-1 px-2">
                            {[30, 35, 45, 40, 55, 60, 65, 75, 70, 85, 88, 92].map((h, i) => (
                                <motion.div key={i} initial={{ height: 0 }} animate={{ height: `${h}%` }} transition={{ delay: i * 0.05 }} className="flex-1 bg-emerald-500/30 rounded-t-sm border-t border-emerald-500/50" />
                            ))}
                        </div>
                        <p className="text-[10px] text-slate-500 mt-4 text-center font-bold uppercase tracking-widest">Quality Assurance Drift: LOW</p>
                    </motion.div>
                )}

                {userInfo.role === 'annotator' && (
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass p-8 rounded-[2.5rem] border border-purple-500/20 bg-gradient-to-br from-purple-500/5 to-transparent flex flex-col justify-center items-center text-center">
                        <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-400 mb-4 border border-purple-500/30">
                            <FileCheck size={32} />
                        </div>
                        <h4 className="text-3xl font-bold text-white mb-1">κ = 0.88</h4>
                        <p className="text-slate-400 text-sm font-medium mb-4">Inter-Annotator Agreement</p>
                        <div className="px-4 py-1.5 bg-purple-500 text-white rounded-full text-[10px] font-black uppercase tracking-widest">
                            High Consistency Match
                        </div>
                    </motion.div>
                )}

                {userInfo.role === 'labeler' && (
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass p-8 rounded-[2.5rem] border border-cyan-500/20 bg-gradient-to-br from-cyan-500/5 to-transparent">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                <History className="text-cyan-400" size={20} />
                                Daily Quota Progress
                            </h3>
                            <span className="text-[10px] font-black text-cyan-400 bg-cyan-400/10 px-2 py-1 rounded-lg">8/10 Tasks</span>
                        </div>
                        <div className="space-y-4">
                            <div className="h-4 bg-white/5 rounded-full overflow-hidden border border-white/5 p-1">
                                <motion.div initial={{ width: 0 }} animate={{ width: '80%' }} className="h-full bg-cyan-500 rounded-full" />
                            </div>
                            <div className="flex justify-between text-[10px] font-black text-slate-500 uppercase">
                                <span>80% Complete</span>
                                <span>2 Remaining</span>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Shared Insight (Contextual PII Trends) */}
                <div className="glass p-8 rounded-[2.5rem] border border-white/5 flex flex-col justify-between">
                    <div>
                        <h4 className="text-sm font-black uppercase text-slate-500 tracking-widest mb-4">Global PII Distribution</h4>
                        <div className="flex gap-2">
                            {['CIN', 'PHONE', 'IBAN', 'EMAIL'].map(t => (
                                <span key={t} className="px-3 py-1 bg-white/5 rounded-lg border border-white/5 text-[10px] font-bold text-slate-400">{t}</span>
                            ))}
                        </div>
                    </div>
                    <div className="mt-8 flex items-center gap-4">
                        <div className="flex -space-x-2">
                            {[1, 2, 3].map(i => <div key={i} className="w-8 h-8 rounded-full border-2 border-slate-900 bg-slate-800" />)}
                        </div>
                        <p className="text-xs text-slate-400">Collaborating with <span className="text-white font-bold">4 active nodes</span></p>
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="glass p-6 rounded-3xl glass-hover group"
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-2xl bg-white/5 ${stat.color} group-hover:scale-110 transition-transform`}>
                                <stat.icon size={24} />
                            </div>
                            <span className={`text-[10px] font-black px-2 py-1 rounded-lg ${stat.trend.startsWith('+') ? 'bg-green-500/10 text-green-500' :
                                stat.trend === 'STABLE' || stat.trend === 'ACTIVE' ? 'bg-blue-500/10 text-blue-500' :
                                    'bg-slate-700 text-slate-400'
                                }`}>
                                {stat.trend}
                            </span>
                        </div>
                        <p className="text-3xl font-bold text-white mb-1">{stat.value}</p>
                        <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">{stat.label}</p>
                    </motion.div>
                ))}
            </div>

            {/* Governance Actions (Steward/Admin Only) */}
            {
                isGovernanceRole && (
                    <div className="glass p-8 rounded-[2.5rem] border border-white/5 bg-emerald-500/5">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                <Database className="text-emerald-500" size={24} />
                                Governance Operations
                            </h3>
                            <span className="text-[10px] font-black uppercase tracking-widest text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-full">
                                {userInfo.role} Access
                            </span>
                        </div>
                        <div className="flex flex-wrap gap-4">
                            <Button onClick={handleSyncAtlas} className="bg-emerald-500 hover:bg-emerald-600 text-white border-none shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                                <RefreshCw size={18} className="mr-2" />
                                Sync Taxonomy to Atlas
                            </Button>
                            <Button variant="ghost" onClick={() => navigate('/audit')}>
                                <Activity size={18} className="mr-2" />
                                View Audit Logs
                            </Button>
                            <Button variant="ghost" onClick={() => navigate('/discovery')}>
                                <Search size={18} className="mr-2" />
                                Data Discovery
                            </Button>
                        </div>
                    </div>
                )
            }

            {/* Node Cluster */}
            <div className="grid lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 glass rounded-[2.5rem] p-8 border border-white/5">
                    <div className="flex justify-between items-center mb-8">
                        <div>
                            <h3 className="text-2xl font-bold text-white">Node Cluster</h3>
                            <p className="text-slate-500 text-sm">Click a service to view details</p>
                        </div>
                        <button
                            onClick={fetchData}
                            className={`p-3 bg-white/5 rounded-full ${isRefreshing ? 'animate-spin' : ''}`}
                        >
                            <RefreshCw size={20} className="text-slate-400" />
                        </button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {services.map((s, i) => (
                            <div
                                key={i}
                                onClick={() => setSelectedService(s.id)}
                                className="flex items-center justify-between p-3 rounded-2xl bg-white/5 border border-white/5 group hover:bg-white/10 transition-colors cursor-pointer hover:border-brand-primary/30"
                            >
                                <div>
                                    <p className="text-sm font-bold text-white group-hover:text-brand-primary transition-colors">{s.name}</p>
                                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tight">{s.latency}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`text-[10px] font-bold uppercase ${s.status === 'Healthy' ? 'text-green-500' : 'text-red-500'}`}>
                                        {s.status}
                                    </span>
                                    <span className={`w-2.5 h-2.5 rounded-full ${s.status === 'Healthy' ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-red-500 animate-pulse'}`} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Role Legend */}
                <div className="glass rounded-[2.5rem] p-8 border border-white/5">
                    <h3 className="text-xl font-bold text-white mb-6">Role Hierarchy</h3>
                    <div className="space-y-4">
                        {Object.entries(ROLE_CONFIG).map(([key, config]) => (
                            <div key={key} className={`p-4 rounded-2xl ${userInfo.role === key ? 'bg-brand-primary/10 border border-brand-primary/30' : 'bg-white/5'}`}>
                                <div className="flex items-center justify-between mb-1">
                                    <span className={`font-bold ${userInfo.role === key ? 'text-brand-primary' : 'text-white'}`}>
                                        {config.title}
                                    </span>
                                    {userInfo.role === key && (
                                        <span className="text-[10px] bg-brand-primary text-white px-2 py-0.5 rounded-full">YOU</span>
                                    )}
                                </div>
                                <p className="text-slate-500 text-xs">{config.tasks.length} tasks available</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Service Detail Modal */}
            <AnimatePresence>
                {selectedService && SERVICE_INFO[selectedService] && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
                        onClick={() => setSelectedService(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="glass p-8 rounded-3xl max-w-md w-full mx-4 border border-white/10"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex justify-between items-start mb-6">
                                <div>
                                    <h3 className="text-2xl font-bold text-white">{services.find(s => s.id === selectedService)?.name}</h3>
                                    <p className="text-slate-400 text-sm">Port: {SERVICE_INFO[selectedService].port}</p>
                                </div>
                                <button onClick={() => setSelectedService(null)} className="p-2 hover:bg-white/10 rounded-full">
                                    <X size={20} className="text-slate-400" />
                                </button>
                            </div>
                            <p className="text-slate-300 mb-6">{SERVICE_INFO[selectedService].description}</p>
                            <div className="flex gap-3">
                                <Button variant="primary" className="flex-1" onClick={() => setSelectedService(null)}>
                                    Close
                                </Button>
                                <a
                                    href={SERVICE_INFO[selectedService].docs}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-slate-400 transition-colors"
                                >
                                    <ExternalLink size={16} />
                                    API Docs
                                </a>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default DashboardPage;
