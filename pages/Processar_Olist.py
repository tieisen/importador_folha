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

def processar_revisao(i:int):
    if  (
            f"divergenciah_{i}" in st.session_state
        ) and (
            st.session_state[f"divergenciah_{i}"]!=0.0
        ) and ((
            round(st.session_state[f"receitah_{i}"],2) != round(st.session_state.df.loc[i,"lcto_receita"],2)
        ) or (
            round(st.session_state[f"despesah_{i}"],2) != round(st.session_state.df.loc[i,"lcto_despesa"],2)
        )):
            st.session_state[f"divergenciah_{i}"] = (
                round(st.session_state[f"receitah_{i}"] - st.session_state[f"despesah_{i}"],2) - round(st.session_state[f"repasseh_{i}"],2)
            )
            st.session_state.df.loc[i,"lcto_receita"] = round(st.session_state[f"receitah_{i}"],2)
            st.session_state.df.loc[i,"lcto_despesa"] = round(st.session_state[f"despesah_{i}"],2)
            st.session_state.df.loc[i,"divergencia"] = round(st.session_state[f"divergenciah_{i}"],2)
            if st.session_state.df.loc[i,"divergencia"] == 0:
                st.session_state.df.loc[i,"confirmado"] = True

@st.dialog("Revisão de repasses",icon="⚠️",width='medium')
def revisao():
    for i in st.session_state.df.loc[st.session_state.df["confirmado"]==False].index:
        with st.container(border=True,key=f'container_{i}'):
            st.write(st.session_state.df.loc[i,"lcto_historico"])
            colA, colB, colC, colD = st.columns(4,vertical_alignment='bottom')
            colA.number_input("Vlr. Receita",value=st.session_state.df.loc[i,"lcto_receita"],key=f'receitah_{i}',on_change=processar_revisao,args=(i,))
            colB.number_input("Vlr. Despesa",value=st.session_state.df.loc[i,"lcto_despesa"],key=f'despesah_{i}',on_change=processar_revisao,args=(i,))
            colC.number_input("Vlr. Repasse",value=st.session_state.df.loc[i,"lcto_repasse"],key=f'repasseh_{i}',on_change=processar_revisao,args=(i,))
            colD.number_input("Divergência",value=st.session_state.df.loc[i,"divergencia"],key=f'divergenciah_{i}',disabled=True)
    
    if st.session_state.df["divergencia"].sum() == 0:
        st.rerun()

def finalizar():
    st.success("Registros processados com sucesso!",icon="✅")
    progress_text = "Saindo..."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.02)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()
    # Delete all the items in Session state
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()  

def iniciar_processamento():
    st.session_state.disabled = True

@st.dialog("Confirmação")
def confirmacao():
    if len(st.session_state.data.get("selection",{}).get("rows",[])) == 1:
        st.write(f"Deseja processar o registro selecionado com vencimento para {st.session_state.dtvcto.strftime("%d/%m/%Y")}?")
    else:
        st.write(f"Deseja processar os {len(st.session_state.data["selection"]["rows"])} registros selecionados com vencimento para {st.session_state.dtvcto.strftime("%d/%m/%Y")}?")

    if st.button("Confirmar",type="primary",width='stretch',key="btn_confirmar",disabled=st.session_state.disabled,on_click=iniciar_processamento):        
        processar_selecionados()
    
    if st.button("Cancelar",type="tertiary",width='stretch'):
        st.rerun()
    
def processar_selecionados():
    response = None
    with st.spinner("Processando...",show_time=True,width="stretch"):
        st.session_state.remessa = ecomm.extrai_registros(st.session_state.empresa,
                                                          st.session_state.df.loc[st.session_state.data["selection"]["rows"]],
                                                          st.session_state.dtvcto)
        import json
        from datetime import datetime
        with open(f"remessa_{datetime.now().date().strftime('%Y%m%d')}.test.json","w",encoding='utf-8') as f:
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

def find_non_serializable(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_non_serializable(v, f"{path}.{k}")

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_non_serializable(v, f"{path}[{i}]")

    elif isinstance(obj, np.integer):
        print(f"{path} -> {type(obj)} = {obj}")

    elif isinstance(obj, np.floating):
        print(f"{path} -> {type(obj)} = {obj}")

    elif isinstance(obj, np.bool_):
        print(f"{path} -> {type(obj)} = {obj}")

def normalize(obj):
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

def valida_arquivo():
    if not st.session_state.file_uploader:
        # Delete all the items in Session state
        for key in st.session_state.keys():
            del st.session_state[key]

def mostrar_aviso():
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

st.title("Processar títulos de E-commerce")

colA, colB = st.columns([.75,.25],vertical_alignment='bottom')

arquivoUpload = colA.file_uploader("Selecione um arquivo",
                  type=["xls","xlsx"],
                  key="file_uploader",
                  label_visibility="collapsed",
                  accept_multiple_files=False,
                  on_change=valida_arquivo,
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
        
        if st.session_state.aviso["tipo"] == "warning" and btn_acao:
            revisao()

        with st.expander("Ver detalhes",expanded=(st.session_state.aviso["tipo"]=="warning")):
            st.dataframe(
                data=st.session_state.df,
                key='data',
                hide_index=True,
                width='stretch',
                on_select='rerun', selection_mode="multi-row",
                column_config={
                    "tipo": st.column_config.TextColumn(label="Tipo lcto.", help="Renda, Ajuste ou Estorno"),
                    "lcto_pedido": None, # st.column_config.TextColumn(label="Pedido", help="Número do pedido relacionado ao lançamento"),
                    "lcto_receita": st.column_config.NumberColumn(label="Vlr. Receita",format="R$ %.2f", help="Valor a receber"),
                    "lcto_despesa": st.column_config.NumberColumn(label="Vlr. Despesa",format="R$ %.2f", help="Valor a pagar"),
                    "lcto_repasse": st.column_config.NumberColumn(label="Vlr. Repasse",format="R$ %.2f", help="Valor depositado pelo E-commerce"),
                    "lcto_historico": st.column_config.TextColumn(label="Histórico", help="Descrição do lançamento"),
                    "lcto_data": st.column_config.DatetimeColumn(label="Data",format="DD/MM/YYYY", help="Data da liberação do valor pelo E-commerce"),
                    "confirmado": st.column_config.CheckboxColumn(label="Confirmado",help="Se os valores da planilha estão corretos de acordo com o cálculo do repasse"),
                    "divergencia": st.column_config.NumberColumn(label="Divergência",format="R$ %.2f", help="Quando o cálculo do repasse e o valor da planilha não batem"),
                }
            )
            
        if st.session_state.aviso["tipo"] == "success" and btn_acao:
            if not st.session_state.data.get("selection",{}).get("rows",[]):
                st.toast("Selecione ao menos um registro para processar",icon="⚠️")
            else:                
                confirmacao()
