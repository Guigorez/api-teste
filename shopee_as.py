import pandas as pd
import os
import shutil
from pathlib import Path
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