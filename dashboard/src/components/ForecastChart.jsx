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

const ForecastChart = ({ data, filters }) => {
    const { theme } = useTheme();

    if (!data || data.length === 0) {
        return (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 h-96 flex items-center justify-center">
                <p className="text-gray-400">Sem dados para previsão</p>
            </div>
        );
    }

    if (data[0] && data[0].error) {
        return (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 h-96 flex flex-col items-center justify-center gap-2">
                <p className="text-red-500 font-medium">Erro ao gerar previsão</p>
                <p className="text-gray-400 text-sm">{data[0].error}</p>
            </div>
        );
    }

    // --- PROCESSAMENTO DE DADOS ---
    // 1. Identificar o índice de transição
    let lastHistoryIndex = -1;
    data.forEach((item, index) => {
        if (item.type === 'history') lastHistoryIndex = index;
    });

    // 2. Mapear dados para o Recharts
    const chartData = data.map((item, index) => {
        const isHistory = item.type === 'history';
        const isTransition = index === lastHistoryIndex;

        // Histórico puro
        let val_history = isHistory ? item.revenue_real : null;

        // Previsão (Ancorada no último histórico)
        let val_forecast = null;
        if (item.type === 'forecast') {
            val_forecast = item.revenue_forecast;
        } else if (isTransition) {
            val_forecast = item.revenue_real;
        }

        // Faixa de Incerteza [min, max]
        let range = null;
        if (item.type === 'forecast') {
            range = [item.revenue_lower, item.revenue_upper];
        } else if (isTransition) {
            // No ponto zero, a incerteza é zero (ou mínima)
            range = [item.revenue_real, item.revenue_real];
        }

        return {
            date: item.date,
            val_history,
            val_forecast,
            range,
            _original: item
        };
    });

    const formatCurrency = (val) => {
        if (val === null || val === undefined) return '';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);
    };

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const point = payload[0].payload;
            const isForecast = point.range !== null;
            const value = isForecast ? point.val_forecast : point.val_history;
            const originalDate = new Date(point.date).toLocaleDateString('pt-BR');

            return (
                <div className={`p-4 border rounded-xl shadow-xl backdrop-blur-sm ${theme === 'dark' ? 'bg-gray-800/90 border-gray-700 text-gray-200' : 'bg-white/90 border-gray-200 text-gray-800'}`}>
                    <p className="font-bold mb-3 text-sm border-b pb-2 border-gray-100 dark:border-gray-700">{originalDate}</p>

                    {isForecast ? (
                        <>
                            <div className="mb-2">
                                <p className="text-xs text-gray-500 dark:text-gray-400">Projeção Central</p>
                                <p className="text-lg font-bold text-green-600 dark:text-green-400">{formatCurrency(value)}</p>
                            </div>
                            <div className="flex gap-4 text-xs bg-gray-50 dark:bg-gray-900/50 p-2 rounded-lg">
                                <div>
                                    <p className="text-gray-400">Pessimista (Mín)</p>
                                    <p className="font-semibold text-gray-700 dark:text-gray-300">{formatCurrency(point.range[0])}</p>
                                </div>
                                <div className="border-l pl-4 border-gray-200 dark:border-gray-700">
                                    <p className="text-gray-400">Otimista (Máx)</p>
                                    <p className="font-semibold text-gray-700 dark:text-gray-300">{formatCurrency(point.range[1])}</p>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Faturamento Real</p>
                            <p className="text-lg font-bold text-green-700 dark:text-green-500">{formatCurrency(value)}</p>
                        </div>
                    )}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow duration-300">
            <div className="mb-6 flex justify-between items-end">
                <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        Projeção de Fluxo de Receita
                        <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 border border-green-200 dark:border-green-800">
                            12 Semanas
                        </span>
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Previsão estatística de receita com margem de segurança.
                    </p>
                </div>
            </div>

            <div className="h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={chartData}
                        margin={{ top: 20, right: 30, left: 10, bottom: 10 }}
                    >
                        <defs>
                            <linearGradient id="colorRange" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10B981" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#10B981" stopOpacity={0.05} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />

                        <XAxis
                            dataKey="date"
                            stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                            tick={{ fontSize: 11 }}
                            tickFormatter={(val) => {
                                const d = new Date(val);
                                return `${d.getDate()}/${d.getMonth() + 1}`;
                            }}
                            minTickGap={30}
                        />

                        <YAxis
                            tickFormatter={(val) => `R$ ${(val / 1000).toFixed(0)}k`}
                            stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                            tick={{ fontSize: 11 }}
                        />

                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ paddingTop: '10px' }} />

                        {/* Área de Incerteza */}
                        <Area
                            type="monotone"
                            dataKey="range"
                            name="Margem de Erro"
                            stroke="none"
                            fill="url(#colorRange)"
                            connectNulls={true}
                        />

                        {/* Histórico - Verde Forte Sólido */}
                        <Line
                            type="monotone"
                            dataKey="val_history"
                            name="Realizado"
                            stroke="#059669" // emerald-600
                            strokeWidth={3}
                            dot={{ r: 3, fill: '#059669' }}
                            activeDot={{ r: 6 }}
                        />

                        {/* Previsão - Verde Médio Pontilhado */}
                        <Line
                            type="monotone"
                            dataKey="val_forecast"
                            name="Projeção"
                            stroke="#10B981" // emerald-500
                            strokeWidth={3}
                            strokeDasharray="5 5"
                            dot={{ r: 3, fill: '#10B981', strokeWidth: 2, stroke: '#fff' }}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default ForecastChart;
