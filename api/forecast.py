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
    Gera Projeção de Faturamento (12 semanas) com Análise de Risco Analítica.
    
    Lógica Financeira (Especialista):
    - Granularidade: Semanal (W-MON) para Fluxo de Caixa.
    - Modelos: HW (Sazonal), Holt (Tendência), SES (Nível).
    - Risco (Incerteza): Calculado via desvio padrão dos resíduos históricos.
      - Fórmula: Intervalo_t = 1.96 * StdDev * sqrt(t)
      - Onde t é o nº da semana futura (incerteza expande com o tempo).
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

        # 2. PRÉ-PROCESSAMENTO & RESAMPLE 'W-MON'
        df_raw['data_filtro'] = pd.to_datetime(df_raw['data_filtro'])
        
        # Agrupa por Semana (Segunda-feira) e preenche buracos com 0
        df_weekly = df_raw.set_index('data_filtro').resample('W-MON')['faturamento'].sum().fillna(0)
        
        # Remove período pré-operacional (zeros iniciais)
        if not df_weekly.empty:
            first_valid = df_weekly.gt(0).idxmax()
            if df_weekly[first_valid] > 0:
                df_weekly = df_weekly.loc[first_valid:]

        n_weeks = len(df_weekly)
        logger.info(f"Forecast: {n_weeks} semanas de histórico.")
        
        if n_weeks < 4:
            return [{"error": "Dados insuficientes (mínimo 4 semanas)."}]

        # 3. MODELAGEM (Seleção Automática)
        forecast_values = []
        resid_std = 0
        model_name = ""
        
        try:
            # Epsilon para evitar erro log(0) se modelo usar multiplicativo (aqui usamos aditivo, mas bom garantir)
            ts_data = df_weekly
            
            # Escolha do Modelo
            if n_weeks >= 52:
                model_name = "Holt-Winters"
                model = ExponentialSmoothing(
                    ts_data,
                    trend='add',
                    seasonal='add',
                    seasonal_periods=52, 
                    initialization_method="estimated"
                )
            elif n_weeks >= 12:
                model_name = "Holt Linear"
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
            forecast_result = fitted_model.forecast(weeks_to_predict)
            forecast_values = forecast_result.tolist()
            
            # Cálculo do Risco (Desvio Padrão dos Resíduos)
            # Resíduos = Observado - Ajustado
            residuals = fitted_model.resid
            resid_std = np.std(residuals)
            
            # Se resid_std for muito baixo (overfit) ou zero, definimos um piso heurístico (ex: 5% da média)
            if resid_std == 0:
                resid_std = df_weekly.mean() * 0.05

        except Exception as e:
            logger.warning(f"Erro Modelagem ({model_name}): {e}. Usando Média Móvel.")
            model_name = "Fallback AVG"
            
            # Fallback: Média das últimas 4 semanas
            avg_last_4 = df_weekly.tail(4).mean()
            forecast_values = [avg_last_4] * weeks_to_predict
            
            # Risco estimado: Desvio padrão das últimas 4 semanas (ou 10% da média se for constante)
            resid_std = df_weekly.tail(4).std()
            if np.isnan(resid_std) or resid_std == 0:
                resid_std = avg_last_4 * 0.1

        # 4. CONSTRUÇÃO DO RETORNO JSON (Estrutura Financeira)
        final_list = []
        
        # A) Histórico
        for date_idx, val in df_weekly.items():
            final_list.append({
                "date": date_idx.strftime("%Y-%m-%d"),
                "revenue_real": float(val),
                "revenue_forecast": None,
                "revenue_lower": None,
                "revenue_upper": None,
                "type": "history"
            })
            
        # B) Previsão com Intervalo de Confiança Dinâmico
        last_date = df_weekly.index[-1]
        
        for i, val_central in enumerate(forecast_values):
            future_date = last_date + pd.Timedelta(weeks=i+1)
            week_step = i + 1 # t = 1, 2, 3...
            
            # Fórmula do Especialista: Margem = 1.96 * Std * sqrt(t)
            # 1.96 = Z-score para 95% de confiança
            margin = 1.96 * resid_std * np.sqrt(week_step)
            
            val_central = max(0, float(val_central))
            val_lower = max(0, val_central - margin)
            val_upper = val_central + margin # Sem teto (receita pode explodir)
            
            final_list.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "revenue_real": None,
                "revenue_forecast": round(val_central, 2),
                "revenue_lower": round(val_lower, 2),
                "revenue_upper": round(val_upper, 2),
                "type": "forecast"
            })
            
        logger.info(f"Finance Forecast ({model_name}) generated. StdResid={resid_std:.2f}")
        return final_list

    except Exception as e:
        logger.error(f"Erro Forecast Critical: {e}")
        import traceback
        traceback.print_exc()
        return [{"error": str(e)}]
