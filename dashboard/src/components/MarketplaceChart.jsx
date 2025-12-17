import React, { useState } from 'react';
import { PieChart, Pie, Sector, Cell, ResponsiveContainer, Legend } from 'recharts';
import { useTheme } from '../context/ThemeContext';

const BRAND_COLORS = {
    'Mercado Livre': '#FFE600', // Yellow
    'Shopee': '#EE4D2D',      // Red/Orange
    'Amazon': '#232F3E',      // Dark Blue (Amazon/AWS) - High contrast
    'Magalu': '#0086FF',      // Blue
    'MadeiraMadeira': '#F58220', // Orange
    'Madeira': '#F58220',
    'Olist': '#1F2D6B',       // Navy Blue
    'B2W': '#E60014',         // Red
    'Americanas': '#E60014',
    'Simples Nacional': '#22C55E'
};

const DEFAULT_COLORS = ['#FF6B00', '#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#6B7280'];

const getColor = (name, index) => {
    return BRAND_COLORS[name] || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
};

const renderActiveShape = (props) => {
    const { cx, cy, midAngle, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value, theme } = props;
    const sin = Math.sin(-RADIAN * midAngle);
    const cos = Math.cos(-RADIAN * midAngle);
    const sx = cx + (outerRadius + 10) * cos;
    const sy = cy + (outerRadius + 10) * sin;
    const mx = cx + (outerRadius + 30) * cos;
    const my = cy + (outerRadius + 30) * sin;
    const ex = mx + (cos >= 0 ? 1 : -1) * 22;
    const ey = my;
    const textAnchor = cos >= 0 ? 'start' : 'end';

    return (
        <g>
            <text x={cx} y={cy} dy={8} textAnchor="middle" fill={theme === 'dark' ? '#fff' : '#111827'} className="text-xl font-bold">
                {`${(percent * 100).toFixed(0)}%`}
            </text>
            <Sector
                cx={cx}
                cy={cy}
                innerRadius={innerRadius}
                outerRadius={outerRadius}
                startAngle={startAngle}
                endAngle={endAngle}
                fill={fill}
            />
            <Sector
                cx={cx}
                cy={cy}
                startAngle={startAngle}
                endAngle={endAngle}
                innerRadius={outerRadius + 6}
                outerRadius={outerRadius + 10}
                fill={fill}
            />
            <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
            <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill={theme === 'dark' ? '#fff' : '#374151'} className="font-medium">{payload.MarketPlace}</text>
            <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} dy={18} textAnchor={textAnchor} fill="#999" className="text-xs">
                {`R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`}
            </text>
        </g>
    );
};

const RADIAN = Math.PI / 180;

const MarketplaceChart = ({ data }) => {
    const { theme } = useTheme();
    const [activeIndex, setActiveIndex] = useState(0);

    if (!data || data.length === 0) return null;

    const onPieEnter = (_, index) => {
        setActiveIndex(index);
    };

    return (
        <div className="bg-white dark:bg-gray-800 p-0 rounded-xl transition-colors duration-200 h-full flex flex-col items-center justify-center">
            {/* Title removed for cleaner layout integration */}
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            activeIndex={activeIndex}
                            activeShape={(props) => renderActiveShape({ ...props, theme })}
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={70}
                            outerRadius={90}
                            fill="#8884d8"
                            dataKey="faturamento"
                            nameKey="MarketPlace"
                            onMouseEnter={onPieEnter}
                            paddingAngle={2}
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={getColor(entry.MarketPlace, index)} strokeWidth={0} />
                            ))}
                        </Pie>
                        <Legend
                            layout="horizontal"
                            verticalAlign="bottom"
                            align="center"
                            height={36}
                            formatter={(value, entry) => <span className="text-gray-600 dark:text-gray-400 text-sm font-medium ml-1">{value}</span>}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default MarketplaceChart;


