export const updateFavicon = (role: string) => {
    // Exact colors from RoleThemeContext
    const getColors = (r: string) => {
        switch (r?.toLowerCase()) {
            case 'admin': return '#ef4444'; // red-500
            case 'steward': return '#10b981'; // emerald-500
            case 'annotator': return '#a855f7'; // purple-500
            case 'labeler': return '#06b6d4'; // cyan-500
            default: return '#06b6d4';
        }
    };

    const color = getColors(role);

    // Exact SVG geometry from DynamicLogo.tsx
    // Using simple fill/stroke instead of gradients for crisp favicon
    const svg = `
    <svg width="64" height="64" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 38C20 38 36 30 36 14V6L20 2L4 6V14C4 30 20 38 20 38Z" stroke="${color}" stroke-width="3" fill="none"/>
        <circle cx="20" cy="16" r="3" fill="${color}"/>
        <path d="M20 19V26" stroke="${color}" stroke-width="3" stroke-linecap="round"/>
        <circle cx="14" cy="28" r="2.5" fill="${color}" fill-opacity="0.8"/>
        <circle cx="26" cy="28" r="2.5" fill="${color}" fill-opacity="0.8"/>
    </svg>`.trim();

    let link = document.querySelector("link[rel*='icon']") as HTMLLinkElement;
    if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
    }

    link.type = 'image/svg+xml';
    link.href = `data:image/svg+xml;base64,${btoa(svg)}`;
};
