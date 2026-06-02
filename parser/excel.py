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
        return linha["motivo_do_ajuste"] if pd.notna(linha["motivo_do_ajuste"]) else linha["tipo_descricao_do_ajuste"]

    def extrai_valores_adjustment(self,linha:pd.Series):
        
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

        COLUNAS_RELATORIO_VENDA = [ 
            'Ver', 'ID do pedido', 'Data de conclusão do pagamento', 'Quantia total lançada (R$)',
            'Preço do produto', 'Valor do Reembolso', 'Ajuste por pagamento via PIX', 'Cupom',
            'Taxa de frete paga pelo comprador', 'Frete cobrado pelo parceiro logístico',
            'Desconto de frete pela Shopee', 'Incentivo de cupom', 'Taxa de comissão líquida',
            'Taxa de serviço líquida', 'Taxa de transação', 'Taxa de comissão Afiliados do Vendedor',
            'Taxa de Devolução Fácil Shopee'
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
        return linha[[  'valor_do_reembolso',
                        'ajuste_por_pagamento_via_pix',
                        'cupom',
                        'taxa_de_frete_paga_pelo_comprador',
                        'frete_cobrado_pelo_parceiro_logistico',
                        'desconto_de_frete_pela_shopee',
                        'incentivo_de_cupom',
                        'taxa_de_comissao_liquida',
                        'taxa_de_servico_liquida',
                        'taxa_de_transacao',
                        'taxa_de_comissao_afiliados_do_vendedor',
                        'taxa_de_devolucao_facil_shopee'
                    ]].sum()

    def valida_planilha_vs_calculado_shopee(self,linha):
        return True if round(linha['lcto_receita']-linha['lcto_despesa'],2) == linha['quantia_total_lancada_r'] else False
    
    def extrai_valores_renda(self,linha:pd.Series):
        despesa_total:float = self.calcula_despesa_total_shopee(linha)
        pedido_id:str = linha["id_do_pedido"]
        linha['tipo'] = "Renda"
        linha['lcto_pedido'] = pedido_id
        linha['lcto_receita'] = round(float(linha["preco_do_produto"]),2)
        linha['lcto_despesa'] = abs(round(despesa_total,2))        
        linha['lcto_repasse'] = round(linha['lcto_receita']-despesa_total,2)        
        linha['lcto_historico'] = f"Renda do pedido {pedido_id}"
        linha['lcto_data'] = pd.to_datetime(linha["data_de_conclusao_do_pagamento"]).strftime("%Y-%m-%d")
        linha['confirmado'] = self.valida_planilha_vs_calculado_shopee(linha)
        linha['divergencia'] = None if self.valida_planilha_vs_calculado_shopee(linha) else round(linha['lcto_receita']-linha['lcto_despesa'],2)
        return linha
    
    # BLZ
    def tratar_dados_blz(self,df:pd.DataFrame) -> pd.DataFrame:
        
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
        if linha['descricao_do_evento']=="Devolução total":
            return linha['valor_repasse']
        return linha[['valor_da_comissao','taxa_blz_envios']].sum()

    def valida_historico_blz(self,linha:pd.Series):
        if linha['descricao_do_evento']=="Devolução total":
            return f"Devolução total do pedido {linha["numero_do_pedido"]}"
        return f"Renda do pedido {linha["numero_do_pedido"]}"

    def valida_planilha_vs_calculado_blz(self,linha):
        return True if (linha['descricao_do_evento']=="Devolução total") or (round(linha['lcto_receita']-linha['lcto_despesa'],2) == linha['valor_repasse']) else False

    def valida_tipo_blz(self,linha:pd.Series):
        return "Renda" if linha['descricao_do_evento']=="Pacote entregue" else "Ajuste"    

    def calcula_divergencia_blz(self,linha:pd.Series):
        taxa_fixa_frete = 5.5
        taxa_comissao = .22        
        return linha['lcto_receita']-(linha['lcto_despesa']-taxa_fixa_frete)/taxa_comissao

    def extrai_valores_blz(self,linha:pd.Series):
        
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
        COLUNAS = ['tipo','lcto_pedido','lcto_receita','lcto_despesa','lcto_repasse','lcto_historico','lcto_data','confirmado','divergencia']
        lista_unificada:pd.DataFrame = pd.concat([df[COLUNAS] for df in dfs]).sort_values(['tipo','lcto_data','lcto_historico']).reset_index(drop=True)
        return lista_unificada

    def formata_payload(self,df:pd.DataFrame) -> list[dict]:
        payload:list[dict] = []
        
        for i in df.index.to_list():
            receita:dict = {}
            despesa:dict = {}            
            linha = df.iloc[i,:]
            
            receita = {
                "valor": linha["lcto_receita"],
                "descricao": linha["lcto_historico"],
                "data": linha["lcto_data"],
                "pendente": True
            } if not pd.isna(linha["lcto_receita"]) else None

            despesa = {
                "valor": linha["lcto_despesa"],
                "descricao": linha["lcto_historico"],
                "data": linha["lcto_data"],
                "pendente": True
            } if not pd.isna(linha["lcto_despesa"]) else None
                
            payload.append({
                "id_pedido": linha["lcto_pedido"],
                "receita": receita,
                "despesa": despesa
            })
            
        return payload

    def verifica_origem(self,df:pd.DataFrame) -> str:
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
        
        lista_dfs = []
        relatorio_summary = df.get("Summary")
        relatorio_renda = df.get("Renda")
        relatorio_adjustment = df.get("Adjustment")
        
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
        
        if relatorio_adjustment:
            df_ajuste = self.tratar_dados_ajustment(relatorio_adjustment)
            df_ajuste = df_ajuste.apply(lambda x: self.extrai_valores_adjustment(x),axis=1)        
            lista_dfs.append(df_ajuste)

        if relatorio_renda:
            df_renda = self.tratar_dados_renda(relatorio_renda)
            df_renda = df_renda.apply(lambda x: self.extrai_valores_renda(x),axis=1)
            lista_dfs.append(df_renda)

        self.data = self.unifica_lista_lctos(lista_dfs)
        return  
    
    def processa_dados_blz(self,df) -> pd.DataFrame:

        if not isinstance(df,dict) or 'Itens' not in df:
            raise ValueError("O arquivo fornecido não possui a estrutura esperada para arquivos BLZ. Verifique se o arquivo contém a aba 'Itens'.")

        self.empresa = "Storya"
        self.loja = "Blz na Web"
            
        df_blz = self.tratar_dados_blz(df.get("Itens"))
        df_blz = df_blz.apply(lambda x: self.extrai_valores_blz(x),axis=1)

        self.data = self.unifica_lista_lctos([df_blz])
        return          

    def carregarArquivo(self,filePath:str,fileType:str=None) -> tuple[str,str,list,pd.DataFrame]:

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
        return round(abs(valor),2)

    def padroniza_datas(self, data:datetime) -> str:
        return data.strftime("%Y-%m-%d")

    def extrai_registros(self, empresa:str, report_data:pd.DataFrame, dt_vcto:datetime) -> list[dict]:
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
