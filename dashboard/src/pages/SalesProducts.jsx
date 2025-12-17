import React from 'react';
import TimeAnalysis from '../components/TimeAnalysis';
import TopProducts from '../components/TopProducts';
import PaymentChart from '../components/PaymentChart';

const SalesProducts = ({ diario, semanal, mensal, anual, topProdutos, topProductsSort, onSortChange, paymentData }) => {
    return (
        <div className="space-y-8 animate-fade-in">
            {/* Análise Temporal */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Histórico de Vendas</h3>
                <TimeAnalysis
                    diario={diario}
                    semanal={semanal}
                    mensal={mensal}
                    anual={anual}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Top Produtos */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                    <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Top Produtos</h3>
                    <TopProducts
                        data={topProdutos}
                        sortBy={topProductsSort}
                        onSortChange={onSortChange}
                    />
                </div>

                {/* Pagamentos */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                    <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Métodos de Pagamento</h3>
                    <PaymentChart data={paymentData} />
                </div>
            </div>
        </div>
    );
};

export default SalesProducts;
