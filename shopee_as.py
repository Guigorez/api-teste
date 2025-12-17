import pandas as pd
import os
from marketplace_base_as import MarketplaceBase

class ShopeeProcessor(MarketplaceBase):
    def __init__(self):
        super().__init__(
            marketplace_name='Shopee',
            input_folder=r'Dados\AnimoShop\planilhas\Shopee',
            output_folder=r'Dados\AnimoShop\planilhas limpas',
            final_filename='shopee_consolidado_final.csv'
        )
        self.COLUNAS_REMOVER = [
            'Cancelar Motivo','Status da Devolução / Reembolso','Número de rastreamento',
            'Opção de envio','Método de envio','Data prevista de envio','Tempo de Envio',
            'Data de criação do pedido','Número de referência SKU','Nome da variação',
            'Peso total SKU','Quantidade','Peso total do pedido','Código do Cupom',
            'Indicador da Leve Mais por Menos','Total descontado Cartão de Crédito',
            'Nome de usuário (comprador)','Nome do destinatário','Telefone',
            'CPF do Comprador','Endereço de entrega','Cidade','Bairro',
            'Observação do comprador','Hora completa do pedido','Nota'
        ]
        self.MESES_MAPA = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }

    def _read_file(self, file_path):
        # Shopee header=0
        try:
            return pd.read_excel(file_path, sheet_name=0, header=0)
        except Exception as e:
            print(f"Erro ao ler {os.path.basename(file_path)}: {e}")
            return None

    def custom_preprocessing(self):
        # Filtro de Cancelados
        if 'Status do pedido' in self.df_final.columns:
            total_antes = len(self.df_final)
            self.df_final = self.df_final[~self.df_final['Status do pedido'].astype(str).str.contains('cancelado', case=False, na=False)]
            print(f"ℹ️  Linhas removidas (Cancelados): {total_antes - len(self.df_final)}")

        # Remoção de Colunas
        self.remove_columns(self.COLUNAS_REMOVER)

        # Padronização Produto
        if 'Nome do Produto' in self.df_final.columns:
            self.df_final.rename(columns={'Nome do Produto': 'Produto'}, inplace=True)

    def calculate_metrics(self):
        colunas_numericas = [
            'Valor estimado do frete', 'Desconto de Frete Aproximado', 'Taxa de transação',
            'Taxa de comissão', 'Taxa de serviço', 'Total global', 'Reembolso Shopee',
            'Preço acordado', 'Número de produtos pedidos'
        ]
        
        for col in colunas_numericas:
            if col in self.df_final.columns:
                self.df_final[col] = pd.to_numeric(self.df_final[col], errors='coerce').fillna(0.0)

        # Cálculos
        val_frete = self.df_final.get('Valor estimado do frete', 0)
        desc_frete = self.df_final.get('Desconto de Frete Aproximado', 0)
        self.df_final['frete'] = (val_frete - desc_frete).fillna(0.0)

        taxa_transacao = self.df_final.get('Taxa de transação', 0).abs()
        taxa_comissao = self.df_final.get('Taxa de comissão', 0).abs()
        taxa_servico = self.df_final.get('Taxa de serviço', 0).abs()
        self.df_final['taxas_totais'] = (taxa_transacao + taxa_comissao + taxa_servico).fillna(0.0)

        self.df_final['faturamento'] = self.df_final.get('Total global', 0).fillna(0.0)
        self.df_final['reembolso'] = self.df_final.get('Reembolso Shopee', 0).abs().fillna(0.0)
        self.df_final['contagem_pedidos'] = self.df_final.get('Número de produtos pedidos', 0).fillna(0.0)

        self.df_final['comissoes'] = (self.df_final['taxas_totais'] - self.df_final['reembolso']).fillna(0.0)
        self.df_final['lucro_liquido'] = (self.df_final['faturamento'] - (self.df_final['comissoes'] + self.df_final['frete'])).fillna(0.0)

        # ID Shopee -> Texto
        if 'ID do pedido' in self.df_final.columns:
            self.df_final.rename(columns={'ID do pedido': 'Id do Pedido Unificado'}, inplace=True)
            self.df_final['Id do Pedido Unificado'] = self.df_final['Id do Pedido Unificado'].astype(str)

    def extract_dates(self):
        if 'Hora do pagamento do pedido' in self.df_final.columns:
            datas = pd.to_datetime(self.df_final['Hora do pagamento do pedido'], errors='coerce')
            self.df_final['dia'] = datas.dt.day.astype('Int64')
            self.df_final['ano'] = datas.dt.year.astype('Int64')
            self.df_final['mes'] = datas.dt.month.map(self.MESES_MAPA).fillna('Desconhecido')
        else:
            self.df_final['dia'] = pd.NA
            self.df_final['mes'] = 'Desconhecido'
            self.df_final['ano'] = pd.NA

def processar_shopee():
    processor = ShopeeProcessor()
    processor.process()

if __name__ == "__main__":
    processar_shopee()