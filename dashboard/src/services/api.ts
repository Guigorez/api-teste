import axios from 'axios';
import { Filters, SummaryData, MonthlyData, TopProduct, GeoData, MarketplaceData, RiskData } from '../types';

const api = axios.create({
    baseURL: '/api', // Uses Vite Proxy
});

const getParams = (filters?: Filters) => {
    const params: any = {};
    if (filters?.startDate) params.start_date = filters.startDate;
    if (filters?.endDate) params.end_date = filters.endDate;
    if (filters?.source) params.source = filters.source;
    if (filters?.marketplace) params.marketplace = filters.marketplace;
    if (filters?.company) params.company = filters.company;
    return { params };
};

export const getResumo = async (filters?: Filters): Promise<SummaryData> => {
    const response = await api.get<SummaryData>('/resumo', getParams(filters));
    return response.data;
};

export const getMarketplace = async (filters?: Filters): Promise<MarketplaceData[]> => {
    const response = await api.get<MarketplaceData[]>('/marketplace', getParams(filters));
    return response.data;
};

export const getMensal = async (filters?: Filters): Promise<MonthlyData[]> => {
    const response = await api.get<MonthlyData[]>('/mensal', getParams(filters));
    return response.data;
};

export const getDiario = async (filters?: Filters): Promise<any[]> => {
    const response = await api.get('/diario', getParams(filters));
    return response.data;
};

export const getSemanal = async (filters?: Filters): Promise<any[]> => {
    const response = await api.get('/semanal', getParams(filters));
    return response.data;
};

export const getAnual = async (filters?: Filters): Promise<any[]> => {
    const response = await api.get('/anual', getParams(filters));
    return response.data;
};

export const getGeoSales = async (filters?: Filters): Promise<GeoData[]> => {
    const response = await api.get<GeoData[]>('/geo', getParams(filters));
    return response.data;
};

export const getPagamentos = async (filters?: Filters): Promise<any[]> => {
    const response = await api.get('/pagamentos', getParams(filters));
    return response.data;
};

export const getTopProdutos = async (limit: number = 10, filters?: Filters, sortBy: 'faturamento' | 'quantidade' = 'faturamento'): Promise<TopProduct[]> => {
    const { params } = getParams(filters);
    params.limit = limit;
    params.sort_by = sortBy;
    const response = await api.get<TopProduct[]>('/produtos/top', { params });
    return response.data;
};

export const getForecast = async (filters?: Filters, granularity: 'weekly' | 'monthly' = 'weekly', periods: number = 12): Promise<any> => {
    const { params } = getParams(filters);
    params.granularity = granularity;
    params.periods = periods;
    const response = await api.get('/forecast/sales', { params });
    return response.data;
};

export const getClustering = async (filters?: Filters): Promise<any> => {
    const response = await api.get('/analysis/clustering', getParams(filters));
    return response.data;
};

export const getBundles = async (filters?: Filters): Promise<any> => {
    const response = await api.get('/analysis/bundles', getParams(filters));
    return response.data;
};

export const getElasticity = async (productName: string, filters?: Filters): Promise<any> => {
    const { params } = getParams(filters);
    const mergedParams = { ...params, product_name: productName };
    const response = await api.get('/analysis/elasticity', { params: mergedParams });
    return response.data;
};

export const processData = async (company: 'animoshop' | 'novoon' = 'animoshop'): Promise<any> => {
    const response = await api.post('/processar', null, { params: { company } });
    return response.data;
};

export const getRiskAnalysis = async (filters?: Filters): Promise<RiskData> => {
    // Risk endpoint ignores date filters usually (uses full history or internal logic), 
    // but we pass company param at least. UPDATE: Now it accepts all filters!
    const response = await api.get<RiskData>('/analysis/risk-analysis', getParams(filters));
    return response.data;
};
