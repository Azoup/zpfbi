import streamlit as st
from database import get_firebird_connection
import os
import re
from datetime import date, timedelta

def show_dashboard():
    # Acessar dados da empresa e usuário do session_state
    empresa = st.session_state.empresa
    user = st.session_state.user
    
    # Título da página
    col1, col2 = st.columns([1, 5])
    with col1:
        # Tentar carregar o logo de várias localizações possíveis
        logo_paths = ["./Includes/logo.png", "./assets/logo.png", "./logo.png"]
        logo = None
        for path in logo_paths:
            if os.path.exists(path):
                logo = path
                break
                
        if logo:
            st.image(logo, width=80)
    with col2:
       # st.subheader("Dashboard Principal")
       st.markdown('<div class="azoup-title">Dashboard Principal</div>', unsafe_allow_html=True)
    # Filtros de data - ABAIXO DO TÍTULO 
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    with col2:
        data_inicial = st.date_input(
            "Data Inicial",
            value=st.session_state.data_inicial,
            format="DD/MM/YYYY",
            key="data_inicial_filter"
        )
    
    with col3:
        data_final = st.date_input(
            "Data Final", 
            value=st.session_state.data_final,
            format="DD/MM/YYYY",
            key="data_final_filter"
        )
    
    # Atualizar session_state com as novas datas
    st.session_state.data_inicial = data_inicial
    st.session_state.data_final = data_final
    
    # Converter datas para o formato do banco de dados
    data_inicial_formatada = data_inicial.strftime("%Y-%m-%d")
    data_final_formatada = data_final.strftime("%Y-%m-%d")
    
    # Tentar conectar ao banco de dados Firebird
    try:
        conn_data = {
            'host': empresa.get('host', ''),
            'porta': empresa.get('porta', '3050'),
            'database': empresa.get('caminho', ''),
            'user': empresa.get('usuario', ''),
            'password': empresa.get('senha', '')
        }
        
        # Usar a conexão para buscar dados reais (implementar consultas reais aqui)
        # Por enquanto, vamos usar valores fixos como exemplo
        with get_firebird_connection(conn_data) as conn:
            # NOVOS CLIENTES
            cursor = conn.cursor()
            sql = """
            SELECT
                CAST(COUNT(*) AS INTEGER) AS Novos_Clientes
            FROM Clientes
            WHERE data_cadastro >= CURRENT_DATE - 90
            """
            cursor.execute(sql)
            novos_clientes = int(cursor.fetchone()[0] or 0)

            # CLIENTES ATIVOS
            cursor = conn.cursor()
            sql = """
            SELECT
                CAST(COUNT(*) AS INTEGER) AS Novos_Clientes
            FROM Clientes
            WHERE INATIVO = 'N'
            """
            cursor.execute(sql)
            clientes_ativos = int(cursor.fetchone()[0] or 0)

            # Função auxiliar para buscar o valor de uma métrica
            def get_valor(tipo, data_ini, data_fim):
                sql = """
                 SELECT COALESCE(SUM(valor), 0)
                    FROM VW_KPI_BI
                    WHERE TIPO = ?
                    AND DATA BETWEEN ? AND ?
                    """
                cursor.execute(sql, (tipo, data_ini, data_fim))
                return cursor.fetchone()[0] or 0            
            
            
            # Valores da view VW_KPI_BI 
            total_vendas = get_valor("TOTAL VENDAS", data_inicial_formatada, data_final_formatada)
            total_custo = get_valor("TOTAL CUSTO", data_inicial_formatada, data_final_formatada)
            indice_recompra = get_valor("INDICE RECOMPRA", data_inicial_formatada, data_final_formatada)         
            pecas_atendimento = get_valor("PECAS ATEND", data_inicial_formatada, data_final_formatada)
            ticket_medio = get_valor("TICKET MEDIO", data_inicial_formatada, data_final_formatada)
            lucro_bruto = total_vendas - total_custo
            margem_lucro = (lucro_bruto / total_vendas) * 100 if total_vendas > 0 else 0
            
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        # Valores padrão em caso de erro
        total_vendas = 0
        total_custo = 0
        indice_recompra = 0
        clientes_ativos = 0
        novos_clientes = 0
        pecas_atendimento = 0
        ticket_medio = 0
        lucro_bruto = 0
        margem_lucro = 0
    
    # KPIs
    kpis = [
        {"titulo": "Total de Vendas", "valor": f"R$ {total_vendas:,.2f}", "icone": "💰"},
        {"titulo": "Total Custo Produto", "valor": f"R$ {total_custo:,.2f}", "icone": "📦"},
        {"titulo": "Índice de Recompra", "valor": f"{indice_recompra}%", "icone": "🔄"},
        {"titulo": "Clientes Ativos", "valor": f"{clientes_ativos:,}", "icone": "👥"},
        {"titulo": "Novos Clientes (3 meses)", "valor": f"{novos_clientes}", "icone": "⭐"},
        {"titulo": "Peças Por Atendimento", "valor": f"{pecas_atendimento}", "icone": "🔧"},
        {"titulo": "Ticket Médio", "valor": f"R$ {ticket_medio:,.2f}", "icone": "🎫"},
        {"titulo": "Lucro Bruto", "valor": f"R$ {lucro_bruto:,.2f}", "icone": "📈"},
        {"titulo": "Margem de Lucro", "valor": f"{margem_lucro:.1f}%", "icone": "💹"}
    ]
    
    # Exibir KPIs em grid responsivo
    st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
    
    for i, kpi in enumerate(kpis):
        # Criar 3 colunas para desktop, 2 para mobile
        if i % 3 == 0:
            cols = st.columns(3)
        
        with cols[i % 3]:
            st.markdown(f'''
                <div class="kpi-box">
                    <div class="kpi-title">
                        <span>{kpi["icone"]}</span>
                        <span>{kpi["titulo"]}</span>
                    </div>
                    <div class="kpi-value">{kpi["valor"]}</div>
                    <div class="kpi-sub">Período: {data_inicial.strftime("%d/%m/%Y")} a {data_final.strftime("%d/%m/%Y")}</div>
                </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Botões de ação
    #col1, col2, col3 = st.columns(3)
    #with col2:
    #    if st.button("🔄 Atualizar Dados", use_container_width=True):
    #        st.rerun()
    
    # Adicionar informações de debug (opcional)
    with st.expander("ℹ️ Informações do Sistema"):
        st.write(f"Usuário: {user.get('nome_usuario', 'N/A')}")
        st.write(f"Empresa: {empresa.get('nome', 'N/A')}")
        st.write(f"API: {empresa.get('api', 'N/A')}")
        st.write(f"Data inicial (formato BD): {data_inicial_formatada}")
        st.write(f"Data final (formato BD): {data_final_formatada}")
        
        # Botão para testar conexão
        if st.button("Testar Conexão com Banco de Dados"):
            from database import test_firebird_connection
            if test_firebird_connection(conn_data):
                st.success("Conexão bem-sucedida!")
            else:
                st.error("Falha na conexão")

# Para testar o dashboard diretamente
if __name__ == "__main__":
    # Configuração para teste direto
    st.set_page_config(
        page_title="Azoup - Business Intelligence",
        page_icon="📊",
        layout="wide"
    )
    
    # Carregar CSS para teste
    css_paths = ["./style.css", "./assets/style.css", "./Includes/style.css"]
    for path in css_paths:
        if os.path.exists(path):
            with open(path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            break
    
    # Dados de exemplo para teste
    if 'empresa' not in st.session_state:
        st.session_state.empresa = {
            'nome': 'Empresa Teste',
            'host': 'localhost',
            'porta': '3050',
            'caminho': '/path/to/database.fdb',
            'usuario': 'sysdba',
            'senha': 'masterkey',
            'api': 'TEST123'
        }
    
    if 'user' not in st.session_state:
        st.session_state.user = {
            'nome_usuario': 'Usuário Teste',
            'perfil': 'Admin'
        }
    
    if 'data_inicial' not in st.session_state:
        st.session_state.data_inicial = date.today().replace(day=1)
    
    if 'data_final' not in st.session_state:
        st.session_state.data_final = date.today()
    
    if 'selected_menu' not in st.session_state:
        st.session_state.selected_menu = "Dashboard"
    
    show_dashboard()