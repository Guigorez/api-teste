import pandas as pd
import os
import warnings
import shutil
from pathlib import Path
from marketplace_base_as import MarketplaceBase

# Ignorar avisos desnecessários do Excel
warnings.filterwarnings('ignore')

class OlistProcessor(MarketplaceBase):
    def __init__(self):
        super().__init__(
            marketplace_name='Olist',
            input_folder=r'Dados\AnimoShop\planilhas\Olist',
            output_folder=r'Dados\AnimoShop\planilhas limpas',
            final_filename='olist_consolidado_final.csv'
        )
        self.COLUNAS_REMOVER = [
            'ciclo de repasse', 'tipo da transação', 'descrição da transação',
            'motivo tratativa', 'descrição da tratativa', 'consumidor', 'cidade',
            'SKU', 'número da nota fiscal', 'chave da nota fiscal',
            'valor da nota fiscal', 'valor do repasse', 'participação em promoção', 
            'comissão olist full', 'devolução olist full', 'percentual de comissão (%)'
        ]
        self.MESES_MAPA = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        # Performance: Controle de arquivos processados
        self.files_to_move = []
        self.processed_dir = Path(self.input_folder) / 'Processados'
        
        # Cria pasta se não existir
        try:
            self.processed_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Erro ao criar pasta Processados: {e}")
            self.processed_dir = None

    def load_data(self):
        print("="*80)
        print(f"PROCESSANDO CONSOLIDAÇÃO {self.marketplace_name.upper()} (Otimizado - Pathlib)...")
        
        input_path = Path(self.input_folder)
        if not input_path.exists():
            print(f"❌ Pasta de entrada não encontrada: {input_path}")
            return

        # Lista arquivos na raiz (ignora pastas)
        arquivos = [
            f for f in input_path.iterdir() 
            if f.is_file() and f.suffix.lower() in ['.csv', '.xlsx', '.xls']
        ]
        
        print(f"Encontrados {len(arquivos)} arquivos para processar.")
        
        for file_path in arquivos:
            try:
                # O método _read_file espera string ou path-like
                df = self._read_file(str(file_path))
                
                if df is not None and not df.empty:
                    # Padroniza colunas
                    df.columns = df.columns.str.strip()
                    self.dfs.append(df)
                    self.files_to_move.append(file_path) # Guarda objeto Path
                    print(f" -> Lido com sucesso: {file_path.name}")
                else:
                    print(f" -> Arquivo vazio ou ilegível (ignorado): {file_path.name}")
            except Exception as e:
                print(f"❌ ERRO CRÍTICO ao ler {file_path.name}: {e}")
                # Não adiciona a files_to_move

        if not self.dfs:
            print("❌ Nenhum arquivo novo processado.")
        else:
            self.df_final = pd.concat(self.dfs, ignore_index=True)

    def move_processed_files(self):
        """Move arquivos processados com sucesso para a pasta Processados"""
        if not self.files_to_move or not self.processed_dir:
            return

        print("\n" + "-"*40)
        print("Movendo arquivos processados...")
        count = 0
        for src_path in self.files_to_move:
            dst_path = self.processed_dir / src_path.name
            
            try:
                if dst_path.exists():
                    dst_path.unlink() # Remove destino se existir
                
                shutil.move(str(src_path), str(dst_path))
                count += 1
            except Exception as e:
                print(f"Erro ao mover {src_path.name}: {e}")
        
        print(f"Arquivos movidos: {count}/{len(self.files_to_move)}")
        self.files_to_move = [] # Limpa lista

    def _read_file(self, file_path):
        # Olist header=2 e engine=openpyxl
        try:
            return pd.read_excel(file_path, sheet_name=0, header=2, engine='openpyxl')
        except Exception as e:
            print(f"Erro ao ler {os.path.basename(file_path)}: {e}")
            return None

    def custom_preprocessing(self):
        # Padroniza colunas para minúsculo (Olist específico)
        self.df_final.columns = self.df_final.columns.str.strip().str.lower()

        # Filtro de itens vazios
        if 'item' in self.df_final.columns:
            self.df_final = self.df_final[self.df_final['item'].notna() & (self.df_final['item'] != '')]

        # Remoção de Colunas (usando lista lower)
        colunas_remover_lower = [c.lower() for c in self.COLUNAS_REMOVER]
        cols_drop = [c for c in self.df_final.columns if c in colunas_remover_lower]
        self.df_final.drop(columns=cols_drop, inplace=True)

        # Padronização Produto
        if 'produto' in self.df_final.columns:
            self.df_final.rename(columns={'produto': 'Produto'}, inplace=True)

    def calculate_metrics(self):
        colunas_numericas = [
            'valor de venda', 'frete', 'taxa fixa', 'valor da comissão',
            'incentivo olist', 'subsídio', 'item'
        ]
        
        for col in colunas_numericas:
            if col in self.df_final.columns:
                self.df_final[col] = pd.to_numeric(self.df_final[col], errors='coerce').fillna(0.0)
            else:
                self.df_final[col] = 0.0

        # Cálculos
        self.df_final['faturamento'] = self.df_final['valor de venda']
        self.df_final['frete'] = self.df_final['frete'].abs()
        self.df_final['contagem_pedidos'] = self.df_final['item']

        comissao_positiva = self.df_final['incentivo olist'] + self.df_final['subsídio']
        comissao_negativa = self.df_final['valor da comissão'].abs() + self.df_final['taxa fixa'].abs()
        
        self.df_final['comissoes'] = comissao_negativa - comissao_positiva
        self.df_final['lucro_liquido'] = self.df_final['faturamento'] - (self.df_final['comissoes'] + self.df_final['frete'])

        # ID Olist
        if 'pedido' in self.df_final.columns:
            self.df_final.rename(columns={'pedido': 'Id do Pedido Unificado'}, inplace=True)

    def extract_dates(self):
        # Formato específico do Olist: dd/mm/YYYY HHhMM (ex: 25/08/2025 02h16)
        if 'data do pedido' in self.df_final.columns:
            datas = pd.to_datetime(self.df_final['data do pedido'], format='%d/%m/%Y %Hh%M', errors='coerce')
            self.df_final['dia'] = datas.dt.day.astype('Int64')
            self.df_final['ano'] = datas.dt.year.astype('Int64')
            self.df_final['mes'] = datas.dt.month.map(self.MESES_MAPA).fillna('Desconhecido')
        else:
            self.df_final['dia'] = pd.NA
            self.df_final['mes'] = 'Desconhecido'
            self.df_final['ano'] = pd.NA

    def process(self):
        super().process() # Executa fluxo padrão da base
        self.move_processed_files() # Executa movimentação no final

def processar_olist():
    processor = OlistProcessor()
    processor.process()

if __name__ == "__main__":
    processar_olist()