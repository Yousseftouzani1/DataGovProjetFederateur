import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import DynamicLogo from '../components/ui/DynamicLogo';
import {
    ShieldCheck,
    ChevronRight,
    Map,
    Shield,
    Eye,
    Wind,
    Lock,
    Zap,
    Code,
    Database,
    MessageSquare,
    Box
} from 'lucide-react';

const LandingPage = () => {
    const navigate = useNavigate();

    // Team Members
    const team = [
        { name: "Prof. Karim Baïna", role: "Project Supervisor" },
        { name: "Mme. Manal Gasmi", role: "Project Co-Supervisor" },
        { name: "Nisrine IBNOU-KADY", role: "Contributor" },
        { name: "Younes Bazzaoui", role: "Contributor" },
        { name: "Youssef Elgarch", role: "Contributor" },
        { name: "Youssef Touzani", role: "Contributor" },
    ];

    // Tech Stack
    const techStack = [
        { name: "Apache Atlas", icon: Map, color: "text-blue-500" },
        { name: "Apache Ranger", icon: Shield, color: "text-green-500" },
        { name: "Presidio", icon: Eye, color: "text-cyan-500" },
        { name: "Apache Airflow", icon: Wind, color: "text-teal-400" },
        { name: "TenSEAL", icon: Lock, color: "text-purple-500" },
        { name: "FastAPI", icon: Zap, color: "text-yellow-400" },
        { name: "React", icon: Code, color: "text-blue-400" },
        { name: "MongoDB", icon: Database, color: "text-green-400" },
        { name: "RabbitMQ", icon: MessageSquare, color: "text-orange-500" },
        { name: "Docker", icon: Box, color: "text-blue-600" }
    ];

    return (
        <div className="min-h-screen bg-[#02040a] text-white selection:bg-teal-500 selection:text-white overflow-hidden font-sans">

            {/* BACKGROUND EFFECTS */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-teal-600/10 rounded-full blur-[120px] mix-blend-screen" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-emerald-600/10 rounded-full blur-[120px] mix-blend-screen" />
                <div className="absolute top-[40%] left-[50%] transform -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[url('/grid.svg')] opacity-[0.03]" />
            </div>

            {/* NAVBAR */}
            <nav className="relative z-50 flex justify-between items-center px-8 py-6 max-w-7xl mx-auto">
                <div className="flex items-center gap-3">
                    {/* Dynamic Logo */}
                    <div className="text-emerald-500">
                        <DynamicLogo role="steward" size={48} animate={true} />
                    </div>
                    <span className="text-2xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-emerald-400">
                        DataSentinel
                    </span>
                </div>

                <div className="flex items-center gap-6">
                    {/* ENSIAS LOGO */}
                    <img src="/ensias.png" alt="ENSIAS" className="h-14 w-auto object-contain" />

                    <button
                        onClick={() => navigate('/login')}
                        className="px-6 py-2 rounded-full bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/20 backdrop-blur-md transition-all font-bold text-sm text-teal-400 flex items-center gap-2 group"
                    >
                        Login
                        <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>
            </nav>

            {/* HERO SECTION */}
            <main className="relative z-10 pt-24 pb-32 px-6">
                <div className="max-w-6xl mx-auto text-center">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8 }}
                        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-900/30 border border-teal-500/30 text-teal-400 text-xs font-bold uppercase tracking-[0.2em] mb-8 shadow-[0_0_20px_rgba(20,184,166,0.2)]"
                    >
                        <ShieldCheck className="w-3.5 h-3.5" />
                        GovOps • Privacy • Security
                    </motion.div>

                    <h1 className="text-7xl md:text-9xl font-black tracking-tighter mb-8 leading-[0.9]">
                        <span className="block text-white opacity-90">Secure The</span>
                        <Typewriter text={["Future Data", "Privacy Ops", "Compliance", "Governance"]} />
                    </h1>

                    <p className="text-xl md:text-2xl text-slate-400 max-w-3xl mx-auto mb-12 leading-relaxed font-light">
                        The ultimate federated platform integrating
                        <span className="text-teal-400 font-medium"> Apache Atlas</span>,
                        <span className="text-teal-400 font-medium"> Ranger</span>, and
                        <span className="text-teal-400 font-medium"> Presidio</span>.
                        Automating data protection across the enterprise.
                    </p>

                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => navigate('/login')}
                        className="px-10 py-5 bg-gradient-to-r from-teal-600 to-emerald-600 rounded-2xl font-bold text-lg shadow-[0_0_40px_rgba(20,184,166,0.4)] hover:shadow-[0_0_60px_rgba(20,184,166,0.6)] transition-all flex items-center gap-3 mx-auto text-white border border-teal-400/20"
                    >
                        Launch Console
                        <ChevronRight className="w-5 h-5" />
                    </motion.button>
                </div>

                {/* TECH STACK CAROUSEL */}
                <div className="mt-40 border-y border-white/5 bg-black/20 backdrop-blur-sm py-10 overflow-hidden relative">
                    <div className="absolute inset-y-0 left-0 w-48 bg-gradient-to-r from-[#02040a] to-transparent z-10" />
                    <div className="absolute inset-y-0 right-0 w-48 bg-gradient-to-l from-[#02040a] to-transparent z-10" />

                    <motion.div
                        className="flex gap-20 whitespace-nowrap"
                        animate={{ x: ["0%", "-50%"] }}
                        transition={{ repeat: Infinity, ease: "linear", duration: 40 }}
                    >
                        {[...techStack, ...techStack].map((tech, i) => (
                            <div key={i} className={`font-black text-2xl uppercase tracking-widest opacity-60 flex items-center gap-4 hover:opacity-100 transition-all cursor-default ${tech.color}`}>
                                <tech.icon className="w-8 h-8" />
                                {tech.name}
                            </div>
                        ))}
                    </motion.div>
                </div>
            </main>

            {/* FEATURES GRID (IMAGES) */}
            <section className="py-32 relative z-10 max-w-7xl mx-auto px-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <FeatureCard
                        image="/ethimask_feature.png"
                        title="EthiMask Encryption"
                        desc="Homomorphic encryption using TenSEAL to perform computations on encrypted data without decryption."
                    />
                    <FeatureCard
                        image="/pii_feature.png"
                        title="PII Sentinel"
                        desc="Automated scanning with Microsoft Presidio to detect and redact sensitive entities (CIN, RIB, Email)."
                    />
                    <FeatureCard
                        image="/governance_feature.png"
                        title="Federated Governance"
                        desc="Unified cataloging via Apache Atlas and granular access control via Apache Ranger."
                    />
                </div>
            </section>

            {/* ROLES SECTION (UPDATED: 4 ROLES + BACKGROUND IMAGES) */}
            <section className="py-32 bg-gradient-to-b from-[#02040a] to-[#050a14] border-t border-white/5 relative z-10">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="text-center mb-20">
                        <h2 className="text-5xl font-black mb-6 tracking-tight">The Guardians of AI</h2>
                        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
                            DataSentinel empowers four key roles to maintain dataset integrity, security, and compliance across the platform.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Admin */}
                        <RoleCard
                            role="Admin"
                            image="/role_admin.png"
                            desc="System orchestration, user management, and global configuration of governance policies."
                        />
                        {/* Data Steward */}
                        <RoleCard
                            role="Data Steward"
                            image="/role_steward.png"
                            desc="Orchestrates the governance lifecycle. Approves policies, manages schemas, and oversees compliance."
                        />
                        {/* Annotator */}
                        <RoleCard
                            role="Annotator"
                            image="/role_annotator.png"
                            desc="Validates AI corrections and enriches raw data. The first line of defense in data quality assurance."
                        />
                        {/* Labeler */}
                        <RoleCard
                            role="Labeler"
                            image="/role_labeler.png"
                            desc="Classifies verified data for ML training. Ensures the ground truth is accurate and unbiased."
                        />
                    </div>
                </div>
            </section>

            {/* TEAM SECTION */}
            <section className="py-32 bg-[#02040a] border-t border-white/5 relative z-10">
                <div className="max-w-5xl mx-auto px-6 text-center">
                    <h2 className="text-3xl font-bold mb-16 text-slate-300 uppercase tracking-widest">Project Contributors</h2>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-12">
                        {team.map((member, idx) => (
                            <motion.div
                                key={idx}
                                whileHover={{ scale: 1.05 }}
                                className="group p-6 rounded-xl border border-white/5 hover:border-teal-500/30 hover:bg-teal-500/5 transition-all"
                            >
                                <h3 className="font-bold text-white text-lg group-hover:text-teal-400 transition-colors">{member.name}</h3>
                                <p className="text-slate-500 text-xs uppercase tracking-wider mt-2 font-medium">{member.role}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* FOOTER */}
            <footer className="py-12 border-t border-white/5 text-center text-slate-600 text-sm relative z-10 bg-[#010205]">
                <p className="mb-4">&copy; {new Date().getFullYear()} DataSentinel Project.</p>
                <div className="flex justify-center gap-6 font-medium tracking-wide">
                    <span className="hover:text-teal-500 cursor-pointer transition-colors">ENSIAS</span>
                    <span>•</span>
                    <span className="hover:text-teal-500 cursor-pointer transition-colors">GovOps</span>
                    <span>•</span>
                    <span className="hover:text-teal-500 cursor-pointer transition-colors">Federated Learning</span>
                </div>
            </footer>
        </div>
    );
};

// --- Subcomponents ---

const Typewriter = ({ text }: { text: string[] }) => {
    const [index, setIndex] = React.useState(0);
    const [subIndex, setSubIndex] = React.useState(0);
    const [reverse, setReverse] = React.useState(false);
    const [blink, setBlink] = React.useState(true);

    React.useEffect(() => {
        const timeout = setInterval(() => setBlink((prev) => !prev), 500);
        return () => clearInterval(timeout);
    }, []);

    React.useEffect(() => {
        if (subIndex === text[index].length + 1 && !reverse) {
            setTimeout(() => setReverse(true), 1000);
            return;
        }
        if (subIndex === 0 && reverse) {
            setReverse(false);
            setIndex((prev) => (prev + 1) % text.length);
            return;
        }
        const timeout = setTimeout(() => {
            setSubIndex((prev) => prev + (reverse ? -1 : 1));
        }, Math.max(reverse ? 75 : subIndex === text[index].length ? 1000 : 150, Math.floor(Math.random() * 350)));
        return () => clearTimeout(timeout);
    }, [subIndex, index, reverse, text]);

    return (
        <span className="bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-emerald-500">
            {`${text[index].substring(0, subIndex)}${blink ? "|" : " "}`}
        </span>
    );
};

const FeatureCard = ({ image, title, desc }: { image: string, title: string, desc: string }) => (
    <motion.div
        whileHover={{ y: -10 }}
        className="relative overflow-hidden h-[400px] rounded-3xl bg-white/5 border border-white/10 group cursor-pointer"
    >
        <div className="absolute inset-0 z-0">
            <img src={image} alt={title} className="w-full h-full object-cover opacity-50 group-hover:opacity-70 group-hover:scale-110 transition-all duration-700 ease-out grayscale group-hover:grayscale-0" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#02040a] via-[#02040a]/80 to-transparent" />
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-8 z-10 translate-y-2 group-hover:translate-y-0 transition-transform">
            <h3 className="text-2xl font-black mb-3 text-white drop-shadow-lg">{title}</h3>
            <p className="text-slate-300 leading-relaxed text-sm drop-shadow-md opacity-80 group-hover:opacity-100 transition-opacity">{desc}</p>
        </div>
    </motion.div>
);

const RoleCard = ({ role, desc, image }: any) => (
    <motion.div
        whileHover={{ scale: 1.02 }}
        className="relative overflow-hidden h-[320px] rounded-2xl border border-white/10 group bg-[#050a14]"
    >
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
            <img src={image} alt={role} className="w-full h-full object-cover opacity-40 group-hover:opacity-60 transition-all duration-500" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#02040a] via-[#02040a]/80 to-transparent" />
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-6 z-10">
            <h3 className="text-xl font-bold mb-2 text-white">{role}</h3>
            <p className="text-slate-400 leading-relaxed text-xs">{desc}</p>
        </div>
    </motion.div>
);

export default LandingPage;
