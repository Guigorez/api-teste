import pandas as pd
import logging
from .database import get_db_connection

logger = logging.getLogger(__name__)

def calculate_market_risk(company='animoshop', start_date=None, end_date=None, source=None, marketplace=None):
    """
    Calcula o Risco de Concentração de Mercado (HHI) e Simulação de Impacto.
    
    Lógica Econômica:
    - HHI (Herfindahl-Hirschman Index): Soma dos quadrados dos market shares.
    - Classificação (DoJ/CADE):
        < 1500: Baixo
        1500-2500: Moderado
        > 2500: Alto
        
    Simulação:
    - Estima perda de receita se o canal dominante for bloqueado.
    """
    try:
        from .routes import get_filtered_query
        
        # 1. Obter Dados Base (Todas as vendas para calcular share real)
        # Usamos uma janela de 12 meses idealmente para "Risco Anual", 
        # mas aqui usaremos o dataset total disponível para ser consistente com a base.
        # Poderíamos filtrar last 365 days se quiséssemos precisão de "Anual".
        # Vamos assumir o período total filtrado (ou últimos 12 meses se não houver filtro na função).
        # Para ser mais útil "Anualmente", vamos forçar um filtro de 1 ano atrás?
        # O prompt diz "Busque o faturamento total...". Vamos usar o total disponível.
        
        base_query, params, _ = get_filtered_query(company, start_date, end_date, source, marketplace)
        conn = get_db_connection(company)
        
        if not base_query:
            conn.close()
            return {"status": "error", "message": "Sem dados."}
            
        params['company'] = company
        query = f"""
            SELECT marketplace, SUM(faturamento) as revenue
            FROM ({base_query})
            WHERE faturamento > 0
            GROUP BY marketplace
            ORDER BY revenue DESC
        """
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            return {"status": "error", "message": "Sem faturamento registrado."}
            
        # 2. Métricas Básicas
        total_revenue = df['revenue'].sum()
        hhi_score = 0
        distribution = []
        
        df['share'] = df['revenue'] / total_revenue
        df['share_pct'] = df['share'] * 100
        
        # 3. Cálculo HHI
        for _, row in df.iterrows():
            s_pct = row['share_pct']
            hhi_score += s_pct ** 2
            
            distribution.append({
                "marketplace": row['marketplace'],
                "revenue": float(row['revenue']),
                "share_percentage": round(s_pct, 2)
            })
            
        # 4. Classificação de Risco (DoJ/CADE)
        hhi_score = round(hhi_score, 0)
        
        if hhi_score < 1500:
            risk_level = "Baixo"
            risk_desc = "Portfólio diversificado. Baixo risco estrutural."
            color = "green"
        elif hhi_score <= 2500:
            risk_level = "Moderado"
            risk_desc = "Concentração moderada. Atenção recomendada."
            color = "yellow"
        else:
            risk_level = "Alto"
            risk_desc = "Alta concentração. Vulnerabilidade crítica a bloqueios."
            color = "red"
            
        # 5. Simulação "O Que Acontece Se..." (Impacto do Líder)
        dominant = df.iloc[0]
        dominant_name = dominant['marketplace']
        loss_amount = dominant['revenue']
        loss_share = dominant['share_pct']
        
        simulation_message = (
            f"Se o {dominant_name} fosse bloqueado hoje, sua operação perderia "
            f"aproximadamente {loss_share:.1f}% da receita bruta "
            f"(R$ {loss_amount:,.2f} no período analisado)."
        )

        return {
            "status": "success",
            "company": company,
            "metrics": {
                "hhi_score": hhi_score,
                "risk_level": risk_level,
                "risk_color": color,
                "risk_description": risk_desc,
                "total_revenue": float(round(total_revenue, 2))
            },
            "simulation": {
                "scenario": f"Bloqueio do {dominant_name}",
                "revenue_at_risk": float(round(loss_amount, 2)),
                "impact_description": simulation_message
            },
            "distribution": distribution
        }

    except Exception as e:
        logger.error(f"Erro em calculate_market_risk: {e}")
        return {"status": "error", "message": str(e)}
