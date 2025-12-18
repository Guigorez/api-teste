import pandas as pd
import numpy as np
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

# Configuração de Logger
logger = logging.getLogger(__name__)

def generate_forecast(company='animoshop', periods_to_predict=12, granularity='weekly'):
    """
    Gera Projeção de Faturamento com Granularidade Dinâmica.
    
    Args:
        periods_to_predict (int): Número de períodos futuros (semanas ou meses).
        granularity (str): 'weekly' (Semanal) ou 'monthly' (Mensal).
    
    Lógica Financeira:
    - Semanal ('weekly'): Resample W-MON, Sazonalidade 52. Ideal para fluxo de caixa curto prazo.
    - Mensal ('monthly'): Resample ME, Sazonalidade 12. Ideal para orçamento anual.
    - Incerteza: Intervalo_t = 1.96 * StdDev * sqrt(t).
    """
    try:
        # Importação tardia
        from .routes import get_filtered_query
        
        # 1. OBTER DADOS (Faturamento > 0)
        base_query, params, conn = get_filtered_query(company, source='limpas')
        if not base_query: return []

        query = f"SELECT data_filtro, faturamento FROM ({base_query}) WHERE faturamento > 0"
        df_raw = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df_raw.empty: return []

        # 2. PRÉ-PROCESSAMENTO & RESAMPLE
        df_raw['data_filtro'] = pd.to_datetime(df_raw['data_filtro'])
        
        # Lógica de Granularidade
        resample_rule = 'W-MON'
        seasonal_periods = 52
        min_history_seasonal = 52     # Mínimo para tentar Sazonalidade (idealmente 2x, mas 1x abre a chance)
        min_history_trend = 12        # Mínimo para Tendência
        
        if granularity == 'monthly':
            resample_rule = 'ME'         # Month End
            seasonal_periods = 12
            min_history_seasonal = 24    # Mensal requer 2 anos para sazonalidade robusta
            min_history_trend = 6        # 6 meses para tendência
        
        # Agrupa e preenche buracos com 0
        df_grouped = df_raw.set_index('data_filtro').resample(resample_rule)['faturamento'].sum().fillna(0)
        
        # Remove período pré-operacional (zeros iniciais)
        if not df_grouped.empty:
            first_valid = df_grouped.gt(0).idxmax()
            if df_grouped[first_valid] > 0:
                df_grouped = df_grouped.loc[first_valid:]

        n_obs = len(df_grouped)
        logger.info(f"Forecast {granularity}: {n_obs} observações históricas.")
        
        if n_obs < 4:
            return [{"error": f"Dados insuficientes ({n_obs} obs, mínimo 4)."}]

        # 3. MODELAGEM (Seleção Automática)
        forecast_values = []
        resid_std = 0
        model_name = ""
        
        try:
            ts_data = df_grouped
            
            # Escolha do Modelo Adaptativa
            if n_obs >= min_history_seasonal:
                model_name = f"Holt-Winters ({granularity})"
                model = ExponentialSmoothing(
                    ts_data,
                    trend='add',
                    seasonal='add',
                    seasonal_periods=seasonal_periods, 
                    initialization_method="estimated"
                )
            elif n_obs >= min_history_trend:
                model_name = f"Holt Linear ({granularity})"
                model = ExponentialSmoothing(
                    ts_data,
                    trend='add',
                    seasonal=None,
                    initialization_method="estimated"
                )
            else:
                model_name = "Simple Custom"
                model = SimpleExpSmoothing(
                    ts_data,
                    initialization_method="estimated"
                )

            # Fit
            fitted_model = model.fit()
            
            # Previsão Central
            forecast_result = fitted_model.forecast(periods_to_predict)
            forecast_values = forecast_result.tolist()
            
            # Cálculo do Risco
            residuals = fitted_model.resid
            resid_std = np.std(residuals)
            
            if resid_std == 0:
                resid_std = df_grouped.mean() * 0.05

        except Exception as e:
            logger.warning(f"Erro Modelagem ({model_name}): {e}. Usando Média Móvel Fallback.")
            model_name = "Fallback AVG"
            avg_last_4 = df_grouped.tail(4).mean()
            forecast_values = [avg_last_4] * periods_to_predict
            resid_std = df_grouped.tail(4).std()
            if np.isnan(resid_std) or resid_std == 0:
                resid_std = avg_last_4 * 0.1

        # 4. CONSTRUÇÃO DO RETORNO JSON
        final_list = []
        
        # A) Histórico
        for date_idx, val in df_grouped.items():
            final_list.append({
                "date": date_idx.strftime("%Y-%m-%d"),
                "revenue_real": float(val),
                "revenue_forecast": None,
                "revenue_lower": None,
                "revenue_upper": None,
                "type": "history"
            })
            
        # B) Previsão
        last_date = df_grouped.index[-1]
        
        for i, val_central in enumerate(forecast_values):
            # Avança a data conforme granularidade
            step_count = i + 1
            if granularity == 'monthly':
                future_date = last_date + relativedelta(months=step_count)
                # Ajusta para final do mês se a série original for ME
                # relativedelta preserva dia, mas pd.resample('ME') joga para ultimo dia.
                # Vamos apenas somar mês a mês.
                # Melhor: usar DateOffset do pandas se quiser precisão, ou relativedelta.
                # pd resample ME dates are like 2023-01-31. +1 month -> 2023-02-28?
                future_date = future_date + relativedelta(day=31) # força final do mes
            else:
                future_date = last_date + pd.Timedelta(weeks=step_count)
            
            # Fórmula de Risco: 1.96 * Std * sqrt(t)
            margin = 1.96 * resid_std * np.sqrt(step_count)
            
            val_central = max(0, float(val_central))
            val_lower = max(0, val_central - margin)
            val_upper = val_central + margin
            
            final_list.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "revenue_real": None,
                "revenue_forecast": round(val_central, 2),
                "revenue_lower": round(val_lower, 2),
                "revenue_upper": round(val_upper, 2),
                "type": "forecast"
            })
            
        logger.info(f"Forecast {granularity} generated ({model_name}). Steps={periods_to_predict}")
        return final_list

    except Exception as e:
        logger.error(f"Erro Forecast Critical: {e}")
        import traceback
        traceback.print_exc()
        return [{"error": str(e)}]
