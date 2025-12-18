import pandas as pd

def calculate_bundles(company='animoshop', min_lift=1.1, min_confidence=0.3):
    from .routes import get_filtered_query
    try:
        from mlxtend.frequent_patterns import fpgrowth, association_rules
        from mlxtend.preprocessing import TransactionEncoder
    except ImportError:
        print("Erro: mlxtend não instalado.")
        return []

    
    # 1. Obter dados
    base_query, params, conn = get_filtered_query(company)
    if not base_query: return []
    
    # Busca apenas colunas necessárias para minimizar tráfego e uso de memória
    query = f"""
        SELECT produto, id_do_pedido_unificado
        FROM ({base_query})
        WHERE id_do_pedido_unificado IS NOT NULL 
          AND id_do_pedido_unificado != ''
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if df.empty or 'produto' not in df.columns:
        return []

    # 2. Agrupa Transações por ID Real
    # Agrupa produtos por pedido (Cesta de Compras)
    transactions = df.groupby(['id_do_pedido_unificado'])['produto'].apply(list).tolist()
    
    # Filtra transações com < 2 itens (não gera regra, pois precisamos de par para associar)
    transactions = [t for t in transactions if len(t) >= 2]
    
    # Validação mínima de volume
    if len(transactions) < 5:
        return [] # Sem dados suficientes para análise estatística
        
    # 3. One-Hot Encoding
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_trans = pd.DataFrame(te_ary, columns=te.columns_)
    
    # 4. Frequent Itemsets (FPGrowth)
    # min_support=0.01 (1%) -> Filtra ruído e foca em padrões recorrentes reais
    frequent_itemsets = fpgrowth(df_trans, min_support=0.01, use_colnames=True)
    
    if frequent_itemsets.empty:
        return []
        
    # 5. Association Rules
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
    
    # Filtra confiança
    rules = rules[rules['confidence'] >= min_confidence]
    
    # Ordena por Lift
    # Ordena por Lift e limita a 50 melhores para não quebrar o frontend
    rules = rules.sort_values(by='lift', ascending=False).head(50)
    
    # Formata output para JSON
    results = []
    for _, row in rules.iterrows():
        antecedents = list(row['antecedents'])
        consequents = list(row['consequents'])
        
        # Gera frase de recomendação
        rec_text = f"Quem compra {', '.join(antecedents)} tem alta chance de levar {', '.join(consequents)}"
        
        results.append({
            "antecedents": antecedents,
            "consequents": consequents,
            "support": round(row['support'], 4),
            "confidence": round(row['confidence'], 4),
            "lift": round(row['lift'], 4),
            "recommendation": rec_text
        })
        
    return results
