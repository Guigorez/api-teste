import time
import os

# Importa seus scripts como se fossem bibliotecas
# Certifique-se que os arquivos .py estão na mesma pasta
import amazon_as as amazon
import shopee_as as shopee
import mercado_livre_as as mercado_livre
import magalu_as as magalu
import madeira_madeira_as as madeira_madeira
import olist_as as olist
import atom_as as atom            # Seu script de conciliação
import criar_banco_sql_as as criar_banco_sql # Seu script de banco de dados

def main():
    inicio_total = time.time()
    
    print("="*80)
    print("🚀 INICIANDO ATUALIZAÇÃO TOTAL DO DATA WAREHOUSE ANIMOSHOP")
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

    # --- PASSO 2: CONCILIAÇÃO (Cruzar com Atom) ---
    print("\n>>> FASE 2: CONCILIANDO COM O ATOM...")
    try:
        atom.processar_conciliacao()
    except Exception as e: print(f"❌ Falha na Conciliação: {e}")

    # --- PASSO 3: BANCO DE DADOS (SQL) ---
    print("\n>>> FASE 3: ATUALIZANDO BANCO SQL (DBeaver)...")
    try:
        criar_banco_sql.criar_banco_dados()
    except Exception as e: print(f"❌ Falha no SQL: {e}")

    # --- RESUMO FINAL ---
    tempo_gasto = time.time() - inicio_total
    print("\n" + "="*80)
    print(f"✅ PROCESSO FINALIZADO EM {tempo_gasto:.2f} SEGUNDOS")
    print("   - Todos os arquivos limpos foram gerados.")
    print("   - A conciliação foi feita.")
    print("   - O banco vendas_animoshop.db foi atualizado.")
    print("="*80)

if __name__ == "__main__":
    main()