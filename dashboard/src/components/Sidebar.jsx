import React from 'react';
import { LayoutDashboard, ShoppingBag, PieChart, TrendingUp, Brain, Lightbulb, Settings } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const Sidebar = ({ activeTab, onTabChange }) => {
  const { theme } = useTheme();

  const menuItems = [
    { id: 'overview', label: 'Visão Geral', icon: LayoutDashboard },
    { id: 'sales', label: 'Vendas & Produtos', icon: ShoppingBag },
    { id: 'financials', label: 'Financeiro', icon: PieChart },
    { id: 'intelligence', label: 'Inteligência (IA)', icon: Brain },
    { id: 'opportunities', label: 'Oportunidades', icon: Lightbulb },
  ];

  return (
    <div className="hidden lg:flex flex-col w-20 lg:w-64 h-screen bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 fixed left-0 top-0 z-50 transition-all duration-300">
      <div className="flex items-center justify-center h-20 border-b border-gray-200 dark:border-gray-700">
        <div className="bg-[#FF6B00] text-white p-2 rounded-lg">
          <LayoutDashboard className="w-8 h-8" />
        </div>
        <span className="ml-3 text-xl font-bold text-gray-800 dark:text-white hidden lg:block">Dash</span>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-2 px-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center p-3 rounded-xl transition-colors group ${isActive
                    ? 'bg-orange-50 dark:bg-orange-900/20 text-[#FF6B00]'
                    : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                    }`}
                >
                  <Icon className="w-6 h-6" />
                  <span className="ml-3 font-medium hidden lg:block">{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <button className="flex items-center p-3 rounded-xl text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white transition-colors w-full">
          <Settings className="w-6 h-6" />
          <span className="ml-3 font-medium hidden lg:block">Configurações</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;

