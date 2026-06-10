import re, unicodedata
import pandas as pd
from datetime import datetime

class Ecommerce:
    def __init__(self):
        self.data:pd.DataFrame = None
        self.loja:str = None
        self.trasacoes:list[str] = None
        self.origem:str = None
        self.empresa:str = None

    def normalizarColunas(self,texto: str) -> str:
        """Normaliza os nomes das colunas, removendo acentos, caracteres especiais e convertendo para minúsculas.
            :param texto: Nome da coluna a ser normalizada.
            :return: Nome da coluna normalizada.
        """
        if not texto:
            return texto
        
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join(c for c in texto if not unicodedata.combining(c))
        texto = texto.replace(" ","_").replace("/","_")
        texto = re.sub(r'[^a-zA-Z0-9\s_]', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()    
        return texto.lower()

    # ADJUSTMENT    
    def tratar_dados_ajustment(self,df:pd.DataFrame) -> pd.DataFrame:
        """ Trata os dados da aba de ajustes, extraindo as informações relevantes e padronizando os campos.
            :param df: DataFrame contendo os dados da aba de ajustes.
            :return: DataFrame tratado com as informações relevantes extraídas e campos padronizados.
        """
        inicio = 0
        fim = 0
        for i in range(df.shape[0]):    
            if df.iloc[i, 0] == "Detalhes da Lista de Transações e Ajustes":
                inicio = i+1
                break

        for j in range(inicio,df.shape[0]):    
            if pd.isna(df.iloc[j, 0]):
                fim = j
                break

        aux_df = df.iloc[inicio:fim,:].copy().reset_index(drop=True)
        cols = [self.normalizarColunas(c) for c in aux_df.loc[0,:].to_list()]
        aux_df.columns = cols
        aux_df = aux_df.iloc[1:,:].copy()
        aux_df.reset_index(drop=True,inplace=True)
        aux_df["valor_do_ajuste"] = aux_df["valor_do_ajuste"].astype(float)    
        aux_df["tipo"] = "Ajuste"
        
        return aux_df    
    
    def coalescer(self,linha) -> str:
        """ Coalescer os campos de motivo e descrição do ajuste para criar um histórico mais completo.
            :param linha: Série do DataFrame representando uma linha da aba de ajustes.
            :return: String contendo o histórico do ajuste, combinando motivo e descrição quando disponíveis.
        """
        return linha["motivo_do_ajuste"] if pd.notna(linha["motivo_do_ajuste"]) else linha["tipo_descricao_do_ajuste"]

    def extrai_valores_adjustment(self,linha:pd.Series):
        """ Extrai os valores relevantes de cada linha da aba de ajustes, padronizando os campos para o formato esperado pela aplicação.
            :param linha: Série do DataFrame representando uma linha da aba de ajustes.
            :return: Série do DataFrame com os campos extraídos e padronizados para a aplicação.
        """
        historico:str = self.coalescer(linha)
        if not "DIFAL" in historico:
            historico = f"{historico} - {linha['numero_do_pedido_relacionado']}"
        linha['tipo'] = "Ajuste"
        linha['lcto_pedido'] = linha["numero_do_pedido_relacionado"]
        linha['lcto_receita'] = abs(round(float(linha["valor_do_ajuste"]),2)) if linha["valor_do_ajuste"] > 0 else None
        linha['lcto_despesa'] = abs(round(float(linha["valor_do_ajuste"]),2)) if linha["valor_do_ajuste"] < 0 else None
        linha['lcto_repasse'] = round(float(linha["valor_do_ajuste"]),2)
        linha['lcto_historico'] = historico
        linha['lcto_data'] = pd.to_datetime(linha["data_de_conclusao_do_ajuste"]).strftime("%Y-%m-%d")
        linha['confirmado'] = True
        linha['divergencia'] = None
        
        return linha

    # RENDA
    def tratar_dados_renda(self,df:pd.DataFrame) -> pd.DataFrame:
        """ Trata os dados da aba de renda, extraindo as informações relevantes e padronizando os campos.
            :param df: DataFrame contendo os dados da aba de renda.
            :return: DataFrame tratado com as informações relevantes extraídas e campos padronizados.
        """

        COLUNAS_RELATORIO_VENDA = [ 
            'Ver', 'ID do pedido', 'Data de conclusão do pagamento', 'Quantia total lançada (R$)',
            'Preço do produto', 'Valor do Reembolso', 'Ajuste por pagamento via PIX', 'Cupom',
            'Taxa de frete paga pelo comprador', 'Frete cobrado pelo parceiro logístico',
            'Desconto de frete pela Shopee', 'Voucher subsidiado pelo Seller','Incentivo de cupom',
            'Taxa de comissão líquida', 'Taxa de serviço líquida', 'Taxa de transação',
            'Taxa de comissão Afiliados do Vendedor', 'Taxa de Devolução Fácil Shopee'
        ]

        aux_df = df.iloc[1:,:].copy().reset_index(drop=True)
        cols = aux_df.loc[0,:].to_list()
        aux_df.columns = cols
        aux_df = aux_df.loc[1:,COLUNAS_RELATORIO_VENDA].copy()
        aux_df = aux_df.drop(aux_df.loc[aux_df["Ver"]=="Sku"].index,axis=0)
        aux_df.columns = [self.normalizarColunas(c) for c in aux_df.columns]
        aux_df.reset_index(drop=True,inplace=True)

        aux_df['quantia_total_lancada_r']                 =  aux_df['quantia_total_lancada_r'].astype(float)
        aux_df['preco_do_produto']                        =  aux_df['preco_do_produto'].astype(float)
        aux_df['valor_do_reembolso']                      =  aux_df['valor_do_reembolso'].astype(float)
        aux_df['ajuste_por_pagamento_via_pix']            =  aux_df['ajuste_por_pagamento_via_pix'].astype(float)
        aux_df['ajuste_por_pagamento_via_pix']            =  aux_df['ajuste_por_pagamento_via_pix'].astype(float)
        aux_df['cupom']                                   =  aux_df['cupom'].astype(float)
        aux_df['taxa_de_frete_paga_pelo_comprador']       =  aux_df['taxa_de_frete_paga_pelo_comprador'].astype(float)
        aux_df['frete_cobrado_pelo_parceiro_logistico']   =  aux_df['frete_cobrado_pelo_parceiro_logistico'].astype(float)
        aux_df['desconto_de_frete_pela_shopee']           =  aux_df['desconto_de_frete_pela_shopee'].astype(float)
        aux_df['incentivo_de_cupom']                      =  aux_df['incentivo_de_cupom'].astype(float)
        aux_df['taxa_de_comissao_liquida']                =  aux_df['taxa_de_comissao_liquida'].astype(float)
        aux_df['taxa_de_servico_liquida']                 =  aux_df['taxa_de_servico_liquida'].astype(float)
        aux_df['taxa_de_transacao']                       =  aux_df['taxa_de_transacao'].astype(float)
        aux_df['taxa_de_comissao_afiliados_do_vendedor']  =  aux_df['taxa_de_comissao_afiliados_do_vendedor'].astype(float)
        aux_df['taxa_de_devolucao_facil_shopee']          =  aux_df['taxa_de_devolucao_facil_shopee'].astype(float)
        aux_df["tipo"] = "Renda"
        
        return aux_df    
    
    def calcula_despesa_total_shopee(self,linha:pd.Series):
        """ Calcula a despesa total de uma linha da aba de renda, somando os valores das taxas e descontos relacionados à venda.
            :param linha: Série do DataFrame representando uma linha da aba de renda.
            :return: Valor total da despesa calculada para a linha, considerando as taxas e descontos aplicáveis.
        """
        return linha[[  'valor_do_reembolso',
                        'ajuste_por_pagamento_via_pix',
                        'cupom',
                        'taxa_de_frete_paga_pelo_comprador',
                        'frete_cobrado_pelo_parceiro_logistico',
                        'desconto_de_frete_pela_shopee',
                        'voucher_subsidiado_pelo_seller',
                        'incentivo_de_cupom',
                        'taxa_de_comissao_liquida',
                        'taxa_de_servico_liquida',
                        'taxa_de_transacao',
                        'taxa_de_comissao_afiliados_do_vendedor',
                        'taxa_de_devolucao_facil_shopee'
                    ]].sum()

    def valida_planilha_vs_calculado_shopee(self,linha):
        """ Compara o valor da quantia total lançada presente na planilha com o resultado do cálculo da receita menos a despesa para validar se os valores conferem.
            :param linha: Série do DataFrame representando uma linha da aba de renda.
            :return: Booleano indicando se os valores conferem (True) ou se há divergência (False) entre o valor da planilha e o cálculo realizado.
        """
        return True if round(linha['lcto_receita']-linha['lcto_despesa'],2) == linha['quantia_total_lancada_r'] else False
    
    def extrai_valores_renda(self,linha:pd.Series):
        """ Extrai os valores relevantes de cada linha da aba de renda, padronizando os campos para o formato esperado pela aplicação.
            :param linha: Série do DataFrame representando uma linha da aba de renda.
            :return: Série do DataFrame com os campos extraídos e padronizados para a aplicação.
        """
        despesa_total:float = self.calcula_despesa_total_shopee(linha)
        pedido_id:str = linha["id_do_pedido"]
        linha['tipo'] = "Renda"
        linha['lcto_pedido'] = pedido_id
        linha['lcto_receita'] = round(float(linha["preco_do_produto"]),2)
        linha['lcto_despesa'] = abs(round(despesa_total,2))        
        linha['lcto_repasse'] = round(linha['lcto_receita']-abs(despesa_total),2)        
        linha['lcto_historico'] = f"Renda do pedido {pedido_id}"
        linha['lcto_data'] = pd.to_datetime(linha["data_de_conclusao_do_pagamento"]).strftime("%Y-%m-%d")
        linha['confirmado'] = self.valida_planilha_vs_calculado_shopee(linha)
        linha['divergencia'] = None if self.valida_planilha_vs_calculado_shopee(linha) else round(linha['lcto_receita']-linha['lcto_despesa'],2)
        return linha
    
    # BLZ
    def tratar_dados_blz(self,df:pd.DataFrame) -> pd.DataFrame:
        """ Trata os dados do relatório da Blz, extraindo as informações relevantes e padronizando os campos.
            :param df: DataFrame contendo os dados do relatório da Blz.
            :return: DataFrame tratado com as informações relevantes extraídas e campos padronizados.
        """        
        COLUNAS_RELATORIO_BLZ = [ 
            'Número do Pedido', 'Valor dos produtos',
            'Valor da comissão', 'Taxa Blz Envios',
            'Valor repasse', 'Data do evento', 'Descrição do evento'
        ]

        aux_df = df[COLUNAS_RELATORIO_BLZ].copy()
        cols = [self.normalizarColunas(c) for c in aux_df.columns]
        aux_df.columns = cols
        aux_df.reset_index(drop=True,inplace=True)
        
        return aux_df

    def calcula_despesa_total_blz(self,linha:pd.Series):
        """ Calcula a despesa total de uma linha do relatório da Blz, considerando a comissão e a taxa de envios, ou o valor repasse em casos de devolução total.
            :param linha: Série do DataFrame representando uma linha do relatório da Blz.
            :return: Valor total da despesa calculada para a linha, considerando as regras específicas para casos de devolução total e demais eventos.
        """
        if linha['descricao_do_evento']=="Devolução total":
            return linha['valor_repasse']
        return linha[['valor_da_comissao','taxa_blz_envios']].sum()

    def valida_historico_blz(self,linha:pd.Series):
        """ Valida o histórico de uma linha do relatório da Blz, verificando se o evento é uma devolução total para ajustar a descrição do histórico.
            :param linha: Série do DataFrame representando uma linha do relatório da Blz.
            :return: String contendo a descrição do histórico ajustada para refletir corretamente o tipo de evento, diferenciando entre renda e devolução total.
        """
        if linha['descricao_do_evento']=="Devolução total":
            return f"Devolução total do pedido {linha["numero_do_pedido"]}"
        return f"Renda do pedido {linha["numero_do_pedido"]}"

    def valida_planilha_vs_calculado_blz(self,linha):
        """ Compara o valor do repasse presente na planilha com o resultado do cálculo da receita menos a despesa para validar se os valores conferem, considerando as regras específicas para casos de devolução total.
            :param linha: Série do DataFrame representando uma linha do relatório da Blz.
            :return: Booleano indicando se os valores conferem (True) ou se há divergência (False) entre o valor da planilha e o cálculo realizado.
        """
        return True if (linha['descricao_do_evento']=="Devolução total") or (round(linha['lcto_receita']-linha['lcto_despesa'],2) == linha['valor_repasse']) else False

    def valida_tipo_blz(self,linha:pd.Series):
        """ Valida o tipo de uma linha do relatório da Blz, verificando se o evento é uma devolução total para classificar corretamente como ajuste, ou renda para demais eventos.
            :param linha: Série do DataFrame representando uma linha do relatório da Blz.
            :return: String indicando o tipo do lançamento, classificando como "Renda" para eventos de renda e "Ajuste" para eventos de devolução total, conforme as regras específicas para o relatório da Blz.
        """
        return "Renda" if linha['descricao_do_evento']=="Pacote entregue" else "Ajuste"    

    def calcula_divergencia_blz(self,linha:pd.Series):
        """ Calcula a divergência entre o valor do repasse presente na planilha e o resultado do cálculo da receita menos a despesa para uma linha do relatório da Blz, considerando as regras específicas para casos de devolução total.
            :param linha: Série do DataFrame representando uma linha do relatório da Blz.
            :return: Valor da divergência calculada para a linha, considerando as regras específicas para casos de devolução total e demais eventos, aplicando uma fórmula de cálculo diferenciada para refletir corretamente a estrutura de custos e repasses do relatório da Blz.
        """
        taxa_fixa_frete = 5.5
        taxa_comissao = .22        
        return linha['lcto_receita']-(linha['lcto_despesa']-taxa_fixa_frete)/taxa_comissao

    def extrai_valores_blz(self,linha:pd.Series):
        """ Extrai os valores relevantes de cada linha do relatório da Blz, padronizando os campos para o formato esperado pela aplicação, e aplicando as regras específicas para cálculo de despesa, validação de histórico, tipo e divergência.
            :param linha: Série do DataFrame representando uma linha do relatório da Blz.
            :return: Série do DataFrame com os campos extraídos e padronizados para a aplicação, incluindo as regras específicas para cálculo de despesa, validação de histórico, tipo e divergência conforme a estrutura do relatório da Blz.
        """
        despesa_total:float = self.calcula_despesa_total_blz(linha)        
        linha['tipo'] = self.valida_tipo_blz(linha)
        linha['lcto_pedido'] = linha["numero_do_pedido"]
        linha['lcto_receita'] = round(float(linha["valor_dos_produtos"]),2)
        linha['lcto_despesa'] = abs(round(despesa_total,2))
        linha['lcto_repasse'] = round(float(linha["valor_repasse"]),2)
        linha['lcto_historico'] = self.valida_historico_blz(linha)
        linha['lcto_data'] = linha["data_do_evento"].strftime("%Y-%m-%d")
        linha['confirmado'] = self.valida_planilha_vs_calculado_blz(linha)
        linha['divergencia'] = None if self.valida_planilha_vs_calculado_blz(linha) else round(self.calcula_divergencia_blz(linha),2)
        
        return linha        

    def unifica_lista_lctos(self,dfs:list[pd.DataFrame]) -> pd.DataFrame:
        """ Unifica as listas de lançamentos extraídas das abas de ajustes e renda da Shopee, ou do relatório da Blz, em um único DataFrame padronizado para a aplicação.
            :param dfs: Lista de DataFrames contendo os lançamentos extraídos das abas de ajustes e renda da Shopee, ou do relatório da Blz.
            :return: DataFrame unificado contendo todos os lançamentos extraídos, padronizados e organizados para a aplicação, facilitando o processamento e análise dos dados de forma integrada.
        """
        COLUNAS = ['tipo','lcto_pedido','lcto_receita','lcto_despesa','lcto_repasse','lcto_historico','lcto_data','confirmado','divergencia']
        lista_unificada:pd.DataFrame = pd.concat([df[COLUNAS] for df in dfs]).sort_values(['tipo','lcto_data','lcto_historico']).reset_index(drop=True)
        return lista_unificada

    def formata_payload(self,df:pd.DataFrame) -> list[dict]:
        """ Formata o DataFrame unificado de lançamentos em uma lista de dicionários no formato esperado pela API, estruturando as informações de receita e despesa para cada pedido de forma clara e organizada.
            :param df: DataFrame unificado contendo os lançamentos extraídos, padronizados e organizados para a aplicação.
            :return: Lista de dicionários formatada para a API, onde cada dicionário representa um pedido com suas respectivas informações de receita e despesa, facilitando a integração e o envio dos dados para a API de forma estruturada e eficiente.
        """
        payload:list[dict] = []
        
        for linha in df.itertuples():
            receita:dict = {}
            despesa:dict = {}
            
            receita = {
                "valor": linha.lcto_receita,
                "descricao": linha.lcto_historico,
                "data": linha.lcto_data,
                "pendente": True
            } if not pd.isna(linha.lcto_receita) else None

            despesa = {
                "valor": linha.lcto_despesa,
                "descricao": linha.lcto_historico,
                "data": linha.lcto_data,
                "pendente": True
            } if not pd.isna(linha.lcto_despesa) else None
                
            payload.append({
                "id_pedido": linha.lcto_pedido,
                "receita": receita,
                "despesa": despesa
            })
            
        return payload

    def verifica_origem(self,df:pd.DataFrame) -> str:
        """Verifica a origem do arquivo importado, identificando se é um relatório da Shopee ou da Blz com base na estrutura e nas colunas presentes no DataFrame.
            :param df: DataFrame contendo os dados importados do arquivo.
            :return: String indicando a origem do arquivo, classificando como "shopee" para relatórios da Shopee e "blz" para relatórios da Blz, ou levantando um erro caso a origem não possa ser identificada.
        """
        if isinstance(df,dict):
            if 'Itens' in df:
                self.origem = 'blz'
            else:
                self.origem = 'shopee'
        else:        
            if df.shape[1] == 9:
                self.origem = 'shopee'
            elif df.shape[1] == 17:
                self.origem = 'blz'
            else:
                raise ValueError(f"Não foi possível identificar a origem do arquivo. Número de colunas: {df.shape[1]}")
        return self.origem

    def processa_dados_shopee(self,df) -> pd.DataFrame:
        """ Processa os dados do relatório da Shopee, extraindo as informações relevantes das abas de ajustes e renda, padronizando os campos e unificando os lançamentos em um único DataFrame para a aplicação.
            :param df: DataFrame contendo os dados do relatório da Shopee, organizado por abas.
            :return: DataFrame unificado contendo os lançamentos extraídos das abas de ajustes e renda da Shopee, padronizados e organizados para a aplicação.
        """
        lista_dfs = []
        relatorio_summary = df.get("Summary",pd.DataFrame)
        relatorio_renda = df.get("Renda",pd.DataFrame)
        relatorio_adjustment = df.get("Adjustment",pd.DataFrame)
        
        if relatorio_summary.empty:
            raise ValueError("Formato do relatório inválido. Aba Summary não encontrado ou vazio.")
        
        match relatorio_summary.iloc[4,1]:
            case 'shop.storya':
                self.empresa = "Storya"
                self.loja = "Shopee"
            case 'compre.batom':
                self.empresa = "Compre Batom"
                self.loja = "Shopee"
            case 'lojaoutbeauty':
                self.empresa = "Outbeauty"
                self.loja = "Shopee"
            case _:
                raise ValueError(f"Não foi possível identificar a empresa a partir do relatório. Valor encontrado: {relatorio_summary.iloc[4,1]}")
        
        if not relatorio_adjustment.empty:
            df_ajuste = self.tratar_dados_ajustment(relatorio_adjustment)
            df_ajuste = df_ajuste.apply(lambda x: self.extrai_valores_adjustment(x),axis=1)        
            lista_dfs.append(df_ajuste)

        if not relatorio_renda.empty:
            df_renda = self.tratar_dados_renda(relatorio_renda)
            df_renda = df_renda.apply(lambda x: self.extrai_valores_renda(x),axis=1)
            lista_dfs.append(df_renda)

        self.data = self.unifica_lista_lctos(lista_dfs)
        return  
    
    def processa_dados_blz(self,df) -> pd.DataFrame:
        """ Processa os dados do relatório da Blz, extraindo as informações relevantes, padronizando os campos e unificando os lançamentos em um único DataFrame para a aplicação.
            :param df: DataFrame contendo os dados do relatório da Blz, organizado por abas.
            :return: DataFrame unificado contendo os lançamentos extraídos do relatório da Blz, padronizados e organizados para a aplicação.
        """
        if not isinstance(df,dict) or 'Itens' not in df:
            raise ValueError("O arquivo fornecido não possui a estrutura esperada para arquivos BLZ. Verifique se o arquivo contém a aba 'Itens'.")

        self.empresa = "Storya"
        self.loja = "Blz na Web"
            
        df_blz = self.tratar_dados_blz(df.get("Itens"))
        df_blz = df_blz.apply(lambda x: self.extrai_valores_blz(x),axis=1)

        self.data = self.unifica_lista_lctos([df_blz])
        return          

    def carregarArquivo(self,filePath:str,fileType:str=None) -> tuple[str,str,list,pd.DataFrame]:
        """ Carrega o arquivo fornecido pelo usuário, identificando a extensão do arquivo, lendo o conteúdo e processando os dados de acordo com a origem identificada (Shopee ou Blz), retornando as informações relevantes para a aplicação.
            :param filePath: Caminho do arquivo a ser carregado.
            :param fileType: Tipo do arquivo, opcional. Se não fornecido, a extensão será extraída do nome do arquivo.
            :return: Tupla contendo a empresa, loja, data e DataFrame com os dados processados do arquivo, prontos para serem utilizados na aplicação.
        """
        REGEX_FILE_EXTENSION = r'\w+$'
        match:re.Match = None
        df:pd.DataFrame = None
        if not fileType:
            match = re.search(REGEX_FILE_EXTENSION, filePath)
            if not match:
                raise ValueError(f"Não foi possível extrair a extensão do arquivo: {f.name}")
            fileType = match.group(0)
            
        if fileType not in ["csv","xls", "xlsx","text/csv"]:
            raise ValueError(f"Extensão de arquivo não suportada: {fileType}")
        
        if fileType in ["xls"]:
            df = pd.read_excel(filePath,sheet_name=None,engine='xlrd')
        
        if fileType in ["xlsx"]:
            df = pd.read_excel(filePath,sheet_name=None,engine="calamine")
        
        if fileType in ["csv","text/csv"]:
            df = pd.read_csv(filePath,encoding="utf-8")
            
        self.verifica_origem(df)
        if self.origem == "shopee":
            self.processa_dados_shopee(df)
            
        if self.origem == "blz":    
            self.processa_dados_blz(df)
            
        return self.empresa, self.loja, self.data

    def padroniza_valores(self, valor:str) -> float:
        """ Padroniza os valores numéricos extraídos do arquivo convertendo para float.
            :param valor: String representando o valor a ser padronizado.
            :return: Valor padronizado como float.
        """
        return round(abs(valor),2)

    def padroniza_datas(self, data:datetime) -> str:
        """ Padroniza as datas extraídas do arquivo convertendo para o formato "YYYY-MM-DD".
            :param data: Objeto datetime representando a data a ser padronizada.
            :return: Data padronizada como string no formato "YYYY-MM-DD".
        """
        return data.strftime("%Y-%m-%d")

    def extrai_registros(self, empresa:str, report_data:pd.DataFrame, dt_vcto:datetime) -> list[dict]:
        """ Extrai os registros do DataFrame processado, padronizando os valores e as datas, e estruturando os dados em uma lista de dicionários no formato esperado pela API.
            :param empresa: Nome da empresa para a qual os dados estão sendo extraídos.
            :param report_data: DataFrame contendo os dados processados do arquivo, com os lançamentos extraídos e padronizados.
            :param dt_vcto: Data de vencimento a ser associada aos registros extraídos, padronizada para o formato "YYYY-MM-DD".
            :return: Lista de dicionários contendo os registros extraídos, com os valores e as datas padronizadas, estruturados no formato esperado pela API para integração e envio dos dados de forma organizada e eficiente.
        """
        retorno:dict={}
        
        match empresa:
            case "Storya":
                retorno["codemp"] = "31"
                retorno["idLoja"] = "10940" if self.loja == "Blz na Web" else "9227"
            case "Outbeauty":
                retorno["codemp"] = "21"
                retorno["idLoja"] = "9265"
            case "Compre Batom":
                retorno["codemp"] = "31423"
                retorno["idLoja"] = "26196"
        
        retorno["dtVcto"] = dt_vcto.strftime("%Y-%m-%d")

        retorno["registros"] = self.formata_payload(report_data)

        return retorno

class ExcelVr:

    def __init__(self):
        pass

    def ler_arquivo(self,arquivo) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
        """ 
            Lê o conteúdo do arquivo enviado pelo usuário e retorna uma lista de linhas.
                :param arquivo: Arquivo enviado pelo usuário.
                :return cabecalho: Cabeçalho do arquivo.
                :return data_credito: Data do crédito.
                :return conteudo: Conteúdo do arquivo.
        """

        conteudo = arquivo.read()

        cabecalho = pd.read_excel(conteudo,engine="openpyxl",header=5,nrows=4,usecols="B:C")
        data_credito = pd.read_excel(conteudo,engine="openpyxl",header=12,nrows=1,usecols="B:C")
        conteudo = pd.read_excel(conteudo,engine="openpyxl",header=19,usecols="B:J")
        return cabecalho, data_credito, conteudo

    def padroniza_campos(self,cabecalho:pd.DataFrame,data_credito:pd.DataFrame,conteudo:pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
        """
            Padroniza o nome dos campos.
                :param cabecalho: Cabeçalho do arquivo.
                :param data_credito: Data do crédito.
                :param conteudo: Conteúdo do arquivo.
                :return cabecalho: Cabeçalho formatado do arquivo.
                :return data_credito: Data do crédito formatada.
                :return conteudo: Conteúdo formatado do arquivo.
        """
        
        cabecalho['Unnamed: 1'] = cabecalho['Unnamed: 1'].apply(lambda x: x.replace(':',''))
        cabecalho = cabecalho.T.reset_index(drop=True)
        cabecalho.columns = cabecalho.loc[0,:]
        cabecalho.drop(index=0,axis=0,inplace=True)
        cols = conteudo.columns
        cols = [c.replace('.','').replace('(R$)','').strip().replace(' ','_').lower() for c in cols]
        data_credito.pop('Produto')
        conteudo.columns = cols

        return cabecalho, data_credito, conteudo
    
    def extrai_conteudo(self, cabecalho:pd.DataFrame,data_credito:pd.DataFrame,conteudo:pd.DataFrame) -> tuple[dict,dict]:
        """
            Extrai o conteúdo do arquivo Excel pra dicionário.
                :param cabecalho: Cabeçalho formatador do arquivo
                :param data_credito: Data do crédito formatada.
                :param conteudo: Conteúdo formatado do arquivo.
                :return cabecalho: Dicionário contendo o cabeçalho do arquivo com a data do crédito.
                :return conteudo: Dicionário contendo o conteúdo do arquivo.
        """

        cabecalho, data_credito, conteudo = self.padroniza_campos(cabecalho,data_credito,conteudo)
        return cabecalho.to_dict(orient='records')[0] | data_credito.to_dict(orient='records')[0], conteudo.to_dict(orient='records')
