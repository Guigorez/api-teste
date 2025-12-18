import pandas as pd
import os
import shutil
from marketplace_base_as import MarketplaceBase

class AmazonProcessor(MarketplaceBase):
    def __init__(self):
        super().__init__(
            marketplace_name='Amazon',
            input_folder=r'Dados\AnimoShop\planilhas\Amazon',
            output_folder=r'Dados\AnimoShop\planilhas limpas',
            final_filename='amazon_consolidado_final.csv'
        )
        self.TIPOS_MANTER = ['Reembolso', 'Serviços de Envio', 'Pedido', 'Reembolsos', 'Reembolso de estorno']
        self.COLUNAS_EXCLUIR = ['mercado', 'id de liquidação', 'data/hora', 'atendimento']
        self.RENOMEAR = {
            'id do pedido': 'Id do Pedido Unificado',
            'estado do pedido': 'UF',
            'cidade do pedido': 'Cidade',
            'descrição': 'Produto',
            'postal do pedido': 'CEP',
            'quantidade': 'Contagem de pedidos',
            'tipo': 'Status',
            'sku': 'SKU',
            'tipo de conta': 'Metodo de pagamento',
        }
        self.MESES_MAPA = {
            'jan': 'Janeiro', 'fev': 'Fevereiro', 'mar': 'Março', 'abr': 'Abril',
            'mai': 'Maio', 'jun': 'Junho', 'jul': 'Julho', 'ago': 'Agosto',
            'set': 'Setembro', 'out': 'Outubro', 'nov': 'Novembro', 'dez': 'Dezembro',
            '1': 'Janeiro', '01': 'Janeiro', '2': 'Fevereiro', '02': 'Fevereiro',
            '3': 'Março', '03': 'Março', '4': 'Abril', '04': 'Abril',
            '5': 'Maio', '05': 'Maio', '6': 'Junho', '06': 'Junho',
            '7': 'Julho', '07': 'Julho', '8': 'Agosto', '08': 'Agosto',
            '9': 'Setembro', '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
        }
        
        # Performance: Controle de arquivos processados
        self.files_to_move = []
        self.processed_dir = os.path.join(self.input_folder, 'Processados')
        if not os.path.exists(self.processed_dir):
            try:
                os.makedirs(self.processed_dir)
            except Exception as e:
                print(f"Erro ao criar pasta Processados: {e}")
                self.processed_dir = None # Disable feature on error

    def load_data(self):
        print("="*80)
        print(f"PROCESSANDO CONSOLIDAÇÃO {self.marketplace_name.upper()} (Otimizado)...")
        
        if not os.path.exists(self.input_folder):
            print(f"❌ Pasta de entrada não encontrada: {self.input_folder}")
            return

        # Lista apenas arquivos na raiz (ignora pastas como Processados)
        arquivos = [f for f in os.listdir(self.input_folder) 
                   if os.path.isfile(os.path.join(self.input_folder, f)) 
                   and f.endswith(('.csv', '.xlsx', '.xls'))]
        
        print(f"Encontrados {len(arquivos)} arquivos para processar.")
        
        for file in arquivos:
            caminho = os.path.join(self.input_folder, file)
            try:
                df = self._read_file(caminho)
                if df is not None and not df.empty:
                    # Padroniza colunas
                    df.columns = df.columns.str.strip()
                    self.dfs.append(df)
                    self.files_to_move.append(file) # Marca para mover no final
                    print(f" -> Lido com sucesso: {file}")
                else:
                    print(f" -> Arquivo vazio ou ilegível (ignorado): {file}")
            except Exception as e:
                print(f"❌ ERRO CRÍTICO ao ler {file}: {e}")
                # Não adiciona a files_to_move, então não será movido

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
        for file in self.files_to_move:
            src = os.path.join(self.input_folder, file)
            dst = os.path.join(self.processed_dir, file)
            
            try:
                if os.path.exists(dst):
                    # Se já existe, renomeia com timestamp ou sobrescreve?
                    # Para simplificar: Remove destino antigo e move novo
                    os.remove(dst)
                
                shutil.move(src, dst)
                count += 1
            except Exception as e:
                print(f"Erro ao mover {file}: {e}")
        
        print(f"Arquivos movidos: {count}/{len(self.files_to_move)}")
        self.files_to_move = [] # Limpa lista

    def _read_file(self, file_path):
        # Amazon tem skiprows=7
        try:
            try:
                return pd.read_csv(file_path, encoding='utf-8-sig', sep=None, engine='python', skiprows=7)
            except:
                return pd.read_csv(file_path, encoding='latin-1', sep=None, engine='python', skiprows=7)
        except Exception as e:
            print(f"Erro ao ler {os.path.basename(file_path)}: {e}")
            return None

    def custom_preprocessing(self):
        # Filtros específicos
        if 'tipo' in self.df_final.columns:
            self.df_final = self.df_final[self.df_final['tipo'].isin(self.TIPOS_MANTER)]
        
        if 'descrição' in self.df_final.columns:
            self.df_final = self.df_final[~self.df_final['descrição'].str.contains('Estorno do frete', case=False, na=False)]

        # Renomeação
        self.rename_columns(self.RENOMEAR)
        
        # Remoção de colunas
        self.remove_columns(self.COLUNAS_EXCLUIR)

    def calculate_metrics(self):
        # Conversão de Valores
        cols_valor = ['taxas de outras transações', 'créditos de remessa', 'tarifas de venda', 'vendas do produto', 'descontos promocionais']
        for col in cols_valor:
            self.clean_numeric_col(col)

        # Cálculos Financeiros
        self.df_final['frete'] = self.df_final['taxas de outras transações'] + self.df_final['créditos de remessa']
        self.df_final['comissoes'] = self.df_final['tarifas de venda']
        self.df_final['faturamento'] = self.df_final['vendas do produto'] + self.df_final['descontos promocionais']
        self.df_final['custo_operacional'] = self.df_final['comissoes'] + self.df_final['frete']
        self.df_final['lucro_liquido'] = self.df_final['faturamento'] + self.df_final['custo_operacional']
        
        # Contagem de Pedidos (Lógica específica Amazon)
        if 'Status' in self.df_final.columns:
            self.df_final['contagem_pedidos'] = (self.df_final['Status'] == 'Pedido').astype(int)

    def extract_dates(self):
        # Amazon usa coluna 'data/hora' que foi removida no custom_preprocessing, mas precisamos dela antes?
        # Ops, removemos 'data/hora' no custom_preprocessing. Precisamos extrair antes de remover ou garantir que não removemos antes.
        # CORREÇÃO: A lista COLUNAS_EXCLUIR tem 'data/hora'.
        # O método custom_preprocessing roda ANTES de calculate_metrics e extract_dates no base.process().
        # Então preciso ajustar a ordem ou não remover 'data/hora' lá.
        # Melhor: sobrescrever process() ou ajustar custom_preprocessing para não remover data/hora ainda.
        # Mas o base chama remove_columns dentro de custom_preprocessing se eu chamar.
        
        # Vamos ajustar: A data original estava em 'data/hora'.
        # Se eu já removi, perdi.
        # Vou recarregar a coluna se necessário ou mudar a lógica.
        # No código original, ele extrai datas ANTES de drop.
        pass

    # Sobrescrevendo process para garantir a ordem correta da Amazon que é chata
    def process(self):
        self.load_data()
        if self.df_final.empty: return

        # 1. Filtros (antes de rename)
        if 'tipo' in self.df_final.columns:
            self.df_final = self.df_final[self.df_final['tipo'].isin(self.TIPOS_MANTER)]
        if 'descrição' in self.df_final.columns:
            self.df_final = self.df_final[~self.df_final['descrição'].str.contains('Estorno do frete', case=False, na=False)]

        # 2. Extração de Datas (Antes de qualquer rename/drop que possa afetar)
        if 'data/hora' in self.df_final.columns:
            regex_data = r'(\d+).*?([a-zA-ZçÇ]{3,}|\d+).*?(\d{4})'
            datas_extraidas = self.df_final['data/hora'].astype(str).str.extract(regex_data)
            if not datas_extraidas.empty:
                self.df_final['dia'] = pd.to_numeric(datas_extraidas[0], errors='coerce').astype('Int64')
                self.df_final['ano'] = pd.to_numeric(datas_extraidas[2], errors='coerce').astype('Int64')
                self.df_final['mes'] = datas_extraidas[1].str.lower().str[:3].map(self.MESES_MAPA).fillna('Desconhecido')

        # 3. Rename
        self.rename_columns(self.RENOMEAR)

        # 4. Cálculos
        self.calculate_metrics()

        # 5. Remove Colunas (Agora seguro)
        self.remove_columns(self.COLUNAS_EXCLUIR)

        # 6. Finalização Padrão
        self.standardize_product_name()
        
        # Arredondamento
        cols_fin = ['frete', 'comissoes', 'faturamento', 'custo_operacional', 'lucro_liquido']
        for c in cols_fin:
            if c in self.df_final.columns:
                self.df_final[c] = self.df_final[c].round(2)

        self.save_and_segregate()
        self.print_summary()
        
        # Finaliza movendo arquivos
        self.move_processed_files()

def processar_amazon():
    processor = AmazonProcessor()
    processor.process()

if __name__ == "__main__":
    processar_amazon()