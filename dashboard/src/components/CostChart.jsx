import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import { useTheme } from '../context/ThemeContext';

const CostChart = ({ data }) => {
    const { theme } = useTheme();
    if (!data || data.length === 0) return null;

    const formatCurrency = (val) =>
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 transition-colors duration-200">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Análise de Custos (Frete vs Comissões)</h2>
            <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                        data={data}
                        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? "#374151" : "#e5e7eb"} />
                        <XAxis
                            dataKey="mes"
                            tick={{ fill: theme === 'dark' ? '#9CA3AF' : '#4B5563' }}
                            tickFormatter={(val) => val.substring(0, 3)}
                        />
                        <YAxis
                            tick={{ fill: theme === 'dark' ? '#9CA3AF' : '#4B5563' }}
                            tickFormatter={(val) => `R$ ${val / 1000}k`}
                        />
                        <Tooltip
                            formatter={(value) => formatCurrency(value)}
                            contentStyle={{
                                backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
                                border: theme === 'dark' ? 'none' : '1px solid #e5e7eb',
                                borderRadius: '8px',
                                color: theme === 'dark' ? '#fff' : '#111827',
                                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                            }}
                        />
                        <Legend />
                        <Area type="monotone" dataKey="frete" stackId="1" stroke="#FF8042" fill="#FF8042" name="Frete" />
                        <Area type="monotone" dataKey="comissoes" stackId="1" stroke="#FFBB28" fill="#FFBB28" name="Comissões" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default CostChart;
