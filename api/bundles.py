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
    base_query, conn = get_filtered_query(company)
    if not base_query: return []
    
    query = f"SELECT * FROM ({base_query})"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty or 'produto' not in df.columns:
        return []

    # Criar ID de Transação Artificial (Marketplace + Data + Hora/Minuto)
    # Se não tiver hora, usa Data. Se tiver Hora, arredonda.
    
    # Garante conversão de data
    if 'data_filtro' not in df.columns:
        # Tenta criar se não existir (muito improvável dado o ETL)
        pass 
        
    df['txn_id'] = df['marketplace'].astype(str) + "_" + df['data_filtro'].astype(str)
    
    # Se tiver hora, refina
    # (Assumindo que talvez não tenhamos hora estruturada em todas as tabelas, vamos usar o que der)
    # Para simplificar e garantir funcionamento, vamos agrupar por DIA por enquanto, 
    # pois "Hora" exata pode não estar limpa em todos os marketplaces consolidados.
    # O ideal seria 'pedido_id', mas o prompt diz que não temos customer ID ou ID unificado confiável.
    # Agrupar por dia pode gerar "cestas" muito grandes (todas vendas do dia), o que pode distorcer.
    # Vamos tentar usar uma coluna de 'hora' se existir, ou 'Numero Pedido' se existir (mas user disse que não confia).
    # O prompt sugere: "Marketplace + Data + Hora (arredonde para minuto)".
    
    time_col = None
    for col in ['Hora', 'hora', 'Horario', 'time']:
        if col in df.columns:
            time_col = col
            break
            
    if time_col:
        # Tenta limpar a hora Para HH:MM
        # Assumindo string HH:MM:SS
        df['txn_time'] = df[time_col].astype(str).str.slice(0, 5) # HH:MM
        df['txn_id'] = df['txn_id'] + "_" + df['txn_time']
    
    # 2. Agrupa Transações
    # List of lists for transaction encoder
    transactions = df.groupby(['txn_id'])['produto'].apply(list).tolist()
    
    # Filtra transações com < 2 itens (não gera regra)
    transactions = [t for t in transactions if len(t) >= 2]
    
    if len(transactions) < 10:
        return [] # Poucas transações multi-item para analise
        
    # 3. One-Hot Encoding
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_trans = pd.DataFrame(te_ary, columns=te.columns_)
    
    # 4. Frequent Itemsets (FPGrowth é mais rápido que Apriori)
    # min_support: produto deve aparecer em pelo menos 0.5% das cestas (ajustável)
    frequent_itemsets = fpgrowth(df_trans, min_support=0.005, use_colnames=True)
    
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
