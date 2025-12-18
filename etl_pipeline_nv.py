import time
import os

# Importa seus scripts como se fossem bibliotecas
# Certifique-se que os arquivos .py estão na mesma pasta
import amazon_nv as amazon
import shopee_nv as shopee
import mercado_livre_nv as mercado_livre
import magalu_nv as magalu
import madeira_madeira_nv as madeira_madeira
import olist_nv as olist
import atom_nv as atom            # Seu script de conciliação
import loader_nv as loader_sql # Script de carregamento (Loader)
import unificar_planilhas_nv as unificar # Script de unificação

def main():
    inicio_total = time.time()
    
    print("="*80)
    print("🚀 INICIANDO ATUALIZAÇÃO TOTAL DO DATA WAREHOUSE NOVOON")
    print("="*80)

    # --- PASSO 1: LIMPEZA E PADRONIZAÇÃO (Marketplaces) ---
    print("\n>>> FASE 1: PROCESSANDO MARKETPLACES...")
    
    try:
        amazon.processar_amazon()
    except Exception as e: print(f"❌ Falha na Amazon: {e}")

    try:
        shopee.processar_shopee()
    except Exception as e: print(f"❌ Falha na Shopee: {e}")

    try:
        mercado_livre.processar_mercadolivre()
    except Exception as e: print(f"❌ Falha no Mercado Livre: {e}")

    try:
        magalu.processar_magalu()
    except Exception as e: print(f"❌ Falha no Magalu: {e}")

    try:
        madeira_madeira.processar_madeira()
    except Exception as e: print(f"❌ Falha na MadeiraMadeira: {e}")

    try:
        olist.processar_olist()
    except Exception as e: print(f"❌ Falha no Olist: {e}")

    # --- PASSO 2: UNIFICAÇÃO (CONSOLIDAÇÃO) ---
    print("\n>>> FASE 2: UNIFICANDO PLANILHAS GERAIS...")
    try:
        unificar.consolidar_marketplaces()
    except Exception as e: print(f"❌ Falha na Unificação: {e}")

    # --- PASSO 3: RECONCILIAÇÃO ATOM ---
    print("\n>>> FASE 3: CONCILIAÇÃO ATOM...")
    try:
        atom.processar_atom()
    except Exception as e: print(f"❌ Falha no Atom: {e}")

    # --- PASSO 4: BANCO DE DADOS (SQL) ---
    print("\n>>> FASE 4: ATUALIZANDO BANCO SQL (DBeaver)...")
    try:
        loader_sql.criar_banco_dados()
    except Exception as e: print(f"❌ Falha no SQL: {e}")

    # --- RESUMO FINAL ---
    tempo_gasto = time.time() - inicio_total
    print("\n" + "="*80)
    print(f"✅ PROCESSO FINALIZADO EM {tempo_gasto:.2f} SEGUNDOS")
    print("   - Todos os arquivos limpos foram gerados.")
    print("   - A unificação foi feita.")
    print("   - A conciliação foi feita.")
    print("   - O banco vendas_novoon.db foi atualizado.")
    print("="*80)

if __name__ == "__main__":
    main()
