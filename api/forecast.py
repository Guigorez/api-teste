import pandas as pd
import numpy as np
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

# Configuração de Logger
logger = logging.getLogger(__name__)

def generate_forecast(company='animoshop', months_to_predict=6):
    """
    Gera previsão de vendas profissional usando Holt-Winters (Suavização Exponencial Tripla).
    - Adapta o modelo conforme a quantidade de dados históricos.
    - Captura Sazonalidade se possível (ex: Black Friday, Natal).
    
    Estratégia Adaptativa:
    1. >= 24 meses: Holt-Winters Completo (Tendência + Sazonalidade Aditiva)
    2. >= 6 meses: Holt Linear (Tendência apenas)
    3. < 6 meses: Média Móvel Simples
    """
    try:
        # Importação tardia
        from .routes import get_filtered_query
        
        # 1. OBTER DADOS HISTÓRICOS
        base_query, conn = get_filtered_query(company, source='limpas')
        if not base_query: return []

        query = f"SELECT data_filtro, faturamento FROM ({base_query}) WHERE faturamento > 0"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty: return []

        # 2. PRÉ-PROCESSAMENTO (SÉRIE TEMPORAL CONTÍNUA)
        df['data_filtro'] = pd.to_datetime(df['data_filtro'])
        
        # Agrupa por mês e preenche buracos com zero (Essencial para sazonalidade!)
        ts_data = df.set_index('data_filtro').resample('MS')['faturamento'].sum().fillna(0)
        
        # Remove zeros do início se existirem (para não viesar tendência inicial), mas mantem zeros 'reais' no meio
        # ts_data = ts_data.loc[ts_data.ne(0).idxmax():] 

        n_samples = len(ts_data)
        logger.info(f"Forecast: Iniciando previsão com {n_samples} meses de histórico.")

        forecast_values = []
        
        # 3. SELEÇÃO E TREINAMENTO DE MODELO
        try:
            model = None
            fitted_model = None

            # A) Holt-Winters Completo (Nível + Tendência + Sazonalidade)
            if n_samples >= 24:
                logger.info("Forecast: Usando Holt-Winters (Trend+Seasonal)")
                # seasonal_periods=12 para dados mensais
                model = ExponentialSmoothing(
                    ts_data, 
                    trend='add', 
                    seasonal='add', 
                    seasonal_periods=12,
                    initialization_method="estimated"
                )
            
            # B) Holt Linear (Apenas Nível + Tendência)
            elif n_samples >= 6:
                logger.info("Forecast: Usando Holt Linear (Trend only)")
                model = ExponentialSmoothing(
                    ts_data, 
                    trend='add', 
                    seasonal=None,
                    initialization_method="estimated"
                )
            
            # C) Fallback: Média Simples dos últimos N meses
            else:
                logger.info("Forecast: Dados insuficientes. Usando Média Simples.")
                avg_val = ts_data.mean()
                forecast_values = [max(0, avg_val)] * months_to_predict

            # Fit e Predict (se modelo foi definido)
            if model:
                fitted_model = model.fit(optimized=True)
                forecast_series = fitted_model.forecast(months_to_predict)
                forecast_values = forecast_series.tolist()

        except Exception as e:
            logger.warning(f"Forecast: Falha no modelo estatístico ({e}). Usando fallback (Média).")
            # Fallback de emergência: média dos últimos 3 meses ou total
            fallback_val = ts_data.tail(3).mean() if n_samples >= 3 else ts_data.mean()
            forecast_values = [max(0, fallback_val)] * months_to_predict

        # 4. FORMATAR RESPOSTA
        result_list = []

        # a) Histórico
        for date_idx, val in ts_data.items():
            result_list.append({
                "date": date_idx.strftime("%Y-%m"),
                "value": float(val),
                "type": "history"
            })

        # b) Previsão
        last_date = ts_data.index[-1]
        for i, val in enumerate(forecast_values):
            future_date = last_date + relativedelta(months=i+1)
            # Garantir não negativo
            final_val = max(0, float(val))
            
            result_list.append({
                "date": future_date.strftime("%Y-%m"),
                "value": final_val,
                "type": "forecast"
            })
            
        logger.info(f"Forecast: Sucesso. Gerados {len(result_list)} pontos.")
        return result_list

    except Exception as e:
        logger.error(f"Erro crítico no Forecast: {str(e)}")
        import traceback
        traceback.print_exc()
        return [{"error": f"Erro interno: {str(e)}"}]
