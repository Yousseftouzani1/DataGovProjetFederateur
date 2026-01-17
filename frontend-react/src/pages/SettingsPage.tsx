import { motion } from 'framer-motion';
import {
    Settings,
    Shield,
    Bell,
    Globe,
    Lock,
    Cpu,
    Database,
    Palette
} from 'lucide-react';
import { Button } from '../components/ui/Button';

const SettingsPage = () => {
    const sections = [
        { icon: Shield, title: 'Governance Policy', desc: 'Configure ISO 25012 thresholds and compliance rules.' },
        { icon: Bell, title: 'Alert Configurations', desc: 'Manage system-wide notification protocols.' },
        { icon: Globe, title: 'Node Network', desc: 'Configure cluster endpoints and latency buffers.' },
        { icon: Lock, title: 'Access Control', desc: 'Define granular role permissions and MFA rules.' },
        { icon: Cpu, title: 'Engine Scaling', desc: 'Modify Presidio and Cleaning service concurrency.' },
        { icon: Database, title: 'Storage Schema', desc: 'Update MongoDB and Atlas connection pools.' },
        { icon: Palette, title: 'Interface Theme', desc: 'Customize platform aesthetics and branding.' },
    ];

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

            <div className="glass p-10 rounded-[3rem] border border-white/5 bg-gradient-to-br from-brand-primary/5 to-transparent flex flex-col items-center text-center">
                <div className="p-4 bg-brand-primary/10 rounded-full mb-6">
                    <Settings className="text-brand-primary animate-spin-slow" size={32} />
                </div>
                <h2 className="text-2xl font-bold text-white mb-4">Master Sync Required</h2>
                <p className="text-slate-400 max-w-md mb-8">Changing critical network or storage parameters requires a rolling restart of the node cluster. Proceed with caution.</p>
                <div className="flex gap-4">
                    <Button variant="primary">Apply Global Sync</Button>
                    <Button variant="ghost">Revert to Safe State</Button>
                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
