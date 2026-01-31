import React, { useEffect, useState } from 'react';
import { Database } from 'lucide-react';
import { getDbHealth } from '../api';


interface HealthData {
    status: string;
    prometheus_healthy: boolean;
    metrics: Record<string, any>;
    alerts: string[];
}

export const Sidebar: React.FC = () => {
    const [health, setHealth] = useState<HealthData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const data = await getDbHealth();
                setHealth(data);
            } catch (err) {
                console.error('Failed to fetch health:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchHealth();
        const interval = setInterval(fetchHealth, 30000);
        return () => clearInterval(interval);
    }, []);


    return (
        <div className="w-80 border-r border-[#2f2f2f] h-screen flex flex-col bg-[#000000] p-6 overflow-y-auto custom-scrollbar">
            <div className="flex items-center gap-3 mb-10">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                    <Database className="text-blue-400 w-6 h-6" />
                </div>
                <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                    PG Debugger
                </h1>
            </div>

            <div className="space-y-6">

                <div>
                    <h2 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-4">Core Metrics</h2>
                    <div className="grid gap-3">
                        {loading ? (
                            <div className="animate-pulse space-y-3">
                                {[1, 2, 3].map(i => <div key={i} className="h-20 bg-white/5 rounded-xl" />)}
                            </div>
                        ) : health?.metrics ? (
                            Object.entries(health.metrics).map(([key, value]: [string, any]) => (
                                <div key={key} className="p-4 rounded-xl bg-white/5 border border-white/5 group hover:border-white/10 transition-colors">
                                    <div className="text-xs text-white/40 mb-1 capitalize">{key.replace(/_/g, ' ')}</div>
                                    <div className="text-lg font-semibold flex items-baseline gap-1">
                                        {typeof value === 'object' ? (value.current_values?.[0]?.value?.toFixed(2) || 'N/A') : value}
                                        <span className="text-xs text-white/40 font-normal">{value.unit || ''}</span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-sm text-white/40 italic">No metrics available</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
