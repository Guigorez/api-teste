import React from 'react';
import SummaryCards from '../components/SummaryCards';
import MarketplaceChart from '../components/MarketplaceChart';
import SalesMap from '../components/SalesMap';

const Overview = ({ resumo, marketplaceData, geoData }) => {
    return (
        <div className="space-y-8 animate-fade-in">
            {/* Cards de Resumo */}
            <SummaryCards data={resumo} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Gráfico de Marketplaces */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                    <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Composição por Marketplace</h3>
                    <MarketplaceChart data={marketplaceData} />
                </div>

                {/* Mapa de Vendas */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                    <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Mapa de Vendas</h3>
                    <SalesMap data={geoData} />
                </div>
            </div>
        </div>
    );
};

export default Overview;
