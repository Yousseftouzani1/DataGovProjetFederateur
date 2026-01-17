import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ClipboardList,
    Clock,
    ShieldCheck,
    CheckCircle2,
    RefreshCw,
    Filter,
    Trophy,
    Timer,
    X,
    Eye,
    FileText,
    Download,
    History,
    Database
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import apiClient from '../services/api';
import { useAuthStore } from '../store/authStore';
import { useToast } from '../context/ToastContext';
import TaskDetailsModal from '../components/TaskDetailsModal';

const TaskQueuePage = () => {
    const user = useAuthStore((state) => state.user);
    const { addToast } = useToast();
    const [tasks, setTasks] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'completed' | 'rejected'>('pending');
    const [priorityFilter, setPriorityFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');
    const [activeTab, setActiveTab] = useState<'tasks' | 'exports'>('tasks');
    const [exports, setExports] = useState<any[]>([]);

    // Modal State
    const [selectedTask, setSelectedTask] = useState<any>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const username = user?.username || localStorage.getItem('username');

            // Parallel fetch for efficiency
            const [tasksResp, statsResp] = await Promise.all([
                apiClient.get('/annotation/tasks'),
                username ? apiClient.get(`/annotation/users/${username}/stats`) : Promise.resolve({ data: null })
            ]);

            setTasks(tasksResp.data.tasks || []);
            setStats(statsResp.data);
        } catch (err) {
            console.error('Failed to fetch tasks/stats', err);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchExports = async () => {
        setIsLoading(true);
        try {
            const resp = await apiClient.get('/annotation/exports');
            setExports(resp.data || []);
        } catch (err) {
            console.error('Failed to fetch exports', err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'tasks') {
            fetchData();
        } else {
            fetchExports();
        }
    }, [activeTab]);

    const handleDownload = async (filename: string) => {
        try {
            // Use window.open for direct download if backend supports it or use blob
            const response = await apiClient.get(`/annotation/exports/download/${filename}`, {
                responseType: 'blob'
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
            addToast(`Downloading ${filename}`, 'success');
        } catch (err) {
            addToast('Failed to download file', 'error');
        }
    };

    const filteredTasks = tasks.filter(t => {
        const sMatch = statusFilter === 'all' || t.status === statusFilter;
        const pMatch = priorityFilter === 'all' || t.priority === priorityFilter;
        return sMatch && pMatch;
    });

    const handleTaskAction = async (taskId: string, isValid: boolean, editedData?: any) => {
        try {
            await apiClient.post(`/annotation/tasks/${taskId}/submit`, {
                annotations: [{
                    field: "pii_validation",
                    is_valid: isValid,
                    label: isValid ? "Validated by Annotator" : "Rejected by Annotator",
                    confidence: 1.0,
                    corrected_data: editedData || null
                }],
                time_spent_seconds: 0
            });

            // Optimistic update
            setTasks(prev => prev.filter(t => t.id !== taskId));

            // Notification
            addToast(isValid ? 'Task Validated Successfully' : 'Task Rejected', isValid ? 'success' : 'info');

            // Close modal if open
            setIsModalOpen(false);

            // Refresh stats
            fetchData();
        } catch (err) {
            console.error('Failed to submit task action', err);
            addToast('Failed to submit action. Please try again.', 'error');
        }
    };

    const openDetails = (task: any) => {
        setSelectedTask(task);
        setIsModalOpen(true);
    };

    return (
        <div className="space-y-10">
            {/* Modal */}
            <TaskDetailsModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                task={selectedTask}
                onValidate={(id: string, data?: any) => handleTaskAction(id, true, data)}
                onReject={(id: string) => handleTaskAction(id, false)}
            />

            {/* Sophisticated Performance Header */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-2 glass p-8 rounded-[2.5rem] bg-gradient-to-br from-brand-primary/10 to-transparent flex items-center gap-8 border border-brand-primary/20">
                    <div className="w-20 h-20 bg-brand-primary rounded-3xl flex items-center justify-center text-white shadow-2xl shadow-brand-primary/40">
                        <Trophy size={40} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-white mb-1">Annotator Command</h2>
                        <p className="text-slate-400 text-sm mb-4 tracking-tight">System Authority: <span className="text-brand-primary font-black uppercase text-[10px]">{user?.role || 'Annotator'}</span></p>
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-green-500" />
                                <span className="text-[10px] font-black text-white uppercase tracking-widest">{stats?.completed || 0} Resolved</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-orange-500" />
                                <span className="text-[10px] font-black text-white uppercase tracking-widest">{stats?.pending || 0} Active</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="glass p-8 rounded-[2rem] flex flex-col justify-center border border-white/5">
                    <div className="flex items-center gap-3 mb-2 text-slate-500">
                        <Timer size={16} />
                        <span className="text-[10px] font-black uppercase tracking-widest">Avg Pulse Rate</span>
                    </div>
                    <div className="text-3xl font-bold text-white">{stats?.avg_time || 0}s <span className="text-xs text-slate-600">/ record</span></div>
                </div>

                <div className="glass p-8 rounded-[2rem] flex flex-col justify-center border border-white/5">
                    <div className="flex items-center gap-3 mb-2 text-slate-500">
                        <ShieldCheck size={16} />
                        <span className="text-[10px] font-black uppercase tracking-widest">System Status</span>
                    </div>
                    <div className="text-3xl font-bold text-emerald-400">v2.0 <span className="text-xs text-slate-500">Live</span></div>
                </div>
            </div>

            <div className="space-y-6">
                <div className="flex bg-white/5 p-1 rounded-2xl border border-white/5 self-start">
                    <button
                        onClick={() => setActiveTab('tasks')}
                        className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all duration-300 font-bold text-sm ${activeTab === 'tasks'
                            ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20'
                            : 'text-slate-500 hover:text-slate-300'
                            }`}
                    >
                        <ClipboardList size={18} />
                        Active Tasks
                    </button>
                    <button
                        onClick={() => setActiveTab('exports')}
                        className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all duration-300 font-bold text-sm ${activeTab === 'exports'
                            ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20'
                            : 'text-slate-500 hover:text-slate-300'
                            }`}
                    >
                        <History size={18} />
                        Export History
                    </button>
                </div>

                {activeTab === 'tasks' && (
                    <div className="flex items-center gap-3 bg-white/5 p-1.5 rounded-2xl border border-white/5">
                        <div className="relative">
                            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                            <select
                                className="bg-transparent pl-9 pr-8 py-2 text-xs font-black uppercase text-slate-400 focus:outline-none appearance-none cursor-pointer"
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value as any)}
                            >
                                <option value="all">All Status</option>
                                <option value="pending">Pending</option>
                                <option value="assigned">Assigned</option>
                                <option value="completed">Completed</option>
                            </select>
                        </div>
                        <div className="w-px h-6 bg-white/10" />
                        <select
                            className="bg-transparent px-4 py-2 text-xs font-black uppercase text-slate-400 focus:outline-none appearance-none cursor-pointer"
                            value={priorityFilter}
                            onChange={(e) => setPriorityFilter(e.target.value as any)}
                        >
                            <option value="all">All Priority</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>
                        <button onClick={fetchData} className="p-2 ml-2 hover:bg-white/10 rounded-xl transition-colors text-slate-400">
                            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
                        </button>
                    </div>
                )}
                {activeTab === 'exports' && (
                    <div className="flex items-center gap-3 bg-white/5 p-1.5 rounded-2xl border border-white/5">
                        <button onClick={fetchExports} className="p-2 px-4 hover:bg-white/10 rounded-xl transition-colors text-slate-400 flex items-center gap-2 text-xs font-bold uppercase">
                            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
                            Refresh Files
                        </button>
                    </div>
                )}
            </div>

            {activeTab === 'tasks' ? (
                <div className="space-y-4">
                    <AnimatePresence mode="popLayout">
                        {filteredTasks.length === 0 ? (
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="p-20 glass rounded-[2.5rem] text-center border-dashed border-2 border-white/5"
                            >
                                <div className="p-4 bg-white/5 rounded-full w-fit mx-auto mb-6">
                                    <CheckCircle2 size={32} className="text-slate-700" />
                                </div>
                                <p className="text-slate-500 font-black uppercase text-[10px] tracking-widest">Queue Clear</p>
                                <p className="text-slate-600 text-xs">No active annotation requirements found</p>
                            </motion.div>
                        ) : (
                            filteredTasks.map((task, i) => (
                                <motion.div
                                    key={task.id}
                                    layout
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    transition={{ delay: i * 0.05 }}
                                    className={`glass p-6 rounded-3xl flex items-center justify-between glass-hover group border-l-[6px] ${task.priority === 'critical' ? 'border-l-red-600' :
                                        task.priority === 'high' ? 'border-l-red-400' :
                                            task.priority === 'medium' ? 'border-l-orange-400' : 'border-l-brand-primary'
                                        }`}
                                >
                                    <div className="flex items-center gap-8">
                                        <div className="text-center min-w-[80px]">
                                            <p className="text-[10px] font-black text-slate-600 uppercase mb-1">Batch ID</p>
                                            <span className="text-sm font-bold text-white">{task.id.split('-')[0].toUpperCase()}</span>
                                        </div>

                                        <div className="h-10 w-px bg-white/5" />

                                        <div>
                                            <div className="flex items-center gap-3 mb-2">
                                                <h4 className="text-lg font-bold text-white tracking-tight">{task.annotation_type.replace('_', ' ').toUpperCase()}</h4>
                                                <span className={`text-[10px] font-black px-2 py-0.5 rounded-lg uppercase ${task.status === 'pending' ? 'bg-slate-500/10 text-slate-500' :
                                                    task.status === 'assigned' ? 'bg-blue-500/10 text-blue-500' :
                                                        'bg-green-500/10 text-green-500'
                                                    }`}>
                                                    {task.status}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-4 text-xs">
                                                <span className="text-slate-500 flex items-center gap-1.5 font-medium">
                                                    <Database size={14} />
                                                    {task.dataset_id.substring(0, 12)}...
                                                </span>
                                                <div className="w-1 h-1 rounded-full bg-slate-700" />
                                                <span className="text-slate-500 flex items-center gap-1.5 font-medium">
                                                    <Clock size={14} />
                                                    {new Date(task.created_at).toLocaleTimeString()}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-6">
                                        <div className="hidden xl:block text-right">
                                            <p className="text-[10px] font-black text-slate-600 uppercase mb-1 tracking-widest">Metadata Fragment</p>
                                            <code className="text-[10px] bg-white/5 px-2 py-1 rounded text-brand-primary border border-white/5">
                                                {JSON.stringify(task.data_sample).substring(0, 40)}...
                                            </code>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="ghost"
                                                className="h-12 w-12 !p-0 rounded-2xl bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 transition-transform"
                                                onClick={() => openDetails(task)}
                                                title="View Details"
                                            >
                                                <Eye size={20} />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                className="h-12 w-12 !p-0 rounded-2xl bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-transform"
                                                onClick={() => handleTaskAction(task.id, false)}
                                                title="Reject Detection"
                                            >
                                                <X size={20} />
                                            </Button>
                                            <Button
                                                variant="primary"
                                                className="h-12 w-12 !p-0 rounded-2xl bg-green-500/20 text-green-500 hover:bg-green-500/30 border-green-500/30 transition-transform"
                                                onClick={() => handleTaskAction(task.id, true)}
                                                title="Validate Detection"
                                            >
                                                <CheckCircle2 size={20} />
                                            </Button>
                                        </div>
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </AnimatePresence>
                </div>
            ) : (
                /* Export History View */
                <div className="space-y-4">
                    <AnimatePresence mode="popLayout">
                        {exports.length === 0 ? (
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="p-20 glass rounded-[2.5rem] text-center border-dashed border-2 border-white/5"
                            >
                                <div className="p-4 bg-white/5 rounded-full w-fit mx-auto mb-6">
                                    <FileText size={32} className="text-slate-700" />
                                </div>
                                <p className="text-slate-500 font-black uppercase text-[10px] tracking-widest">No Exports</p>
                                <p className="text-slate-600 text-xs">Complete and validate tasks to generate golden records</p>
                            </motion.div>
                        ) : (
                            exports.map((file, i) => (
                                <motion.div
                                    key={file.filename}
                                    layout
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className="glass p-6 rounded-3xl flex items-center justify-between glass-hover group"
                                >
                                    <div className="flex items-center gap-6">
                                        <div className="p-4 bg-emerald-500/10 rounded-2xl text-emerald-400">
                                            <FileText size={24} />
                                        </div>
                                        <div>
                                            <h4 className="text-white font-bold text-lg">{file.filename}</h4>
                                            <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-tighter text-slate-500 mt-1">
                                                <span>{file.size_kb} KB</span>
                                                <div className="w-1 h-1 rounded-full bg-slate-700" />
                                                <span>{new Date(file.created_at).toLocaleString()}</span>
                                                <div className="w-1 h-1 rounded-full bg-slate-700" />
                                                <span className="text-emerald-400/60">{file.type}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <Button
                                        onClick={() => handleDownload(file.filename)}
                                        variant="primary"
                                        className="group-hover:bg-brand-primary group-hover:text-white"
                                    >
                                        <Download size={18} className="mr-2" />
                                        Download
                                    </Button>
                                </motion.div>
                            ))
                        )}
                    </AnimatePresence>
                </div>
            )}
        </div>
    );
};

export default TaskQueuePage;
