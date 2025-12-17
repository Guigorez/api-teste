import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime
from dateutil.relativedelta import relativedelta

def generate_forecast(company='animoshop', months_to_predict=6):
    # Importação local para evitar ciclo
    from .routes import get_all_sales_data
    
    # 1. Obter dados históricos
    df = get_all_sales_data(company)
    
    if df.empty or 'data_filtro' not in df.columns:
        return []

    # Agrupa por mês (YYYY-MM-01)
    df['data_mes'] = df['data_filtro'].dt.to_period('M').dt.to_timestamp()
    monthly_sales = df.groupby('data_mes')['faturamento'].sum().reset_index()
    monthly_sales.sort_values('data_mes', inplace=True)
    
    # Se tivermos poucos dados (menos de 6 meses), retornamos apenas histórico ou erro
    if len(monthly_sales) < 3:
        # Retorna apenas histórico formatado
        return [
            {"date": row['data_mes'].strftime("%Y-%m"), "value": row['faturamento'], "type": "history"}
            for _, row in monthly_sales.iterrows()
        ]

    # 2. Preparar dados para Regressão (Tendência)
    # X = Índice numérico do mês (0, 1, 2...)
    # Y = Faturamento
    monthly_sales['month_index'] = np.arange(len(monthly_sales))
    
    X = monthly_sales[['month_index']]
    y = monthly_sales['faturamento']
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Tendência Linear: y = ax + b
    monthly_sales['trend'] = model.predict(X)
    
    # 3. Calcular Sazonalidade
    # Índice Sazonal = Valor Real / Tendência
    # (Evita divisão por zero)
    monthly_sales['seasonal_index'] = monthly_sales['faturamento'] / monthly_sales['trend'].replace(0, 1)
    
    # Agrupa índices por mês do ano (1=Jan, 12=Dez)
    monthly_sales['month_num'] = monthly_sales['data_mes'].dt.month
    seasonal_factors = monthly_sales.groupby('month_num')['seasonal_index'].mean()
    
    # Preenche meses faltantes com média global (1.0) se necessário
    global_avg_seasonality = seasonal_factors.mean()
    seasonal_dict = seasonal_factors.to_dict()
    for m in range(1, 13):
        if m not in seasonal_dict:
            seasonal_dict[m] = global_avg_seasonality

    # 4. Gerar Previsão Futura
    last_date = monthly_sales['data_mes'].iloc[-1]
    last_index = monthly_sales['month_index'].iloc[-1]
    
    forecast_data = []
    
    for i in range(1, months_to_predict + 1):
        future_date = last_date + relativedelta(months=i)
        future_index = last_index + i
        month_num = future_date.month
        
        # Tendência Futura
        future_trend = model.predict([[future_index]])[0]
        
        # Aplica Sazonalidade
        seasonality = seasonal_dict.get(month_num, 1.0)
        forecast_value = future_trend * seasonality
        
        # Evita valores negativos
        forecast_value = max(0, forecast_value)
        
        forecast_data.append({
            "date": future_date.strftime("%Y-%m"),
            "value": forecast_value,
            "type": "forecast",
            "trend": future_trend # Opcional: para debug ou visualização
        })

    # 5. Formatar Resposta Unificada
    history_data = [
        {"date": row['data_mes'].strftime("%Y-%m"), "value": row['faturamento'], "type": "history"}
        for _, row in monthly_sales.iterrows()
    ]
    
    return history_data + forecast_data
