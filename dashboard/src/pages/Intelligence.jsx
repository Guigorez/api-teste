import React from 'react';
import ForecastChart from '../components/ForecastChart';

import ClusterChart from '../components/ClusterChart';
import ElasticityChart from '../components/ElasticityChart';

const Intelligence = ({ forecastData, clusteringData, filters }) => {
    return (
        <div className="space-y-8 animate-fade-in">
            {/* Seção 1: Previsão de Demanda */}
            <div className="w-full">
                <ForecastChart data={forecastData} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Seção 2: Clusterização */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                    <ClusterChart data={clusteringData} />
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                    <ElasticityChart filters={filters} />
                </div>
            </div>
        </div>
    );
};

export default Intelligence;
