import React, { useEffect, useState } from 'react';
import BundleSuggestions from '../components/BundleSuggestions';

const Opportunities = ({ bundlesData }) => {
    return (
        <div className="space-y-8 animate-fade-in">
            {/* Seção 1: Sugestão de Kits */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="mb-6">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">Oportunidades de Kits (Bundles)</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Produtos frequentemente comprados juntos. Crie anúncios combinados para aumentar o ticket médio.
                    </p>
                </div>
                <BundleSuggestions data={bundlesData} loading={!bundlesData} />
            </div>

            {/* Espaço para futuras oportunidades (Ex: Re-stock, Promoções) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 opacity-50 border-dashed">
                    <h4 className="font-bold text-gray-400 flex items-center gap-2">
                        Sugestão de Re-stock (Em Breve)
                    </h4>
                    <p className="text-sm text-gray-500 mt-2">IA analisando velocidade de vendas para sugerir reposição.</p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 opacity-50 border-dashed">
                    <h4 className="font-bold text-gray-400 flex items-center gap-2">
                        Produtos "Encalhados" (Em Breve)
                    </h4>
                    <p className="text-sm text-gray-500 mt-2">Sugestões de liquidação para liberar capital de giro.</p>
                </div>
            </div>
        </div>
    );
};

export default Opportunities;
