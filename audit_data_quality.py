import pandas as pd
from sqlalchemy import create_engine, inspect
import os
import sys

# Ajuste para garantir encoding correto no terminal Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def audit_database():
    print("\n🕵️  INICIANDO AUDITORIA DE DADOS (QA ENGINEER MODE)\n" + "="*80)
    
    # 1. Configurar Conexão
    db_path = "vendas_animoshop.db"
    full_path = os.path.join(os.getcwd(), db_path)
    
    if not os.path.exists(full_path):
        print(f"❌ Erro Crítico: Banco de dados '{db_path}' não encontrado em {os.getcwd()}.")
        return

    connection_string = f"sqlite:///{db_path}"
    try:
        engine = create_engine(connection_string)
        inspector = inspect(engine)
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return

    # 2. Identificar Tabela Principal
    tables = inspector.get_table_names()
    print(f"📋 Tabelas encontradas: {tables}")
    
    target_table = None
    max_rows = -1
    
    # Priority check: look for consolidated tables
    candidates = [t for t in tables if 'consolidado' in t]
    
    if candidates:
        # Pick the one that seems 'geral' or first available
        if 'animoshop_consolidado_geral' in candidates:
             target_table = 'animoshop_consolidado_geral'
        else:
             target_table = candidates[0]
    else:
        # Fallback: Find largest table by row count
        print("   ⚠️ Nenhuma tabela 'consolidado' explícita. Buscando a maior...")
        for t in tables:
            try:
                with engine.connect() as conn:
                    # SQLite count is fast-ish
                    count = conn.execute(pd.io.sql.text(f"SELECT COUNT(*) FROM {t}")).scalar()
                    # print(f"   - {t}: {count} linhas")
                if count > max_rows:
                    max_rows = count
                    target_table = t
            except Exception as e:
                print(f"   Erro ao ler {t}: {e}")
                continue

    if not target_table:
        print("❌ Nenhuma tabela válida encontrada para auditoria.")
        return

    print(f"🎯 Tabela Selecionada para Auditoria: '{target_table}'")
    
    # Carregar Dados
    print("⏳ Carregando dados para memória (Pandas)...")
    try:
        # Determine columns first to be efficient? No, load all for full audit.
        df = pd.read_sql(f"SELECT * FROM {target_table}", engine)
    except Exception as e:
        print(f"❌ Erro ao ler tabela: {e}")
        return

    total_rows = len(df)
    print(f"📊 Total de Linhas: {total_rows:,}")
    
    if total_rows == 0:
        print("❌ Tabela vazia. Auditoria abortada.")
        return

    # Normalize columns to lowercase for easier checking
    df.columns = [c.lower().strip().replace(' ', '_').replace('/', '_') for c in df.columns]
    
    # --- AUDITORIA 1: CHECK FORECAST (DATA) ---
    print("\n1️⃣  Check Forecast (Série Temporal)")
    col_data = 'data_filtro'
    
    if col_data in df.columns:
        df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
        valid_dates_count = df[col_data].notnull().sum()
        pct_valid_dates = (valid_dates_count / total_rows) * 100
        
        status_date = "✅" if pct_valid_dates > 99.9 else "⚠️" if pct_valid_dates > 95 else "❌"
        print(f"   {status_date} Datas Válidas: {pct_valid_dates:.2f}% ({total_rows - valid_dates_count} nulos)")
    else:
        print(f"   ❌ Coluna '{col_data}' não encontrada!")
        pct_valid_dates = 0

    # --- AUDITORIA 2: CHECK RISCO (MARKETPLACE) ---
    print("\n2️⃣  Check Risco (HHI/Marketplace)")
    col_mkt = 'marketplace'
    normalized_mkts_ok = False
    
    if col_mkt.lower() in df.columns:
        mkts = df[col_mkt].dropna().astype(str)
        unique_raw = mkts.unique()
        unique_norm = mkts.str.lower().str.strip().unique()
        
        print(f"   ℹ️  Valores únicos ({len(unique_raw)}): {list(unique_raw)[:10]}...")
        
        if len(unique_raw) != len(unique_norm):
            print("   ❌ ALERT: Duplicatas 'sujas' encontradas (Ex: 'Amazon' vs 'amazon ').")
        else:
            print("   ✅ Normalização OK.")
            normalized_mkts_ok = True
    else:
        print("   ❌ Coluna de Marketplace não encontrada.")

    # --- AUDITORIA 3: CHECK BUNDLES (IDS) ---
    print("\n3️⃣  Check Bundles (Rastreabilidade)")
    col_id = 'id_do_pedido_unificado'
    pct_traceability = 0
    
    if col_id in df.columns:
        # Preenche nulos e conta vazios
        # IDs podem ser string ou numero
        valid_ids = df[col_id].notnull() & (df[col_id] != '')
        # Check string empty if object
        if df[col_id].dtype == object:
             valid_ids = valid_ids & (df[col_id].astype(str).str.strip() != '')
             
        count_valid_ids = valid_ids.sum()
        pct_traceability = (count_valid_ids / total_rows) * 100
        
        status_id = "✅" if pct_traceability >= 90 else "❌"
        print(f"   {status_id} IDs Preenchidos: {pct_traceability:.1f}% ({total_rows - count_valid_ids} gaps)")
        
        if pct_traceability < 90:
            print("      ⚠️ Crítico: FPGrowth/Associações serão pouco representativos.")
    else:
        print(f"   ❌ Coluna '{col_id}' não encontrada!")

    # --- AUDITORIA 4: CHECK ELASTICIDADE (PREÇOS) ---
    print("\n4️⃣  Check Elasticidade (Qualidade Numérica)")
    col_rev = 'faturamento'
    col_qty = 'contagem_pedidos'
    
    zeros_found = 0
    
    for c in [col_rev, col_qty]:
        if c in df.columns:
            # Check <= 0
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            zeros = (df[c] <= 0).sum()
            status_num = "✅" if zeros == 0 else "⚠️"
            print(f"   {status_num} {c}: {zeros} linhas com valor <= 0")
            zeros_found += zeros
        else:
            print(f"   ❌ Coluna '{c}' ausente.")
            
    # Check Division by Zero implications
    # Elasticity uses calculated price
    
    # RELATÓRIO FINAL
    print("\n" + "="*80)
    print("[AUDITORIA DE DADOS - RESULTADOS]")
    print("-" * 35)
    
    # 1. Datas
    if pct_valid_dates > 99.5:
        print("✅ Datas: 100% válidas (Forecast OK)")
    else:
        print("❌ Datas: Problemas de qualidade (Forecast em risco)")
        
    # 2. Marketplaces
    if normalized_mkts_ok:
        print("✅ Marketplaces: consistentes (Risco HHI OK)")
    else:
        print("⚠️ Marketplaces: precisam de normalização (HHI pode estar fragmentado)")
        
    # 3. IDs
    if pct_traceability >= 90:
        print(f"✅ IDs de Pedido: {pct_traceability:.1f}% rastreáveis (Bundles OK)")
    else:
        print(f"❌ IDs de Pedido: Insuficientes ({pct_traceability:.1f}%). Bundles comprometido.")
        
    # 4. Preços
    if zeros_found < (total_rows * 0.05): # Less than 5% problem
        print(f"✅ Preços: Base majoritariamente saudável ({zeros_found} issues)")
    else:
        print(f"⚠️ Preços: Muitos valores zerados/negativos ({zeros_found}). Elasticidade pode falhar.")

    print("="*80 + "\n")

if __name__ == "__main__":
    audit_database()
