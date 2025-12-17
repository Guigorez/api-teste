import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

import { useTheme } from '../context/ThemeContext';

const SalesChart = ({ data, title, xKey = "mes" }) => {
    const { theme } = useTheme();
    if (!data || data.length === 0) return null;

    return (
        <div className="bg-white dark:bg-gray-800 p-0 rounded-xl transition-colors duration-200">
            {/* Title handled by parent container now for layout consistency, but keeping fallback */}
            {/* <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">{title}</h2> */}
            <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorFaturamento" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#FF6B00" stopOpacity={0.1} />
                                <stop offset="95%" stopColor="#FF6B00" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'dark' ? "#374151" : "#F3F4F6"} />
                        <XAxis
                            dataKey={xKey}
                            stroke={theme === 'dark' ? "#9CA3AF" : "#9CA3AF"}
                            tickLine={false}
                            axisLine={false}
                            dy={10}
                        />
                        <YAxis
                            stroke={theme === 'dark' ? "#9CA3AF" : "#9CA3AF"}
                            tickLine={false}
                            axisLine={false}
                            dx={-10}
                            tickFormatter={(value) => `R$ ${value / 1000}k`}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: theme === 'dark' ? '#1F2937' : '#ffffff',
                                border: 'none',
                                borderRadius: '12px',
                                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
                            }}
                            itemStyle={{ color: theme === 'dark' ? '#E5E7EB' : '#111827' }}
                        />
                        <Legend iconType="circle" />
                        <Line
                            type="monotone"
                            dataKey="faturamento"
                            name="Faturamento"
                            stroke="#FF6B00"
                            strokeWidth={4}
                            dot={false}
                            activeDot={{ r: 8, strokeWidth: 0 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="lucro_liquido"
                            name="Lucro Bruto"
                            stroke="#10B981" // Green for Profit
                            strokeWidth={4}
                            dot={false}
                            activeDot={{ r: 8, strokeWidth: 0 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default SalesChart;

