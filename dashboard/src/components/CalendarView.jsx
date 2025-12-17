import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const CalendarView = ({ diario }) => {
    // Encontra a última data com dados para iniciar o calendário
    const initialDate = useMemo(() => {
        if (!diario || diario.length === 0) return new Date();
        // Assume que diario está ordenado ou pega o último
        const lastItem = diario[diario.length - 1];
        if (lastItem && lastItem.data_iso) {
            // Adiciona T00:00:00 para evitar problemas de fuso horário ao instanciar
            return new Date(lastItem.data_iso + 'T12:00:00');
        }
        return new Date();
    }, [diario]);

    const [currentDate, setCurrentDate] = useState(initialDate);

    const daysInMonth = (date) => new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
    const firstDayOfMonth = (date) => new Date(date.getFullYear(), date.getMonth(), 1).getDay();

    const prevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    };

    const nextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    };

    const formatCurrency = (val) =>
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

    const monthData = useMemo(() => {
        if (!diario) return {};
        const currentMonthStr = currentDate.toISOString().slice(0, 7); // YYYY-MM

        const map = {};
        let maxRev = 0;

        diario.forEach(item => {
            if (item.data_iso.startsWith(currentMonthStr)) {
                map[item.data_iso] = item;
                if (item.faturamento > maxRev) maxRev = item.faturamento;
            }
        });

        return { map, maxRev };
    }, [diario, currentDate]);

    const renderDays = () => {
        const totalDays = daysInMonth(currentDate);
        const startDay = firstDayOfMonth(currentDate);
        const days = [];

        // Empty cells for previous month
        for (let i = 0; i < startDay; i++) {
            days.push(<div key={`empty-${i}`} className="h-24 bg-gray-50/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50 transition-colors duration-200"></div>);
        }

        // Days of current month
        for (let day = 1; day <= totalDays; day++) {
            const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const data = monthData.map[dateStr];

            let bgColor = null; // Let CSS handle default

            if (data) {
                // Calculate intensity based on revenue relative to max of the month
                const intensity = monthData.maxRev > 0 ? (data.faturamento / monthData.maxRev) : 0;

                // HSL Scale: 0 (Red) -> 120 (Green)
                const hue = intensity * 120;
                bgColor = `hsla(${hue}, 70%, 35%, 0.8)`;
            }

            days.push(
                <div
                    key={day}
                    className={`h-24 border border-gray-200 dark:border-gray-700 p-2 relative group transition-all hover:scale-[1.02] hover:z-10 cursor-default bg-white dark:bg-gray-800`}
                    style={{ backgroundColor: data ? bgColor : undefined }}
                >
                    <span className={`text-sm font-medium ${data ? 'text-white' : 'text-gray-500 dark:text-gray-400'}`}>{day}</span>
                    {data && (
                        <div className="mt-1">
                            <p className="text-xs font-bold text-white truncate">
                                {formatCurrency(data.faturamento)}
                            </p>
                            <p className="text-[10px] text-gray-200 dark:text-gray-300">
                                {data.contagem_pedidos || 0} peds
                            </p>
                        </div>
                    )}

                    {/* Tooltip */}
                    {data && (
                        <div className="absolute z-10 invisible group-hover:visible bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-600 p-3 rounded-lg shadow-xl -top-16 left-1/2 transform -translate-x-1/2 w-48 text-xs z-50">
                            <p className="font-bold text-gray-900 dark:text-white mb-1">{dateStr.split('-').reverse().join('/')}</p>
                            <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">Faturamento:</span>
                                <span className="text-green-600 dark:text-green-400">{formatCurrency(data.faturamento)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">Lucro:</span>
                                <span className="text-blue-600 dark:text-blue-400">{formatCurrency(data.lucro_liquido)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">Pedidos:</span>
                                <span className="text-gray-900 dark:text-white">{data.contagem_pedidos || 0}</span>
                            </div>
                        </div>
                    )}
                </div>
            );
        }

        return days;
    };

    const weekDays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    const monthName = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' }).format(currentDate);

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 mb-8 overflow-hidden transition-colors duration-200">
            <div className="p-6 flex items-center justify-between border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white capitalize">{monthName}</h2>
                <div className="flex gap-2">
                    <button onClick={prevMonth} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <button onClick={nextMonth} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors">
                        <ChevronRight className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-7 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 transition-colors duration-200">
                {weekDays.map(day => (
                    <div key={day} className="py-3 text-center text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {day}
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-7 bg-white dark:bg-gray-800 transition-colors duration-200">
                {renderDays()}
            </div>
        </div>
    );
};

export default CalendarView;
