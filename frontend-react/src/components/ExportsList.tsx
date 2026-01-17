import { useState, useEffect } from 'react';
import { Download, FileCheck, RefreshCw, Clock } from 'lucide-react';
import apiClient from '../services/api';
import { Button } from './ui/Button';

interface ExportFile {
    filename: string;
    size_kb: number;
    created_at: string;
    type: string;
}

const ExportsList = () => {
    const [exports, setExports] = useState<ExportFile[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const fetchExports = async () => {
        setIsLoading(true);
        try {
            const resp = await apiClient.get('/annotation/exports');
            setExports(resp.data);
        } catch (err) {
            console.error('Failed to fetch exports', err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchExports();
    }, []);

    const handleDownload = (filename: string) => {
        // Direct download link
        // Note: In production, use a proper blob download, but for MVP direct link is fine
        const url = `${apiClient.defaults.baseURL}/annotation/exports/download/${filename}`;
        window.open(url, '_blank');
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                        <FileCheck className="text-brand-accent" />
                        Certified Exports Hub
                    </h3>
                    <p className="text-slate-500 text-sm">Download validated "Golden Records" produced by the pipeline</p>
                </div>
                <button onClick={fetchExports} className="p-2 bg-white/5 rounded-xl text-slate-400 hover:text-white transition-colors">
                    <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
                </button>
            </div>

            <div className="glass rounded-[2rem] overflow-hidden border border-brand-accent/20">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-white/5 bg-white/5">
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Filename</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Generated</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500">Size</th>
                            <th className="px-6 py-4 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {exports.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-12 text-center">
                                    <div className="flex flex-col items-center justify-center text-slate-500">
                                        <Clock size={32} className="mb-2 opacity-50" />
                                        <p className="italic">No certified exports available yet.</p>
                                        <p className="text-xs mt-1">Complete an annotation cycle to generate one.</p>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            exports.map((file) => (
                                <tr key={file.filename} className="hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-brand-accent/10 rounded-lg text-brand-accent">
                                                <FileCheck size={16} />
                                            </div>
                                            <span className="font-bold text-white font-mono text-xs">{file.filename}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-xs font-medium text-slate-400">
                                        {new Date(file.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 text-xs font-mono text-slate-500">
                                        {file.size_kb} KB
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <Button
                                            size="sm"
                                            variant="primary"
                                            className="bg-brand-accent hover:bg-brand-accent/80 text-white border-none"
                                            onClick={() => handleDownload(file.filename)}
                                        >
                                            <Download size={14} className="mr-2" />
                                            Download
                                        </Button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ExportsList;
