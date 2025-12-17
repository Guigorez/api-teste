import pandas as pd
import os
import numpy as np

# --- CONFIGURAÇÃO DE CAMINHOS ---
PASTA_ATOM = r'C:\Users\MatheusSampaio\Documents\AnimoShop - Python\Dados\AnimoShop\Atom'
PASTA_MKT_LIMPAS = r'C:\Users\MatheusSampaio\Documents\AnimoShop - Python\Dados\AnimoShop\planilhas limpas'
PASTA_SAIDA = r'C:\Users\MatheusSampaio\Documents\AnimoShop - Python\Dados\AnimoShop\planilhas atom'

COLUNA_ID_ATOM = 'SEUPEDIDO'

POSSIVEIS_IDS_MKT = [
    'Id do Pedido Unificado', 'Nº do pedido', 'ID do pedido', 
    'Order ID', 'order_id', 'Número da operação'
]

MARKETPLACES = ['amazon', 'shopee', 'mercado_livre', 'magalu', 'madeira', 'olist']

def normalizar_id_inteligente(serie, truncar=False):
    """
    Normaliza IDs para comparação, tratando erros de Excel e notação científica.
    """
    # 1. Converte para numérico (Resolve 2.00E+15)
    numeros = pd.to_numeric(serie, errors='coerce')
    
    # 2. Converte para Inteiro (Mata decimais .0)
    inteiros = numeros.astype('Int64')
    
    # 3. Vira Texto (Mantém original se for alfanumérico)
    texto_final = np.where(numeros.notna(), inteiros.astype(str), serie.astype(str))
    series_str = pd.Series(texto_final).str.strip().replace({'<NA>': '', 'nan': ''})
    
    if truncar:
        # CORREÇÃO ML: Pega apenas os primeiros 15 dígitos para ignorar o arredondamento do Excel
        return series_str.apply(lambda x: x[:15] if len(x) >= 16 and x.isdigit() else x)
    
    return series_str

def encontrar_coluna_id(df):
    cols_map = {c.lower().strip().replace('\ufeff', ''): c for c in df.columns}
    for nome_possivel in POSSIVEIS_IDS_MKT:
        if nome_possivel.lower() in cols_map:
            return cols_map[nome_possivel.lower()]
    return None

def encontrar_arquivo(pasta, palavra_chave):
    if not os.path.exists(pasta): return None
    chave = palavra_chave.lower().replace('_', '')
    for arquivo in os.listdir(pasta):
        nome_arq = arquivo.lower()
        if nome_arq.startswith('~$'): continue
        if (chave in nome_arq.replace('_', '') or palavra_chave.lower() in nome_arq):
            return os.path.join(pasta, arquivo)
    return None

def carregar_arquivo_robusto(caminho):
    try:
        if caminho.endswith(('.xlsx', '.xls')):
            return pd.read_excel(caminho)
        else:
            try: return pd.read_csv(caminho, sep=None, engine='python', encoding='utf-8-sig')
            except: return pd.read_csv(caminho, sep=None, engine='python', encoding='latin-1')
    except Exception:
        return None

def processar_conciliacao():
    print("="*80)
    print("RELATÓRIO DE CONCILIAÇÃO (ATOM x MARKETPLACES)")
    print("="*80)

    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)

    for mkt in MARKETPLACES:
        print(f"\n🔍 {mkt.upper()}...", end=" ")

        arq_mkt = encontrar_arquivo(PASTA_MKT_LIMPAS, mkt)
        arq_atom = encontrar_arquivo(PASTA_ATOM, mkt)

        if not arq_mkt: print("⚠️ Arq MKT não achado."); continue
        if not arq_atom: print("⚠️ Arq ATOM não achado."); continue

        df_mkt = carregar_arquivo_robusto(arq_mkt)
        df_atom = carregar_arquivo_robusto(arq_atom)
        
        if df_mkt is None or df_atom is None: print("❌ Erro leitura."); continue

        # Identificar colunas
        col_id_mkt = encontrar_coluna_id(df_mkt)
        if not col_id_mkt: print("❌ Coluna ID MKT sumiu."); continue
            
        col_id_atom_real = None
        cols_atom_map = {c.lower().strip().replace('\ufeff', ''): c for c in df_atom.columns}
        if COLUNA_ID_ATOM.lower() in cols_atom_map:
            col_id_atom_real = cols_atom_map[COLUNA_ID_ATOM.lower()]
        else:
            print(f"❌ Coluna '{COLUNA_ID_ATOM}' não está no Atom."); continue

        # --- CRUZAMENTO ---
        # Ativa truncagem APENAS para Mercado Livre (Correção de Excel)
        modo_truncar = (mkt == 'mercado_livre')

        ids_mkt_comp = normalizar_id_inteligente(df_mkt[col_id_mkt], truncar=modo_truncar)
        ids_atom_comp = normalizar_id_inteligente(df_atom[col_id_atom_real], truncar=modo_truncar)

        mask_conciliado = ids_mkt_comp.isin(ids_atom_comp)
        df_final = df_mkt[mask_conciliado].copy()
        
        # Padroniza nome final
        if col_id_mkt != 'Id do Pedido Unificado':
            df_final.rename(columns={col_id_mkt: 'Id do Pedido Unificado'}, inplace=True)

        # Salvar
        nome_final = f"{mkt}_conciliado.csv"
        caminho_final = os.path.join(PASTA_SAIDA, nome_final)
        df_final.to_csv(caminho_final, index=False, encoding='utf-8-sig', float_format='%.2f')

        total_mkt = len(df_mkt)
        total_ok = len(df_final)
        furo = total_mkt - total_ok
        perc_ok = (total_ok / total_mkt) * 100 if total_mkt > 0 else 0
        
        print(f"✅ OK")
        print(f"   - Total MKT: {total_mkt} | Confirmados Atom: {total_ok} ({perc_ok:.1f}%)")
        
        if furo > 0:
             print(f"   ⚠️ FURO: {furo} pedidos não encontrados no Atom (Verifique se a base Atom está atualizada).")
        else:
             print(f"   ✨ Conciliação Perfeita (100%).")

    print("\n" + "="*80)
    print("PROCESSO FINALIZADO - ARQUIVOS SALVOS EM 'planilhas atom'")
    print("="*80)

if __name__ == "__main__":
    processar_conciliacao()