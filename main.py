import os, time, asyncio
import streamlit as st
import pandas as pd
from src.app import App

if __name__ == "__main__":
    st.set_page_config(page_title="Importador mvt. financeira", layout="wide")
    st.title("Importador de movimentação financeira")
    
    app = App()

    # Inicializa as variáveis de sessão
    if 'arquivo' not in st.session_state:
        st.session_state.arquivo = None
    if 'dados_cabecalho' not in st.session_state:
        st.session_state.dados_cabecalho = pd.DataFrame()
    if 'lista_lctos' not in st.session_state:
        st.session_state.lista_lctos = pd.DataFrame()
    tipo_lcto=None
    empresa=None
    my_bar=None
    nome_arquivo=None
    download_btn=None
    
    # Carrega os arquivos de ajuda
    with open(os.getenv('PATH_AJUDA_FOLHA'), "r", encoding="utf-8") as f:
        md_folha = f.read()
    with open(os.getenv('PATH_AJUDA_VR'), "r", encoding="utf-8") as f:
        md_vr = f.read()
    with st.sidebar:
        st.header("ℹ️ Como utilizar:")
        with st.expander("Folha de pagamento"):
            st.markdown(md_folha)
        with st.expander("Vale refeição"):
            st.markdown(md_vr)

    # Carrega o arquivo e verifica o tipo
    st.session_state.arquivo = st.file_uploader("Selecione um arquivo", type=["txt","xls","xlsx","csv"])
    if st.session_state.arquivo:
        rotina = app.verifica_tipo_arquivo(st.session_state.arquivo)
        match app.tipo_rotina:
            case 'vr':
                st.success("Vale refeição",icon="🍔")
            case 'folha':
                st.info("Folha de pagamento",icon="💰")
            case 'olist':
                st.info("Remessa de guias Olist",icon="💱")
                empresa = st.pills(label="Empresa", options=['storya', 'outbeauty','compre'], selection_mode="single")
            case _:
                pass

        if app.tipo_rotina == 'olist':
            if empresa:
                my_bar, nome_arquivo = rotina(st.session_state.arquivo,empresa)
                download_btn = st.download_button(
                    label="Baixar arquivo",
                    data=open(nome_arquivo,"r").read(),
                    file_name=nome_arquivo,
                    mime="text/csv",
                    icon=":material/download:",
                )
                
                if download_btn:
                    my_bar.empty()
                    st.cache_resource.clear()
                    st.session_state.arquivo = None
                    empresa=None

            # Limpa o cache quando o arquivo importado é removido
            if not st.session_state.arquivo:
                empresa=None
                my_bar=None
                nome_arquivo=None
                download_btn=None
                st.cache_resource.clear()
            
        else:
        
            # Roda a rotina de leitura do arquivo
            if st.session_state.dados_cabecalho.empty:
                st.session_state.dados_cabecalho, st.session_state.lista_lctos = asyncio.run(rotina(st.session_state.arquivo))

            # Cria tela se o arquivo foi lido com sucesso
            if not all([isinstance(st.session_state.dados_cabecalho,bool),isinstance(st.session_state.lista_lctos,bool)]):
                
                with st.expander("**Cabeçalho**", expanded=True):
                    col1, col2 = st.columns([0.2,0.8])
                    for i in range(len(st.session_state.dados_cabecalho.columns)):
                        col1.write(f"{st.session_state.dados_cabecalho.columns[i]}:")
                        col2.write(st.session_state.dados_cabecalho.iloc[0,i])
                
                if app.tipo_rotina == 'folha':
                    # Configura a tabela da importação da folha
                    naturezas = ["Salário","Férias"]
                    opcoes_tipo_lcto = ["Salário","Adiantamento"]
                    tipo_lcto = st.pills(label="Tipo de lançamento", options=opcoes_tipo_lcto, default=opcoes_tipo_lcto[0], selection_mode="single")
                    referencia:str = (pd.to_datetime(st.session_state.lista_lctos.at[0,'Data pagamento'],format='%d/%m/%Y') - pd.DateOffset(months=1)).strftime('%m/%Y') if tipo_lcto == "Salário" else pd.to_datetime(st.session_state.lista_lctos.at[0,'Data pagamento'],format='%d/%m/%Y').strftime('%m/%Y')
                    st.session_state.lista_lctos['Referencia'] = referencia                    
                    column_config={
                                "Nome": st.column_config.TextColumn(),
                                "Codigo sankhya": st.column_config.NumberColumn(),
                                "Valor pagamento": st.column_config.NumberColumn(format="R$ %.2f"),
                                "Natureza": st.column_config.SelectboxColumn(options=naturezas,required=True),
                                "Inicio ferias": st.column_config.DateColumn(help="Preencha apenas para lançamentos de Férias",format="DD/MM/YYYY"),
                                "Fim ferias": st.column_config.DateColumn(help="Preencha apenas para lançamentos de Férias",format="DD/MM/YYYY")
                            }
                elif app.tipo_rotina == 'vr':
                    # Configura a tabela da importação do VR
                    column_config={"Valor do benefício": st.column_config.NumberColumn(format="R$ %.2f")}

                # Exibe a tabela
                with st.expander("**Lançamentos**", expanded=True):
                    df = st.data_editor(
                        st.session_state.lista_lctos,
                        hide_index=True,
                        num_rows="dynamic",
                        column_config=column_config)

                # Executa o envio dos dados
                btn_enviar = st.button("Enviar",use_container_width=True)
                if btn_enviar:
                    if not all([not st.session_state.dados_cabecalho.empty, not df.empty]):
                        st.warning(body="Faltam informações. Verifique se o arquivo foi importado corretamente e se o Tipo de lançamento foi informado")
                    else:
                        registros_enviados:int = asyncio.run(app.enviar_dados(dados_bancarios=st.session_state.dados_cabecalho.to_dict(orient='records')[0],
                                                            dados_lancamentos=df.to_dict(orient='records'),
                                                            tipo_lcto=tipo_lcto if tipo_lcto else app.tipo_rotina))
                        # Retorna na UI e limpa o cache após 2 segundos
                        if registros_enviados:
                            st.success(f'{registros_enviados} registros enviados com sucesso!', icon="✅")
                            st.balloons()
                            time.sleep(2)
                            st.cache_resource.clear()
                            st.session_state.arquivo = None
                            tipo_lcto=None
                            st.session_state.dados_cabecalho = pd.DataFrame()
                            st.session_state.lista_lctos = pd.DataFrame()
                        else:
                            st.error('Falha ao realizar os registros', icon="🚨")

            else:
                st.warning("Dados do arquivo não puderam ser extraídos. Verifique se o arquivo é válido.")
    
    # Limpa o cache quando o arquivo importado é removido
    if not st.session_state.arquivo and any([not st.session_state.dados_cabecalho.empty,not st.session_state.lista_lctos.empty]):
        st.session_state.dados_cabecalho, st.session_state.lista_lctos = pd.DataFrame(), pd.DataFrame()
        tipo_lcto=None
        empresa=None
        my_bar=None
        nome_arquivo=None
        st.cache_resource.clear()