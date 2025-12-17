import React from 'react';
import {
    ComposedChart,
    Line,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import { useTheme } from '../context/ThemeContext';

const ForecastChart = ({ data }) => {
    const { theme } = useTheme();

    if (!data || data.length === 0) {
        return (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 h-96 flex items-center justify-center">
                <p className="text-gray-400">Sem dados para previsão</p>
            </div>
        );
    }

    // Prepara dados para garantir continuidade visual
    // O último ponto histórico deve ser também o primeiro da previsão para a linha não quebrar
    // Porém, a API retorna lista plana. O Recharts lida bem se tiverem datas compartilhadas ou se for contínuo.
    // Vamos assumir que a API retorna lista ordenada.

    const formattedData = data.map(item => ({
        ...item,
        // Separa valores para linhas diferentes cores
        val_history: item.type === 'history' ? item.value : null,
        val_forecast: item.type === 'forecast' ? item.value : null,
        // Truque: para o ponto de transição, podemos precisar que ele tenha ambos ou que a previsão comece onde o historico termina.
    }));

    const formatCurrency = (val) => {
        if (val === null || val === undefined) return '';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);
    };

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="mb-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Previsão de Demanda (6 Meses)</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                    Projeção baseada em tendência linear e sazonalidade histórica.
                </p>
            </div>

            <div className="h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={formattedData}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                        <XAxis
                            dataKey="date"
                            stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                            tick={{ fill: theme === 'dark' ? '#9CA3AF' : '#6B7280' }}
                            tickMargin={10}
                        />
                        <YAxis
                            tickFormatter={(val) => `R$ ${(val / 1000).toFixed(0)}k`}
                            stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                            tick={{ fill: theme === 'dark' ? '#9CA3AF' : '#6B7280' }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: theme === 'dark' ? '#1F2937' : '#fff',
                                borderColor: theme === 'dark' ? '#374151' : '#E5E7EB',
                                color: theme === 'dark' ? '#fff' : '#000'
                            }}
                            formatter={(value, name) => [formatCurrency(value), name === 'val_history' ? 'Histórico' : 'Previsão']}
                            labelFormatter={(label) => `Mês: ${label}`}
                        />
                        <Legend />

                        {/* Linha Histórica (Sólida) */}
                        <Area
                            type="monotone"
                            dataKey="val_history"
                            name="Histórico"
                            stroke="#2563eb"
                            fill="url(#colorHistory)"
                            strokeWidth={3}
                            connectNulls={true}
                        />
                        <defs>
                            <linearGradient id="colorHistory" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1} />
                                <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                            </linearGradient>
                        </defs>

                        {/* Linha de Previsão (Tracejada) */}
                        <Line
                            type="monotone"
                            dataKey="val_forecast"
                            name="Previsão"
                            stroke="#dc2626"
                            strokeDasharray="5 5"
                            strokeWidth={3}
                            dot={{ r: 4, fill: '#dc2626' }}
                            connectNulls={true}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default ForecastChart;
