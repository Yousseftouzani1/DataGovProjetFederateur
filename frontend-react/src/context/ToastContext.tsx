import React, { createContext, useContext, useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, X, Info } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

interface Toast {
    id: string;
    message: string;
    type: ToastType;
}

interface ToastContextType {
    addToast: (message: string, type: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((message: string, type: ToastType) => {
        const id = Math.random().toString(36).substring(7);
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 4000);
    }, []);

    const removeToast = (id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    };

    return (
        <ToastContext.Provider value={{ addToast }}>
            {children}
            <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
                <AnimatePresence mode="popLayout">
                    {toasts.map(toast => (
                        <motion.div
                            key={toast.id}
                            initial={{ opacity: 0, x: 20, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, x: 0, scale: 1, y: 0 }}
                            exit={{ opacity: 0, x: 20, scale: 0.9 }}
                            layout
                            className={`
                                pointer-events-auto flex items-center gap-3 px-5 py-4 rounded-2xl shadow-2xl backdrop-blur-xl border min-w-[300px]
                                ${toast.type === 'success' ? 'bg-green-500/90 border-green-400/30 text-white shadow-green-500/20' :
                                    toast.type === 'error' ? 'bg-red-500/90 border-red-400/30 text-white shadow-red-500/20' :
                                        'bg-slate-800/90 border-white/10 text-white shadow-black/20'}
                            `}
                        >
                            <div className={`p-2 rounded-full ${toast.type === 'success' ? 'bg-white/20' : toast.type === 'error' ? 'bg-white/20' : 'bg-brand-primary/20'}`}>
                                {toast.type === 'success' && <CheckCircle2 size={20} />}
                                {toast.type === 'error' && <AlertCircle size={20} />}
                                {toast.type === 'info' && <Info size={20} />}
                            </div>
                            <span className="text-sm font-bold pr-2 flex-grow">{toast.message}</span>
                            <button onClick={() => removeToast(toast.id)} className="p-1 hover:bg-white/20 rounded-full transition-colors">
                                <X size={16} />
                            </button>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
};

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) throw new Error('useToast must be used within ToastProvider');
    return context;
};
