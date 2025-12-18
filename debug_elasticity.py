import pandas as pd
import sqlite3
import logging
from api.routes import get_filtered_query
from api.database import get_db_connection

# Config logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_product(product_name, company='animoshop'):
    print(f"--- Debugging: {product_name} ---")
    
    # 1. Get Query
    base_query, params, conn = get_filtered_query(company)
    if not base_query:
        print("Error: Could not construct query.")
        return

    try:
        params['product_name'] = product_name
        query = f"""
            SELECT data_filtro, faturamento, contagem_pedidos, produto
            FROM ({base_query})
            WHERE produto = :product_name
        """
        print("Executing Query...")
        df = pd.read_sql_query(query, conn, params=params)
        print(f"Rows found: {len(df)}")
        
        if df.empty:
            print("DataFrame is empty.")
            return

        # 2. Check Data
        if 'preco_unitario' not in df.columns:
            df['preco_unitario'] = df['faturamento'] / df['contagem_pedidos'].replace(0, 1)
            
        print("\nPrice Statistics:")
        print(df['preco_unitario'].describe())
        
        unique_prices = df['preco_unitario'].round(2).unique()
        print(f"\nUnique Prices (rounded): {unique_prices}")
        print(f"Price Std Dev: {df['preco_unitario'].std()}")
        
        if df['preco_unitario'].std() == 0:
            print("\n>>> CONCLUSION: Price Variance is ZERO. Cannot calculate elasticity.")
        elif len(unique_prices) < 2:
            print("\n>>> CONCLUSION: Only 1 unique price point. Cannot calculate elasticity.")
        else:
            print("\n>>> CONCLUSION: Data seems OK variance-wise. Checking grouping...")
            
            # Grouping Logic
            if 'data_filtro' in df.columns:
                 # Agrupa por DIA primeiro para ter observações independentes
                grp = df.groupby('data_filtro').agg({
                    'preco_unitario': 'mean',
                    'contagem_pedidos': 'sum'
                }).reset_index()
            else:
                grp = df.groupby('preco_unitario')['contagem_pedidos'].sum().reset_index()
                
            print(f"\nGrouped Rows: {len(grp)}")
            print(grp.head())

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    debug_product("Saco de Boxe Inflável para Treinos")
