from parser_cnab240 import ParserCnab240
from sankhya import Sankhya
import time
import asyncio
import pandas as pd
import streamlit as st

def ler_arquivo(arquivo) -> list[str]:
    """Lê o conteúdo do arquivo enviado pelo usuário e retorna uma lista de linhas."""

    conteudo = arquivo.read().decode("utf-8")
    return conteudo.split('\n')

def extrai_conteudo(conteudo:list[str]) -> dict:
    """Extrai o conteúdo do arquivo CNAB240 utilizando o parser adequado conforme o banco identificado."""

    cnab = ParserCnab240()
    extracao:dict={}

    if conteudo[0][0:3] == '237':
        extracao = cnab.bradesco(conteudo=conteudo)
    elif conteudo[0][0:3] == '341':
        extracao = cnab.itau(conteudo=conteudo)
    else:
        extracao = {}

    extracao = cnab.padroniza_campos(extracao)

    return extracao

def busca_funcionarios(_snk:Sankhya,token:str,dados:list[dict]) -> list[dict]:
    """Busca os códigos Sankhya dos funcionários com base nos nomes fornecidos."""

    import time
    for d in dados:
        d['codigo_parceiro'] = asyncio.run(_snk.busca_parceiro(token=token,texto=d.get('nome')))
        time.sleep(0.5)
    return dados

def busca_banco(_snk:Sankhya,token:str,dados:dict) -> dict:
    """Busca o código Sankhya da conta bancária com base nos dados bancários fornecidos."""

    retorno = asyncio.run(_snk.busca_conta_bancaria(token=token,dados_bancarios=dados))
    dados['codigo_conta'], dados['codigo_empresa'] = retorno.get('codctabcoint'), retorno.get('codemp')
    return dados

def converte_dataframe(conteudo:list[dict]) -> pd.DataFrame:
    """Converte a lista de dicionários em um DataFrame do Pandas e adiciona colunas."""

    df = pd.DataFrame(conteudo)
    df['natureza'] = 'Salário'
    df['referencia'] = ''
    df['inicio_ferias'] = None
    df['fim_ferias'] = None
    cols = df.columns
    cols = [c.replace("_"," ").capitalize() for c in cols]
    df.columns = cols
    return df

def filtra_colunas(dataframe:pd.DataFrame) -> pd.DataFrame:
    """Filtra as colunas do DataFrame para exibir apenas as necessárias."""

    return dataframe[['Nome','Codigo parceiro','Valor pagamento','Data pagamento','Referencia','Natureza','Inicio ferias','Fim ferias']]

def formata_cabecalho(header:dict,trailer:dict) -> pd.DataFrame:
    """Formata o cabeçalho e trailer em um DataFrame do Pandas."""

    dados = [header | trailer]

    df = pd.DataFrame(dados)
    df['conta_bancaria'] = f"{dados[0].get('conta')}-{dados[0].get('dv')}" if dados[0].get('dv') in df.columns else str(dados[0].get('conta'))[:-1]+'-'+str(dados[0].get('conta'))[-1]
    df['banco'] = f"{dados[0].get('codigo_banco')} - {dados[0].get('banco')}"
    df['valor_total'] = f"R$ {dados[0].get('valor_total'):,.2f}"
    cols = df.columns
    cols = [c.replace("_"," ").capitalize() for c in cols]
    df.columns = cols
    df = df.rename(columns={"Nome":"Empresa"})    
    return df[['Empresa','Codigo empresa','Banco','Conta bancaria','Codigo conta','Qtde registros','Valor total']]

def enviar_dados(dados_bancarios:dict,dados_lancamentos:list[dict],tipo_lcto:str) -> int:
    """Envia os dados formatados para a Sankhya e retorna o número de registros realizados."""

    snk = Sankhya()
    my_bar = st.progress(0, text="Preparando dados...")
    payload:list[dict]=[]

    payload = snk.formata_lancamentos_sankhya(dados_bancarios=dados_bancarios,
                                              dados_lancamentos=dados_lancamentos,
                                              tipo_lcto=tipo_lcto)
    time.sleep(1)

    my_bar.progress(int(100/3*1), text="Enviando lançamentos...")
    token = asyncio.run(snk.logar())
    time.sleep(1)

    my_bar.progress(int(100/3*2), text="Enviando lançamentos...")
    registros_realizados:int = asyncio.run(snk.registrar_despesas(token=token.get('bearerToken'),lancamentos=payload))
    time.sleep(1)

    my_bar.progress(int(100/3*3), text="Concluído!")
    time.sleep(2)

    my_bar.empty()

    return registros_realizados

@st.cache_data(show_spinner=False)
def rotina(arquivo) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Rotina principal para processar o arquivo e retornar os dados formatados."""

    my_bar = st.progress(0, text="Carregando arquivo...")
    conteudo = ler_arquivo(arquivo)
    time.sleep(1)

    my_bar.progress(int(100/7*1), text="Extraindo conteúdo...")
    dados = extrai_conteudo(conteudo)
    time.sleep(1)

    my_bar.progress(int(100/7*2), text="Validando dados bancários...")
    snk = Sankhya()
    token = asyncio.run(snk.logar())
    if not token:
        my_bar.empty()
        st.error("Não foi possível autenticar na Sankhya.")
        return None, None
    time.sleep(1)
    dados['header_arquivo'] = busca_banco(snk, token.get('bearerToken'), dados.get('header_arquivo'))
    time.sleep(1)

    my_bar.progress(int(100/7*3), text="Buscando dados dos funcionários...")
    lista_lctos = busca_funcionarios(snk, token.get('bearerToken'), dados.get('detalhes'))
    time.sleep(1)

    my_bar.progress(int(100/7*4), text="Finalizando...")
    lista_lctos = converte_dataframe(lista_lctos)
    time.sleep(1)

    my_bar.progress(int(100/7*5), text="Finalizando...")
    lista_lctos = filtra_colunas(lista_lctos)
    time.sleep(1)

    my_bar.progress(int(100/7*6), text="Finalizando...")
    dados_cabecalho = formata_cabecalho(dados.get('header_arquivo'),dados.get('trailer_lote')[0])
    time.sleep(1)

    my_bar.progress(int(100/7*7), text="Concluído!")
    time.sleep(2)

    my_bar.empty()

    return dados_cabecalho, lista_lctos

if __name__ == "__main__":
    st.set_page_config(page_title="Importador da folha", layout="wide")
    st.title("💰 Importador de folha de pagamento - BASE TESTE")

    if 'arquivo' not in st.session_state:
        st.session_state.arquivo = None
    if 'dados_cabecalho' not in st.session_state:
        st.session_state.dados_cabecalho = pd.DataFrame()
    if 'lista_lctos' not in st.session_state:
        st.session_state.lista_lctos = pd.DataFrame()
    
    with open("ajuda.md", "r", encoding="utf-8") as f:
        md = f.read()
    with st.sidebar:
        st.header("ℹ️ Como utilizar:")
        st.markdown(md)

    st.session_state.arquivo = st.file_uploader("Selecione um arquivo", type=["txt"])
    if st.session_state.arquivo:
        st.session_state.dados_cabecalho, st.session_state.lista_lctos = rotina(st.session_state.arquivo)

        if not all([isinstance(st.session_state.dados_cabecalho,bool),isinstance(st.session_state.lista_lctos,bool)]):
            st.subheader("Cabeçalho")
            st.table(st.session_state.dados_cabecalho)

            st.subheader("Lançamentos")
            naturezas = ["Salário","Férias"]
            opcoes_tipo_lcto = ["Salário","Adiantamento"]
            tipo_lcto = st.pills(label="Tipo de lançamento", options=opcoes_tipo_lcto, default=opcoes_tipo_lcto[0], selection_mode="single")
            referencia:str = (pd.to_datetime(st.session_state.lista_lctos.at[0,'Data pagamento'],format='%d/%m/%Y') - pd.DateOffset(months=1)).strftime('%m/%Y') if tipo_lcto == "Salário" else pd.to_datetime(st.session_state.lista_lctos.at[0,'Data pagamento'],format='%d/%m/%Y').strftime('%m/%Y')
            st.session_state.lista_lctos['Referencia'] = referencia            
            df = st.data_editor(
                st.session_state.lista_lctos,
                hide_index=True,
                column_config={
                    "Nome": st.column_config.TextColumn(),
                    "Codigo sankhya": st.column_config.NumberColumn(),
                    "Valor pagamento": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Natureza": st.column_config.SelectboxColumn(options=naturezas,required=True),
                    "Inicio ferias": st.column_config.DateColumn(help="Preencha apenas para lançamentos de Férias",format="DD/MM/YYYY"),
                    "Fim ferias": st.column_config.DateColumn(help="Preencha apenas para lançamentos de Férias",format="DD/MM/YYYY")
                })
            
            btn_enviar = st.button("Enviar",use_container_width=True)
            if btn_enviar:            
                if not all([not st.session_state.dados_cabecalho.empty, not df.empty,tipo_lcto]):
                    st.warning(body="Faltam informações. Verifique se o arquivo foi importado corretamente e se o Tipo de lançamento foi informado")
                else:
                    registros_enviados:int = enviar_dados(dados_bancarios=st.session_state.dados_cabecalho.to_dict(orient='records')[0],
                                                        dados_lancamentos=df.to_dict(orient='records'),
                                                        tipo_lcto=tipo_lcto)
                    if registros_enviados:
                        st.success(f'{registros_enviados} registros enviados com sucesso!', icon="✅")
                        st.balloons()
                        time.sleep(2)
                        st.cache_data.clear()
                        st.session_state.arquivo = None
                        st.session_state.dados_cabecalho = pd.DataFrame()
                        st.session_state.lista_lctos = pd.DataFrame()
                        rotina.clear()
                    else:
                        st.error('Falha ao realizar os registros', icon="🚨")
        else:
            st.warning("Dados do arquivo não puderam ser extraídos. Verifique se o arquivo é válido.")
    if not st.session_state.arquivo and any([not st.session_state.dados_cabecalho.empty,not st.session_state.lista_lctos.empty]):
        st.session_state.dados_cabecalho, st.session_state.lista_lctos = pd.DataFrame(), pd.DataFrame()
        rotina.clear()
