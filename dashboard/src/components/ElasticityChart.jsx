import React, { useState, useEffect } from 'react';
import {
    ComposedChart,
    Line,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Bar,
    ReferenceLine,
    Legend
} from 'recharts';
import { useTheme } from '../context/ThemeContext';
import { getElasticity, getTopProdutos } from '../services/api';

const ElasticityChart = ({ filters }) => {
    const { theme } = useTheme();
    const [loading, setLoading] = useState(false);
    const [products, setProducts] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState('');
    const [data, setData] = useState(null);

    // Carrega lista de produtos ao montar ou quando filtros mudam
    // Carrega lista de produtos ao montar ou quando filtros mudam
    useEffect(() => {
        const loadProducts = async () => {
            // Usa apenas o filtro de empresa para listar produtos (All Time), ignorando datas
            const productFilters = { company: filters?.company };

            // Pega top 20 produtos para o dropdown
            const top = await getTopProdutos(20, productFilters);
            if (top && top.length > 0) {
                setProducts(top);
                // Se o produto selecionado não estiver na nova lista, seleciona o primeiro
                if (!selectedProduct || !top.find(p => p.produto === selectedProduct)) {
                    setSelectedProduct(top[0].produto);
                }
            } else {
                setProducts([]);
                setSelectedProduct('');
            }
        };
        loadProducts();
    }, [filters?.company]); // Recarrega apenas se a empresa mudar

    // Carrega dados de elasticidade quando o produto muda
    useEffect(() => {
        if (!selectedProduct) {
            setData(null);
            return;
        }

        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await getElasticity(selectedProduct);
                setData(result);
            } catch (error) {
                console.error("Erro elasticidade:", error);
                setData(null);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [selectedProduct]);

    const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

    if (!products.length && loading) return null; // Wait for initial load

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">Análise de Elasticidade de Preço</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Simulação de demanda e receita baseada em inteligência artificial.
                    </p>
                </div>

                <div className="w-full md:w-64">
                    <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Selecionar Produto</label>
                    <select
                        value={selectedProduct}
                        onChange={(e) => setSelectedProduct(e.target.value)}
                        className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-2 text-sm text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {products.map(p => (
                            <option key={p.produto} value={p.produto}>
                                {p.produto.length > 30 ? p.produto.substring(0, 30) + '...' : p.produto}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {loading ? (
                <div className="h-[400px] flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            ) : data && data.status === 'success' ? (
                <>
                    <div className="flex flex-wrap gap-4 mb-6">
                        <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 flex-1">
                            <p className="text-xs text-gray-500 dark:text-gray-400">Preço Atual</p>
                            <p className="text-xl font-bold text-blue-600 dark:text-blue-400">{formatCurrency(data.current_avg_price)}</p>
                        </div>
                        <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 flex-1">
                            <p className="text-xs text-gray-500 dark:text-gray-400">Preço Ótimo (Sugerido)</p>
                            <p className="text-xl font-bold text-green-600 dark:text-green-400">
                                {data.optimal_price ? formatCurrency(data.optimal_price) : "N/A (Inelástico)"}
                            </p>
                        </div>
                        <div className="p-4 rounded-lg bg-purple-50 dark:bg-purple-900/20 border border-purple-100 dark:border-purple-800 flex-1">
                            <p className="text-xs text-gray-500 dark:text-gray-400">Elasticidade</p>
                            <p className="text-xl font-bold text-purple-600 dark:text-purple-400">{data.elasticity_status}</p>
                        </div>
                    </div>

                    <div className="h-[400px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={data.chart_data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme === 'dark' ? '#374151' : '#E5E7EB'} />
                                <XAxis
                                    dataKey="price"
                                    unit=" R$"
                                    stroke={theme === 'dark' ? '#9CA3AF' : '#6B7280'}
                                />
                                <YAxis
                                    yAxisId="left"
                                    orientation="left"
                                    stroke="#3B82F6"
                                    label={{ value: 'Demanda (Qtd)', angle: -90, position: 'insideLeft', fill: '#3B82F6' }}
                                />
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    stroke="#10B981"
                                    tickFormatter={(val) => `R$${(val / 1000).toFixed(0)}k`}
                                    label={{ value: 'Receita Prevista', angle: 90, position: 'insideRight', fill: '#10B981' }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: theme === 'dark' ? '#1F2937' : '#fff',
                                        borderColor: theme === 'dark' ? '#374151' : '#E5E7EB',
                                        color: theme === 'dark' ? '#fff' : '#000'
                                    }}
                                    formatter={(value, name) => [
                                        name === 'projected_revenue' ? formatCurrency(value) : value,
                                        name === 'projected_revenue' ? 'Receita' : 'Demanda'
                                    ]}
                                    labelFormatter={(label) => `Preço: ${formatCurrency(label)}`}
                                />
                                <Legend />

                                {/* Linha de Demanda (Azul) */}
                                <Line
                                    yAxisId="left"
                                    type="monotone"
                                    dataKey="demand_qty"
                                    name="Demanda Estimada"
                                    stroke="#3B82F6"
                                    strokeWidth={3}
                                    dot={false}
                                />

                                {/* Curva de Receita (Verde - Area) */}
                                <Area
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="projected_revenue"
                                    name="Receita Projetada"
                                    fill="#10B981"
                                    fillOpacity={0.2}
                                    stroke="#10B981"
                                    strokeWidth={2}
                                />

                                <ReferenceLine x={data.current_avg_price} stroke="#3B82F6" strokeDasharray="3 3" label="Preço Atual" />
                                {data.optimal_price && (
                                    <ReferenceLine x={data.optimal_price} stroke="#10B981" strokeDasharray="3 3" label="Preço Ótimo" />
                                )}

                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </>
            ) : (
                <div className="h-64 flex flex-col items-center justify-center text-center p-6 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
                    <p className="text-gray-500 mb-2">
                        {!products.length ? "Nenhum produto encontrado para análise." : "Não foi possível calcular a elasticidade para este produto."}
                    </p>
                    <p className="text-xs text-gray-400">
                        debug: {JSON.stringify(filters)} <br />
                        len: {products.length} <br />
                        sel: "{selectedProduct}" <br />
                        p0: {JSON.stringify(products[0])}
                    </p>
                </div>
            )}
        </div>
    );
};

export default ElasticityChart;
