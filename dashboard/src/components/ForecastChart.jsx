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

    // Se houver erro retornado pela API
    if (data[0] && data[0].error) {
        return (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 h-96 flex flex-col items-center justify-center gap-2">
                <p className="text-red-500 font-medium">Erro ao gerar previsão</p>
                <p className="text-gray-400 text-sm">{data[0].error}</p>
            </div>
        );
    }

    // PREPARAÇÃO DOS DADOS
    // Para criar um gráfico contínuo visualmente, precisamos conectar o último ponto do histórico ao primeiro da previsão.
    // Estrategia: Adicionar o valor 'val_forecast' também no último ponto de 'history'.

    let lastHistoryIndex = -1;
    data.forEach((item, index) => {
        if (item.type === 'history') lastHistoryIndex = index;
    });

    const chartData = data.map((item, index) => {
        const isHistory = item.type === 'history';
        const isForecast = item.type === 'forecast';

        // Se for o último ponto de histórico, ele serve de "âncora" para o início do tracejado vermelho
        const showAsForecastStart = (index === lastHistoryIndex && lastHistoryIndex !== -1);

        return {
            ...item,
            val_history: isHistory ? item.value : null,
            // A linha de previsão desenha se for forecast OU se for o ponto de conexão
            val_forecast: (isForecast || showAsForecastStart) ? item.value : null
        };
    });

    const formatCurrency = (val) => {
        if (val === null || val === undefined) return '';
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);
    };

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow duration-300">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        Previsão de Demanda
                        <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                            IA Beta
                        </span>
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Projeção para os próximos 6 meses baseada em tendência e sazonalidade.
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
                            <linearGradient id="colorHistory" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />

                        <XAxis
                            dataKey="date"
                            stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                            tick={{ fill: theme === 'dark' ? '#9CA3AF' : '#6B7280', fontSize: 12 }}
                            tickMargin={10}
                        />

                        <YAxis
                            tickFormatter={(val) => `R$ ${(val / 1000).toFixed(0)}k`}
                            stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                            tick={{ fill: theme === 'dark' ? '#9CA3AF' : '#6B7280', fontSize: 12 }}
                        />

                        <Tooltip
                            contentStyle={{
                                backgroundColor: theme === 'dark' ? '#1F2937' : '#fff',
                                borderColor: theme === 'dark' ? '#374151' : '#E5E7EB',
                                borderRadius: '0.5rem',
                                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                                color: theme === 'dark' ? '#F3F4F6' : '#111827'
                            }}
                            formatter={(value, name) => [
                                formatCurrency(value),
                                name === 'val_history' ? 'Histórico' : 'Previsão'
                            ]}
                            labelFormatter={(label) => `Período: ${label}`}
                        />

                        <Legend wrapperStyle={{ paddingTop: '20px' }} />

                        {/* Área para Histórico (Sólida Azul) */}
                        <Area
                            type="monotone"
                            dataKey="val_history"
                            name="Histórico"
                            stroke="#2563eb"
                            fill="url(#colorHistory)"
                            strokeWidth={3}
                            connectNulls={true}
                            activeDot={{ r: 6, strokeWidth: 0 }}
                        />

                        {/* Linha para Previsão (Tracejada Vermelha) */}
                        <Line
                            type="monotone"
                            dataKey="val_forecast"
                            name="Previsão"
                            stroke="#dc2626"
                            strokeDasharray="5 5"
                            strokeWidth={3}
                            dot={{ r: 4, fill: '#dc2626', strokeWidth: 2, stroke: '#fff' }}
                            connectNulls={true}
                            animationDuration={1500}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default ForecastChart;
