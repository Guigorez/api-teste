import React from 'react';
import { DollarSign, ShoppingBag, TrendingUp, TrendingDown, CreditCard, Truck, Percent, AlertTriangle } from 'lucide-react';

const Card = ({ title, value, icon: Icon, color, trend, trendLabel, className = "" }) => {
    const isPositive = parseFloat(trend) >= 0;
    const TrendIcon = isPositive ? TrendingUp : TrendingDown;
    const trendColor = isPositive ? "text-green-500" : "text-red-500";

    // For specific metrics like Costs/Freight, increase is actually bad, but let's keep it simple for now: Green = Up, Red = Down.
    // Ideally we would have a 'inverseTrend' prop.

    return (
        <div className={`bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col justify-between ${className}`}>
            <div className="flex justify-between items-start">
                <div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-1">{title}</p>
                    <h3 className="text-2xl font-extrabold text-gray-900 dark:text-white tracking-tight">{value}</h3>
                </div>
                {Icon && (
                    <div className={`p-3 rounded-xl ${color} bg-opacity-10 dark:bg-opacity-20`}>
                        <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
                    </div>
                )}
            </div>

            {trend !== undefined && trend !== null && (
                <div className="mt-4 flex items-center text-sm">
                    <span className={`${trendColor} font-semibold flex items-center`}>
                        <TrendIcon className="w-4 h-4 mr-1" />
                        {Math.abs(trend).toFixed(1)}%
                    </span>
                    <span className="text-gray-400 ml-2 text-xs">{trendLabel || "vs período anterior"}</span>
                </div>
            )}
        </div>
    );
};

const HeroCard = ({ title, value, trend, trendLabel }) => {
    const isPositive = parseFloat(trend) >= 0;

    return (
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 col-span-1 md:col-span-2 lg:col-span-2 relative overflow-hidden group">
            <div className="relative z-10">
                <h2 className="text-gray-500 dark:text-gray-400 font-medium mb-2">{title}</h2>
                <div className="flex items-baseline mb-4">
                    <span className="text-5xl font-extrabold text-gray-900 dark:text-white tracking-tighter">{value}</span>
                </div>

                {trend !== undefined && trend !== null && (
                    <div className={`flex items-center font-medium w-fit px-3 py-1 rounded-full text-sm ${isPositive ? 'bg-green-50 text-green-600 dark:bg-green-900/20' : 'bg-red-50 text-red-600 dark:bg-red-900/20'}`}>
                        {isPositive ? <TrendingUp className="w-4 h-4 mr-1.5" /> : <TrendingDown className="w-4 h-4 mr-1.5" />}
                        {Math.abs(trend).toFixed(1)}% <span className="text-gray-400 dark:text-gray-500 ml-1 font-normal opacity-80">{trendLabel}</span>
                    </div>
                )}
            </div>

            {/* Decorative Element */}
            <div className="absolute right-[-20px] bottom-[-20px] opacity-10 transform rotate-12 transition-transform duration-500 group-hover:scale-110">
                <DollarSign className="w-48 h-48 text-[#FF6B00]" />
            </div>
        </div>
    );
};

const SummaryCards = ({ data }) => {
    if (!data) return null;

    const comps = data.comparisons || {};
    const hasTrend = Object.keys(comps).length > 0;
    const trendLabel = hasTrend ? "vs periodo anterior" : null;

    const formatCurrency = (val) =>
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Row 1: Hero Card + Top Stats */}
            <HeroCard
                title="Faturamento"
                value={formatCurrency(data.faturamento_total)}
                trend={hasTrend ? comps.faturamento_pct : null}
                trendLabel={trendLabel}
            />

            <div className="flex flex-col gap-6 col-span-1 md:col-span-2 lg:col-span-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 h-full">
                    <Card
                        title="Alertas Inteligentes"
                        value={data.total_pedidos > 0 ? "0" : "0"}
                        icon={AlertTriangle}
                        color="bg-yellow-500"
                        className="h-full"
                    // Static for now, logic to be implemented later
                    />
                    <Card
                        title="Ticket Médio"
                        value={formatCurrency(data.ticket_medio)}
                        icon={CreditCard}
                        color="bg-[#FF6B00]" // Orange accent
                        trend={hasTrend ? comps.ticket_pct : null}
                        trendLabel={trendLabel}
                        className="h-full"
                    />
                </div>
            </div>

            {/* Row 2: Secondary Metrics */}
            <Card
                title="Lucro Bruto"
                value={formatCurrency(data.lucro_liquido_total)}
                icon={TrendingUp}
                color="bg-green-500"
                trend={hasTrend ? comps.lucro_pct : null}
                trendLabel={trendLabel}
            />
            <Card
                title="Frete"
                value={formatCurrency(data.frete_total)}
                icon={Truck}
                color="bg-purple-500"
            />
            <Card
                title="Comissões"
                value={formatCurrency(data.comissoes_total)}
                icon={Percent}
                color="bg-blue-500"
            />
            <Card
                title="Total Pedidos"
                value={data.total_pedidos}
                icon={ShoppingBag}
                color="bg-pink-500"
                trend={hasTrend ? comps.pedidos_pct : null}
                trendLabel={trendLabel}
            />
        </div>
    );
};

export default SummaryCards;
