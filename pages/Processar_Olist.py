import time
import numpy as np
import pandas as pd
import streamlit as st
from parser.excel import Ecommerce
from datetime import datetime

st.set_page_config(page_title="Processar títulos de E-commerce",
                   initial_sidebar_state="collapsed",
                   layout="wide",
                   page_icon="🛒")

if 'done' not in st.session_state:
    st.session_state.done = False

if 'empresa' not in st.session_state:
    st.session_state.empresa = ""

if 'loja' not in st.session_state:
    st.session_state.loja = ""

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

if 'data' not in st.session_state:
    st.session_state.data = {
        "selection": {
            "rows": [],
            "columns": [],
            "data": []
        }
    }

if 'aviso' not in st.session_state:
    st.session_state.aviso = {"texto":"","tipo":""}
    
if 'andamento' not in st.session_state:
    st.session_state.andamento = None
    
if 'remessa' not in st.session_state:
    st.session_state.remessa = {  }
    
if "disabled" not in st.session_state:
    st.session_state.disabled = False    
    
if "dtvcto" not in st.session_state:
    st.session_state.dtvcto = datetime.now().date()

if "previsao" not in st.session_state:
    st.session_state.previsao = ""

OLIST_SESSION_KEYS = {
    "done",
    "empresa",
    "loja",
    "df",
    "data",
    "aviso",
    "andamento",
    "remessa",
    "disabled",
    "dtvcto",
    "previsao",
    "file_uploader",
    "btn_confirmar",
    "btn_acao",
}
OLIST_SESSION_PREFIXES = ("divergencia_", "receita_", "despesa_", "repasse_")

def limpar_estado_olist():
    for key in list(st.session_state.keys()):
        if key in OLIST_SESSION_KEYS or str(key).startswith(OLIST_SESSION_PREFIXES):
            del st.session_state[key]

def processar_revisao(i:int):
    """ Valida os valores de receita e despesa após input do usuário
        :param i (int): Índice do registro a ser validado
    """
    if  (
            f"divergencia_{i}" in st.session_state
        ) and (
            st.session_state[f"divergencia_{i}"]!=0.0
        ) and ((
            round(st.session_state[f"receita_{i}"],2) != round(st.session_state.df.loc[i,"lcto_receita"],2)
        ) or (
            round(st.session_state[f"despesa_{i}"],2) != round(st.session_state.df.loc[i,"lcto_despesa"],2)
        )):
            st.session_state[f"divergencia_{i}"] = (
                round(st.session_state[f"receita_{i}"] - st.session_state[f"despesa_{i}"],2) - round(st.session_state[f"repasse_{i}"],2)
            )
            st.session_state.df.loc[i,"lcto_receita"] = round(st.session_state[f"receita_{i}"],2)
            st.session_state.df.loc[i,"lcto_despesa"] = round(st.session_state[f"despesa_{i}"],2)
            st.session_state.df.loc[i,"divergencia"] = round(st.session_state[f"divergencia_{i}"],2)
            if st.session_state.df.loc[i,"divergencia"] == 0:
                st.session_state.df.loc[i,"confirmado"] = True

@st.dialog("Revisão de repasses",icon="⚠️",width='medium')
def revisao():
    """ Modal para revisão dos registros com divergência entre o cálculo do repasse e o valor da planilha.
        Permite ajuste manual dos valores de receita e despesa para correção do repasse.
        O campo de divergência é atualizado automaticamente conforme os ajustes são feitos.
    """
    for i in st.session_state.df.loc[st.session_state.df["confirmado"]==False].index:
        with st.container(border=True,key=f'container_{i}'):
            st.write(st.session_state.df.loc[i,"lcto_historico"])
            colA, colB, colC, colD = st.columns(4,vertical_alignment='bottom')
            colA.number_input("Vlr. Receita",value=st.session_state.df.loc[i,"lcto_receita"],key=f'receita_{i}',on_change=processar_revisao,args=(i,))
            colB.number_input("Vlr. Despesa",value=st.session_state.df.loc[i,"lcto_despesa"],key=f'despesa_{i}',on_change=processar_revisao,args=(i,))
            colC.number_input("Vlr. Repasse",value=st.session_state.df.loc[i,"lcto_repasse"],key=f'repasse_{i}',on_change=processar_revisao,args=(i,))
            colD.number_input("Divergência",value=st.session_state.df.loc[i,"divergencia"],key=f'divergencia_{i}',disabled=True)
    
    if st.session_state.df["divergencia"].sum() == 0:
        st.rerun()

def finalizar():
    """Exibe mensagem de conclusão e limpa os dados da sessão para novo processamento"""
    st.success("Registros processados com sucesso!",icon="✅")
    progress_text = "Saindo..."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.05)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()
    limpar_estado_olist()
    st.rerun()  

def iniciar_processamento():
    """Seta a variável que controla o botão de processar."""
    st.session_state.disabled = True

def calcular_previsao():
    """Calcula a previsão de tempo para processamento dos registros selecionados com base no tempo médio por registro definido nas variáveis de ambiente."""
    previsao_segundos = float(st.secrets["tempo_medio_lcto"]) * (len(st.session_state.data["selection"]["rows"])*2)
    previsao_minutos = round(previsao_segundos/60)
    texto = f"{previsao_minutos} minutos" if previsao_minutos > 0 else f"{round(previsao_segundos)} segundos"
    st.session_state.previsao = f"Previsão: {texto} (~{st.secrets["tempo_medio_lcto"]}s por registro)"
    return

@st.dialog("Confirmação")
def confirmacao():
    """ Modal de confirmação para processamento dos registros selecionados.
        Exibe a previsão de tempo para conclusão do processamento.
    """
    calcular_previsao()
    
    if len(st.session_state.data.get("selection",{}).get("rows",[])) == 1:
        st.write(f"Deseja processar o registro selecionado com vencimento para {st.session_state.dtvcto.strftime("%d/%m/%Y")}?")
        st.caption(st.session_state.previsao,text_alignment="center")
    else:
        st.write(f"Deseja processar os {len(st.session_state.data["selection"]["rows"])} registros selecionados com vencimento para {st.session_state.dtvcto.strftime("%d/%m/%Y")}?")
        st.caption(st.session_state.previsao,text_alignment="center")

    if st.button("Confirmar",type="primary",width='stretch',key="btn_confirmar",disabled=st.session_state.disabled,on_click=iniciar_processamento):        
        processar_selecionados()
    
    if st.button("Cancelar",type="tertiary",width='stretch'):
        st.rerun()
    
def processar_selecionados():
    """ Processa os registros selecionados.
        Salva uma cópia local dos registros a serem processados para conferência futura e envia para a API.
        Exibe mensagens de sucesso ou erro conforme o resultado da requisição."""
    response = None
    try:
        with st.spinner("Processando...",show_time=True,width="stretch"):
            st.session_state.remessa = ecomm.extrai_registros(st.session_state.empresa,
                                                            st.session_state.df.loc[st.session_state.data["selection"]["rows"]],
                                                            st.session_state.dtvcto)
            import json
            from datetime import datetime
            with open(f"remessas/olist/{st.session_state.empresa.replace(" ","")}_{st.session_state.loja.replace(" ","")}_{datetime.now().date().strftime('%Y%m%d')}.test.json","w",encoding='utf-8') as f:
                json.dump(st.session_state.remessa,f,indent=4,default=str,ensure_ascii=False)
            
            if st.session_state.remessa:
                import requests
                response = requests.post(url=st.secrets["api_url"],
                                        json=normalize(st.session_state.remessa))
        if response and response.status_code == 200:
            finalizar()
        else:
            st.error(f"Erro {response.status_code}: Ocorreu um erro ao processar os registros. Tente novamente mais tarde.\n{response.json()}",icon="❌")
        st.session_state.disabled=False
    except Exception as e:
        st.error(f"Erro: {str(e)}",icon="❌")
        st.session_state.disabled=False

def normalize(obj):
    """Função recursiva para normalizar os dados antes de enviar para a API.
       Converte tipos de dados específicos (como numpy) para tipos nativos do Python que podem ser serializados em JSON."""
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [normalize(v) for v in obj]

    if isinstance(obj, np.integer):
        return str(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.bool_):
        return bool(obj)

    return obj

def montar_aviso():
    """Configura a mensagem de aviso e o estado do botão de ação com base na presença de divergências nos registros carregados.
       Se houver registros com divergências, o aviso é configurado para solicitar revisão.
       Caso contrário, o aviso indica que os registros estão prontos para processamento.
    """
    if st.session_state.df.shape[0] != st.session_state.df["confirmado"].sum():
        st.session_state.aviso["texto"] = f"{st.session_state.df.shape[0]} registros carregados. **:red[{st.session_state.df.shape[0]-st.session_state.df["confirmado"].sum()} registros com divergência]**‼️"
        st.session_state.aviso["tipo"] = "warning"
        st.session_state.aviso["pendente"] = True
        st.session_state.aviso["btnDesc"] = "Revisar"
        st.session_state.aviso["btnType"] = "primary"   
    else:
        if all(pd.isna(st.session_state.df[['divergencia']]).values):
            st.session_state.aviso["texto"] = f"{st.session_state.df.shape[0]} registros carregados. Nenhum registro com divergência ☑️"
        else:
            st.session_state.aviso["texto"] = f"{st.session_state.df.shape[0]} registros carregados. Todas as divergências foram revisadas 💡"
        st.session_state.aviso["tipo"] = "success"
        st.session_state.aviso["pendente"] = True
        st.session_state.aviso["btnDesc"] = "Processar"
        st.session_state.aviso["btnType"] = "secondary"
        st.session_state.df_revisao = pd.DataFrame()
    return

def valida_arquivo_carregado():
    """Valida se existe um arquivo carregado na sessão.
       Se não houver, limpa os dados da sessão para evitar inconsistências.
    """
    if not st.session_state.file_uploader:
        limpar_estado_olist()

def mostrar_aviso():
    """Exibe o aviso configurado na sessão.
       O tipo do aviso determina o estilo da mensagem exibida (warning ou success).
       Após exibir o aviso, a função marca o aviso como não pendente para evitar que seja exibido novamente sem uma nova ação do usuário.
    """
    
    match st.session_state.aviso["tipo"]:
        case "warning":
            container_aviso.warning(st.session_state.aviso["texto"])
            st.session_state.aviso["pendente"] = False
        case "success":
            container_aviso.success(st.session_state.aviso["texto"])
            st.session_state.aviso["pendente"] = False
        case _:
            pass
    return

# Carrega os arquivos de ajuda
with open(st.secrets["path_ajuda_olist"], "r", encoding="utf-8") as f:
    md_olist = f.read()
with st.sidebar:
    st.header("ℹ️ Como utilizar:")
    st.markdown(md_olist)

st.title("Processar títulos de E-commerce")

colA, colB = st.columns([.75,.25],vertical_alignment='bottom')
arquivoUpload = colA.file_uploader("Selecione um arquivo",
                  type=["xls","xlsx"],
                  key="file_uploader",
                  label_visibility="collapsed",
                  accept_multiple_files=False,
                  on_change=valida_arquivo_carregado,
                  disabled=st.session_state.disabled)

with colB:
    st.caption("Data vcto")
    st.date_input("Data vcto",
                   key="dtvcto",
                   label_visibility="collapsed",
                   format="DD/MM/YYYY",
                   disabled=st.session_state.disabled)

col1, col2, col3, col4, col5 = st.columns(5,vertical_alignment='bottom')
if arquivoUpload:
    with st.spinner("Processando...",show_time=True,width="stretch"):
        ecomm = Ecommerce()
        st.session_state.empresa, st.session_state.loja, df = ecomm.carregarArquivo(st.session_state.file_uploader, st.session_state.file_uploader.name.split(".")[-1])
        
        # Evita que o DataFrame seja sobrescrito com o arquivo fonte a cada atualização da tela pelo Streamlit, mantendo os dados atualizados após revisão.
        if st.session_state.df.empty:
            st.session_state.df = df
        
        with col1:
            st.caption("Empresa")
            st.markdown(f"#### {st.session_state.empresa}")
        with col2:
            st.caption("Loja")
            st.markdown(f"#### {st.session_state.loja}")
        with col3:
            st.caption("Receita total")
            st.markdown(f"#### R$ {st.session_state.df.loc[st.session_state.data["selection"]["rows"],'lcto_receita'].sum():.2f}")
        with col4:
            st.caption("Despesa total")
            st.markdown(f"#### R$ {st.session_state.df.loc[st.session_state.data["selection"]["rows"],'lcto_despesa'].sum():.2f}")
        with col5:
            st.caption("Repasse total")
            st.markdown(f"#### R$ {st.session_state.df.loc[st.session_state.data["selection"]["rows"],'lcto_repasse'].sum():.2f}")        

        container_aviso = st.container()
        montar_aviso()
        mostrar_aviso()

        btn_acao = st.button(st.session_state.aviso["btnDesc"],
                             key="btn_acao",
                             width="stretch",
                             type=st.session_state.aviso["btnType"])
        
        if btn_acao and (st.session_state.aviso["tipo"] == "warning"):
            revisao()
            
        if btn_acao and (st.session_state.aviso["tipo"] == "success"):
            if not st.session_state.data.get("selection",{}).get("rows",[]):
                st.toast("Selecione ao menos um registro para processar",icon="⚠️")
            else:                
                confirmacao()            

        with st.expander("Ver detalhes",expanded=(st.session_state.aviso["tipo"]=="warning")):
            st.dataframe(
                data=st.session_state.df,
                key='data',
                hide_index=True,
                width='stretch',
                on_select='rerun',
                selection_mode='multi-row',
                column_config={
                    "tipo": st.column_config.TextColumn(
                        label="Tipo lcto.",
                        help="Renda, Ajuste ou Estorno"),
                    "lcto_pedido": None, # st.column_config.TextColumn(label="Pedido", help="Número do pedido relacionado ao lançamento"),
                    "lcto_receita": st.column_config.NumberColumn(
                        label="Vlr. Receita",
                        format="R$ %.2f",
                        help="Valor a receber"),
                    "lcto_despesa": st.column_config.NumberColumn(
                        label="Vlr. Despesa",
                        format="R$ %.2f",
                        help="Valor a pagar"),
                    "lcto_repasse": st.column_config.NumberColumn(
                        label="Vlr. Repasse",
                        format="R$ %.2f",
                        help="Valor depositado pelo E-commerce"),
                    "lcto_historico": st.column_config.TextColumn(
                        label="Histórico",
                        help="Descrição do lançamento"),
                    "lcto_data": st.column_config.DatetimeColumn(
                        label="Data",
                        format="DD/MM/YYYY",
                        help="Data da liberação do valor pelo E-commerce"),
                    "confirmado": st.column_config.CheckboxColumn(
                        label="Confirmado",
                        help="Se os valores da planilha estão corretos de acordo com o cálculo do repasse"),
                    "divergencia": st.column_config.NumberColumn(
                        label="Divergência",
                        format="R$ %.2f",
                        help="Quando o cálculo do repasse e o valor da planilha não batem"),
                }
            )
