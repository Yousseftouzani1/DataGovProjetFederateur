import React from 'react';
import { useRangerPermissions } from '../context/RangerContext';
import { Shield, ShieldCheck, ShieldX, EyeOff } from 'lucide-react';

/**
 * AccessIndicator Component
 * Shows the user's current Ranger access level visually.
 * Per Cahier des Charges: Frontend awareness of Ranger policies.
 */
const AccessIndicator: React.FC = () => {
    const permissions = useRangerPermissions();

    if (permissions.loading) {
        return (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-700/50 rounded-lg animate-pulse">
                <Shield className="w-4 h-4 text-gray-400" />
                <span className="text-xs text-gray-400">Checking...</span>
            </div>
        );
    }

    const getAccessBadge = () => {
        switch (permissions.access_level) {
            case 'full':
                return {
                    icon: <ShieldCheck className="w-4 h-4" />,
                    text: 'Full Access',
                    className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                };
            case 'masked':
                return {
                    icon: <EyeOff className="w-4 h-4" />,
                    text: 'Masked View',
                    className: 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                };
            case 'denied':
            default:
                return {
                    icon: <ShieldX className="w-4 h-4" />,
                    text: 'Restricted',
                    className: 'bg-red-500/20 text-red-400 border-red-500/30'
                };
        }
    };

    const badge = getAccessBadge();

    return (
        <div className="flex items-center gap-3">
            {/* Main Access Badge */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${badge.className}`}>
                {badge.icon}
                <span className="text-xs font-medium">{badge.text}</span>
            </div>

            {/* PII/SPI Indicators */}
            <div className="flex items-center gap-1.5">
                <div
                    className={`px-2 py-1 rounded text-xs font-mono ${permissions.can_view_pii
                        ? 'bg-blue-500/20 text-blue-400'
                        : 'bg-gray-700/50 text-gray-500'
                        }`}
                    title={permissions.can_view_pii ? 'Can view PII data' : 'PII data hidden'}
                >
                    PII {permissions.can_view_pii ? '✓' : '✗'}
                </div>
                <div
                    className={`px-2 py-1 rounded text-xs font-mono ${permissions.can_view_spi
                        ? 'bg-purple-500/20 text-purple-400'
                        : 'bg-gray-700/50 text-gray-500'
                        }`}
                    title={permissions.can_view_spi ? 'Can view SPI data' : 'SPI data hidden'}
                >
                    SPI {permissions.can_view_spi ? '✓' : '✗'}
                </div>
            </div>

            {/* Ranger Connection Status */}
            <div
                className={`w-2 h-2 rounded-full ${permissions.ranger_connected ? 'bg-green-500' : 'bg-orange-500'
                    }`}
                title={permissions.ranger_connected ? 'Ranger Connected' : 'Ranger Offline (using defaults)'}
            />
        </div>
    );
};

export default AccessIndicator;
