import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

# Configuração de Logger
logger = logging.getLogger(__name__)

def generate_forecast(company='animoshop', months_to_predict=6):
    """
    Gera previsão de vendas para os próximos N meses usando:
    1. Regressão Linear para Tendência
    2. Índices Mensais Médios para Sazonalidade
    
    Retorno:
    [
        { "date": "YYYY-MM", "value": float, "type": "history" },
        ...
        { "date": "YYYY-MM", "value": float, "type": "forecast" }
    ]
    """
    try:
        # Importação tardia para evitar ciclo de importação com routes.py
        from .routes import get_filtered_query
        
        # 1. OBTER DADOS HISTÓRICOS
        # Busca todas as vendas limpas do banco de dados
        base_query, conn = get_filtered_query(company, source='limpas')
        
        if not base_query:
            logger.warning(f"Forecast: Nenhuma query gerada para empresa {company}")
            return []

        query = f"""
            SELECT data_filtro, faturamento 
            FROM ({base_query}) 
            WHERE faturamento > 0
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            logger.warning("Forecast: DataFrame vazio retornado do banco.")
            return []

        # 2. PRÉ-PROCESSAMENTO
        # Converte datas e agrupa por mês
        df['data_filtro'] = pd.to_datetime(df['data_filtro'])
        df['periodo'] = df['data_filtro'].dt.to_period('M')
        
        monthly_data = df.groupby('periodo')['faturamento'].sum().reset_index()
        monthly_data['timestamp'] = monthly_data['periodo'].dt.to_timestamp()
        monthly_data = monthly_data.sort_values('timestamp')

        # Se houver menos de 12 meses, a sazonalidade pode ser pouco precisa, mas calculamos mesmo assim
        if len(monthly_data) < 3:
            logger.info("Forecast: Dados insuficientes para previsão confiável (menos de 3 meses).")
            # Retorna apenas histórico
            return [
                {
                    "date": row['timestamp'].strftime("%Y-%m"),
                    "value": float(row['faturamento']),
                    "type": "history"
                }
                for _, row in monthly_data.iterrows()
            ]

        # 3. CÁLCULO DA TENDÊNCIA (REGRESSÃO LINEAR)
        # X = Índice numérico do mês (0, 1, 2...)
        # y = Faturamento
        monthly_data['month_idx'] = np.arange(len(monthly_data))
        
        X = monthly_data[['month_idx']]
        y = monthly_data['faturamento']
        
        model = LinearRegression()
        model.fit(X, y)
        
        monthly_data['trend'] = model.predict(X)
        
        # 4. CÁLCULO DA SAZONALIDADE
        # Índice Sazonal = Valor Real / Tendência
        # Usamos .replace(0, 1) para evitar divisão por zero, embora tendência 0 seja rara em dados reais de vendas
        monthly_data['seasonal_index'] = monthly_data['faturamento'] / monthly_data['trend'].replace(0, 1)
        
        # Agrupa índices por mês do ano (1=Jan, ..., 12=Dez) para achar o Perfil Sazonal Médio
        monthly_data['month_num'] = monthly_data['timestamp'].dt.month
        seasonal_profile = monthly_data.groupby('month_num')['seasonal_index'].mean().to_dict()
        
        # Média global de sazonalidade deve ser ~1.0. Se faltar algum mês no histórico, assumimos 1.0 (neutro)
        for m in range(1, 13):
            if m not in seasonal_profile:
                seasonal_profile[m] = 1.0

        # 5. GERAR PREVISÃO FUTURA
        last_idx = monthly_data['month_idx'].iloc[-1]
        last_date = monthly_data['timestamp'].iloc[-1]
        
        forecast_results = []
        
        for i in range(1, months_to_predict + 1):
            future_idx = last_idx + i
            future_date = last_date + relativedelta(months=i)
            month_num = future_date.month
            
            # a) Projetar Tendência
            future_trend = model.predict([[future_idx]])[0]
            
            # b) Aplicar Sazonalidade
            seasonal_factor = seasonal_profile.get(month_num, 1.0)
            forecast_value = future_trend * seasonal_factor
            
            # Garantir não-negatividade
            if forecast_value < 0:
                forecast_value = 0.0
                
            forecast_results.append({
                "date": future_date.strftime("%Y-%m"),
                "value": float(forecast_value),
                "type": "forecast"
            })

        # 6. FORMATAR RETORNO UNIFICADO
        history_results = [
            {
                "date": row['timestamp'].strftime("%Y-%m"),
                "value": float(row['faturamento']),
                "type": "history"
            }
            for _, row in monthly_data.iterrows()
        ]
        
        logger.info(f"Forecast gerado com sucesso: {len(history_results)} meses históricos + {len(forecast_results)} meses previstos.")
        
        return history_results + forecast_results

    except Exception as e:
        logger.error(f"Erro ao gerar forecast: {str(e)}")
        # Em caso de erro, retorna erro explicito ou lista vazia, dependendo da estratégia
        # Aqui optamos por propagar o erro para que o endpoint possa tratá-lo se quiser
        # ou retornar um objeto de erro na lista.
        return [{"error": str(e)}]
