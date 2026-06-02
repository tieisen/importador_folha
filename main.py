import streamlit as st

if __name__ == "__main__":
    st.set_page_config(page_title="Automações financeiras",
                       layout="wide",
                       page_icon="🦅")
    st.title("Automações financeiras - Eisen")
    st.page_link("main.py", label="Início", icon="🏠")
    st.page_link("pages/Importador_Mvt_Financeira.py", label="Importador de Movimentações Financeiras", icon="💵")
    st.page_link("pages/Processar_Olist.py", label="Processar títulos de E-commerce", icon="🛒")