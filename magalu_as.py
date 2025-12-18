#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import os
import shutil
from pathlib import Path
from marketplace_base_as import MarketplaceBase

class MagaluProcessor(MarketplaceBase):
    def __init__(self):
        super().__init__(
            marketplace_name='Magalu',
            input_folder=r'Dados\AnimoShop\planilhas\Magalu',
            output_folder=r'Dados\AnimoShop\planilhas limpas',
            final_filename='magalu_consolidado_final.csv'
        )
        self.COLUNAS_REMOVER = [
            'Pedido de diversos pacotes?',
            'Quantidade de pacotes',
            'Total de parcelas (Forma de Pagamento 1)',
            'Valor total (Forma de Pagamento 1)',
            'Bandeira (Forma de pagamento 1)',
            'Código de Autorização (Forma de pagamento 1)',
            'Tipo de Integração (Forma de pagamento 1)',
            'Credenciadora (Forma de pagamento 1)',
            'Forma de pagamento 2',
            'Total de parcelas (Forma de Pagamento 2)',
            'Valor total (Forma de Pagamento 2)',
            'Bandeira (Forma de pagamento 2)',
            'Código de Autorização (Forma de pagamento 2)',
            'Tipo de Integração (Forma de pagamento 2)',
            'Credenciadora (Forma de pagamento 2)',
            'Nome do cliente',
            'CPF/CNPJ do Cliente',
            '% Taxa de antecipação',
            'Serviços de tecnologia (1)',
            'Serviços de intermediação (2)',
            'Intermediações financeiras (MDR) (3)',
            'Previsão de liberação de recebível',
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
        # Magalu tenta utf-8 com , ou latin-1 com ;
        try:
            return pd.read_csv(file_path, encoding='utf-8', sep=',')
        except:
            try:
                return pd.read_csv(file_path, encoding='latin-1', sep=';')
            except Exception as e:
                print(f"Erro ao ler {os.path.basename(file_path)}: {e}")
                return None

    def custom_preprocessing(self):
        # Remoção de colunas
        self.remove_columns(self.COLUNAS_REMOVER)

        # Garantir colunas essenciais
        cols = [
            'Valor bruto do pedido',
            'Serviços do marketplace (1+2+3)',
            'Tarifa fixa',
            'Coparticipação de Fretes estimada',
            'Valor líquido estimado a receber',
            'Quantidade de itens',
            'Data do Pedido',
            'Número do pedido'
        ]
        for c in cols:
            if c not in self.df_final.columns:
                self.df_final[c] = 0.0

        # Padronização Produto (Magalu tem nomes estranhos as vezes)
        col_produto_origem = next((col for col in self.df_final.columns if 'Título do produto' in col), None)
        if col_produto_origem:
            self.df_final.rename(columns={col_produto_origem: 'Produto'}, inplace=True)
        else:
            col_produto_enc = next((col for col in self.df_final.columns if 'TÃ­tulo do produto' in col), None)
            if col_produto_enc:
                self.df_final.rename(columns={col_produto_enc: 'Produto'}, inplace=True)

    def calculate_metrics(self):
        # Converter numéricos
        cols_numericas = [
            'Valor bruto do pedido',
            'Serviços do marketplace (1+2+3)',
            'Tarifa fixa',
            'Coparticipação de Fretes estimada',
            'Valor líquido estimado a receber',
            'Quantidade de itens'
        ]
        for c in cols_numericas:
            if c in self.df_final.columns:
                # Magalu usa R$ 191.9
                self.df_final[c] = pd.to_numeric(
                    self.df_final[c].astype(str).str.replace('R$', '', regex=False).str.strip(),
                    errors='coerce'
                ).fillna(0.0)

        # Métricas
        self.df_final['faturamento'] = self.df_final['Valor bruto do pedido']
        self.df_final['frete'] = (self.df_final['Coparticipação de Fretes estimada']).abs()
        self.df_final['comissoes'] = (self.df_final['Serviços do marketplace (1+2+3)']).abs() + (self.df_final['Tarifa fixa']).abs()
        self.df_final['outros'] = 0.0
        self.df_final['lucro_liquido'] = self.df_final['Valor líquido estimado a receber']

        # Contagem e ID
        self.df_final['contagem_pedidos'] = self.df_final['Quantidade de itens']
        self.df_final.rename(columns={'Número do pedido':'Id do Pedido Unificado'}, inplace=True)

    def extract_dates(self):
        def _extrair(data_str):
            try:
                d = str(data_str).split(' ')[0]
                dd, mm, yy = d.split('/')
                dd = int(dd); mm = int(mm); yy = int(yy)
                meses = {1:'Janeiro',2:'Fevereiro',3:'Março',4:'Abril',5:'Maio',6:'Junho',7:'Julho',8:'Agosto',9:'Setembro',10:'Outubro',11:'Novembro',12:'Dezembro'}
                return pd.Series([dd, meses.get(mm), yy])
            except:
                return pd.Series([None, None, None])

        if 'Data do Pedido' in self.df_final.columns:
            self.df_final[['dia','mes','ano']] = self.df_final['Data do Pedido'].apply(_extrair)

    def process(self):
        super().process() # Executa fluxo padrão da base
        self.move_processed_files() # Executa movimentação no final

def processar_magalu():
    processor = MagaluProcessor()
    processor.process()

if __name__ == "__main__":
    processar_magalu()