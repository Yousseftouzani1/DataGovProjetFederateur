import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import apiClient from '../../services/api';
import AccessIndicator from '../AccessIndicator';

interface ShellProps {
    children: React.ReactNode;
}

const Shell = ({ children }: ShellProps) => {
    const [nodeStatus, setNodeStatus] = useState({ online: 0, total: 6, status: 'Initializing' });

    const checkNodes = async () => {
        const services = [
            '/auth/health',
            '/cleaning/health',
            '/quality/health',
            '/presidio/health',
            '/taxonomie/health',
            '/ethimask/health'
        ];

        try {
            const results = await Promise.allSettled(services.map(s => apiClient.get(s)));
            const onlineCount = results.filter(r => r.status === 'fulfilled').length;
            setNodeStatus({
                online: onlineCount,
                total: services.length,
                status: onlineCount === services.length ? 'Operational' : onlineCount > 0 ? 'Degraded' : 'Critical'
            });
        } catch (err) {
            setNodeStatus(prev => ({ ...prev, status: 'Error' }));
        }
    };

    useEffect(() => {
        checkNodes();
        const interval = setInterval(checkNodes, 60000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="h-screen bg-bg-deep flex overflow-hidden">
            <Sidebar />
            <main className="flex-1 p-8 overflow-y-auto max-h-screen">
                <header className="flex justify-between items-center mb-10">
                    <div>
                        <h1 className="text-sm font-medium text-slate-500 uppercase tracking-widest mb-1">System Workspace</h1>
                        <div className="flex items-center gap-2">
                            <span className={`w-2.5 h-2.5 rounded-full ${nodeStatus.status === 'Operational' ? 'bg-green-500 animate-pulse' :
                                nodeStatus.status === 'Degraded' ? 'bg-orange-500 animate-pulse' : 'bg-red-500 animate-bounce'
                                } shadow-[0_0_10px_currentColor]`} />
                            <h2 className="text-xl font-bold text-white tracking-tight">Main Command Deck</h2>
                        </div>
                    </div>

                    {/* Ranger Access Indicator - Shows user's security level */}
                    <AccessIndicator />

                    <div className="flex items-center gap-8">
                        <div className="flex flex-col text-right">
                            <span className="text-sm font-bold text-white uppercase tracking-tighter">{nodeStatus.status} Status</span>
                            <span className="text-[10px] text-brand-primary font-black uppercase tracking-widest">
                                {nodeStatus.online} / {nodeStatus.total} Nodes Active
                            </span>
                        </div>
                        <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-brand-primary to-brand-secondary p-[1px] shadow-lg shadow-brand-primary/20">
                            <div className="w-full h-full rounded-[15px] bg-bg-deep flex items-center justify-center text-brand-primary font-bold">
                                GV
                            </div>
                        </div>
                    </div>
                </header>

                <AnimatePresence mode="wait">
                    <motion.div
                        key={window.location.pathname}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.3 }}
                    >
                        {children}
                    </motion.div>
                </AnimatePresence>
            </main>
        </div>
    );
};

export default Shell;
