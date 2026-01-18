import { useState, useEffect } from 'react';
import {
    RadialBarChart,
    RadialBar,
    Tooltip,
    ResponsiveContainer,
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import {
    RefreshCw,
    Activity,
    ShieldCheck,
    ChevronDown,
    ArrowDownToLine
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import apiClient from '../services/api';

const QualityPage = () => {
    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedId, setSelectedId] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [report, setReport] = useState<any>(null);

    const fetchDatasets = async () => {
        try {
            const resp = await apiClient.get('/cleaning/datasets');
            setDatasets(resp.data);
            if (resp.data.length > 0) setSelectedId(resp.data[0].id);
        } catch (err) {
            console.error('Failed to fetch datasets', err);
        }
    };

    useEffect(() => {
        fetchDatasets();
    }, []);

    const handleEvaluate = async () => {
        if (!selectedId) return;
        setIsLoading(true);
        try {
            const resp = await apiClient.post(`/quality/evaluate/${selectedId}`);
            setReport(resp.data);
        } catch (err) {
            console.error('Evaluation failed. Ensure dataset is in memory cache.', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportPDF = () => {
        if (!report) return;
        const doc = new jsPDF();

        doc.setFillColor(15, 23, 42);
        doc.rect(0, 0, 210, 40, 'F');

        doc.setFontSize(22);
        doc.setTextColor(255, 255, 255);
        doc.text("ISO 25012 Quality Report", 14, 20);

        doc.setFontSize(12);
        doc.text(`Grade: ${report.grade} (${report.global_score}%)`, 14, 30);

        autoTable(doc, {
            startY: 45,
            head: [['Dimension', 'Score', 'Status']],
            body: report.dimensions.map((d: any) => [
                d.dimension.toUpperCase(),
                `${d.score}%`,
                d.score > 80 ? 'EXCELLENT' : d.score > 50 ? 'ACCEPTABLE' : 'CRITICAL'
            ]),
            headStyles: { fillColor: [16, 185, 129] }
        });

        doc.text("Recommendations:", 14, (doc as any).lastAutoTable.finalY + 10);

        report.recommendations.forEach((rec: string, i: number) => {
            doc.setFontSize(10);
            doc.text(`• ${rec}`, 14, (doc as any).lastAutoTable.finalY + 20 + (i * 7));
        });

        doc.save(`quality_report_${selectedId}.pdf`);
    };

    const chartData = report ? report.dimensions.map((d: any) => ({
        name: d.dimension.charAt(0).toUpperCase() + d.dimension.slice(1),
        value: d.score,
        fill: d.score > 80 ? '#10b981' : d.score > 50 ? '#f59e0b' : '#ef4444'
    })) : [
        { name: 'Completeness', value: 0, fill: '#6366f1' },
        { name: 'Accuracy', value: 0, fill: '#8b5cf6' },
        { name: 'Consistency', value: 0, fill: '#06b6d4' },
    ];

    return (
        <div className="space-y-10">
            <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Quality Hub</h1>
                    <p className="text-slate-400">ISO 25012 Data Quality Model Analysis (Sub-Second Evaluation)</p>
                </div>
                <div className="flex gap-4 w-full md:w-auto">
                    <div className="relative flex-1 md:w-64">
                        <select
                            className="input-premium w-full pr-10 appearance-none text-xs font-bold"
                            value={selectedId}
                            onChange={(e) => setSelectedId(e.target.value)}
                        >
                            {datasets.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                            {datasets.length === 0 && <option>No Datasets</option>}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" size={16} />
                    </div>
                    {report && (
                        <Button variant="ghost" onClick={handleExportPDF}>
                            <ArrowDownToLine size={18} />
                        </Button>
                    )}
                    <Button onClick={handleEvaluate} isLoading={isLoading} disabled={!selectedId}>
                        <RefreshCw size={18} />
                        Trigger Audit
                    </Button>
                </div>
            </header>

            <AnimatePresence mode="wait">
                {!report ? (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="glass p-20 rounded-[3rem] text-center border-dashed border-2 border-white/5"
                    >
                        <div className="w-20 h-20 bg-brand-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Activity size={40} className="text-brand-primary" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">Ready for ISO 25012 Evaluation</h3>
                        <p className="text-slate-500 mb-8 max-w-sm mx-auto tracking-tight uppercase text-[10px] font-black">Select a dataset from the repository above to generate a high-precision quality report.</p>
                    </motion.div>
                ) : (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-10"
                    >
                        {/* Primary Metrics */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            <div className="lg:col-span-1 glass p-8 rounded-3xl flex flex-col items-center border border-white/5">
                                <h3 className="text-xl font-bold text-white mb-8 w-full flex items-center justify-between">
                                    CORE COMPLIANCE
                                    <span className="text-[10px] bg-brand-primary/20 text-brand-primary px-2 py-1 rounded-lg">GRADE {report.grade}</span>
                                </h3>
                                <div className="h-64 w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <RadialBarChart
                                            cx="50%"
                                            cy="50%"
                                            innerRadius="30%"
                                            outerRadius="100%"
                                            barSize={12}
                                            data={chartData}
                                        >
                                            <RadialBar
                                                background
                                                dataKey="value"
                                                cornerRadius={10}
                                            />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                            />
                                        </RadialBarChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="grid grid-cols-2 gap-4 w-full mt-4">
                                    {chartData.map((m: any, i: number) => (
                                        <div key={i} className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: m.fill }} />
                                            <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">{m.name}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="lg:col-span-2 glass p-8 rounded-3xl border border-white/5 flex flex-col justify-between">
                                <div className="flex justify-between items-center mb-10">
                                    <h3 className="text-xl font-bold text-white uppercase tracking-tighter">Global Score Index</h3>
                                    <div className="text-4xl font-black text-white">
                                        {report.global_score}%
                                    </div>
                                </div>
                                <div className="space-y-6">
                                    {report.dimensions.map((d: any, i: number) => (
                                        <div key={i} className="space-y-2">
                                            <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                                                <span className="text-slate-400">{d.dimension}</span>
                                                <span className="text-white">{d.score}%</span>
                                            </div>
                                            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${d.score}%` }}
                                                    className={`h-full ${d.score > 80 ? 'bg-green-500' : d.score > 50 ? 'bg-orange-500' : 'bg-red-500'}`}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Recommendations */}
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                            {report.recommendations.map((rec: string, i: number) => (
                                <motion.div
                                    key={i}
                                    whileHover={{ scale: 1.02 }}
                                    className="glass p-6 rounded-3xl border border-white/5 flex items-start gap-4"
                                >
                                    <div className="p-3 bg-brand-primary/10 rounded-2xl text-brand-primary h-fit">
                                        <ShieldCheck size={20} />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-white mb-1 uppercase text-[10px] tracking-widest">Recommendation {i + 1}</h4>
                                        <p className="text-slate-400 text-sm leading-relaxed">{rec}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default QualityPage;
