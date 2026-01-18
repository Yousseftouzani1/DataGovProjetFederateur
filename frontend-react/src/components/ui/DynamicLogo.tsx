// React import removed
import { motion } from 'framer-motion';

interface DynamicLogoProps {
    role?: string;
    size?: number;
    className?: string;
    animate?: boolean;
}

const DynamicLogo = ({ role = 'default', size = 40, className = '', animate = true }: DynamicLogoProps) => {

    // Map roles to gradients/colors
    const getColor = (r: string) => {
        switch (r.toLowerCase()) {
            case 'admin': return 'from-red-500 to-orange-600';
            case 'steward': return 'from-emerald-400 to-green-600';
            case 'annotator': return 'from-purple-400 to-pink-600';
            case 'labeler': return 'from-cyan-400 to-teal-600';
            default: return 'from-cyan-400 to-teal-600'; // Default to labeler theme
        }
    };

    const gradient = getColor(role);

    return (
        <div className={`relative flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
            {/* Glow Effect */}
            <div className={`absolute inset-0 bg-gradient-to-br ${gradient} blur-xl opacity-30 rounded-full`} />

            <svg
                width={size}
                height={size}
                viewBox="0 0 40 40"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="relative z-10"
            >
                <defs>
                    <linearGradient id={`grad-${role}`} x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" className={`stop-color-${role}-start`} style={{ stopColor: 'currentColor' }} />
                        <stop offset="100%" className={`stop-color-${role}-end`} style={{ stopColor: 'currentColor' }} />
                    </linearGradient>
                </defs>

                {/* Shield Base */}
                <motion.path
                    initial={animate ? { pathLength: 0, opacity: 0 } : { pathLength: 1, opacity: 1 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 1.5, ease: "easeInOut" }}
                    d="M20 38C20 38 36 30 36 14V6L20 2L4 6V14C4 30 20 38 20 38Z"
                    className={`fill-none stroke-[3]`}
                    stroke="url(#gradient)"
                    style={{ stroke: `url(#grad-${role})` }}
                />

                {/* Inner Data Nodes */}
                <motion.circle
                    initial={animate ? { scale: 0 } : { scale: 1 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.5, duration: 0.5 }}
                    cx="20" cy="16" r="3"
                    className={`fill-current`}
                />
                <motion.path
                    initial={animate ? { pathLength: 0 } : { pathLength: 1 }}
                    animate={{ pathLength: 1 }}
                    transition={{ delay: 0.8, duration: 0.5 }}
                    d="M20 19V26"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                />
                <motion.circle
                    initial={animate ? { scale: 0 } : { scale: 1 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 1, duration: 0.5 }}
                    cx="14" cy="28" r="2.5"
                    className={`fill-current opacity-80`}
                />
                <motion.circle
                    initial={animate ? { scale: 0 } : { scale: 1 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 1.1, duration: 0.5 }}
                    cx="26" cy="28" r="2.5"
                    className={`fill-current opacity-80`}
                />
            </svg>

            {/* Dynamic Styling Injection for specific gradient logic if needed */}
            <div className={`hidden bg-gradient-to-br ${gradient} text-transparent bg-clip-text`}>
                <span className="text-current">{/* Hack to apply gradient text color classes for usage above */}</span>
            </div>
        </div>

    );
};

export default DynamicLogo;
