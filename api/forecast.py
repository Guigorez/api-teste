import pandas as pd
import numpy as np
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

# Configuração de Logger
logger = logging.getLogger(__name__)

def generate_forecast(company='animoshop', weeks_to_predict=12):
    """
    Gera previsão de vendas SEMANAL (Weekly Granularity).
    
    NOVA LÓGICA (Varejo Ágil):
    - Granularidade: Semanal (W-MON).
    - Modelos Adaptativos:
      1. Holt-Winters (Sazonal) se >= 52 semanas (1 ano).
      2. Holt Linear (Tendência) se >= 12 semanas.
      3. Média Móvel Exponencial (EMA) se < 12 semanas.
    """
    try:
        # Importação tardia
        from .routes import get_filtered_query
        
        # 1. OBTER DADOS
        base_query, params, conn = get_filtered_query(company, source='limpas')
        if not base_query: return []

        query = f"SELECT data_filtro, faturamento FROM ({base_query}) WHERE faturamento > 0"
        df_raw = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df_raw.empty: return []

        # 2. PRÉ-PROCESSAMENTO & RESAMPLE 'W-MON'
        df_raw['data_filtro'] = pd.to_datetime(df_raw['data_filtro'])
        
        # Agrupa por SEMANA (Começando Segunda-feira)
        # fillna(0) preenche semanas sem vendas com zero (importante para varejo)
        df_weekly = df_raw.set_index('data_filtro').resample('W-MON')['faturamento'].sum().fillna(0)
        
        # Remove zeros do início (antes de começar a operar), mas mantém zeros "reais" (semanas ruins)
        # Acha o primeiro índice com valor > 0
        if not df_weekly.empty:
            first_valid = df_weekly.gt(0).idxmax()
            # Se for tudo zero, first_valid será o primeiro, mas vamos checar
            if df_weekly[first_valid] > 0:
                df_weekly = df_weekly.loc[first_valid:]

        n_weeks = len(df_weekly)
        logger.info(f"Forecast Weekly: {n_weeks} semanas de histórico.")
        
        if n_weeks < 4:
             return [{"error": "Dados insuficientes (mínimo 4 semanas)."}]

        # 3. SELEÇÃO DE MODELO ADAPTATIVO
        forecast_values = []
        model_name = ""
        
        try:
            model = None
            # Adiciona epsilon para estabilidade numérica se houver zeros
            ts_data_safe = df_weekly + 1e-6

            # A) Holt-Winters Sazonal (Requer ~2 ciclos, ou pelo menos 1 ciclo completo sólido)
            # Para 52 semanas, statsmodels pode reclamar se não tiver 2x52. 
            # Mas com initialization_method='estimated' ele tenta.
            # Vamos ser conservadores: HW só com 2 anos (104 semanas)? 
            # O prompt pede 52. Vamos tentar HW com 52.
            if n_weeks >= 52:
                model_name = "Holt-Winters (Seasonal 52)"
                model = ExponentialSmoothing(
                    ts_data_safe,
                    trend='add',
                    seasonal='add',
                    seasonal_periods=52, 
                    initialization_method="estimated"
                )
            
            # B) Holt Linear (Tendência)
            elif n_weeks >= 12:
                model_name = "Holt Linear (Trend)"
                model = ExponentialSmoothing(
                    ts_data_safe,
                    trend='add',
                    seasonal=None,
                    initialization_method="estimated"
                )
                
            # C) Média Móvel Exponencial (Simples)
            else:
                model_name = "Simple EMA"
                model = SimpleExpSmoothing(
                    ts_data_safe,
                    initialization_method="estimated"
                )

            # Fit & Predict
            fitted_model = model.fit()
            forecast_result = fitted_model.forecast(weeks_to_predict)
            forecast_values = forecast_result.tolist()
            
        except Exception as e:
            logger.warning(f"Erro no modelo {model_name}: {e}. Fallback para Média Móvel Simples.")
            # Fallback último recurso
            avg_last_4 = df_weekly.tail(4).mean()
            forecast_values = [max(0, avg_last_4)] * weeks_to_predict

        # 4. FORMATAR RETORNO
        final_list = []
        
        # Histórico
        for date_idx, val in df_weekly.items():
            final_list.append({
                "date": date_idx.strftime("%Y-%m-%d"),
                "value": float(val),
                "type": "history"
            })
            
        # Previsão
        last_date = df_weekly.index[-1]
        for i, val in enumerate(forecast_values):
            future_date = last_date + pd.Timedelta(weeks=i+1)
            final_list.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "value": max(0, float(val)), # Clip 0
                "type": "forecast"
            })
            
        logger.info(f"Forecast Weekly ({model_name}) gerado com sucesso. {len(forecast_values)} semanas futuras.")
        return final_list

    except Exception as e:
        logger.error(f"Erro Forecast Weekly: {e}")
        import traceback
        traceback.print_exc()
        return [{"error": str(e)}]
