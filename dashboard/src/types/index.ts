export interface Filters {
    company?: 'animoshop' | 'novoon';
    startDate?: string;
    endDate?: string;
    source?: string;
    marketplace?: string;
}

export interface SummaryData {
    faturamento_total: number;
    lucro_liquido_total: number;
    frete_total: number;
    comissoes_total: number;
    total_pedidos: number;
    ticket_medio: number;
    custo_total: number;
    comparisons?: {
        faturamento_pct?: number;
        lucro_pct?: number;
        pedidos_pct?: number;
        periodo_anterior?: string;
    }
}

export interface MonthlyData {
    ano: number;
    mes_num: number;
    mes: string;
    faturamento: number;
    lucro_liquido: number;
    frete: number;
    comissoes: number;
}

export interface TopProduct {
    produto: string;
    faturamento: number;
    contagem_pedidos: number;
}

export interface GeoData {
    uf: string;
    faturamento: number;
    contagem_pedidos: number;
    frete_medio: number;
}

export interface MarketplaceData {
    MarketPlace: string;
    faturamento: number;
    lucro_liquido: number;
    contagem_pedidos: number;
}
