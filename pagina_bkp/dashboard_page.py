import streamlit as st
import time

def show_dashboard_page():
    # Subtítulo
    st.subheader("📊 Dashboard Principal")

    # Barra de progresso
    with st.spinner("🔄 Carregando Dashboard, aguarde..."):
        steps = [
            "Conectando ao banco",
            "Buscando dados",
            "Processando informações",
            "Renderizando gráficos"
        ]
        my_bar = st.progress(0)
        for i, step in enumerate(steps):
            pct = int((i + 1) / len(steps) * 100)
            my_bar.progress(pct)
            st.caption(f"{step}...")
            time.sleep(0.4)

        my_bar.empty()

    # KPIs e gráficos simulados
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total de Vendas", "R$ 150.000", "+8%")
    with col2:
        st.metric("📦 Total Custo", "R$ 95.000", "-3%")
    with col3:
        st.metric("🔄 Índice de Recompra", "32%", "+5%")
