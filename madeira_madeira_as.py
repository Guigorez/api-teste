import pandas as pd
import os
from marketplace_base_as import MarketplaceBase

class MadeiraProcessor(MarketplaceBase):
    def __init__(self):
        super().__init__(
            marketplace_name='MadeiraMadeira',
            input_folder=r'Dados\AnimoShop\planilhas\Madeira Madeira',
            output_folder=r'Dados\AnimoShop\planilhas limpas',
            final_filename='madeira_consolidado_final.csv'
        )
        self.COLUNAS_REMOVER = [
            'ID do Seller', 'Nome do Seller', 'Pedido Site MM', 'CPF do Cliente',
            'Cliente', 'Telefone', 'Data Pedido', 'Data Prometida', 'Nova Data Prometida',
            'Última atualização', 'Endereço', 'Satisfação', 'URL Rastreio', 'Codigo Rastreio',
            'Número NF', 'Data Emissão', 'Nome da Transportadora', 'Data Previsão Faturamento',
            'Data Faturamento Seller', 'Data Previsão Rastreamento', 'Data Rastreamento Seller',
            'Data Entrega Seller', 'Status Cliente Entrega', 'Parcelas', 'Chave de Acesso', 'EAN', 'Data/Hora Entrega'
        ]
        self.MESES_MAPA = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }

    def _read_file(self, file_path):
        # Madeira usa iso-8859-1 e ;
        try:
            return pd.read_csv(file_path, encoding='iso-8859-1', sep=';', on_bad_lines='skip', engine='python')
        except Exception as e:
            print(f"Erro ao ler {os.path.basename(file_path)}: {e}")
            return None

    def custom_preprocessing(self):
        # Filtro de Cancelados
        if 'Status Cliente Entrega' in self.df_final.columns:
            qtd_inicial = len(self.df_final)
            self.df_final = self.df_final[~self.df_final['Status Cliente Entrega'].astype(str).str.contains('Cancelado', case=False, na=False)]
            qtd_cancelados = qtd_inicial - len(self.df_final)
            print(f"ℹ️  Filtro aplicado: {qtd_cancelados} pedidos cancelados foram removidos.")

        # Remoção de Colunas
        self.remove_columns(self.COLUNAS_REMOVER)

        # Padronização Produto
        if 'Produto' not in self.df_final.columns:
            if 'produto' in self.df_final.columns:
                self.df_final.rename(columns={'produto': 'Produto'}, inplace=True)

    def calculate_metrics(self):
        # Conversão Numérica
        cols_numericas = ['Valor Pedido', 'Comissão', 'Valor Original', '% Desconto', 'Valor', 'Quantidade']
        for col in cols_numericas:
            if col in self.df_final.columns:
                self.df_final[col] = pd.to_numeric(
                    self.df_final[col].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                ).fillna(0.0)
            else:
                self.df_final[col] = 0.0

        # Cálculos
        self.df_final['faturamento'] = self.df_final['Valor']
        self.df_final['frete'] = self.df_final['Valor Pedido'] - self.df_final['Valor']
        self.df_final['comissoes'] = self.df_final['Comissão']
        self.df_final['lucro_liquido'] = self.df_final['faturamento'] - (self.df_final['frete'] + self.df_final['comissoes'])
        
        self.df_final['contagem_pedidos'] = self.df_final['Quantidade'].astype(int)

        # ID Madeira
        if 'Pedido' in self.df_final.columns:
            self.df_final.rename(columns={'Pedido': 'Id do Pedido Unificado'}, inplace=True)

    def extract_dates(self):
        if 'Data Aprovação' in self.df_final.columns:
            datas = pd.to_datetime(self.df_final['Data Aprovação'], dayfirst=True, errors='coerce')
            self.df_final['dia'] = datas.dt.day.astype('Int64')
            self.df_final['ano'] = datas.dt.year.astype('Int64')
            self.df_final['mes'] = datas.dt.month.map(self.MESES_MAPA).fillna('Desconhecido')
        else:
            self.df_final['dia'] = pd.NA
            self.df_final['mes'] = 'Desconhecido'
            self.df_final['ano'] = pd.NA

def processar_madeira():
    processor = MadeiraProcessor()
    processor.process()

if __name__ == "__main__":
    processar_madeira()