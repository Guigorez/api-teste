import pandas as pd
import os

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getcwd()
PASTA_ENTRADA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas', 'Amazon')
PASTA_SAIDA = os.path.join(BASE_DIR, 'Dados', 'Novoon', 'planilhas limpas')
ARQUIVO_SAIDA = 'amazon_novoon_final.csv'

MESES_MAPA = {
    'jan': 'Janeiro', 'feb': 'Fevereiro', 'mar': 'Março', 'apr': 'Abril',
    'may': 'Maio', 'jun': 'Junho', 'jul': 'Julho', 'aug': 'Agosto',
    'sep': 'Setembro', 'oct': 'Outubro', 'nov': 'Novembro', 'dec': 'Dezembro',
    'fev': 'Fevereiro', 'abr': 'Abril', 'mai': 'Maio', 'ago': 'Agosto',
    'set': 'Setembro', 'out': 'Outubro', 'dez': 'Dezembro'
}

def limpar_valor(col):
    """Converte coluna de string numérica (PT-BR) para float"""
    return pd.to_numeric(col.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0.0)

def processar_amazon():
    print("="*80)
    print("PROCESSANDO CONSOLIDAÇÃO AMAZON NOVOON (AGRUPADO)...")
    print("="*80)

    dfs = []
    if os.path.exists(PASTA_ENTRADA):
        arquivos = sorted([f for f in os.listdir(PASTA_ENTRADA) if f.endswith('.csv')])
        for file in arquivos:
            caminho = os.path.join(PASTA_ENTRADA, file)
            try:
                # Tenta ler com separador ',' forçado, pois vimos que funciona melhor
                try:
                    df = pd.read_csv(caminho, encoding='utf-8-sig', sep=',', engine='python', skiprows=7)
                except:
                    df = pd.read_csv(caminho, encoding='latin-1', sep=',', engine='python', skiprows=7)
                
                df.columns = df.columns.str.strip().str.lower()
                dfs.append(df)
                print(f'✓ Lido: {file} ({len(df)} linhas)')
            except Exception as e:
                print(f"⚠ Erro em {file}: {e}")

    if not dfs:
        print("❌ Nenhum dado encontrado.")
        return

    df_raw = pd.concat(dfs, ignore_index=True)

    # --- LIMPEZA INICIAL ---
    # Converter valores numéricos
    cols_valor = ['vendas do produto', 'créditos de remessa', 'créditos de embalagem de presente', 
                  'descontos promocionais', 'imposto de vendas coletados', 'tarifas de venda', 
                  'taxas fba', 'taxas de outras transações', 'outro', 'total']
    
    for col in cols_valor:
        if col in df_raw.columns:
            df_raw[col] = limpar_valor(df_raw[col])
        else:
            df_raw[col] = 0.0

    # Filtrar apenas linhas que tenham ID do pedido (ignora transferencias bancarias, taxas gerais)
    # Mas precisamos manter linhas de ajuste que tenham ID de pedido
    df_vendas = df_raw[df_raw['id do pedido'].notna() & (df_raw['id do pedido'] != '')].copy()

    print(f"\nLinhas com ID de Pedido: {len(df_vendas)}")

    # --- LÓGICA DE AGRUPAMENTO ---
    # Agrupar por 'id do pedido'
    # Regras de agregação:
    # - data/hora: pega a primeira (min)
    # - descrição: pega a primeira que não seja nula e não contenha "Tarifa" se possível (ou max string length)
    # - valores: soma
    
    # Função para pegar a melhor descrição (o nome do produto)
    def melhor_descricao(series):
        # Tenta pegar descrições que não sejam sobre tarifa/frete
        candidatos = [s for s in series if isinstance(s, str) and 'Tarifa' not in s and 'Estorno' not in s and len(s) > 5]
        if candidatos:
            return candidatos[0] # Retorna o primeiro produto real encontrado
        # Se não achar, retorna o maior texto (provavelmente o produto) ou o primeiro
        validos = [s for s in series if isinstance(s, str) and len(s) > 0]
        if validos:
            return max(validos, key=len)
        return "Produto Desconhecido"

    # Configuração do agg
    agg_rules = {
        'data/hora': 'first',
        'descrição': melhor_descricao,
        'cidade do pedido': 'first',
        'estado do pedido': 'first',
        'postal do pedido': 'first',
        # Soma tudo que é dinheiro
        'vendas do produto': 'sum',
        'créditos de remessa': 'sum',
        'créditos de embalagem de presente': 'sum',
        'descontos promocionais': 'sum',
        'imposto de vendas coletados': 'sum',
        'tarifas de venda': 'sum',
        'taxas fba': 'sum',
        'taxas de outras transações': 'sum',
        'outro': 'sum',
        'total': 'sum'
    }

    # Realiza o agrupamento
    print("Agrupando por ID do Pedido...")
    df_grouped = df_vendas.groupby('id do pedido', as_index=False).agg(agg_rules)

    print(f"Linhas após agrupamento (Pedidos Únicos): {len(df_grouped)}")

    # --- CÁLCULOS FINAIS (PÓS-AGRUPAMENTO) ---
    # Agora 'total' deve ser o lucro líquido real daquele pedido (Venda - Taxas - Frete)
    # Mas vamos recalcular para garantir a estrutura do Novoon

    # Faturamento = Vendas + Créditos (o cliente pagou isso)
    df_grouped['faturamento'] = df_grouped['vendas do produto'] + df_grouped['créditos de remessa'] + df_grouped['créditos de embalagem de presente']
    
    # --- CÁLCULOS DETALHADOS (Padrão Novoon) ---
    # Frete = Taxas de outras transações (onde entra a tarifa de envio) + Créditos de remessa
    df_grouped['frete'] = df_grouped['taxas de outras transações'] + df_grouped['créditos de remessa']
    
    # Comissões = Tarifas de venda
    df_grouped['comissoes'] = df_grouped['tarifas de venda']

    # Custo Operacional = Comissões + Frete + Taxas FBA + Outros
    # Nota: 'frete' já inclui 'taxas de outras transações'.
    # Se quisermos ser estritos com a soma do custo:
    df_grouped['custo_operacional'] = (
        df_grouped['comissoes'] + 
        df_grouped['frete'] + 
        df_grouped['taxas fba'] + 
        df_grouped['outro'] +
        df_grouped['descontos promocionais']
    )

    # Lucro Líquido = Faturamento + Custos (como custos são negativos, é uma soma algébrica)
    # Ou simplesmente a coluna 'total' que a Amazon já dá
    df_grouped['lucro_liquido_calculado'] = df_grouped['vendas do produto'] + df_grouped['custo_operacional'] + df_grouped['créditos de embalagem de presente']

    # --- TRATAMENTO DE DATAS ---
    regex_data = r'(\d+).*?([a-zA-ZçÇ]{3,}|\d+).*?(\d{4})'
    datas_extraidas = df_grouped['data/hora'].astype(str).str.extract(regex_data)
    if not datas_extraidas.empty:
        df_grouped['dia'] = pd.to_numeric(datas_extraidas[0], errors='coerce').astype('Int64')
        df_grouped['ano'] = pd.to_numeric(datas_extraidas[2], errors='coerce').astype('Int64')
        df_grouped['mes'] = datas_extraidas[1].str.lower().str[:3].map(MESES_MAPA).fillna('Desconhecido')

    # Renomear para padrão Novoon
    df_grouped.rename(columns={
        'id do pedido': 'Id do Pedido Unificado',
        'descrição': 'Produto',
        'cidade do pedido': 'Cidade',
        'estado do pedido': 'UF',
        'postal do pedido': 'CEP',
        'faturamento': 'Faturamento',
        'frete': 'Frete',
        'comissoes': 'Comissões',
        'custo_operacional': 'Custo Operacional',
        'lucro_liquido_calculado': 'Lucro Bruto'
    }, inplace=True)

    # Remover colunas redundantes (já incorporadas nos cálculos acima)
    cols_to_drop = [
        'vendas do produto', 'créditos de remessa', 'créditos de embalagem de presente',
        'descontos promocionais', 'imposto de vendas coletados', 'tarifas de venda',
        'taxas fba', 'taxas de outras transações', 'outro', 'total', 'data/hora'
    ]
    df_grouped.drop(columns=cols_to_drop, errors='ignore', inplace=True)

    # Reordenar
    cols_ordem = [
        'Id do Pedido Unificado', 'Produto', 'dia', 'mes', 'ano',
        'Cidade', 'UF', 'CEP',
        'Faturamento', 'Frete', 'Comissões', 'Custo Operacional', 'Lucro Bruto'
    ]
    cols_finais = [c for c in cols_ordem if c in df_grouped.columns]
    df_grouped = df_grouped[cols_finais]

    # --- SALVAR RESULTADO ---
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    path_saida = os.path.join(PASTA_SAIDA, ARQUIVO_SAIDA)
    df_grouped.to_csv(path_saida, index=False, encoding='utf-8-sig')

    print("\n" + "="*80)
    print("RESULTADO DA ANÁLISE AGRUPADA:")
    print(f"Arquivo salvo em: {path_saida}")
    print(f"Total de Pedidos Únicos: {len(df_grouped)}")
    print(f"Faturamento Total: R$ {df_grouped['Faturamento'].sum():,.2f}")
    print(f"Lucro Bruto Total: R$ {df_grouped['Lucro Bruto'].sum():,.2f}")
    print("="*80)

if __name__ == "__main__":
    processar_amazon()
