import React, { useEffect, useState } from 'react';
import MarketplaceChart from './components/MarketplaceChart';
import PaymentChart from './components/PaymentChart';
import CostChart from './components/CostChart';
import { getResumo, getMensal, getDiario, getSemanal, getAnual, getTopProdutos, processData, getGeoSales, getMarketplace, getPagamentos } from './services/api';
import SummaryCards from './components/SummaryCards';
import TimeAnalysis from './components/TimeAnalysis';
import TopProducts from './components/TopProducts';
import DateFilter from './components/DateFilter';
import SalesMap from './components/SalesMap';
import Sidebar from './components/Sidebar';
import ThemeToggle from './components/ThemeToggle';
import { RefreshCw, Search, Bell, Plus } from 'lucide-react';

function App() {
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [company, setCompany] = useState('animoshop'); // 'animoshop' or 'novoon'
  const [resumo, setResumo] = useState(null);
  const [mensal, setMensal] = useState([]);
  const [diario, setDiario] = useState([]);
  const [semanal, setSemanal] = useState([]);
  const [anual, setAnual] = useState([]);
  const [topProdutos, setTopProdutos] = useState([]);
  const [geoData, setGeoData] = useState([]);
  const [marketplaceData, setMarketplaceData] = useState([]);
  const [paymentData, setPaymentData] = useState([]);
  const [topProductsSort, setTopProductsSort] = useState('faturamento');
  const [processing, setProcessing] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Include company in filters
      const currentFilters = { ...filters, company };

      const [resumoData, mensalData, diarioData, semanalData, anualData, topData, geoDataRes, marketplaceRes, paymentRes] = await Promise.all([
        getResumo(currentFilters),
        getMensal(currentFilters),
        getDiario(currentFilters),
        getSemanal(currentFilters),
        getAnual(currentFilters),
        getTopProdutos(10, currentFilters, topProductsSort),
        getGeoSales(currentFilters),
        getMarketplace(currentFilters),
        getPagamentos(currentFilters)
      ]);

      setResumo(resumoData);
      setMensal(mensalData);
      setDiario(diarioData);
      setSemanal(semanalData);
      setAnual(anualData);
      setTopProdutos(topData);
      setGeoData(geoDataRes);
      setMarketplaceData(marketplaceRes);
      setPaymentData(paymentRes);
    } catch (error) {
      console.error("Erro ao buscar dados:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filters, topProductsSort, company]);

  const handleUpdate = async () => {
    if (confirm(`Deseja reprocessar todas as planilhas da ${company.toUpperCase()}? Isso pode levar alguns segundos.`)) {
      setProcessing(true);
      try {
        await processData(company);
        alert(`Processamento da ${company.toUpperCase()} iniciado! Os dados serão atualizados em breve.`);
        // Aguarda um pouco e recarrega os dados
        setTimeout(() => {
          fetchData();
          setProcessing(false);
        }, 5000);
      } catch (error) {
        alert("Erro ao iniciar processamento.");
        setProcessing(false);
      }
    }
  };

  const handleFilter = (newFilters) => {
    setFilters(newFilters);
  };

  if (loading && !resumo) {
    return (
      <div className="min-h-screen bg-[#F4F5F7] dark:bg-gray-900 flex items-center justify-center transition-colors duration-200">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#FF6B00]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4F5F7] dark:bg-gray-900 text-gray-900 dark:text-white transition-colors duration-200 font-sans">
      <Sidebar />

      <main className="lg:ml-64 p-8 transition-all duration-300">
        {/* Header Section */}
        <header className="flex flex-col md:flex-row items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Quadro Geral</h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Search Bar - Visual Only */}
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

            {/* Company & Theme Toggle - Moved here for compact layout */}
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
                disabled={processing}
                className={`p-2 rounded-full shadow-sm border border-gray-200 dark:border-gray-700 transition-colors ${processing
                  ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-white dark:bg-gray-800 hover:text-green-600'
                  }`}
                title="Atualizar Dados"
              >
                <RefreshCw className={`w-5 h-5 ${processing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </header>

        {/* Filters */}
        <div className="mb-8">
          <DateFilter onFilter={handleFilter} />
        </div>

        {/* Dashboard Content */}
        <SummaryCards data={resumo} />

        {/* Row 1: Time Analysis & Marketplace */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Histórico de Faturamento</h3>
            <TimeAnalysis
              diario={diario}
              semanal={semanal}
              mensal={mensal}
              anual={anual}
            />
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Composição</h3>
            <MarketplaceChart data={marketplaceData} />
          </div>
        </div>

        {/* Full Width Sections */}
        <div className="space-y-8">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Análise de Custos</h3>
            <CostChart data={mensal} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Mapa de Vendas</h3>
              <SalesMap data={geoData} />
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Top Produtos</h3>
              <TopProducts
                data={topProdutos}
                sortBy={topProductsSort}
                onSortChange={setTopProductsSort}
              />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-white">Pagamentos</h3>
            <PaymentChart data={paymentData} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
