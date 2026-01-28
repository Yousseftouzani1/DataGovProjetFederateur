import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Database, Shield, ExternalLink, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import apiClient from '../services/api';

const DiscoveryPage = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [activeFilters, setActiveFilters] = useState<string[]>([]);
    const [allDatasets, setAllDatasets] = useState<any[]>([]);
    const [results, setResults] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSearching, setIsSearching] = useState(false);

    // Facets (Enriched by data)
    const classifications = ["CONFIDENTIAL", "INTERNAL", "PUBLIC"];
    const domains = ["Health", "Finance", "HR", "Legal", "Gov", "General"];

    // Dynamically compute PII types from available data to ensure Atlas tags show up
    const piiTypes = Array.from(new Set([
        "CIN", "PHONE", "EMAIL", "IBAN", "PASSPORT",
        ...allDatasets.flatMap(d => d.tags)
    ])).sort();

    const fetchDatasets = async () => {
        setIsLoading(true);
        try {
            const resp = await apiClient.get('/cleaning/datasets');
            const data = resp.data || []; // The backend now returns the list directly

            // Map backend fields to frontend format if necessary
            const formatted = data.map((item: any) => ({
                id: item.id,
                name: item.name,
                classification: item.classification || "PUBLIC",
                tags: item.pii_tags || [],
                owner: item.owner || "system",
                date: item.date ? new Date(item.date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
                domain: item.domain || "General",
                atlas_guid: item.atlas_guid
            }));

            setAllDatasets(formatted);
            setResults(formatted);
        } catch (err) {
            console.error('Failed to fetch datasets', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSearch = () => {
        setIsSearching(true);
        // Local filtering for speed, mirroring Atlas/Solr behavior on the fetched set
        const filtered = allDatasets.filter(item =>
            (searchTerm === '' || item.name.toLowerCase().includes(searchTerm.toLowerCase())) &&
            (activeFilters.length === 0 ||
                activeFilters.includes(item.classification) ||
                item.tags.some((t: string) => activeFilters.includes(t)) ||
                activeFilters.includes(item.domain))
        );

        setTimeout(() => {
            setResults(filtered);
            setIsSearching(false);
        }, 300);
    };

    const toggleFilter = (filter: string) => {
        setActiveFilters(prev =>
            prev.includes(filter) ? prev.filter(f => f !== filter) : [...prev, filter]
        );
    };

    useEffect(() => {
        fetchDatasets();
    }, []);

    useEffect(() => {
        handleSearch();
    }, [activeFilters, allDatasets]);

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                        <Search className="text-brand-primary" size={36} />
                        Data Discovery
                    </h1>
                    <p className="text-slate-400">Advanced Catalog Search (Apache Atlas / Solr)</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="ghost" className="text-slate-400" onClick={fetchDatasets}>
                        <Loader2 size={16} className={`mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                        Refresh Catalog
                    </Button>
                    <Button variant="ghost" className="text-slate-400">
                        <ExternalLink size={16} className="mr-2" />
                        Open Atlas UI
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-8">
                {/* Sidebar Facets */}
                <div className="col-span-3 space-y-8">
                    {/* Domain Facet */}
                    <div className="glass p-6 rounded-3xl border border-white/5">
                        <div className="flex items-center gap-2 mb-4 text-white font-bold">
                            <Database size={18} className="text-blue-400" />
                            Data Domain
                        </div>
                        <div className="space-y-2">
                            {domains.map(d => (
                                <div key={d} onClick={() => toggleFilter(d)}
                                    className={`p-2 rounded-xl text-xs font-bold cursor-pointer transition-all flex justify-between items-center ${activeFilters.includes(d) ? 'bg-blue-500/20 text-blue-400' : 'bg-white/5 text-slate-400 hover:bg-white/10'}`}>
                                    {d}
                                    {activeFilters.includes(d) && <ArrowRight size={12} />}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* PII Facet */}
                    <div className="glass p-6 rounded-3xl border border-white/5">
                        <div className="flex items-center gap-2 mb-4 text-white font-bold">
                            <Shield size={18} className="text-red-400" />
                            PII Entities
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {piiTypes.map(p => (
                                <div key={p} onClick={() => toggleFilter(p)}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition-all border ${activeFilters.includes(p) ? 'bg-red-500/20 border-red-500 text-red-400' : 'bg-transparent border-slate-700 text-slate-500 hover:border-slate-500'}`}>
                                    {p}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Classification Facet */}
                    <div className="glass p-6 rounded-3xl border border-white/5">
                        <div className="flex items-center gap-2 mb-4 text-white font-bold">
                            <Shield size={18} className="text-brand-primary" />
                            Classification
                        </div>
                        <div className="space-y-2">
                            {classifications.map(c => (
                                <div key={c} onClick={() => toggleFilter(c)}
                                    className={`p-2 rounded-xl text-xs font-bold cursor-pointer transition-all flex justify-between items-center ${activeFilters.includes(c) ? 'bg-brand-primary text-white' : 'bg-white/5 text-slate-400 hover:bg-white/10'}`}>
                                    {c}
                                    {activeFilters.includes(c) && <ArrowRight size={12} />}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Results Area */}
                <div className="col-span-9 space-y-6">
                    {/* Search Bar */}
                    <div className="glass p-2 rounded-2xl flex items-center border border-white/5 focus-within:border-brand-primary/50 transition-colors">
                        <div className="p-3 text-slate-500">
                            <Search size={20} />
                        </div>
                        <input
                            type="text"
                            placeholder="Search for datasets, columns, or business terms..."
                            className="bg-transparent w-full text-white placeholder:text-slate-600 focus:outline-none"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        />
                        <Button onClick={handleSearch} isLoading={isSearching} className="rounded-xl">
                            Search
                        </Button>
                    </div>

                    {/* Hits */}
                    <div className="space-y-4">
                        <p className="text-xs font-black uppercase tracking-widest text-slate-600 mb-2">
                            {isLoading ? 'Cataloging Assets...' : `${results.length} Assets Found`}
                        </p>

                        {isLoading && (
                            <div className="py-20 text-center">
                                <Loader2 size={40} className="text-brand-primary animate-spin mx-auto mb-4" />
                                <p className="text-slate-500">Connecting to Apache Atlas metadata storage...</p>
                            </div>
                        )}

                        {!isLoading && results.length === 0 && (
                            <div className="py-20 text-center glass rounded-3xl border border-dashed border-white/10">
                                <Database size={40} className="text-slate-700 mx-auto mb-4" />
                                <p className="text-slate-500 font-bold">No assets match your search criteria</p>
                                <Button variant="ghost" className="mt-4" onClick={() => { setSearchTerm(''); setActiveFilters([]); }}>Clear All Filters</Button>
                            </div>
                        )}

                        <AnimatePresence mode="popLayout">
                            {results.map((item, i) => (
                                <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className="glass p-6 rounded-3xl border border-white/5 hover:border-brand-primary/30 transition-all group cursor-pointer"
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex items-center gap-4">
                                            <div className="p-3 bg-brand-primary/10 rounded-2xl text-brand-primary">
                                                <Database size={24} />
                                            </div>
                                            <div>
                                                <h3 className="text-lg font-bold text-white group-hover:text-brand-primary transition-colors">
                                                    {item.name}
                                                </h3>
                                                <div className="flex gap-2 mt-1">
                                                    <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase ${item.classification === 'CRITICAL' || item.classification === 'CONFIDENTIAL' ? 'bg-red-500/20 text-red-400' :
                                                        item.classification === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                                                            'bg-green-500/10 text-green-400'
                                                        }`}>
                                                        {item.classification}
                                                    </span>
                                                    <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded uppercase border border-blue-500/20">
                                                        {item.domain}
                                                    </span>
                                                    {item.tags.map((t: string) => (
                                                        <span key={t} className="text-[10px] bg-white/5 text-slate-400 px-2 py-0.5 rounded uppercase border border-white/5">
                                                            #{t}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right text-xs text-slate-500 flex flex-col items-end gap-1">
                                            <p>Owner: <span className="text-slate-300">{item.owner}</span></p>
                                            <p>Updated: {item.date}</p>
                                            {item.atlas_guid && item.atlas_guid !== 'mock-guid-fallback' && (
                                                <span className="text-[10px] text-brand-primary/60 font-mono mt-1 bg-brand-primary/5 px-2 py-0.5 rounded-full border border-brand-primary/10 flex items-center gap-1 group-hover:bg-brand-primary/10 transition-colors">
                                                    <ExternalLink size={10} />
                                                    {item.atlas_guid.substring(0, 8)}...
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DiscoveryPage;

