import React, { useState, useEffect } from 'react';
import { Calendar, Filter, X } from 'lucide-react';

const DateFilter = ({ onFilter }) => {
    const [month, setMonth] = useState('');
    const [year, setYear] = useState(''); // Default to '' (Todos)
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [source, setSource] = useState('limpas'); // Default to 'limpas'
    const [marketplace, setMarketplace] = useState('');

    const months = [
        { value: '01', label: 'Janeiro' },
        { value: '02', label: 'Fevereiro' },
        { value: '03', label: 'Março' },
        { value: '04', label: 'Abril' },
        { value: '05', label: 'Maio' },
        { value: '06', label: 'Junho' },
        { value: '07', label: 'Julho' },
        { value: '08', label: 'Agosto' },
        { value: '09', label: 'Setembro' },
        { value: '10', label: 'Outubro' },
        { value: '11', label: 'Novembro' },
        { value: '12', label: 'Dezembro' },
    ];

    const marketplaces = [
        'Amazon', 'Shopee', 'Mercado Livre', 'Magalu', 'Madeira', 'Olist'
    ];

    const years = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i);

    // Atualiza datas quando mês/ano muda
    useEffect(() => {
        if (year) {
            if (month) {
                const firstDay = `${year}-${month}-01`;
                const lastDay = new Date(year, parseInt(month), 0).toISOString().split('T')[0];
                setStartDate(firstDay);
                setEndDate(lastDay);
            } else {
                // Se apenas o ano for selecionado, pega o ano todo
                setStartDate(`${year}-01-01`);
                setEndDate(`${year}-12-31`);
            }
        } else {
            // Se ano for "Todos", limpa as datas
            setStartDate('');
            setEndDate('');
        }
    }, [month, year]);

    // Initial load with default source
    useEffect(() => {
        onFilter({ startDate, endDate, source, marketplace });
    }, []);

    const handleApply = () => {
        onFilter({ startDate, endDate, source, marketplace });
    };

    const handleClear = () => {
        setMonth('');
        setYear('');
        setStartDate('');
        setEndDate('');
        setSource('limpas');
        setMarketplace('');
        onFilter({ startDate: null, endDate: null, source: 'limpas', marketplace: null });
    };

    return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700 mb-8 flex flex-wrap items-end gap-4 transition-colors duration-200">
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-1">
                <Filter className="w-4 h-4" />
                <span className="text-sm font-medium">Filtros</span>
            </div>

            {/* Fonte de Dados */}
            <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500 dark:text-gray-400">Fonte</label>
                <select
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    className="bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-lg p-2.5 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                    <option value="limpas">Planilhas Limpas</option>
                    <option value="atom">Planilhas Atom</option>
                </select>
            </div>

            {/* Marketplace */}
            <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500 dark:text-gray-400">Marketplace</label>
                <select
                    value={marketplace}
                    onChange={(e) => setMarketplace(e.target.value)}
                    className="bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-lg p-2.5 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                    <option value="">Todos</option>
                    {marketplaces.map(m => (
                        <option key={m} value={m}>{m}</option>
                    ))}
                </select>
            </div>

            {/* Seleção Rápida de Mês */}
            <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500 dark:text-gray-400">Mês</label>
                <select
                    value={month}
                    onChange={(e) => setMonth(e.target.value)}
                    className="bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-lg p-2.5 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                    <option value="">Todos</option>
                    {months.map(m => (
                        <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                </select>
            </div>

            <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500 dark:text-gray-400">Ano</label>
                <select
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                    className="bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-lg p-2.5 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                    <option value="">Todos</option>
                    {years.map(y => (
                        <option key={y} value={y}>{y}</option>
                    ))}
                </select>
            </div>

            {/* Intervalo Personalizado */}
            <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500 dark:text-gray-400">Data Início</label>
                <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-lg p-2.5 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                />
            </div>

            <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500 dark:text-gray-400">Data Fim</label>
                <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-lg p-2.5 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                />
            </div>

            {/* Botões de Ação */}
            <div className="flex gap-2 ml-auto">
                <button
                    onClick={handleClear}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-white rounded-lg transition-colors text-sm font-medium"
                >
                    <X className="w-4 h-4" />
                    Limpar
                </button>
                <button
                    onClick={handleApply}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
                >
                    <Calendar className="w-4 h-4" />
                    Filtrar
                </button>
            </div>
        </div>
    );
};

export default DateFilter;
