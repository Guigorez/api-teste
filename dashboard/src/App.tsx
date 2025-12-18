import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    getResumo, getMensal, getDiario, getSemanal, getAnual,
    getTopProdutos, processData, getGeoSales, getMarketplace,
    getPagamentos, getForecast, getClustering, getBundles
} from './services/api';
import Sidebar from './components/Sidebar';
import ThemeToggle from './components/ThemeToggle';
import DateFilter from './components/DateFilter';
import { RefreshCw, Search, Bell, Plus } from 'lucide-react';

// Paginas (Assuming they are still .jsx, TS allows importing .jsx if allowed in config)
// I will eventually migrate them too.
// Paginas (Assuming they are still .jsx, TS allows importing .jsx if allowed in config)
// I will eventually migrate them too.
import Overview from './pages/Overview';
import SalesProducts from './pages/SalesProducts';
import Financials from './pages/Financials';
import Intelligence from './pages/Intelligence';
import Opportunities from './pages/Opportunities';
import { Filters } from './types';

console.log("App Module Loaded");

function App() {
    const queryClient = useQueryClient();
    const [filters, setFilters] = useState<Filters>({});
    const [company, setCompany] = useState<'animoshop' | 'novoon'>('animoshop');

    // Navigation State
    const [activeTab, setActiveTab] = useState('overview');
    const [topProductsSort, setTopProductsSort] = useState<'faturamento' | 'quantidade'>('faturamento');

    // Merged Filters for Queries
    const queryFilters: Filters = { ...filters, company };

    // --- QUERIES ---

    // 1. Visão Geral
    const { data: resumo, isLoading: loadingResumo, isError: errorResumo } = useQuery({
        queryKey: ['resumo', queryFilters],
        queryFn: () => getResumo(queryFilters),
        staleTime: 1000 * 60 * 5,
    });

    const { data: marketplaceData } = useQuery({
        queryKey: ['marketplace', queryFilters],
        queryFn: () => getMarketplace(queryFilters),
    });

    const { data: geoData } = useQuery({
        queryKey: ['geo', queryFilters],
        queryFn: () => getGeoSales(queryFilters),
    });

    // 2. Vendas & Produtos
    const { data: diario } = useQuery({ queryKey: ['diario', queryFilters], queryFn: () => getDiario(queryFilters) });
    const { data: semanal } = useQuery({ queryKey: ['semanal', queryFilters], queryFn: () => getSemanal(queryFilters) });
    const { data: mensal } = useQuery({ queryKey: ['mensal', queryFilters], queryFn: () => getMensal(queryFilters) });
    const { data: anual } = useQuery({ queryKey: ['anual', queryFilters], queryFn: () => getAnual(queryFilters) });
    const { data: paymentData } = useQuery({ queryKey: ['pagamentos', queryFilters], queryFn: () => getPagamentos(queryFilters) });

    const { data: topProdutos } = useQuery({
        queryKey: ['topProdutos', queryFilters, topProductsSort],
        queryFn: () => getTopProdutos(10, queryFilters, topProductsSort),
    });

    // 3. Inteligência
    const { data: forecastData } = useQuery({ queryKey: ['forecast', queryFilters], queryFn: () => getForecast(queryFilters) });
    const { data: clusteringData } = useQuery({ queryKey: ['clustering', queryFilters], queryFn: () => getClustering(queryFilters) });
    const { data: bundlesData } = useQuery({ queryKey: ['bundles', queryFilters], queryFn: () => getBundles(queryFilters) });


    // --- MUTATION (Processamento) ---
    const processMutation = useMutation({
        mutationFn: (comp: 'animoshop' | 'novoon') => processData(comp),
        onSuccess: () => {
            alert(`Processamento da ${company.toUpperCase()} finalizado!`);
            queryClient.invalidateQueries();
        },
        onError: () => {
            alert("Erro ao processar dados.");
        }
    });

    const handleUpdate = () => {
        if (confirm(`Deseja reprocessar todas as planilhas da ${company.toUpperCase()}? Isso pode levar alguns segundos.`)) {
            processMutation.mutate(company);
        }
    };

    const handleFilter = (newFilters: any) => {
        if (JSON.stringify(newFilters) !== JSON.stringify(filters)) {
            setFilters(newFilters);
        }
    };


    // Debug Logs
    console.log("App Render State:", { loadingResumo, errorResumo, filters });

    // Renderiza o conteúdo base na aba ativa
    const renderContent = () => {
        if (loadingResumo) {
            return (
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#FF6B00]"></div>
                    <span className="ml-4 text-gray-500">Carregando dados...</span>
                </div>
            );
        }

        if (errorResumo) {
            return (
                <div className="flex flex-col items-center justify-center h-64 text-red-500">
                    <h2 className="text-xl font-bold mb-2">Erro de Conexão</h2>
                    <p>Não foi possível conectar à API.</p>
                </div>
            )
        }

        switch (activeTab) {
            case 'overview':
                return <Overview resumo={resumo} marketplaceData={marketplaceData || []} geoData={geoData || []} />;
            case 'sales':
                return (
                    <SalesProducts
                        diario={diario || []}
                        semanal={semanal || []}
                        mensal={mensal || []}
                        anual={anual || []}
                        topProdutos={topProdutos || []}
                        topProductsSort={topProductsSort}
                        onSortChange={setTopProductsSort}
                        paymentData={paymentData || []}
                    />
                );
            case 'financials':
                return <Financials mensal={mensal || []} forecastData={forecastData || []} filters={queryFilters} />;
            case 'intelligence':
                return <Intelligence forecastData={forecastData || []} clusteringData={clusteringData} filters={queryFilters} />;
            case 'opportunities':
                return <Opportunities bundlesData={bundlesData || []} />;
            default:
                return <Overview resumo={resumo} marketplaceData={marketplaceData} geoData={geoData} />;
        }
    };

    return (
        <div className="min-h-screen bg-[#F4F5F7] dark:bg-gray-900 text-gray-900 dark:text-white transition-colors duration-200 font-sans">
            <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

            <main className="lg:ml-64 p-8 transition-all duration-300">
                {/* Header Section */}
                <header className="flex flex-col md:flex-row items-center justify-between mb-8 gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-white">
                            {activeTab === 'overview' && 'Visão Geral'}
                            {activeTab === 'sales' && 'Vendas & Produtos'}
                            {activeTab === 'financials' && 'Financeiro'}
                            {activeTab === 'intelligence' && 'Inteligência'}
                            {activeTab === 'opportunities' && 'Oportunidades'}
                        </h1>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden md:flex items-center bg-white dark:bg-gray-800 rounded-full px-4 py-2 shadow-sm border border-gray-200 dark:border-gray-700">
                            <Search className="w-5 h-5 text-gray-400" />
                            <input type="text" placeholder="Buscar..." className="ml-2 bg-transparent outline-none text-sm w-32 lg:w-48" />
                        </div>

                        <button className="p-2 rounded-full bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                            <Bell className="w-5 h-5" />
                        </button>

                        <button className="flex items-center gap-2 bg-[#FF6B00] hover:bg-[#e65a00] text-white px-4 py-2 rounded-full text-sm font-medium shadow-md transition-colors">
                            <Plus className="w-4 h-4" />
                            <span>Adicionar OS</span>
                        </button>

                        <div className="flex items-center gap-2 ml-4 pl-4 border-l border-gray-300 dark:border-gray-700">
                            <div className="flex bg-white dark:bg-gray-800 rounded-lg p-1 shadow-sm border border-gray-200 dark:border-gray-700">
                                <button
                                    onClick={() => setCompany('animoshop')}
                                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${company === 'animoshop'
                                        ? 'bg-blue-600 text-white shadow-sm'
                                        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                                        }`}
                                >
                                    Animo
                                </button>
                                <button
                                    onClick={() => setCompany('novoon')}
                                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${company === 'novoon'
                                        ? 'bg-blue-600 text-white shadow-sm'
                                        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                                        }`}
                                >
                                    Novoon
                                </button>
                            </div>

                            <ThemeToggle />

                            <button
                                onClick={handleUpdate}
                                disabled={processMutation.isPending}
                                className={`p-2 rounded-full shadow-sm border border-gray-200 dark:border-gray-700 transition-colors ${processMutation.isPending
                                    ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                                    : 'bg-white dark:bg-gray-800 hover:text-green-600'
                                    }`}
                                title="Atualizar Dados"
                            >
                                <RefreshCw className={`w-5 h-5 ${processMutation.isPending ? 'animate-spin' : ''}`} />
                            </button>
                        </div>
                    </div>
                </header>

                <div className="mb-8">
                    <DateFilter onFilter={handleFilter} />
                </div>

                {renderContent()}
            </main>
        </div>
    );
}

export default App;
