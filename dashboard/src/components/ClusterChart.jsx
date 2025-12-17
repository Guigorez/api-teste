import React from 'react';
import {
    ScatterChart,
    Scatter,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Legend,
    Cell
} from 'recharts';
import { useTheme } from '../context/ThemeContext';

const ClusterChart = ({ data }) => {
    const { theme } = useTheme();

    if (!data || !data.data || data.data.length === 0) {
        return (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 h-96 flex items-center justify-center">
                <p className="text-gray-400">Sem dados para clusterização</p>
            </div>
        );
    }

    const { data: points, averages } = data;

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className={`p-3 rounded shadow border text-sm ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'
                    }`}>
                    <p className="font-bold mb-1">{data.product}</p>
                    <p>Cluster: <span style={{ color: data.color, fontWeight: 'bold' }}>{data.cluster}</span></p>
                    <p>Faturamento: {formatCurrency(data.revenue)}</p>
                    <p>Lucro: {formatCurrency(data.profit)}</p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="mb-6 flex justify-between items-start">
                <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">Matriz de Produtos (Curva ABC 2.0)</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Segmentação baseada em Lucro (X) vs Faturamento (Y).
                    </p>
                </div>
            </div>

            <div className="h-[500px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />

                        <XAxis
                            type="number"
                            dataKey="profit"
                            name="Lucro"
                            tickFormatter={(val) => `R$${(val / 1000).toFixed(0)}k`}
                            stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                            label={{ value: 'Lucro Líquido', position: 'insideBottom', offset: -10, fill: theme === 'dark' ? '#9CA3AF' : '#6B7280' }}
                        />
                        <YAxis
                            type="number"
                            dataKey="revenue"
                            name="Faturamento"
                            tickFormatter={(val) => `R$${(val / 1000).toFixed(0)}k`}
                            stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                            label={{ value: 'Faturamento', angle: -90, position: 'insideLeft', fill: theme === 'dark' ? '#9CA3AF' : '#6B7280' }}
                        />

                        <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />

                        {/* Linhas de Referência (Médias) */}
                        <ReferenceLine x={averages.profit} stroke="red" strokeDasharray="3 3" label={{ value: 'Média Lucro', fill: 'red', fontSize: 10 }} />
                        <ReferenceLine y={averages.revenue} stroke="red" strokeDasharray="3 3" label={{ value: 'Média Fat.', fill: 'red', fontSize: 10 }} />

                        <Scatter name="Produtos" data={points} fill="#8884d8">
                            {points.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Scatter>
                    </ScatterChart>
                </ResponsiveContainer>
            </div>

            <div className="mt-4 flex flex-wrap gap-4 text-xs justify-center">
                <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#10B981]"></span> Campeões (Alto Fat/Alto Lucro)</div>
                <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#3B82F6]"></span> Volumosos (Alto Fat/Baixo Lucro)</div>
                <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#F59E0B]"></span> Oportunidades (Baixo Fat/Alto Lucro)</div>
                <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#9CA3AF]"></span> Abaixo da Média</div>
            </div>
        </div>
    );
};

export default ClusterChart;
