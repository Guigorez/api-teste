import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import { useTheme } from '../context/ThemeContext';

const PaymentChart = ({ data }) => {
    const { theme } = useTheme();
    if (!data || data.length === 0) return null;

    const formatCurrency = (val) =>
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 transition-colors duration-200">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Métodos de Pagamento</h2>
            <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={data}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? "#374151" : "#e5e7eb"} />
                        <XAxis type="number" hide />
                        <YAxis
                            dataKey="metodo"
                            type="category"
                            width={100}
                            tick={{ fill: theme === 'dark' ? '#9CA3AF' : '#4B5563' }}
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
                            cursor={{ fill: theme === 'dark' ? '#374151' : '#f3f4f6', opacity: 0.4 }}
                        />
                        <Bar dataKey="faturamento" fill="#FF6B00" name="Faturamento" radius={[0, 4, 4, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default PaymentChart;
