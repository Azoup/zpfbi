import streamlit as st

def show_financeiro_page():
    st.subheader("💳 Análise Financeira")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Fluxo de Caixa")
        st.info("Gráfico de fluxo de caixa será exibido aqui")
    with col2:
        st.subheader("Despesas por Categoria")
        st.info("Gráfico de despesas por categoria será exibido aqui")
