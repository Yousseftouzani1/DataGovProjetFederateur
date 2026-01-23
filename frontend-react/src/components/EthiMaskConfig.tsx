import React, { useState, useEffect } from 'react';
import { Sliders, Save, RefreshCw, AlertCircle, Lock } from 'lucide-react';
import { Button } from './ui/Button';
import apiClient from '../services/api';
import { useToast } from '../context/ToastContext';

interface Config {
  sensitivity_weight: number;
  role_weight: number;
  context_weight: number;
  purpose_weight: number;
  bias: number;
  alpha: number;
}

const EthiMaskConfig: React.FC = () => {
  const { addToast } = useToast();
  const [config, setConfig] = useState<Config>({
    sensitivity_weight: 0.35,
    role_weight: -0.30,
    context_weight: 0.20,
    purpose_weight: 0.15,
    bias: 0.4,
    alpha: 0.5
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isHeActive, setIsHeActive] = useState(false);
  const [isHeLoading, setIsHeLoading] = useState(false);

  const handleInitHE = async () => {
    setIsHeLoading(true);
    try {
      await apiClient.post('/ethimask/he/context');
      setIsHeActive(true);
      addToast('TenSEAL Context Initialized Successfully', 'success');
    } catch (err) {
      console.error("Failed to init HE", err);
      addToast('Failed to initialize Homomorphic Encryption', 'error');
    } finally {
      setIsHeLoading(false);
    }
  };

  const fetchConfig = async () => {
    setIsLoading(true);
    try {
      const resp = await apiClient.get('/ethimask/config');
      setConfig(resp.data);
    } catch (err) {
      console.error('Failed to fetch EthiMask config', err);
      addToast('Failed to load masking configuration', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const totalWeight = (config.sensitivity_weight || 0) + Math.abs(config.role_weight || 0) + (config.context_weight || 0) + (config.purpose_weight || 0);

  const handleNormalize = () => {
    const sw = config.sensitivity_weight;
    const rw = Math.abs(config.role_weight);
    const cw = config.context_weight;
    const pw = config.purpose_weight;
    const sum = sw + rw + cw + pw;

    if (sum === 0) return;

    setConfig(prev => ({
      ...prev,
      sensitivity_weight: sw / sum,
      role_weight: (config.role_weight < 0 ? -1 : 1) * (rw / sum),
      context_weight: cw / sum,
      purpose_weight: pw / sum
    }));
    addToast('Weights normalized to Σ|w| = 1', 'info');
  };

  const handleSave = async () => {
    if (Math.abs(totalWeight - 1.0) > 0.01) {
      addToast('Error: Total absolute weight must sum to 1.0 for mathematical consistency.', 'error');
      return;
    }
    setIsSaving(true);
    try {
      // Map back to the format expected by the backend
      const payload = {
        ws: config.sensitivity_weight,
        wr: config.role_weight,
        wc: config.context_weight,
        wp: config.purpose_weight,
        bias: config.bias,
        alpha: config.alpha
      };
      await apiClient.post('/ethimask/config', payload);
      addToast('Governance weights updated successfully!', 'success');
    } catch (err) {
      console.error('Failed to save EthiMask config', err);
      addToast('Failed to update weights', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSliderChange = (key: keyof Config, value: number) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  if (isLoading) return <div className="p-8 text-center text-slate-500">Loading Perceptron Weights...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <Sliders className="text-brand-primary" size={20} />
          Perceptron Weight Configuration (V0.1)
        </h3>
        <Button variant="ghost" size="sm" onClick={fetchConfig} disabled={isSaving}>
          <RefreshCw size={16} className={isSaving ? 'animate-spin' : ''} />
        </Button>
      </div>

      <div className="grid gap-6">
        {[
          { key: 'sensitivity_weight', label: 'Sensitivity Weight (ws)', desc: 'Higher value = more aggressive masking for critical data.' },
          { key: 'role_weight', label: 'Role Trust Weight (wr)', desc: 'Lower value = restricted access for low-tier roles.' },
          { key: 'context_weight', label: 'Context Weight (wc)', desc: 'Weight given to environment (API vs Analysis).' },
          { key: 'purpose_weight', label: 'Purpose Weight (wp)', desc: 'Weight given to the intent of access.' },
          { key: 'bias', label: 'Decision Bias (b)', desc: 'Base threshold shift for all decisions.' },
          { key: 'alpha', label: 'Alpha Balance (α)', desc: 'Loss function balance: α·Privacy + (1-α)·Utility' },
        ].map((item) => (
          <div key={item.key} className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-bold text-slate-300">{item.label}</label>
              <span className="text-xs font-mono text-brand-primary bg-brand-primary/10 px-2 py-0.5 rounded-lg">
                {(config[item.key as keyof Config] as number).toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="-1"
              max="1"
              step="0.05"
              value={config[item.key as keyof Config]}
              onChange={(e) => handleSliderChange(item.key as keyof Config, parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-brand-primary"
            />
            <p className="text-[10px] text-slate-500 italic">{item.desc}</p>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-2xl bg-brand-primary/5 border border-brand-primary/20 flex items-start gap-3">
        <AlertCircle size={18} className="text-brand-primary mt-0.5" />
        <p className="text-xs text-slate-400 leading-relaxed">
          <strong>Equation:</strong> Score T' = σ(Σ w_i * x_i + b).
          <br />
          <strong>Loss Function:</strong> L = α·L_privacy + (1-α)·L_utility
        </p>
      </div>

      {/* Homomorphic Encryption (HE) - Restricted to Admin (per request) */}
      {apiClient.defaults.headers.common['X-User-Role'] === 'admin' && (
        <div className="glass p-6 rounded-3xl border border-white/5 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-xl text-purple-400">
              <Lock size={20} />
            </div>
            <div>
              <h4 className="text-white font-bold">Homomorphic Encryption (HE)</h4>
              <p className="text-xs text-slate-500">Manage TenSEAL / Concrete-ML Context</p>
            </div>
          </div>
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isHeActive ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className="text-xs font-mono text-slate-300">
                {isHeActive ? 'Context Active (CKKS Scheme)' : 'Context Not Initialized'}
              </span>
            </div>
            <Button size="sm" variant="ghost" className="text-xs" onClick={handleInitHE} isLoading={isHeLoading}>
              Initialize Context
            </Button>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center px-2 py-1 bg-white/5 rounded-xl border border-white/5">
        <span className="text-[10px] font-black uppercase text-slate-500">Current Sum (|w_i|):</span>
        <div className="flex items-center gap-3">
          <span className={`text-xs font-mono font-bold ${Math.abs(totalWeight - 1.0) < 0.01 ? 'text-green-500' : 'text-red-500'}`}>
            {totalWeight.toFixed(3)}
          </span>
          <Button variant="ghost" size="sm" className="h-7 text-[10px] font-black" onClick={handleNormalize}>
            Normalize
          </Button>
        </div>
      </div>

      <Button variant="primary" className="w-full py-6" onClick={handleSave} isLoading={isSaving}>
        <Save size={18} />
        Commit Weight Configuration
      </Button>
    </div>
  );
};

export default EthiMaskConfig;
