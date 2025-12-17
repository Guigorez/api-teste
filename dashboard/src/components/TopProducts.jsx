import React from 'react';

const TopProducts = ({ data, sortBy, onSortChange }) => {
    if (!data || data.length === 0) return null;

    const formatCurrency = (val) =>
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 transition-colors duration-200">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Top Produtos</h2>

                <div className="flex bg-gray-200 dark:bg-gray-700 rounded-lg p-1 transition-colors">
                    <button
                        onClick={() => onSortChange('faturamento')}
                        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${sortBy === 'faturamento'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                            }`}
                    >
                        Faturamento
                    </button>
                    <button
                        onClick={() => onSortChange('quantidade')}
                        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${sortBy === 'quantidade'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                            }`}
                    >
                        Quantidade
                    </button>
                </div>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                            <th className="pb-3 font-medium">Produto</th>
                            <th className="pb-3 font-medium text-right">Pedidos</th>
                            <th className="pb-3 font-medium text-right">Faturamento</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {data.map((item, index) => (
                            <tr key={index} className="group hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                <td className="py-4 pr-4 text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white truncate max-w-xs">
                                    {item.produto}
                                </td>
                                <td className="py-4 text-right text-gray-700 dark:text-gray-300">
                                    {item.contagem_pedidos}
                                </td>
                                <td className="py-4 text-right font-medium text-green-600 dark:text-green-400">
                                    {formatCurrency(item.faturamento)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TopProducts;
