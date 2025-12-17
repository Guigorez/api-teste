import pandas as pd
import os
import warnings

warnings.filterwarnings('ignore')

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getcwd()
# Arquivo Atom fornecido pelo usuário
ARQUIVO_ATOM = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'Atom', 'Base de Dados Novoon - Atom.xlsx')

# Arquivo consolidado gerado pelo unificar_planilhas_nv.py
ARQUIVO_VENDAS = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas', 'novoon_consolidado_geral.csv')

# Saída
PASTA_SAIDA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas atom')
ARQUIVO_FINAL = 'novoon_conciliado_geral.csv'

def normalizar_id(series):
    """Remove zeros à esquerda, espaços e converte para string para facilitar o match"""
    return series.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

def processar_atom():
    print("="*80)
    print("PROCESSANDO CONCILIAÇÃO ATOM NOVOON...")
    print("="*80)

    if not os.path.exists(ARQUIVO_ATOM):
        print(f"❌ Arquivo Atom não encontrado: {ARQUIVO_ATOM}")
        return

    if not os.path.exists(ARQUIVO_VENDAS):
        print(f"❌ Arquivo de Vendas Consolidado não encontrado: {ARQUIVO_VENDAS}")
        return

    try:
        # 1. Ler Atom
        print("   Lendo base Atom...")
        df_atom = pd.read_excel(ARQUIVO_ATOM)
        # Tenta identificar a coluna de ID do Pedido no Atom
        col_id_atom = None
        for col in df_atom.columns:
            if 'pedido' in col.lower() or 'order' in col.lower() or 'id' in col.lower():
                col_id_atom = col
                break
        
        if not col_id_atom:
            # Fallback: tenta pegar a primeira coluna
            col_id_atom = df_atom.columns[0]
            print(f"   ⚠️ Coluna de ID não identificada automaticamente. Usando a primeira: '{col_id_atom}'")
        else:
            print(f"   Coluna ID Atom identificada: '{col_id_atom}'")

        df_atom['id_match'] = normalizar_id(df_atom[col_id_atom])

        # 2. Ler Vendas Consolidadas
        print("   Lendo vendas consolidadas...")
        df_vendas = pd.read_csv(ARQUIVO_VENDAS, dtype={'Id do Pedido Unificado': str})
        
        if 'Id do Pedido Unificado' not in df_vendas.columns:
            print("❌ Coluna 'Id do Pedido Unificado' não encontrada no consolidado.")
            return

        df_vendas['id_match'] = normalizar_id(df_vendas['Id do Pedido Unificado'])

        # 3. Merge (Left Join: Mantém todas as vendas, traz dados do Atom onde der match)
        print("   Cruzando dados...")
        # Renomeia colunas do Atom para evitar colisão, exceto a chave
        cols_atom = [c for c in df_atom.columns if c != 'id_match']
        df_atom_clean = df_atom[cols_atom].add_prefix('ATOM_')
        df_atom_clean['id_match'] = df_atom['id_match'] # Devolve a chave

        df_final = pd.merge(df_vendas, df_atom_clean, on='id_match', how='left')

        # Remove a coluna auxiliar de match
        df_final.drop(columns=['id_match'], inplace=True)

        # 4. Salvar
        if not os.path.exists(PASTA_SAIDA):
            os.makedirs(PASTA_SAIDA)
        
        caminho_saida = os.path.join(PASTA_SAIDA, ARQUIVO_FINAL)
        df_final.to_csv(caminho_saida, index=False, encoding='utf-8-sig')

        # 5. Resumo
        total = len(df_final)
        com_match = df_final['ATOM_' + col_id_atom].notna().sum()
        sem_match = total - com_match

        print(f"\n✅ CONCILIAÇÃO CONCLUÍDA!")
        print(f"   - Arquivo salvo: {caminho_saida}")
        print(f"   - Total de Vendas: {total}")
        print(f"   - Conciliados com Atom: {com_match} ({(com_match/total)*100:.1f}%)")
        print(f"   - Sem correspondência: {sem_match}")
        print("="*80)

    except Exception as e:
        print(f"❌ Erro crítico na conciliação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    processar_atom()
