import { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Lock, Shield, UserCheck, Briefcase, Eye, EyeOff } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import apiClient from '../services/api';

const SignupPage = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        email: '',
        username: '',
        password: '',
        role: 'analyst'
    });
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.id]: e.target.value });
    };

    const handleRoleSelect = (role: string) => {
        setFormData({ ...formData, role });
    };

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        setSuccess('');

        try {
            const resp = await apiClient.post('/users/create', {
                first_name: formData.firstName,
                last_name: formData.lastName,
                email: formData.email,
                username: formData.username,
                password: formData.password,
                role: formData.role
            });

            setSuccess(resp.data.message || 'Account created successfully! Redirecting to login...');
            setTimeout(() => navigate('/login'), 2000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed');
        } finally {
            setIsLoading(false);
        }
    };

    const roles = [
        { id: 'steward', name: 'Data Steward', desc: 'Quality Expert', icon: Shield },
        { id: 'annotator', name: 'Annotator', desc: 'Data Validator', icon: UserCheck },
        { id: 'labeler', name: 'Labeler', desc: 'Tag Specialist', icon: Briefcase },
        { id: 'analyst', name: 'Analyst', desc: 'Policy Viewer', icon: User }
    ];

    return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-bg-deep to-bg-deep py-12">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-2xl"
            >
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">Create Account</h1>
                    <p className="text-slate-400">Join the DataGov intelligence network</p>
                </div>

                <form onSubmit={handleSignup} className="glass p-8 rounded-3xl space-y-6">
                    {error && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-500 text-sm">
                            {success}
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">First Name</label>
                            <input
                                id="firstName"
                                type="text"
                                required
                                className="input-premium w-full"
                                placeholder="Enter first name"
                                value={formData.firstName}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Last Name</label>
                            <input
                                id="lastName"
                                type="text"
                                required
                                className="input-premium w-full"
                                placeholder="Enter last name"
                                value={formData.lastName}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Email Address</label>
                        <div className="relative">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-primary" size={18} />
                            <input
                                id="email"
                                type="email"
                                required
                                className="input-premium w-full pl-12"
                                placeholder="name@organization.com"
                                value={formData.email}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Username</label>
                        <div className="relative">
                            <User className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-primary" size={18} />
                            <input
                                id="username"
                                type="text"
                                required
                                className="input-premium w-full pl-12"
                                placeholder="Choose a unique ID"
                                value={formData.username}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Secure Password</label>
                        <div className="relative">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-primary" size={18} />
                            <input
                                id="password"
                                type={showPassword ? 'text' : 'password'}
                                required
                                className="input-premium w-full pl-12 pr-12 font-mono tracking-widest"
                                placeholder="••••••••"
                                value={formData.password}
                                onChange={handleChange}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <label className="text-sm font-medium text-slate-300 ml-1">Select Your Role</label>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {roles.map((role) => (
                                <button
                                    key={role.id}
                                    type="button"
                                    onClick={() => handleRoleSelect(role.id)}
                                    className={`flex flex-col items-center p-3 rounded-2xl border transition-all duration-300 ${formData.role === role.id
                                        ? 'bg-brand-primary/10 border-brand-primary text-white shadow-[0_0_15px_rgba(99,102,241,0.2)]'
                                        : 'bg-slate-900/50 border-border-subtle text-slate-400 hover:border-slate-700'
                                        }`}
                                >
                                    <role.icon size={20} className="mb-2" />
                                    <span className="text-xs font-bold leading-tight">{role.name.split(' ')[role.name.split(' ').length - 1]}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    <Button type="submit" className="w-full" isLoading={isLoading}>
                        Create Account
                    </Button>

                    <p className="text-center text-sm text-slate-500">
                        Already have an account? <Link to="/login" className="text-brand-primary cursor-pointer hover:underline">Sign In</Link>
                    </p>
                </form>
            </motion.div>
        </div>
    );
};

export default SignupPage;
