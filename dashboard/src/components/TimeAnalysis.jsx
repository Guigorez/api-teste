import React, { useState } from 'react';
import SalesChart from './SalesChart';
import CalendarView from './CalendarView';

const TimeAnalysis = ({ diario, semanal, mensal, anual }) => {
    const [activeTab, setActiveTab] = useState('mensal');

    const tabs = [
        { id: 'calendario', label: 'Diário' },
        { id: 'mensal', label: 'Mensal' },
        { id: 'anual', label: 'Anual' },
    ];

    const getData = () => {
        switch (activeTab) {
            case 'mensal': return { data: mensal, xKey: 'mes', title: 'Evolução Mensal' };
            case 'anual': return { data: anual, xKey: 'ano', title: 'Evolução Anual' };
            default: return { data: [], xKey: 'mes', title: '' };
        }
    };

    const { data, xKey, title } = getData();

    return (
        <div className="h-full flex flex-col">
            <div className="flex justify-end mb-4">
                <div className="flex bg-gray-100 dark:bg-gray-700/50 p-1 rounded-full w-fit">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${activeTab === tab.id
                                ? 'bg-white dark:bg-gray-600 text-[#FF6B00] shadow-sm'
                                : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {activeTab === 'calendario' ? (
                <CalendarView diario={diario} />
            ) : (
                <SalesChart data={data} title={title} xKey={xKey} />
            )}
        </div>
    );
};

export default TimeAnalysis;

