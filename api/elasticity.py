import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def calculate_elasticity(product_name: str, company='animoshop'):
    # Importação local para evitar ciclo
    from .routes import get_filtered_query
    
    # 1. Obter dados via SQL (Filtrado pelo produto para eficiência)
    base_query, conn = get_filtered_query(company)
    if not base_query:
        return None
        
    try:
        # Busca apenas colunas necessárias para o produto específico
        query = f"""
            SELECT data_filtro, faturamento, contagem_pedidos, produto
            FROM ({base_query})
            WHERE produto = '{product_name.replace("'", "''")}'
        """
        df_prod = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    if df_prod.empty:
        return None
    
    if df_prod.empty:
        return None
        
    # Garante colunas de Preço Unitário
    # Se não tiver preço unitário explícito, calcula: Faturamento / Qtd
    if 'preco_unitario' not in df_prod.columns:
        # Evita divisão por zero
        df_prod['preco_unitario'] = df_prod['faturamento'] / df_prod['contagem_pedidos'].replace(0, 1)
        
    # 2. Agrupar dados (Agrupa por Data/Periodo para ter variação)
    # Vamos agrupar por Dia para ter pontos de "Preço do Dia" vs "Vendas do Dia"
    if 'data_filtro' in df_prod.columns:
        grp = df_prod.groupby('data_filtro').agg({
            'preco_unitario': 'mean',
            'contagem_pedidos': 'sum'
        }).reset_index()
    else:
        # Fallback se não tiver data, agrupa por preço direto (menos preciso mas funciona)
        grp = df_prod.groupby('preco_unitario')['contagem_pedidos'].sum().reset_index()

    # Filtra outliers extremos de preço (erros de cadastro)
    grp = grp[grp['preco_unitario'] > 0]
    
    # Checa variação de preço
    if grp['preco_unitario'].std() == 0 or len(grp) < 3:
        return {
            "status": "insufficient_data",
            "message": "Variação de preço insuficiente para calcular elasticidade."
        }

    # 3. Regressão Linear (Demanda)
    X = grp[['preco_unitario']]
    y = grp['contagem_pedidos']
    
    model = LinearRegression()
    model.fit(X, y)
    
    slope = model.coef_[0]    # b (Coeficiente angular - deve ser negativo)
    intercept = model.intercept_ # a (Coeficiente linear)
    
    # Se slope for positivo, produto é "Bem de Giffen" ou dados sujos (preço sobe, venda sobe)
    # Assumimos inelasticidade ou anomalia
    if slope >= 0:
        elasticity_status = "Anômalo (Demanda cresce com preço)"
    else:
        elasticity_status = "Normal"

    # 4. Otimização de Receita
    # Receita R(p) = p * (intercept + slope * p) = intercept*p + slope*p^2
    # Vértice de parábola ax^2 + bx + c -> x = -b / 2a
    # Aqui: a = slope, b = intercept
    optimal_price = -intercept / (2 * slope)
    
    current_avg_price = float(grp['preco_unitario'].mean())
    
    # Range de simulação (+/- 50% do preço atual)
    min_sim = current_avg_price * 0.5
    max_sim = current_avg_price * 1.5
    
    sim_prices = np.linspace(min_sim, max_sim, 20)
    chart_data = []
    
    for p in sim_prices:
        p = float(p)
        demand = intercept + slope * p
        revenue = p * demand
        
        # Não faz sentido demanda negativa
        if demand < 0: demand = 0
        if revenue < 0: revenue = 0
            
        chart_data.append({
            "price": round(p, 2),
            "demand_qty": round(demand, 2),
            "projected_revenue": round(revenue, 2)
        })
        
    return {
        "status": "success",
        "product_name": product_name,
        "current_avg_price": round(current_avg_price, 2),
        "optimal_price": round(optimal_price, 2) if slope < 0 else None,
        "elasticity_status": "Elástico" if (slope < 0 and abs(slope * current_avg_price / y.mean()) > 1) else "Inelástico",
        "slope": slope,
        "chart_data": chart_data
    }
