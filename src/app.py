from parser import cnab240, excel_vr
from src.sankhya import Sankhya
import time
import pandas as pd
import streamlit as st

class App:

    def __init__(self):
        self.tipo_rotina:str['folha' | 'vr']=None

    async def busca_funcionarios(
            self,
            snk:Sankhya,
            token:str,
            dados:list[dict]
        ) -> list[dict]:
        """ Busca os códigos Sankhya dos funcionários com base nos nomes fornecidos.
                :param snk: Instância da classe Sankhya.
                :param token: Token de autenticação da Sankhya.
                :param dados: Lista de dicionários contendo os dados dos funcionários.
                :return list[dict]: Lista de dicionários contendo os dados dos funcionários com os códigos Sankhya.
        """

        import time
        if self.tipo_rotina == 'folha':
            for d in dados:
                d['codigo_parceiro'] = await snk.busca_parceiro(token=token,nome=d.get('nome'))
                time.sleep(0.5)
        if self.tipo_rotina == 'vr':
            for d in dados:
                d['codigo_parceiro'], d['codigo_empresa'] = await snk.busca_parceiro_empresa(token=token,nome=d.get('nome'),cpf=d.get('cpf'))
                time.sleep(0.5)
        return dados

    async def busca_banco(
            self,
            snk:Sankhya,
            token:str,
            dados:dict={},
            cnpj:str=None
        ) -> dict:
        """
            Busca o código Sankhya da conta bancária com base nos dados bancários fornecidos.
                :param snk: Instância da classe Sankhya.
                :param token: Token de autenticação da Sankhya.
                :param dados: Dicionário contendo os dados do banco.
                :param cnpj: CNPJ da empresa.
                :return dict: Dicionário contendo os dados do banco de da conta.            
        """

        retorno = await snk.busca_conta_bancaria(token=token,
                                                 codigo_banco=dados.get('codigo_banco'),
                                                 numero_agencia=dados.get('agencia'),
                                                 numero_conta=f"{dados.get('conta')}{dados.get('dv')}" if dados.get('dv') else f"{dados.get('conta')}",
                                                 cnpj=cnpj)
        if self.tipo_rotina == 'folha':
            dados = dados | retorno
        if self.tipo_rotina == 'vr':
            dados = retorno
            
        return dados

    def converte_dataframe(
            self,
            conteudo:list[dict],
            dados_cabecalho:dict=None            
        ) -> pd.DataFrame:
        """
            Converte a lista de dicionários em um DataFrame do Pandas e adiciona colunas.
                :param conteudo: Lista de dicionários contendo os dados dos lançamentos.
                :param dados_cabecalho: Dicionário contendo os dados do cabeçalho.
                :return pd.DataFrame: DataFrame contendo os dados dos lançamentos.        
        """

        df = pd.DataFrame(conteudo)
        if self.tipo_rotina == 'folha':            
            df['natureza'] = 'Salário'
            df['referencia'] = ''
            df['inicio_ferias'] = None
            df['fim_ferias'] = None
            cols = df.columns
            cols = [c.replace("_"," ").capitalize() for c in cols]
            df.columns = cols
        if self.tipo_rotina == 'vr':
            df['natureza'] = 'Vale alimentação'
            df['referencia'] = f"PGTO ALIMENTAÇÃO {dados_cabecalho.get('Data do Crédito').strftime('%m/%Y')}" 
            cols = df.columns
            cols = [c.replace("_"," ").capitalize() for c in cols]
            df.columns = cols            

        return df

    def filtra_colunas(
            self,
            dataframe:pd.DataFrame
        ) -> pd.DataFrame:
        """
            Filtra as colunas do DataFrame para exibir apenas as necessárias.            
                :param dataframe: DataFrame contendo os dados dos lançamentos.
                :return pd.DataFrame: DataFrame contendo apenas as colunas filtradas.
        """

        if self.tipo_rotina == 'folha':
            return dataframe[['Nome','Codigo parceiro','Valor pagamento','Data pagamento','Referencia','Natureza','Inicio ferias','Fim ferias']]
        if self.tipo_rotina == 'vr':
            return dataframe[['Nome','Codigo parceiro','Valor do benefício','Referencia','Natureza']]

    def formata_cabecalho(
            self,
            header:dict=None,
            trailer:dict=None,
            cabecalho:dict=None,
            dados_banco:dict=None
        ) -> pd.DataFrame:
        """
            Formata o cabeçalho e trailer em um DataFrame do Pandas.
                :param header: Dicionário contendo os dados do cabeçalho, se arquivo CNAB.
                :param trailer: Dicionário contendo os dados do trailer, se arquivo CNAB.
                :param cabecalho: Dicionário contendo os dados do cabeçalho, se arquivo Excel.
                :param dados_banco: Dicionário contendo os dados do banco, se arquivo Excel.
                :return pd.DataFrame: DataFrame formatado.
        """

        if self.tipo_rotina == 'folha':
            dados = [header | trailer]
            df = pd.DataFrame(dados)
            df['valor_total'] = f"R$ {dados[0].get('valor_total'):,.2f}"
            df['qtde_registros'] = df['qtde_registros'].astype(str)
            cols = df.columns
            cols = [c.replace("_"," ").capitalize() for c in cols]
            df.columns = cols
            return df[['Empresa','Banco','Conta','Qtde registros','Valor total']]
        if self.tipo_rotina == 'vr':
            dados = [ cabecalho | dados_banco ]
            df = pd.DataFrame(dados)                        
            df['Data do Crédito'] = df['Data do Crédito'].apply(lambda x: x.strftime('%d/%m/%Y'))
            cols = df.columns
            cols = [c.replace("_"," ").capitalize() for c in cols]
            df.columns = cols
            return df[['Empresa','Pedido','Data do crédito','Conta','Banco']]

    async def enviar_dados(
            self,
            dados_bancarios:dict,
            dados_lancamentos:list[dict],
            tipo_lcto:str
        ) -> int:
        """
            Envia os dados formatados para a Sankhya e retorna o número de registros realizados.
                :param dados_bancarios: Dicionário contendo os dados do banco.
                :param dados_lancamentos: Lista de dicionários contendo os dados dos lançamentos.
                :param tipo_lcto: Tipo de lançamento.
                :return int: Número de registros realizados.
        """

        snk = Sankhya()
        my_bar = st.progress(0, text="Preparando dados...")
        payload:list[dict]=[]

        payload = snk.formata_lancamentos_sankhya(dados_bancarios=dados_bancarios,
                                                  dados_lancamentos=dados_lancamentos,
                                                  tipo_lcto=tipo_lcto)
        time.sleep(1)

        my_bar.progress(int(100/3*1), text="Enviando lançamentos...")
        token = await snk.logar()
        time.sleep(1)

        my_bar.progress(int(100/3*2), text="Enviando lançamentos...")
        registros_realizados:int = await snk.registrar_despesas(token=token.get('bearerToken'),lancamentos=payload)
        time.sleep(1)

        my_bar.progress(int(100/3*3), text="Concluído!")
        time.sleep(2)

        my_bar.empty()

        return registros_realizados

    def verifica_tipo_arquivo(self,arquivo):
        """
            Verifica o tipo de arquivo e retorna a rotina correspondente.
                :param arquivo: Arquivo enviado pelo usuário
                :return rotina: Rotina correspondente ao tipo de arquivo.    
        """

        rotina = None
        if arquivo.type == 'application/vnd.ms-excel':
            self.tipo_rotina = 'vr'
            rotina = self.rotina_vr
        if arquivo.type == 'text/plain':
            self.tipo_rotina = 'folha'
            rotina = self.rotina_folha
        return rotina

    @st.cache_resource(show_spinner=False)
    async def rotina_folha(_self, arquivo) -> tuple[pd.DataFrame,pd.DataFrame]:
        """
            Rotina principal para processar o arquivo CNAB e retornar os dados formatados.
                :param arquivo: Arquivo enviado pelo usuário
                :return dados_cabecalho: Dicionário contendo os dados do cabeçalho.
                :return lista_lctos: Lista de dicionários contendo os dados dos funcionários.
        """
        
        parser = cnab240.Cnab240()
        
        my_bar = st.progress(0, text="Carregando arquivo...")
        conteudo = parser.ler_arquivo(arquivo)
        time.sleep(1)

        my_bar.progress(int(100/7*1), text="Extraindo conteúdo...")
        dados = parser.extrai_conteudo(conteudo)
        time.sleep(1)

        my_bar.progress(int(100/7*2), text="Validando dados bancários...")
        snk = Sankhya()
        token = await snk.logar()
        if not token:
            my_bar.empty()
            st.error("Não foi possível autenticar na Sankhya.")
            return None, None
        time.sleep(1)
        dados['header_arquivo'] = await _self.busca_banco(snk, token.get('bearerToken'), dados.get('header_arquivo'))
        time.sleep(1)

        my_bar.progress(int(100/7*3), text="Buscando dados dos funcionários...")
        lista_lctos = await _self.busca_funcionarios(snk, token.get('bearerToken'), dados.get('detalhes'))
        time.sleep(1)

        my_bar.progress(int(100/7*4), text="Finalizando...")
        lista_lctos = _self.converte_dataframe(lista_lctos)
        time.sleep(1)

        my_bar.progress(int(100/7*5), text="Finalizando...")
        lista_lctos = _self.filtra_colunas(lista_lctos)
        time.sleep(1)

        my_bar.progress(int(100/7*6), text="Finalizando...")
        dados_cabecalho = _self.formata_cabecalho(dados.get('header_arquivo'),dados.get('trailer_lote')[0])
        time.sleep(1)

        my_bar.progress(int(100/7*7), text="Concluído!")
        time.sleep(2)

        my_bar.empty()

        return dados_cabecalho, lista_lctos

    @st.cache_resource(show_spinner=False)
    async def rotina_vr(_self, arquivo) -> tuple[pd.DataFrame,pd.DataFrame]:
        """
            Rotina principal para processar o arquivo Excel e retornar os dados formatados.
                :param arquivo: Arquivo enviado pelo usuário
                :return dados_cabecalho: Dicionário contendo os dados do cabeçalho.
                :return lista_lctos: Lista de dicionários contendo os dados dos funcionários.
        """
        
        parser = excel_vr.ExcelVr()
        
        my_bar = st.progress(0, text="Carregando arquivo...")
        cabecalho,data_credito,conteudo = parser.ler_arquivo(arquivo)
        time.sleep(1)

        my_bar.progress(int(100/7*1), text="Extraindo conteúdo...")
        dados_cabecalho, dados_conteudo = parser.extrai_conteudo(cabecalho,data_credito,conteudo)
        time.sleep(1)

        my_bar.progress(int(100/7*2), text="Validando dados bancários...")
        snk = Sankhya()
        token = await snk.logar()
        if not token:
            my_bar.empty()
            st.error("Não foi possível autenticar na Sankhya.")
            return None, None
        time.sleep(1)
        dados_banco = await _self.busca_banco(snk, token.get('bearerToken'), cnpj=dados_cabecalho.get('CNPJ'))
        time.sleep(1)

        my_bar.progress(int(100/7*3), text="Buscando dados dos funcionários...")
        lista_lctos = await _self.busca_funcionarios(snk, token.get('bearerToken'), dados_conteudo)
        time.sleep(1)

        my_bar.progress(int(100/7*4), text="Finalizando...")
        lista_lctos = _self.converte_dataframe(lista_lctos,dados_cabecalho)
        time.sleep(1)

        my_bar.progress(int(100/7*5), text="Finalizando...")
        lista_lctos = _self.filtra_colunas(lista_lctos)
        time.sleep(1)

        my_bar.progress(int(100/7*6), text="Finalizando...")
        dados_cabecalho = _self.formata_cabecalho(cabecalho=dados_cabecalho,dados_banco=dados_banco)
        time.sleep(1)

        my_bar.progress(int(100/7*7), text="Concluído!")
        time.sleep(2)

        my_bar.empty()

        return dados_cabecalho, lista_lctos

