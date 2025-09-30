import streamlit as st

def show_producao_page():
    st.subheader("🏭 Monitor de Produção")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Eficiência de Produção")
        st.info("Gráfico de eficiência de produção será exibido aqui")
    with col2:
        st.subheader("Produtos por Linha")
        st.info("Gráfico de produtos por linha será exibido aqui")
