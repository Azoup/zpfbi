import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from auth import login_user, signup_user
from database import get_firebird_connection, test_firebird_connection, init_supabase
from dashboard import show_dashboard
from datetime import datetime, date
import os
from streamlit_option_menu import option_menu
import time

# Configuração da página
st.set_page_config(
    page_title="Azoup - Business Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para carregar CSS externo
def load_external_css():
    css_file = "style.css"
    if not os.path.exists(css_file):
        # CSS fallback se o arquivo não for encontrado
        default_css = """
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 2rem 0;
        }
        .kpi-box {
            background: linear-gradient(180deg, #A9ABAE 0%, #1e1e1e 85%);
            border-radius: 12px;
            padding: 25px;
            color: #F79633;
            min-height: 150px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.18);
        }
        .azoup-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1f77b4;
            margin: 1rem 0 2rem 0;
        }
        """
        st.markdown(f'<style>{default_css}</style>', unsafe_allow_html=True)
        return
    
    try:
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar CSS: {str(e)}")

# Função para verificar e carregar o logo
def load_logo():
    logo_path = "logo.png"
    if not os.path.exists(logo_path):
        # não usamos st.warning aqui para não poluir a tela de produção
        return None
    try:
        with open(logo_path, "rb") as f:
            return f.read()
    except Exception as e:
        st.error(f"Erro ao carregar o logo: {str(e)}")
        return None

# Constrói conn_data a partir do session_state (empresa ou conn_data)
def build_conn_data_from_session():
    """
    Retorna um dicionário no formato esperado por database.get_firebird_connection(conn_data).
    Procura em st.session_state.conn_data primeiro (caso já tenha sido preenchido),
    senão tenta mapear campos a partir de st.session_state.empresa.

    Campos finais: {
      'host': str or '',
      'porta': str or '',
      'database': str (caminho/arquivo),
      'user': str,
      'password': str
    }
    """
    # Se o dev/infra já populou conn_data direto no session_state, usa ele
    maybe = st.session_state.get('conn_data')
    if isinstance(maybe, dict) and maybe:
        # garante nomes padronizados
        conn = {
            'host': maybe.get('host', '') or maybe.get('HOST', '') or '',
            'porta': str(maybe.get('porta', '') or maybe.get('PORT', '') or ''),
            'database': maybe.get('database') or maybe.get('caminho') or maybe.get('DATABASE') or '',
            'user': maybe.get('user') or maybe.get('usuario') or maybe.get('USER') or '',
            'password': maybe.get('password') or maybe.get('senha') or maybe.get('PASSWORD') or ''
        }
        return conn

    empresa = st.session_state.get('empresa')
    if not isinstance(empresa, dict) or not empresa:
        return None

    conn = {
        'host': empresa.get('host') or empresa.get('HOST') or '',
        'porta': str(empresa.get('porta') or empresa.get('PORT') or ''),
        'database': empresa.get('caminho') or empresa.get('database') or empresa.get('banco') or '',
        'user': empresa.get('usuario') or empresa.get('user') or empresa.get('login') or '',
        'password': empresa.get('senha') or empresa.get('password') or ''
    }

    # se database estiver vazio, consideramos inválido
    if not conn['database']:
        return None

    return conn

# Carrega CSS externo
load_external_css()

# Carrega logo
logo_data = load_logo()

# Inicializa session state (corrigido - adicionando referencia)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'empresa' not in st.session_state:
    st.session_state.empresa = None
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "Dashboard"
if 'data_inicial' not in st.session_state:
    st.session_state.data_inicial = datetime.now().replace(day=1)
if 'data_final' not in st.session_state:
    st.session_state.data_final = datetime.now()
# Inicialização corrigida - adicionando referencia
if 'referencia' not in st.session_state:
    st.session_state.referencia = datetime.now().strftime("%Y/%m")
# opcional: conn_data pode ser preenchido por login/config
if 'conn_data' not in st.session_state:
    st.session_state.conn_data = {}

# Página de login
if not st.session_state.logged_in:
    # Container principal para login (REMOVIDO: cabeçalho grande com logo + título)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    # apenas centraliza o formulário de login (o header do formulário fica em auth.py)
    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    with login_col2:
        # login_user() é a sua função existente em auth.py; ela deve setar st.session_state.logged_in, user e empresa
        login_user()
    st.markdown('</div>', unsafe_allow_html=True)

# Aplicação principal (após login)
else:
    # Sidebar
    with st.sidebar:
        # Logo e informações da empresa
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if logo_data:
            st.image(logo_data, width=100)
        st.markdown('</div>', unsafe_allow_html=True)

        company_name = st.session_state.empresa.get('nome') if st.session_state.empresa else "Azoup BI"
        st.markdown(f'<div class="company-name">{company_name}</div>', unsafe_allow_html=True)

        # Informações do usuário
        st.markdown('<div class="user-info">', unsafe_allow_html=True)
        user_display = st.session_state.user.get('nome_usuario') if st.session_state.user else "-"
        perfil_display = st.session_state.user.get('perfil') if st.session_state.user else "-"
        st.write(f"**Usuário:** {user_display}")
        st.write(f"**Perfil:** {perfil_display}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Menu Principal")

        # Menu de navegação
        selected = option_menu(
            menu_title=None,
            #options=["Dashboard", "Vendas", "Vendedores", "Financeiro", "Produção", "Configurações"],
            options=["Dashboard", "Vendas", "Vendedores", "Configurações"],
            #icons=["bar-chart", "currency-dollar", "currency-dollar", "credit-card", "gear", "tools"],
            icons=["bar-chart", "currency-dollar",  "gear", "tools"],
            menu_icon="cast",
            #default_index=["Dashboard", "Vendas", "Vendedores",  "Financeiro", "Produção", "Configurações"].index(
            default_index=["Dashboard", "Vendas", "Vendedores", "Configurações"].index(
                st.session_state.selected_menu
            ),
            orientation="vertical",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "2px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#ff9933"},
            },
        )
        st.session_state.selected_menu = selected

        st.markdown("---")
        
        # Botão logout
        if st.button("🚪 Logout", use_container_width=True):
            try:
                supabase = init_supabase()
                supabase.auth.sign_out()
            except Exception as e:
                st.error(f"Erro ao fazer logout: {str(e)}")
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.empresa = None
            st.rerun()

    # Conteúdo principal das páginas
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    if selected == "Dashboard":
        # Barra de progresso
        with st.spinner("🔄 Carregando Dashboard, aguarde..."):
            progress_text = "Preparando dados..."
            my_bar = st.progress(0, text=progress_text)

            steps = [
                "Conectando ao banco",
                "Buscando dados",
                "Processando informações",
                "Renderizando gráficos"
            ]

            for i, step in enumerate(steps):
                progress_percent = int((i + 1) / len(steps) * 100)
                my_bar.progress(progress_percent, text=f"{progress_text} ({step})")
                time.sleep(0.5)  # Simulação - substitua pelas etapas reais

            # Exibir dashboard
            show_dashboard()
            my_bar.empty()

    elif selected == "Vendas":
        col1, col2 = st.columns([2,5])
        with col1:
            logo_paths = ["./Includes/logo.png", "./assets/logo.png", "./logo.png"]
            logo = None
            for path in logo_paths:
                if os.path.exists(path):
                    logo = path
                    break
                    
            if logo:
                st.image(logo, width=80)
                        
                       
        with col2:
            st.title("Análise de Vendas")
        # Filtros
        colf1, colf2, colf3 = st.columns(3)
        with colf1: 
            referencia = st.text_input("Referência (YYYY/MM)", 
                                    value=st.session_state.get('referencia', datetime.now().strftime("%Y/%m")))
        with colf2: 
            data_inicial = st.date_input("Data Inicial", 
                                    value=st.session_state.get('data_inicial', datetime.now().replace(day=1)))
        with colf3: 
            data_final = st.date_input("Data Final", 
                                    value=st.session_state.get('data_final', datetime.now()))

        # Atualiza session_state com os valores dos filtros
        st.session_state.referencia = referencia
        st.session_state.data_inicial = data_inicial
        st.session_state.data_final = data_final

        conn_data = build_conn_data_from_session()
        if conn_data:
            try:
                conn = get_firebird_connection(conn_data)
                
                # Query para dados filtrados (gráfico de pizza, métricas e tabela)
                query_filtrada = f"""
                    SELECT V.REFERENCIA, coalesce(V.EMPRESA_VENDA,1) as EMPRESA_VENDA, e.RAZAO_SOCIAL, V.DATA,
                        SUM(CAST(V.TOTAL_VENDA AS DECIMAL(10,2))) AS TOTAL_VENDA
                    FROM VW_BI_RELGERENCIAL_CUPOM_PREVENDA V
                    LEFT JOIN EMPRESA e ON e.CODIGO = CASE WHEN EMPRESA_VENDA = 0 
                                                           THEN 1 ELSE COALESCE(v.EMPRESA_VENDA,1) END
                    WHERE V.DATA BETWEEN '{data_inicial}' AND '{data_final}'
                    AND V.REFERENCIA LIKE '{referencia}%'
                    GROUP BY V.REFERENCIA, coalesce(V.EMPRESA_VENDA,1), e.RAZAO_SOCIAL, V.DATA
                """
                df_filtrado = pd.read_sql(query_filtrada, conn)
                
                # Query específica para os últimos 13 meses (gráfico de evolução)
                # Calcular data de 13 meses atrás
                data_13_meses_atras = (datetime.now() - pd.DateOffset(months=13)).strftime('%Y-%m-%d')
                data_hoje = datetime.now().strftime('%Y-%m-%d')
                
                query_13_meses = f"""
                    SELECT V.REFERENCIA, SUM(CAST(V.TOTAL_VENDA AS DECIMAL(10,2))) AS TOTAL_VENDA
                    FROM VW_BI_RELGERENCIAL_CUPOM_PREVENDA V
                    WHERE V.DATA BETWEEN '{data_13_meses_atras}' AND '{data_hoje}'
                    GROUP BY V.REFERENCIA
                    ORDER BY V.REFERENCIA
                """
                df_13_meses = pd.read_sql(query_13_meses, conn)
                conn.close()

                # LINHA 1: Gráfico de Evolução (Últimos 13 meses) - Ocupa toda a largura
                st.subheader("📈 Evolução de Vendas - Últimos 13 Meses")
                
                if not df_13_meses.empty:
                    # Gerar lista completa dos últimos 13 meses
                    hoje = datetime.now()
                    meses_13 = [(hoje - pd.DateOffset(months=i)).strftime('%Y/%m') for i in range(12, -1, -1)]
                    
                    # Criar DataFrame completo com todos os meses
                    df_completo = pd.DataFrame({'REFERENCIA': meses_13})
                    df_completo = df_completo.merge(df_13_meses, on='REFERENCIA', how='left').fillna(0)
                    
                    fig_line = go.Figure()
                    fig_line.add_trace(go.Scatter(
                        x=df_completo['REFERENCIA'], 
                        y=df_completo['TOTAL_VENDA'], 
                        mode='lines+markers',
                        line=dict(color='#F79633', width=4),
                        marker=dict(size=10, color='#F79633'),
                        name='Vendas',
                        hovertemplate='<b>Mês:</b> %{x}<br><b>Total:</b> R$ %{y:,.2f}<extra></extra>'
                    ))
                    
                    # Destacar o mês atual
                    mes_atual = hoje.strftime('%Y/%m')
                    if mes_atual in df_completo['REFERENCIA'].values:
                        idx = df_completo[df_completo['REFERENCIA'] == mes_atual].index[0]
                        fig_line.add_trace(go.Scatter(
                            x=[df_completo['REFERENCIA'].iloc[idx]],
                            y=[df_completo['TOTAL_VENDA'].iloc[idx]],
                            mode='markers',
                            marker=dict(size=12, color='#FF0000', symbol='star'),
                            name='Mês Atual',
                            hovertemplate='<b>Mês Atual:</b> %{x}<br><b>Total:</b> R$ %{y:,.2f}<extra></extra>'
                        ))
                    
                    fig_line.update_layout(
                        height=400,
                        plot_bgcolor='#f5f5f5', 
                        paper_bgcolor='#f5f5f5',
                        xaxis_title='Referencia', 
                        yaxis_title='Total Vendas (R$)',
                        hovermode='x unified',
                        xaxis=dict(tickangle=45, tickmode='array', tickvals=meses_13[::2]),
                        showlegend=True
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("Nenhum dado encontrado para os últimos 13 meses.")

                # LINHA 2: Gráfico de Pizza e Métricas
                if not df_filtrado.empty:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader("🏢 Distribuição por Empresa - Mes Atual")
                        fig_pie = px.pie(df_filtrado, names='RAZAO_SOCIAL', values='TOTAL_VENDA')
                        fig_pie.update_traces(
                            marker=dict(colors=px.colors.qualitative.Set3),
                            textinfo='percent+label',
                            hovertemplate='<b>%{label}</b><br>Total: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
                        )
                        fig_pie.update_layout(
                            height=400,
                            plot_bgcolor='#f5f5f5', 
                            paper_bgcolor='#f5f5f5',
                            showlegend=False
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        st.subheader("📊 Métricas - Mes Atual")
                        total_vendas = df_filtrado['TOTAL_VENDA'].sum()
                        avg_vendas = df_filtrado['TOTAL_VENDA'].mean()
                        num_vendas = len(df_filtrado)
                        empresas = df_filtrado['RAZAO_SOCIAL'].nunique()
                        
                        st.metric("Total de Vendas", f"R$ {total_vendas:,.2f}")
                        st.metric("Média por Venda", f"R$ {avg_vendas:,.2f}")
                        st.metric("Número de Vendas", f"{num_vendas:,}")
                        st.metric("Empresas", empresas)
                        
                        # Adicionar algumas estatísticas adicionais
                        st.markdown("---")
                        st.markdown("**Período Selecionado:**")
                        st.write(f"Início: {data_inicial.strftime('%d/%m/%Y')}")
                        st.write(f"Fim: {data_final.strftime('%d/%m/%Y')}")
                        st.write(f"Referência: {referencia}")

                    # LINHA 3: Tabela Detalhada
                    st.subheader("📋 Detalhamento por Empresa")
                    df_detalhado = df_filtrado.groupby('RAZAO_SOCIAL', as_index=False).agg({
                        'TOTAL_VENDA': 'sum',
                        'DATA': ['min', 'max', 'count']
                    })
                    
                    # Ajustar nomes das colunas
                    df_detalhado.columns = ['Empresa', 'Total Vendas', 'Primeira Venda', 'Última Venda', 'Qtd Vendas']
                    df_detalhado = df_detalhado.sort_values('Total Vendas', ascending=False)
                    df_detalhado['Total Vendas Formatado'] = df_detalhado['Total Vendas'].apply(lambda x: f"R$ {x:,.2f}")
                    df_detalhado['Primeira Venda'] = pd.to_datetime(df_detalhado['Primeira Venda']).dt.strftime('%d/%m/%Y')
                    df_detalhado['Última Venda'] = pd.to_datetime(df_detalhado['Última Venda']).dt.strftime('%d/%m/%Y')
                    
                    # Exibir tabela com as colunas formatadas
                    st.dataframe(df_detalhado[['Empresa', 'Total Vendas Formatado', 'Primeira Venda', 'Última Venda', 'Qtd Vendas']], 
                            use_container_width=True)
                            
                else:
                    st.info("Nenhum dado encontrado para os filtros selecionados.")

            except Exception as e:
                st.error(f"Erro ao buscar dados: {e}")
        else:
            st.error("Conexão com banco não configurada.")
    elif selected == "Vendedores":
        col1, col2 = st.columns([2,5])
        with col1:
            logo_paths = ["./Includes/logo.png", "./assets/logo.png", "./logo.png"]
            logo = None
            for path in logo_paths:
                if os.path.exists(path):
                    logo = path
                    break
                    
            if logo:
                st.image(logo, width=80)
                        
                       
        with col2:
            st.title("Análise de Vendas - Vendedores")
            st.subheader('Analise ultimos 13 Meses')
        conn_data = build_conn_data_from_session()            
        try:
            conn = get_firebird_connection(conn_data)
            cur = conn.cursor()
            
            # Query para análise temporal (agrupando por mês/ano)
            query_temporal = """
                            SELECT 
                                NOME_VENDEDOR,
                                EXTRACT(YEAR FROM DATA_REFERENCIA) AS ANO,
                                EXTRACT(MONTH FROM DATA_REFERENCIA) AS MES,
                                REFERENCIA AS REFERENCIA,
                                SUM(VALOR_TOTAL) AS VALOR_TOTAL,
                                COUNT(*) AS QTD_VENDAS
                            FROM VW_BI_VENDA_VENDEDORES 
                            WHERE DATA_REFERENCIA >= DATEADD(MONTH, -13, CURRENT_DATE)
                            GROUP BY 
                                NOME_VENDEDOR,
                                EXTRACT(YEAR FROM DATA_REFERENCIA),
                                EXTRACT(MONTH FROM DATA_REFERENCIA),
                                REFERENCIA
                            ORDER BY ANO, MES,  NOME_VENDEDOR, VALOR_TOTAL
                            """
            
            cur.execute(query_temporal)
            resultados = cur.fetchall()
            
            # Converter para DataFrame
            colunas = [desc[0] for desc in cur.description]
            df = pd.DataFrame(resultados, columns=colunas)
            
            # Fechar conexão
            cur.close()
            conn.close()
                            
            # Criar coluna de data para ordenação
            df['DATA_REF'] = pd.to_datetime(df['REFERENCIA'] + '-01')
            
            
            # Sidebar - Filtros
            st.sidebar.subheader("🔧 Filtros de Análise")
            
            # Filtro por período
            datas_disponiveis = sorted(df['DATA_REF'].unique())
            if len(datas_disponiveis) > 1:
                data_min = st.sidebar.date_input(
                    "Data inicial",
                    value=datas_disponiveis[0],
                    min_value=datas_disponiveis[0],
                    max_value=datas_disponiveis[-1]
                )
                data_max = st.sidebar.date_input(
                    "Data final", 
                    value=datas_disponiveis[-1],
                    min_value=datas_disponiveis[0],
                    max_value=datas_disponiveis[-1]
                )
                
                df = df[(df['DATA_REF'] >= pd.to_datetime(data_min)) & 
                    (df['DATA_REF'] <= pd.to_datetime(data_max))]
            
            # Filtro por vendedores
            vendedores = sorted(df['NOME_VENDEDOR'].unique())
            vendedores_selecionados = st.sidebar.multiselect(
                "Vendedores",
                options=vendedores,
                default=vendedores[:5] if len(vendedores) > 5 else vendedores
            )
            
            if vendedores_selecionados:
                df = df[df['NOME_VENDEDOR'].isin(vendedores_selecionados)]
            
            # Layout em abas para diferentes visualizações
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Comparativo Mensal", 
                "🔥 Top Performers",
                "📊 % Participação",
                "📋 Dados Detalhados"
                
            ])
            
            with tab1:
                st.subheader("Comparativo Mensal")
                
                fig_barras = px.bar(
                    df.sort_values("DATA_REF"),
                    x='DATA_REF',
                    y='VALOR_TOTAL',
                    color='NOME_VENDEDOR',
                    barmode='group',
                    title='Comparativo Mensal de Vendas por Vendedor',
                    labels={'VALOR_TOTAL': 'Valor Total (R$)', 'DATA_REF': 'Mês/Ano'}
                )
                fig_barras.update_layout(
                    height=500,
                    xaxis_tickangle=-45,
                    xaxis=dict(tickformat="%Y-%m")
                )
                st.plotly_chart(fig_barras, use_container_width=True)

            with tab2:
                st.subheader("Top Performers por Período")
                
                df_top = df.groupby('NOME_VENDEDOR')['VALOR_TOTAL'].sum().reset_index()
                df_top = df_top.sort_values('VALOR_TOTAL', ascending=False).head(10)
                
                fig_top = px.bar(
                    df_top,
                    x='VALOR_TOTAL',
                    y='NOME_VENDEDOR',
                    orientation='h',
                    title='Top 10 Vendedores (Valor Total no Período)',
                    labels={'VALOR_TOTAL': 'Valor Total (R$)', 'NOME_VENDEDOR': 'Vendedor'}
                )
                fig_top.update_layout(height=500)
                st.plotly_chart(fig_top, use_container_width=True)

            with tab3:
                st.subheader("% Participação das Vendas (Top 10 Vendedores)")

                # Conecta e executa sua query já com PARTICIPACAO
                conn_data = build_conn_data_from_session()            
                try:
                    conn = get_firebird_connection(conn_data)
                    cur = conn.cursor()
                    data_13_meses_atras = (datetime.now() - pd.DateOffset(months=13)).strftime('%Y-%m-%d')
                    data_hoje = datetime.now().strftime('%Y-%m-%d')

                    query_participacao = """
                        SELECT
                            V.NOME_VENDEDOR,
                            V.REFERENCIA,
                            SUM(V.VALOR_TOTAL) AS VALOR_TOTAL,
                            SUM(SUM(V.VALOR_TOTAL)) OVER(PARTITION BY V.REFERENCIA) AS TOTAL_FATURADO,
                            CAST(SUM(V.VALOR_TOTAL) * 100.0 / SUM(SUM(V.VALOR_TOTAL)) OVER(PARTITION BY V.REFERENCIA) AS DECIMAL(10,2)) AS PARTICIPACAO
                        FROM VW_BI_VENDA_VENDEDORES V
                        WHERE V.DATA_REFERENCIA BETWEEN ? AND ?
                        AND V.NOME_VENDEDOR NOT IN ('SEM VENDEDOR')
                        GROUP BY V.NOME_VENDEDOR, V.REFERENCIA
                        ORDER BY V.REFERENCIA
                    """
                    
                    cur.execute(query_participacao, (data_13_meses_atras, data_hoje))
                    resultados = cur.fetchall()
                    colunas = [desc[0] for desc in cur.description]
                    df_part = pd.DataFrame(resultados, columns=colunas)
                    cur.close()
                    conn.close()

                    # Converte para numérico
                    df_part['PARTICIPACAO'] = pd.to_numeric(df_part['PARTICIPACAO'], errors='coerce').fillna(0)
                    df_part['VALOR_TOTAL'] = pd.to_numeric(df_part['VALOR_TOTAL'], errors='coerce').fillna(0)

                    # Último mês
                    ultimo_mes = df_part['REFERENCIA'].max()
                    df_mes = df_part[df_part['REFERENCIA'] == ultimo_mes]

                    # Top 10 vendedores
                    df_top10 = df_mes.sort_values('VALOR_TOTAL', ascending=False).head(10)

                    # Gráfico com dois eixos
                    import plotly.graph_objects as go
                    from plotly.subplots import make_subplots

                    fig = make_subplots(specs=[[{"secondary_y": True}]])

                    # Barra do VALOR_TOTAL
                    fig.add_trace(go.Bar(
                        x=df_top10["NOME_VENDEDOR"],
                        y=df_top10["VALOR_TOTAL"],
                        name="Total de Vendas (R$)",
                        marker_color="steelblue",
                        text=df_top10["VALOR_TOTAL"].apply(lambda v: f"R$ {v:,.0f}".replace(",", ".")),
                        textposition="outside"  # R$ aparece fora
                    ), secondary_y=False)

                    # Barra da PARTICIPACAO
                    fig.add_trace(go.Bar(
                        x=df_top10["NOME_VENDEDOR"],
                        y=df_top10["PARTICIPACAO"],
                        name="% Participação",
                        marker_color="#FDCCA0",
                        text=df_top10["PARTICIPACAO"].apply(lambda v: f"{v:.1f}%"),
                        textposition="inside"   # % aparece dentro da barra
                    ), secondary_y=True)


                    # Layout
                    fig.update_layout(
                        title=f"Top 10 Vendedores - {ultimo_mes}",
                        barmode="group",
                        height=550,
                        xaxis=dict(title="Vendedor"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )

                    # Eixos separados
                    fig.update_yaxes(
                        title_text="Total de Vendas (R$)",
                        secondary_y=False,
                        tickprefix="R$ ",
                        separatethousands=True
                    )
                    fig.update_yaxes(
                        title_text="% Participação",
                        secondary_y=True,
                        ticksuffix="%",
                        showgrid=False
                    )

                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro ao gerar gráfico de participação: {e}")
            with tab4:
                st.subheader("Dados Detalhados")
                
                # Pivot table usando DATA_REF (ordenado)
                pivot_df = df.pivot_table(
                    index='NOME_VENDEDOR',
                    columns=df['DATA_REF'].dt.strftime("%Y-%m"),
                    values='VALOR_TOTAL',
                    aggfunc='sum',
                    fill_value=0
                ).round(2)
                
                # Reordena colunas pelo tempo
                pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)
                
                pivot_df['TOTAL_PERIODO'] = pivot_df.sum(axis=1)
                pivot_df = pivot_df.sort_values('TOTAL_PERIODO', ascending=False)
                
                st.dataframe(pivot_df.style.format("R$ {:.2f}"), use_container_width=True)
                
                # Botão para download
                csv = pivot_df.to_csv(sep=';', decimal=',')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"analise_vendedores_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"Erro na análise temporal: {str(e)}")

    # elif selected == "Financeiro":
    #     st.title("💳 Análise Financeira")
    #     st.write("Esta seção apresenta análises e relatórios financeiros")
            
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         st.subheader("Fluxo de Caixa")
    #         st.info("Gráfico de fluxo de caixa será exibido aqui")
    #     with col2:
    #         st.subheader("Despesas por Categoria")
    #         st.info("Gráfico de despesas por categoria será exibido aqui")
                
    #     col3, col4 = st.columns(2)
    #     with col3:
    #         st.subheader("Balanço Financeiro")
    #         st.info("Resumo do balanço financeiro")
    #     with col4:
    #         st.subheader("Contas a Pagar/Receber")
    #         st.info("Situação das contas")

    # elif selected == "Produção":
    #     st.title("🏭 Monitor de Produção")
    #     st.write("Esta seção apresenta monitoramento de produção")
        
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         st.subheader("Eficiência de Produção")
    #         st.info("Gráfico de eficiência de produção será exibido aqui")
    #     with col2:
    #         st.subheader("Produtos por Linha")
    #         st.info("Gráfico de produtos por linha será exibido aqui")
            
    #     col3, col4 = st.columns(2)
    #     with col3:
    #         st.subheader("Controle de Qualidade")
    #         st.info("Métricas de qualidade")
    #     with col4:
    #         st.subheader("Inventário")
    #         st.info("Situação do estoque")

    elif selected == "Configurações":
        st.title("⚙️ Configurações do Sistema")
        
        st.subheader("📋 Informações do Usuário")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nome:** {st.session_state.user.get('nome_usuario', '-')}")
            st.write(f"**Email:** {st.session_state.user.get('email_usuario', '-')}")
        with col2:
            st.write(f"**Perfil:** {st.session_state.user.get('perfil', '-')}")
            st.write(f"**Empresa:** {st.session_state.empresa.get('nome', '-')}")
        
        # Conexão com banco de dados
        # st.subheader("🔗 Configurações de Conexão")
        # if st.session_state.empresa:
        #     conn_info = st.container()
        #     with conn_info:
        #         col1, col2 = st.columns(2)
        #         with col1:
        #             pass 
        #             #st.write(f"**Host:** {st.session_state.empresa.get('host', '-')}")
        #             #st.write(f"**Porta:** {st.session_state.empresa.get('porta', '-')}")
        #         with col2:
        #             pass
        #             #st.write(f"**Banco:** {st.session_state.empresa.get('caminho', '-')}")
        #             #st.write(f"**Usuário:** {st.session_state.empresa.get('usuario', '-')}")
        
        # # Testar conexão
        # if st.button("🧪 Testar Conexão com o Banco"):
        #     with st.spinner("Testando conexão..."):
        #         try:
        #             conn_data = build_conn_data_from_session()
        #             if not conn_data:
        #                 st.error("Dados de conexão incompletos. Preencha os detalhes da empresa.")
        #             else:
        #                 ok = test_firebird_connection(conn_data)
        #                 if ok:
        #                     st.success("✅ Conexão estabelecida com sucesso!")
        #                 else:
        #                     st.error("❌ Falha na conexão")
        #         except Exception as e:
        #             st.error(f"❌ Erro na conexão: {str(e)}")
        
        # Cadastro de novo usuário (apenas para Super Admin)
        if st.session_state.user.get('perfil') == 'Super Admin':
            st.subheader("👥 Cadastro de Novo Usuário")
            with st.expander("Cadastrar Novo Usuário"):
                signup_user()
        
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            pass    
        #     if st.button("🚪 Logout", use_container_width=True):
        #         try:
        #             supabase = init_supabase()
        #             supabase.auth.sign_out()
        #         except Exception as e:
        #             st.error(f"Erro ao fazer logout: {str(e)}")
            # st.session_state.logged_in = False
            # st.session_state.user = None
            # st.session_state.empresa = None
            # st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666; font-size: 0.8rem;">'
        'Azoup Business Intelligence © 2024 - Todos os direitos reservados'
        '</div>', 
        unsafe_allow_html=True
    )