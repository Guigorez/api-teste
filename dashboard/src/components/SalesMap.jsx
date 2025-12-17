import React, { useEffect, useState, useMemo } from 'react';
import { geoMercator, geoPath } from 'd3-geo';
import { feature } from 'topojson-client';
import { scaleLinear } from 'd3-scale';

import { useTheme } from '../context/ThemeContext';

const SalesMap = ({ data }) => {
    const { theme } = useTheme();
    const [geography, setGeography] = useState([]);
    const [tooltip, setTooltip] = useState(null);

    // Garante que data é um array
    const safeData = useMemo(() => Array.isArray(data) ? data : [], [data]);

    useEffect(() => {
        fetch('/br-states.json')
            .then(response => {
                if (!response.ok) throw new Error('Failed to load map data');
                return response.json();
            })
            .then(topoData => {
                const features = feature(topoData, topoData.objects.estados).features;
                setGeography(features);
            })
            .catch(err => console.error("Error loading map:", err));
    }, []);

    // Mapeamento de dados
    const salesByUF = useMemo(() => {
        return safeData.reduce((acc, item) => {
            acc[item.uf] = item;
            return acc;
        }, {});
    }, [safeData]);

    // Escala de cor baseada na QUANTIDADE (contagem_pedidos)
    const maxQuantity = safeData.length > 0 ? Math.max(...safeData.map(d => d.contagem_pedidos)) : 0;

    const colorScale = scaleLinear()
        .domain([0, maxQuantity])
        .range(theme === 'dark' ? ["#E2E8F0", "#16A34A"] : ["#DCFCE7", "#15803D"]);

    // Projeção D3
    const projection = geoMercator()
        .scale(750)
        .center([-54, -15])
        .translate([400, 250]); // Ajuste para container 800x500

    const pathGenerator = geoPath().projection(projection);

    const formatCurrency = (val) =>
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 mb-8 relative transition-colors duration-200">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Mapa de Vendas (Quantidade por Estado)</h2>

            <div className="w-full h-[500px] bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 relative overflow-hidden flex justify-center items-center transition-colors duration-200">
                {geography.length === 0 ? (
                    <div className="text-gray-500 dark:text-gray-400 animate-pulse">Carregando mapa...</div>
                ) : (
                    <svg viewBox="0 0 800 500" className="w-full h-full">
                        <g>
                            {geography.map((geo) => {
                                const uf = geo.id;
                                const stateData = salesByUF[uf];
                                const quantity = stateData ? stateData.contagem_pedidos : 0;
                                const revenue = stateData ? stateData.faturamento : 0;
                                const hasSales = quantity > 0;

                                return (
                                    <path
                                        key={geo.id}
                                        d={pathGenerator(geo)}
                                        fill={hasSales ? colorScale(quantity) : (theme === 'dark' ? "#374151" : "#E5E7EB")}
                                        stroke={theme === 'dark' ? "#1F2937" : "#9CA3AF"}
                                        strokeWidth={0.5}
                                        className="transition-colors duration-200 hover:opacity-80 cursor-pointer outline-none"
                                        onMouseEnter={(e) => {
                                            const rect = e.target.getBoundingClientRect();
                                            setTooltip({
                                                uf: geo.properties.nome,
                                                uf_sigla: uf,
                                                quantity,
                                                revenue,
                                                shipping: stateData ? stateData.frete_medio : 0,
                                                x: rect.left + rect.width / 2,
                                                y: rect.top
                                            });
                                        }}
                                        onMouseLeave={() => setTooltip(null)}
                                    />
                                );
                            })}
                        </g>
                    </svg>
                )}

                {/* Tooltip */}
                {tooltip && (
                    <div
                        className="fixed z-50 px-4 py-3 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 pointer-events-none transform -translate-x-1/2 -translate-y-full"
                        style={{
                            left: tooltip.x,
                            top: tooltip.y - 10
                        }}
                    >
                        <p className="font-bold text-base mb-1">{tooltip.uf} ({tooltip.uf_sigla})</p>
                        <div className="space-y-1">
                            <p className="text-green-600 dark:text-green-400 font-semibold">
                                <span className="text-gray-500 dark:text-gray-400 font-normal">Qtd:</span> {tooltip.quantity} pedidos
                            </p>
                            <p className="text-blue-600 dark:text-blue-400 font-semibold">
                                <span className="text-gray-500 dark:text-gray-400 font-normal">Fat:</span> {formatCurrency(tooltip.revenue)}
                            </p>
                            <p className="text-orange-600 dark:text-orange-400 font-semibold">
                                <span className="text-gray-500 dark:text-gray-400 font-normal">Frete Médio:</span> {formatCurrency(tooltip.shipping)}
                            </p>
                        </div>
                    </div>
                )}
            </div>

            <div className="mt-4 flex justify-center items-center gap-6 text-xs text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-gray-200 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600"></div>
                    <span>Sem vendas</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-green-100 dark:bg-slate-200 rounded border border-gray-300 dark:border-gray-600"></div>
                    <span>Baixa Qtd</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-green-700 dark:bg-green-600 rounded border border-gray-300 dark:border-gray-600"></div>
                    <span>Alta Qtd</span>
                </div>
            </div>
        </div>
    );
};

export default SalesMap;
