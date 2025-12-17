import React from 'react';
import { ArrowRight, ShoppingBag, TrendingUp, AlertCircle } from 'lucide-react';

const BundleSuggestions = ({ data, loading }) => {
    if (loading) {
        return (
            <div className="flex justify-center p-12">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="text-center p-8 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                <ShoppingBag className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400">Nenhuma oportunidade de Kit encontrada com os critérios atuais.</p>
                <p className="text-xs text-gray-400 mt-1">Tente ajustar o Lift ou precisamos de mais histórico de vendas conjuntas.</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.map((rule, idx) => (
                <div key={idx} className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow relative overflow-hidden group">
                    {/* Badge de Força */}
                    <div className={`absolute top-0 right-0 px-3 py-1 text-xs font-bold rounded-bl-xl ${rule.lift > 2 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' :
                            'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                        }`}>
                        Lift: {rule.lift}x
                    </div>

                    <div className="mt-2">
                        {/* Antecedents */}
                        <div className="mb-3">
                            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold mb-1">Se o cliente compra:</p>
                            {rule.antecedents.map((item, i) => (
                                <div key={i} className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-700/50 p-2 rounded-lg mb-1">
                                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                    <span className="truncate">{item}</span>
                                </div>
                            ))}
                        </div>

                        {/* Arrow */}
                        <div className="flex justify-center -my-2 relative z-10">
                            <div className="bg-white dark:bg-gray-800 p-1 rounded-full border border-gray-100 dark:border-gray-700">
                                <ArrowRight className="w-5 h-5 text-gray-400" />
                            </div>
                        </div>

                        {/* Consequents */}
                        <div className="mb-4 mt-1">
                            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold mb-1">Ofereça também:</p>
                            {rule.consequents.map((item, i) => (
                                <div key={i} className="flex items-center gap-2 text-sm font-bold text-gray-900 dark:text-white bg-green-50 dark:bg-green-900/10 border border-green-100 dark:border-green-900/30 p-2 rounded-lg mb-1">
                                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                                    <span className="truncate">{item}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-700">
                        <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400" title="Probabilidade de venda conjunta">
                            <TrendingUp className="w-3 h-3" />
                            <span>Confiança: <strong>{(rule.confidence * 100).toFixed(0)}%</strong></span>
                        </div>
                        <button className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline">
                            Criar Kit Agora
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default BundleSuggestions;
