import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api',
});

const getParams = (filters) => {
    const params = {};
    if (filters?.startDate) params.start_date = filters.startDate;
    if (filters?.endDate) params.end_date = filters.endDate;
    if (filters?.source) params.source = filters.source;
    if (filters?.marketplace) params.marketplace = filters.marketplace;
    if (filters?.company) params.company = filters.company; // Add company param
    return { params };
};

export const getResumo = async (filters) => {
    const response = await api.get('/resumo', getParams(filters));
    return response.data;
};

export const getMarketplace = async (filters) => {
    const response = await api.get('/marketplace', getParams(filters));
    return response.data;
};

export const getMensal = async (filters) => {
    const response = await api.get('/mensal', getParams(filters));
    return response.data;
};

export const getDiario = async (filters) => {
    const response = await api.get('/diario', getParams(filters));
    return response.data;
};

export const getSemanal = async (filters) => {
    const response = await api.get('/semanal', getParams(filters));
    return response.data;
};

export const getAnual = async (filters) => {
    const response = await api.get('/anual', getParams(filters));
    return response.data;
};

export const getGeoSales = async (filters) => {
    const response = await api.get('/geo', getParams(filters));
    return response.data;
};

export const getPagamentos = async (filters) => {
    const response = await api.get('/pagamentos', getParams(filters));
    return response.data;
};

export const getTopProdutos = async (limit = 10, filters = {}, sortBy = 'faturamento') => {
    const { params } = getParams(filters);
    params.limit = limit;
    params.sort_by = sortBy;
    const response = await api.get('/produtos/top', { params });
    return response.data;
};

export const processData = async (company = 'animoshop') => {
    const response = await api.post('/processar', null, { params: { company } });
    return response.data;
};

export default api;
