import pandas as pd
import os
import warnings
import re

# Ignora avisos desnecessários
warnings.filterwarnings('ignore')

class MarketplaceBase:
    def __init__(self, marketplace_name, input_folder, output_folder, final_filename):
        self.marketplace_name = marketplace_name
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.final_filename = final_filename
        self.dfs = []
        self.df_final = pd.DataFrame()

    def _read_file(self, file_path):
        """
        Método genérico para ler arquivos. Pode ser sobrescrito se necessário.
        Tenta ler Excel e CSV com diferentes encodings.
        """
        try:
            if file_path.endswith(('.xlsx', '.xls')):
                # Tenta ler como Excel
                # Alguns arquivos (Olist) precisam de header específico, isso pode ser passado no kwargs se parametrizado,
                # mas por padrão tentamos o básico. Classes filhas podem sobrescrever.
                return pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                try:
                    return pd.read_csv(file_path, encoding='utf-8-sig', sep=None, engine='python')
                except:
                    return pd.read_csv(file_path, encoding='latin-1', sep=None, engine='python')
        except Exception as e:
            print(f"Erro ao ler {os.path.basename(file_path)}: {e}")
            return None
        return None

    def load_data(self):
        print("="*80)
        print(f"PROCESSANDO CONSOLIDAÇÃO {self.marketplace_name.upper()}...")
        
        if not os.path.exists(self.input_folder):
            print(f"❌ Pasta de entrada não encontrada: {self.input_folder}")
            return

        arquivos = [f for f in os.listdir(self.input_folder) if f.endswith(('.csv', '.xlsx', '.xls'))]
        
        for file in arquivos:
            caminho = os.path.join(self.input_folder, file)
            df = self._read_file(caminho)
            
            if df is not None:
                # Padroniza colunas para evitar problemas de espaço
                df.columns = df.columns.str.strip()
                self.dfs.append(df)

        if not self.dfs:
            print("❌ Nenhum arquivo processado.")
        else:
            self.df_final = pd.concat(self.dfs, ignore_index=True)

    def filter_cancelations(self):
        """Implementar nas classes filhas se necessário"""
        pass

    def remove_columns(self, columns_to_remove):
        if not self.df_final.empty:
            # Normaliza para evitar erros de case
            cols_existing = set(self.df_final.columns)
            cols_drop = [c for c in columns_to_remove if c in cols_existing]
            
            # Tenta também remover ignorando case se não achou exato (opcional, mas seguro)
            if not cols_drop:
                cols_lower = {c.lower(): c for c in self.df_final.columns}
                for c_rem in columns_to_remove:
                    if c_rem.lower() in cols_lower:
                        cols_drop.append(cols_lower[c_rem.lower()])
            
            self.df_final.drop(columns=cols_drop, errors='ignore', inplace=True)

    def rename_columns(self, map_rename):
        if not self.df_final.empty:
            self.df_final.rename(columns=map_rename, inplace=True)

    def clean_numeric_col(self, col_name):
        """Converte coluna para float, tratando R$ e ,"""
        if col_name in self.df_final.columns:
             self.df_final[col_name] = pd.to_numeric(
                self.df_final[col_name].astype(str).str.replace('R$', '', regex=False).str.replace(',', '.'),
                errors='coerce'
            ).fillna(0.0)
        else:
            self.df_final[col_name] = 0.0

    def calculate_metrics(self):
        """Implementar nas classes filhas"""
        pass

    def extract_dates(self):
        """Implementar nas classes filhas"""
        pass

    def standardize_product_name(self):
        """Garante que a coluna de produto se chame 'Produto'"""
        # Tenta variações comuns se 'Produto' não existir
        if 'Produto' not in self.df_final.columns:
            for possible in ['produto', 'Título do anúncio', 'Nome do Produto', 'Título do produto', 'TÃ­tulo do produto']:
                if possible in self.df_final.columns:
                    self.df_final.rename(columns={possible: 'Produto'}, inplace=True)
                    break

    def save_and_segregate(self):
        if self.df_final.empty:
            return

        # Garante diretório de saída
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        # Adiciona coluna MarketPlace
        self.df_final['MarketPlace'] = self.marketplace_name

        # Segregação Airfryer
        if 'Produto' in self.df_final.columns:
            mask_airfryer = self.df_final['Produto'].astype(str).str.contains('airfryer|air fryer', case=False, na=False)
            df_airfryer = self.df_final[mask_airfryer].copy()
            df_principal = self.df_final[~mask_airfryer].copy()
            
            # Salva Principal na pasta de saída padrão (planilhas limpas)
            path_principal = os.path.join(self.output_folder, self.final_filename)
            df_principal.to_csv(path_principal, index=False, encoding='utf-8-sig', float_format='%.2f')
            
            # Salva Airfryer na pasta "Novoon na AnimoShop"
            airfryer_folder = os.path.join(os.path.dirname(self.output_folder), "Novoon na AnimoShop")
            if not os.path.exists(airfryer_folder):
                os.makedirs(airfryer_folder)
                
            filename_airfryer = f"airfryer_{self.marketplace_name.lower().replace(' ', '_')}.csv"
            path_airfryer = os.path.join(airfryer_folder, filename_airfryer)
            df_airfryer.to_csv(path_airfryer, index=False, encoding='utf-8-sig', float_format='%.2f')
            
            print(f"   [SEGREGAÇÃO] Principal: {len(df_principal)} | Airfryer: {len(df_airfryer)} (Salvo em '{airfryer_folder}')")
            
            # Atualiza o dataframe final para conter apenas os dados principais (sem airfryer)
            # Isso garante que o resumo impresso e qualquer uso subsequente ignore os airfryers
            self.df_final = df_principal
        else:
            path_principal = os.path.join(self.output_folder, self.final_filename)
            self.df_final.to_csv(path_principal, index=False, encoding='utf-8-sig', float_format='%.2f')
            print(f"   [SALVO] Arquivo único: {len(self.df_final)}")

    def print_summary(self):
        if self.df_final.empty:
            return
        
        print("\n" + "="*80)
        print(f"Resumo Final ({self.marketplace_name}):")
        if 'faturamento' in self.df_final.columns:
            print(f"  - Faturamento total: R$ {self.df_final['faturamento'].sum():,.2f}")
        if 'comissoes' in self.df_final.columns:
            print(f"  - Comissões total: R$ {self.df_final['comissoes'].sum():,.2f}")
        if 'lucro_liquido' in self.df_final.columns:
            print(f"  - Lucro líquido: R$ {self.df_final['lucro_liquido'].sum():,.2f}")
        print("="*80)

    def process(self):
        self.load_data()
        if self.df_final.empty:
            return
        
        self.filter_cancelations()
        self.standardize_product_name() # Tenta padronizar antes de remover colunas, caso o nome original esteja na lista de remover (pouco provável, mas seguro)
        
        # Hooks para lógica específica
        self.custom_preprocessing()
        
        self.calculate_metrics()
        self.extract_dates()
        
        # Arredondamento final padrão
        cols_fin = ['faturamento', 'frete', 'comissoes', 'lucro_liquido']
        for c in cols_fin:
            if c in self.df_final.columns:
                self.df_final[c] = self.df_final[c].round(2)

        self.save_and_segregate()
        self.print_summary()

    def custom_preprocessing(self):
        """Hook para ser sobrescrito com remoção de colunas, renomeação específica, etc."""
        pass
