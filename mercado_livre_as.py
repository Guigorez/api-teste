import pandas as pd
import os
import shutil
from pathlib import Path
from marketplace_base_as import MarketplaceBase

class MercadoLivreProcessor(MarketplaceBase):
    def __init__(self):
        super().__init__(
            marketplace_name='Mercado Livre',
            input_folder=r'Dados\AnimoShop\planilhas\Mercado Livre',
            output_folder=r'Dados\AnimoShop\planilhas limpas',
            final_filename='mercado_livre_consolidado_final.csv'
        )
        self.COLUNAS_REMOVER = [
            'Descrição do status', 'Pacote de diversos produtos', 'Pertence a um kit',
            'Receita por acréscimo no preço (pago pelo comprador)', 'Taxa de parcelamento equivalente ao acréscimo',
            'Custo por diferenças nas medidas e no peso do pacote', 'Mês de faturamento das suas tarifas',
            'Venda por publicidade', 'Tipo de anúncio', 'NF-e em anexo', 'Dados pessoais ou da empresa',
            'Tipo e número do documento', 'Endereço', 'Tipo de contribuinte', 'Inscrição estadual',
            'Comprador', 'Negócio', 'CPF', 'Endereço.1', 'Forma de entrega', 'Data a caminho',
            'Data de entrega', 'Motorista', 'Número de rastreamento', 'URL de acompanhamento',
            'Unidades.1', 'Forma de entrega.1', 'Data a caminho.1', 'Data de entrega.1',
            'Motorista.1', 'Número de rastreamento.1', 'URL de acompanhamento.1',
            'Revisado pelo Mercado Livre', 'Data de revisão', 'Dinheiro liberado', 'Resultado',
            'Destino', 'Motivo do resultado', 'Unidades.2', 'Reclamação aberta',
            'Reclamação encerrada', 'Em mediação'
        ]
        self.STATUS_CANCELADOS = [
            'Cancelada pelo comprador',
            'Pacote cancelado pelo Mercado Livre',
            'Você cancelou a venda'
        ]
        self.MESES_REGEX = {
            'janeiro': 'Janeiro', 'fevereiro': 'Fevereiro', 'março': 'Março', 'abril': 'Abril',
            'maio': 'Maio', 'junho': 'Junho', 'julho': 'Julho', 'agosto': 'Agosto',
            'setembro': 'Setembro', 'outubro': 'Outubro', 'novembro': 'Novembro', 'dezembro': 'Dezembro'
        }

    def _read_file(self, file_path):
        # ML header=5
        try:
            return pd.read_excel(file_path, sheet_name=0, header=5)
        except Exception as e:
            print(f"Erro ao ler {os.path.basename(file_path)}: {e}")
            return None

    def custom_preprocessing(self):
        # Filtro de Cancelamentos
        regex_cancelados = '|'.join(self.STATUS_CANCELADOS)
        if 'Estado' in self.df_final.columns:
            total_antes = len(self.df_final)
            self.df_final = self.df_final[~self.df_final['Estado'].astype(str).str.contains(regex_cancelados, case=False, na=False)]
            print(f"ℹ️ Linhas removidas (Cancelados): {total_antes - len(self.df_final)}")

        # Remoção de colunas Unnamed e lista
        self.df_final = self.df_final.loc[:, ~self.df_final.columns.str.contains('^Unnamed')]
        self.remove_columns(self.COLUNAS_REMOVER)

        # Padronização Produto
        if 'Título do anúncio' in self.df_final.columns:
            self.df_final.rename(columns={'Título do anúncio': 'Produto'}, inplace=True)

    def calculate_metrics(self):
        colunas_numericas = [
            'Receita por produtos (BRL)',
            'Tarifa de venda e impostos (BRL)',
            'Receita por envio (BRL)',
            'Tarifas de envio (BRL)',
            'Cancelamentos e reembolsos (BRL)'
        ]
        
        for col in colunas_numericas:
            if col in self.df_final.columns:
                self.df_final[col] = pd.to_numeric(self.df_final[col], errors='coerce').fillna(0.0)

        # Cálculos
        self.df_final['faturamento'] = self.df_final['Receita por produtos (BRL)']
        self.df_final['comissoes'] = self.df_final['Tarifa de venda e impostos (BRL)'].abs()
        self.df_final['frete'] = (self.df_final['Receita por envio (BRL)'] + self.df_final['Tarifas de envio (BRL)']).abs()
        self.df_final['cancelamentos'] = self.df_final['Cancelamentos e reembolsos (BRL)'].abs()
        
        self.df_final['lucro_liquido'] = self.df_final['faturamento'] - (self.df_final['comissoes'] + self.df_final['frete'] + self.df_final['cancelamentos'])

        # Renomeações Finais
        mapa_renomear = {
            'Unidades': 'contagem_pedidos',
            'N.º de venda': 'Id do Pedido Unificado'
        }
        self.rename_columns(mapa_renomear)

        if 'contagem_pedidos' in self.df_final.columns:
            self.df_final['contagem_pedidos'] = pd.to_numeric(self.df_final['contagem_pedidos'], errors='coerce').fillna(1).astype(int)

        # Correção ID
        if 'Id do Pedido Unificado' in self.df_final.columns:
            self.df_final['Id do Pedido Unificado'] = pd.to_numeric(self.df_final['Id do Pedido Unificado'], errors='coerce').astype('Int64')

    def extract_dates(self):
        regex_data = r'(\d+)\s+de\s+([a-zA-ZçÇ]+)\s+de\s+(\d{4})'
        if 'Data da venda' in self.df_final.columns:
            datas = self.df_final['Data da venda'].astype(str).str.lower().str.extract(regex_data)
            self.df_final['dia'] = pd.to_numeric(datas[0], errors='coerce').astype('Int64')
            self.df_final['ano'] = pd.to_numeric(datas[2], errors='coerce').astype('Int64')
            self.df_final['mes'] = datas[1].map(self.MESES_REGEX).fillna('Desconhecido')
        else:
            self.df_final['dia'] = pd.NA
            self.df_final['mes'] = 'Desconhecido'
            self.df_final['ano'] = pd.NA

    def process(self):
        super().process() # Executa fluxo padrão da base
        self.move_processed_files() # Executa movimentação no final

def processar_mercadolivre():
    processor = MercadoLivreProcessor()
    processor.process()

if __name__ == "__main__":
    processar_mercadolivre()