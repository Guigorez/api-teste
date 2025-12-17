import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def perform_clustering_from_df(product_stats):
    """
    Executa o clustering K-Means a partir de um DataFrame JÁ AGREGADO.
    Esperado: df com colunas ['produto', 'faturamento', 'lucro', 'quantidade']
    """
    # Padroniza colunas para o código abaixo
    # No SQL renomeamos para 'lucro', mas o codigo original usava 'lucro_liquido'
    if 'lucro' in product_stats.columns:
        product_stats = product_stats.rename(columns={'lucro': 'lucro_liquido'})
        
    if product_stats.empty:
        return []

    # Filtra produtos com faturamento zero ou negativo para não sujar a análise
    product_stats = product_stats[product_stats['faturamento'] > 0]
    
    if len(product_stats) < 4:
        # Se tiver menos produtos que clusters, não dá pra rodar KMeans
        return []

    # 3. Preparação para ML (StandardScaler)
    scaler = StandardScaler()
    X = product_stats[['faturamento', 'lucro_liquido']].values
    X_scaled = scaler.fit_transform(X)

    # 4. Aplicar K-Means (k=4)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    product_stats['cluster'] = clusters
    
    # 5. Nomeação Dinâmica dos Clusters (Centróides)
    # Calcula a média real (não normalizada) de cada cluster
    cluster_centers = product_stats.groupby('cluster')[['faturamento', 'lucro_liquido']].mean()
    
    # Médias globais para comparação
    avg_revenue = product_stats['faturamento'].mean()
    avg_profit = product_stats['lucro_liquido'].mean()
    
    cluster_labels = {}
    
    for cluster_id in range(4):
        center_rev = cluster_centers.loc[cluster_id, 'faturamento']
        center_prof = cluster_centers.loc[cluster_id, 'lucro_liquido']
        
        is_high_rev = center_rev >= avg_revenue
        is_high_prof = center_prof >= avg_profit
        
        if is_high_rev and is_high_prof:
            label = "Campeões"
            color = "#10B981" # Green
        elif is_high_rev and not is_high_prof:
            label = "Volumosos"
            color = "#3B82F6" # Blue
        elif not is_high_rev and is_high_prof:
            label = "Oportunidades"
            color = "#F59E0B" # Yellow
        else:
            label = "Abaixo da Média"
            color = "#9CA3AF" # Gray
            
        cluster_labels[cluster_id] = {'label': label, 'color': color}

    # 6. Formatar Saída
    output = []
    for _, row in product_stats.iterrows():
        cluster_info = cluster_labels[row['cluster']]
        output.append({
            "product": row['produto'],
            "revenue": row['faturamento'],
            "profit": row['lucro_liquido'],
            "cluster": cluster_info['label'],
            "color": cluster_info['color']
        })
        
    # Ordenar por Faturamento Decrescente
    output.sort(key=lambda x: x['revenue'], reverse=True)
    
    return {
        "data": output,
        "averages": {
            "revenue": avg_revenue,
            "profit": avg_profit
        }
    }

def perform_clustering(start_date=None, end_date=None, source=None, marketplace=None, company='animoshop'):
    """Deprecated: Use perform_clustering_from_df inves disso."""
    # Mantendo apenas para retrocompatibilidade se algo chamar, mas vai quebrar se get_all_sales_data não existir
    # Melhor jogar erro se for chamado
    raise NotImplementedError("Use perform_clustering_from_df com dados agregados.")
