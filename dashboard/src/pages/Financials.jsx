import React from 'react';
import CostChart from '../components/CostChart';
import ForecastChart from '../components/ForecastChart';

const Financials = ({ mensal, forecastData, filters, granularity, onGranularityChange }) => {
    return (
        <div className="space-y-8 animate-fade-in">
            {/* Projeção de Fluxo de Caixa (Topo) */}
            <div className="bg-gradient-to-br from-indigo-50 to-white dark:from-gray-800 dark:to-gray-900 rounded-2xl p-1 shadow-sm border border-indigo-100 dark:border-gray-700">
                <ForecastChart
                    data={forecastData}
                    filters={filters}
                    granularity={granularity}
                    onGranularityChange={onGranularityChange}
                />
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Análise de Custos & Lucratividade</h3>
                <p className="text-sm text-gray-500 mb-6">Detalhamento mensal de Receita vs Custos (Produtos + Taxas + Impostos).</p>
                <CostChart data={mensal} />
            </div>

            {/* Espaço para futuras tabelas financeiras ou DRE */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 opacity-50">
                    <h4 className="font-bold text-gray-400">Margem Média</h4>
                    <p className="text-2xl font-bold text-gray-300">Em breve</p>
                </div>
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 opacity-50">
                    <h4 className="font-bold text-gray-400">Custo Fixo</h4>
                    <p className="text-2xl font-bold text-gray-300">Em breve</p>
                </div>
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 opacity-50">
                    <h4 className="font-bold text-gray-400">ROI Marketing</h4>
                    <p className="text-2xl font-bold text-gray-300">Em breve</p>
                </div>
            </div>
        </div>
    );
};

export default Financials;
