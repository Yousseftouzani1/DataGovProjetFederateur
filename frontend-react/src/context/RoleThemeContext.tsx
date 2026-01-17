import React, { createContext, useContext, useEffect } from 'react';
import { useAuthStore } from '../store/authStore';

// Role-specific color themes
const ROLE_THEMES = {
    labeler: {
        primary: '#06b6d4',      // cyan-500
        secondary: '#14b8a6',    // teal-500
        gradient: 'from-cyan-400 to-teal-600'
    },
    annotator: {
        primary: '#a855f7',      // purple-500
        secondary: '#ec4899',    // pink-500
        gradient: 'from-purple-400 to-pink-600'
    },
    steward: {
        primary: '#10b981',      // emerald-500
        secondary: '#22c55e',    // green-500
        gradient: 'from-emerald-400 to-green-600'
    },
    admin: {
        primary: '#ef4444',      // red-500
        secondary: '#f97316',    // orange-500
        gradient: 'from-red-500 to-orange-600'
    }
};

type RoleType = 'labeler' | 'annotator' | 'steward' | 'admin';

interface ThemeContextType {
    primary: string;
    secondary: string;
    gradient: string;
    role: RoleType;
}

const ThemeContext = createContext<ThemeContextType>({
    ...ROLE_THEMES.labeler,
    role: 'labeler'
});

export const useRoleTheme = () => useContext(ThemeContext);

interface RoleThemeProviderProps {
    children: React.ReactNode;
}

export const RoleThemeProvider = ({ children }: RoleThemeProviderProps) => {
    const user = useAuthStore((state) => state.user);
    const role = (user?.role || 'labeler') as RoleType;
    const theme = ROLE_THEMES[role] || ROLE_THEMES.labeler;

    // Apply CSS custom properties to document root
    useEffect(() => {
        const root = document.documentElement;
        root.style.setProperty('--color-brand-primary', theme.primary);
        root.style.setProperty('--color-brand-secondary', theme.secondary);

        // Also update the button gradient
        root.style.setProperty('--role-gradient-from', theme.primary);
        root.style.setProperty('--role-gradient-to', theme.secondary);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ ...theme, role }}>
            {children}
        </ThemeContext.Provider>
    );
};

export default RoleThemeProvider;
