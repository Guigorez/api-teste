import pandas as pd
import numpy as np
import statsmodels.api as sm
import logging

# Configuração de Logger
logger = logging.getLogger(__name__)

def calculate_elasticity(product_name: str, company='animoshop'):
    """
    Calcula a Elasticidade-Preço da Demanda usando Modelo Log-Log.
    Ln(Q) = alpha + beta * Ln(P)
    
    Retorna:
    - Elasticidade (beta)
    - Intervalos de Confiança (95%)
    - Projeção de Receita
    """
    try:
        # Importação local para evitar ciclo
        from .routes import get_filtered_query
        
        # 1. OBTER DADOS
        base_query, params, conn = get_filtered_query(company)
        if not base_query:
            return None
            
        try:
            # Busca dados: precisa de preço e quantidade
            # Se não tiver preço explicito, calcula.
            params['product_name'] = product_name
            query = f"""
                SELECT data_filtro, faturamento, contagem_pedidos, produto
                FROM ({base_query})
                WHERE produto = :product_name
            """
            df_prod = pd.read_sql_query(query, conn, params=params)
        finally:
            conn.close()

        if df_prod.empty:
            return None

        # Garante colunas
        if 'preco_unitario' not in df_prod.columns:
            # Evita divisão por zero
            df_prod['preco_unitario'] = df_prod['faturamento'] / df_prod['contagem_pedidos'].replace(0, 1)

        # 2. PRÉ-PROCESSAMENTO & AGRUPAMENTO
        # Agrupa por preço para reduzir ruído de datas. 
        # (Ou por dia/semana se quisermos considerar sazonalidade temporal, mas log-log simples direto PxQ é padrão MVP)
        # Vamos agrupar por Preço Arredondado para dar 'peso' aos price points.
        
        if 'data_filtro' in df_prod.columns:
             # Agrupa por DIA primeiro para ter observações independentes
            grp = df_prod.groupby('data_filtro').agg({
                'preco_unitario': 'mean',
                'contagem_pedidos': 'sum'
            }).reset_index()
        else:
            grp = df_prod.groupby('preco_unitario')['contagem_pedidos'].sum().reset_index()

        # Filtra dados inválidos para Log (Qtd > 0 e Preço > 0)
        grp = grp[(grp['contagem_pedidos'] > 0) & (grp['preco_unitario'] > 0)].copy()
        
        # Remove outliers extremos se necessário (opcional, por enquanto mantemos tudo)
        
        # Validação de Dados Mínimos
        if len(grp) < 5 or grp['preco_unitario'].std() == 0:
            return {
                "status": "insufficient_data",
                "message": "Dados insuficientes ou sem variação de preço para cálculo estatístico."
            }

        # 3. TRANSFORMAÇÃO LOG-LOG
        grp['log_price'] = np.log(grp['preco_unitario'])
        grp['log_qty'] = np.log(grp['contagem_pedidos'])
        
        # 4. MODELAGEM OLS (STATSMODELS)
        X = grp[['log_price']]
        X = sm.add_constant(X) # Adiciona intercepto (alpha)
        y = grp['log_qty']
        
        # Fit Modelo
        model = sm.OLS(y, X).fit()
        
        # Extrai Coeficientes
        intercept_log = model.params['const']
        elasticity = model.params['log_price'] # Beta
        r_squared = model.rsquared
        
        # Validação R2
        if r_squared < 0.3:
            return {
                "status": "inconclusive",
                "message": f"Baixa correlação detectada (R² = {r_squared:.2f}). O preço não parece explicar a demanda.",
                "r_squared": r_squared
            }
            
        # 5. GERAR DADOS PARA GRÁFICO (COM INTERVALO DE CONFIANÇA)
        curr_price = grp['preco_unitario'].mean()
        min_p = curr_price * 0.5
        max_p = curr_price * 1.5
        
        sim_prices = np.linspace(min_p, max_p, 20)
        
        # Predição com Intervalo de Confiança
        # Precisamos criar um DataFrame exog para predição
        df_pred = pd.DataFrame({'log_price': np.log(sim_prices)})
        df_pred = sm.add_constant(df_pred, has_constant='add')
        
        predictions = model.get_prediction(df_pred)
        pred_summary = predictions.summary_frame(alpha=0.05) # 95% CI
        
        # Converte de volta de Log para Escala Real (exp)
        pred_qty = np.exp(pred_summary['mean'])
        pred_qty_lower = np.exp(pred_summary['obs_ci_lower']) # Intervalo de predição (obs) é mais amplo que conf média
        pred_qty_upper = np.exp(pred_summary['obs_ci_upper'])
        
        chart_data = []
        
        for i, p in enumerate(sim_prices):
            q_mean = pred_qty[i]
            q_low = pred_qty_lower[i]
            q_high = pred_qty_upper[i]
            
            # Receita Projetada
            rev_mean = p * q_mean
            rev_low = p * q_low
            rev_high = p * q_high
            
            chart_data.append({
                "price": round(float(p), 2),
                "demand_qty": round(float(q_mean), 2),
                "demand_qty_lower": round(float(q_low), 2),
                "demand_qty_upper": round(float(q_high), 2),
                "projected_revenue": round(float(rev_mean), 2),
                "projected_revenue_lower": round(float(rev_low), 2),
                "projected_revenue_upper": round(float(rev_high), 2)
            })
            
        # 6. INTERPRETAÇÃO E RETORNO
        elasticity_label = "Elástico" if elasticity < -1 else ("Inelástico" if elasticity < 0 else "Anômalo (+)")
        
        # Ponto Ótimo de Receita (Elasticidade = -1)
        # Em log-log constante, a elasticidade é constante.
        # Se E < -1, diminuir preço aumenta receita. Se E > -1, aumentar preço aumenta receita.
        # Não há um "pico" global a menos que E varie. Mas no chart_data vemos o comportamento local.
        
        # Sugestão Simples baseada no Chart Data máximo
        max_rev_idx = np.argmax([c['projected_revenue'] for c in chart_data])
        opt_price_sim = chart_data[max_rev_idx]['price']
        
        result = {
            "status": "success",
            "product_name": product_name,
            "current_avg_price": round(float(curr_price), 2),
            "elasticity": round(float(elasticity), 2),
            "elasticity_status": elasticity_label,
            "r_squared": round(r_squared, 4),
            "optimal_price_suggestion": opt_price_sim,
            "chart_data": chart_data
        }
        
        logger.info(f"Elasticidade calculada para {product_name}: E={elasticity:.2f}, R2={r_squared:.2f}")
        return result

    except Exception as e:
        logger.error(f"Erro Elasticidade: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error", 
            "message": str(e)
        }
