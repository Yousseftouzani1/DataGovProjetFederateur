import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import axios from 'axios';

interface RangerPermissions {
    username: string;
    role: string;
    access_level: 'full' | 'masked' | 'denied';
    can_view_pii: boolean;
    can_view_spi: boolean;
    mask_type: string | null;
    ranger_connected: boolean;
    loading: boolean;
    error: string | null;
}

const defaultPermissions: RangerPermissions = {
    username: '',
    role: 'unknown',
    access_level: 'denied',
    can_view_pii: false,
    can_view_spi: false,
    mask_type: null,
    ranger_connected: false,
    loading: true,
    error: null
};

const RangerContext = createContext<RangerPermissions>(defaultPermissions);

export const useRangerPermissions = () => useContext(RangerContext);

interface RangerProviderProps {
    children: React.ReactNode;
}

export const RangerProvider = ({ children }: RangerProviderProps) => {
    const user = useAuthStore((state) => state.user);
    const [permissions, setPermissions] = useState<RangerPermissions>(defaultPermissions);

    useEffect(() => {
        const fetchPermissions = async () => {
            if (!user?.username) {
                setPermissions({ ...defaultPermissions, loading: false });
                return;
            }

            try {
                // Use username directly
                const username = user.username;
                const role = user.role || 'unknown';

                const response = await axios.get('/api/cleaning/permissions', {
                    params: { username, role }
                });

                setPermissions({
                    ...response.data,
                    loading: false,
                    error: null
                });

                console.log('🛡️ Ranger Permissions:', response.data);
            } catch (error: any) {
                console.warn('⚠️ Could not fetch Ranger permissions:', error.message);
                // Fallback: use role-based defaults
                const role = user.role || 'labeler';
                setPermissions({
                    username: user.username,
                    role: role,
                    access_level: role === 'admin' || role === 'steward' ? 'full' :
                        role === 'annotator' ? 'masked' : 'denied',
                    can_view_pii: role === 'admin' || role === 'steward',
                    can_view_spi: role === 'admin',
                    mask_type: role === 'annotator' ? 'MASK_SHOW_LAST_4' : null,
                    ranger_connected: false,
                    loading: false,
                    error: 'Ranger offline - using defaults'
                });
            }
        };

        fetchPermissions();
    }, [user]);

    return (
        <RangerContext.Provider value={permissions}>
            {children}
        </RangerContext.Provider>
    );
};

export default RangerProvider;
