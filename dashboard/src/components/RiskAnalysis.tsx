import React, { useEffect, useState } from 'react';
import { getRiskAnalysis } from '../services/api';
import { RiskData, Filters } from '../types';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface Props {
    filters: Filters;
}

const RiskAnalysis: React.FC<Props> = ({ filters }) => {
    const [data, setData] = useState<RiskData | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await getRiskAnalysis(filters);
                setData(result);
                setError(null);
            } catch (err) {
                console.error(err);
                setError("Falha ao carregar análise de risco.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [filters]); // Updates whenever filters (date, marketplace, etc.) change

    if (loading) return <div className="p-4 text-gray-500">Calculando Risco de Mercado...</div>;
    if (error) return <div className="p-4 text-red-500">{error}</div>;
    if (!data) return null;

    // Determine Gauge Color
    const hhi = data.metrics.hhi_score;
    let gaugeColor = "#22c55e"; // Green
    if (hhi >= 1500) gaugeColor = "#eab308"; // Yellow
    if (hhi > 2500) gaugeColor = "#ef4444"; // Red

    // Needle logic (Simplified to CSS bar below)


    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                <ShieldCheck className="w-6 h-6 text-indigo-500" />
                Risco de Concentração (HHI)
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left: Score & Details */}
                <div className="flex flex-col items-center justify-center p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    {/* HHI Score Display */}
                    <div className="relative w-full h-8 bg-gray-200 rounded-full overflow-hidden mb-2">
                        <div
                            className="h-full transition-all duration-1000 ease-out"
                            style={{
                                width: `${Math.min((hhi / 6000) * 100, 100)}%`,
                                backgroundColor: gaugeColor
                            }}
                        />
                    </div>
                    <div className="flex justify-between w-full text-xs text-gray-400 mb-4">
                        <span>0 (Diversificado)</span>
                        <span>2500 (Crítico)</span>
                        <span>5000+</span>
                    </div>

                    <div className="text-center">
                        <span className="text-4xl font-black" style={{ color: gaugeColor }}>
                            {hhi}
                        </span>
                        <div className="text-sm font-medium text-gray-500 uppercase tracking-widest mt-1">
                            Score HHI
                        </div>
                        <div className={`inline-block px-3 py-1 rounded-full text-sm font-bold mt-2 text-white`} style={{ backgroundColor: gaugeColor }}>
                            Risco {data.metrics.risk_level}
                        </div>
                    </div>

                    <p className="text-sm text-gray-500 mt-4 text-center px-4">
                        {data.metrics.risk_description}
                    </p>
                </div>

                {/* Right: Distribution List */}
                <div className="flex flex-col justify-center space-y-4">
                    <h3 className="font-semibold text-gray-700 dark:text-gray-300">Share por Marketplace</h3>
                    {data.distribution.map((item, idx) => (
                        <div key={idx} className="relative">
                            <div className="flex justify-between text-sm mb-1 text-gray-600 dark:text-gray-400">
                                <span className="font-medium">{item.marketplace}</span>
                                <span>{item.share_percentage}%</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2.5 dark:bg-gray-700 overflow-hidden">
                                <div
                                    className="h-2.5 rounded-full"
                                    style={{
                                        width: `${item.share_percentage}%`,
                                        backgroundColor: idx === 0 ? gaugeColor : '#94a3b8'
                                    }}
                                ></div>
                            </div>
                            <div className="text-xs text-gray-400 mt-0.5">
                                R$ {item.revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Warning Box */}
            {data.metrics.hhi_score > 2500 && (
                <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded-r-md flex items-start gap-3">
                    <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="font-bold text-red-700 dark:text-red-400">Atenção: Alta Vulnerabilidade</h4>
                        <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                            {data.simulation.impact_description}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RiskAnalysis;
