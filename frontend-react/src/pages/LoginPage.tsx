import { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, User, Home } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { useAuthStore } from '../store/authStore';
import apiClient from '../services/api';
import DynamicLogo from '../components/ui/DynamicLogo';

const LoginPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const setAuth = useAuthStore((state) => state.setAuth);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            // FastAPI OAuth2 expects x-www-form-urlencoded
            const params = new URLSearchParams();
            params.append('username', username);
            params.append('password', password);

            const resp = await apiClient.post('/auth/login', params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            const { access_token, role, username: resUsername } = resp.data;

            // Construct user object expected by store
            const user = {
                username: resUsername,
                role: role.toLowerCase() as any
            };

            setAuth(user, access_token);
            localStorage.setItem('token', access_token);
            // Support legacy components that check localStorage directly
            localStorage.setItem('username', resUsername);
            localStorage.setItem('userRole', role.toLowerCase());

        } catch (err: any) {
            setError(err.response?.data?.detail || 'Authentication failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-bg-deep to-bg-deep relative">
            <Link
                to="/"
                className="absolute top-8 left-8 p-3 rounded-2xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all group flex items-center gap-2"
                title="Return to Landing Page"
            >
                <Home size={20} />
                <span className="text-sm font-bold opacity-0 group-hover:opacity-100 transition-opacity">Home</span>
            </Link>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md"
            >
                <div className="text-center mb-10">
                    <motion.div
                        initial={{ scale: 0.5, rotate: -10 }}
                        animate={{ scale: 1, rotate: 0 }}
                        className="inline-flex mb-6 text-brand-primary"
                    >
                        <DynamicLogo role="default" size={96} animate={true} />
                    </motion.div>
                    <h1 className="text-4xl font-bold tracking-tight text-white mb-2">DataGov</h1>
                    <p className="text-slate-400">Expert Data Intelligence & Governance</p>
                </div>

                <form onSubmit={handleLogin} className="glass p-8 rounded-3xl space-y-6">
                    {error && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
                            {error}
                        </div>
                    )}

                    <div className="space-y-2">
                        <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1">Access ID</label>
                        <div className="relative">
                            <User className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-primary" size={18} />
                            <input
                                type="text"
                                required
                                className="input-premium w-full pl-12 font-mono text-sm"
                                placeholder="admin"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1">Secure Token</label>
                        <div className="relative">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-primary" size={18} />
                            <input
                                type="password"
                                required
                                className="input-premium w-full pl-12 font-mono tracking-widest"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <Button type="submit" className="w-full" isLoading={isLoading}>
                        Sign In
                    </Button>

                    <p className="text-center text-sm text-slate-500">
                        Don't have an account? <Link to="/signup" className="text-brand-primary cursor-pointer hover:underline">Sign up for free</Link>
                    </p>
                </form>
            </motion.div>
        </div>
    );
};

export default LoginPage;
