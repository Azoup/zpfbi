import streamlit as st

def show_vendas_page():
    st.subheader("💰 Análise de Vendas")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Vendas por Categoria")
        st.info("Gráfico de vendas por categoria será exibido aqui")
    with col2:
        st.subheader("Evolução de Vendas")
        st.info("Gráfico de evolução de vendas será exibido aqui")
