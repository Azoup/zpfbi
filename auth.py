import streamlit as st
from database import init_supabase, test_firebird_connection
from datetime import datetime
import os


# Função para carregar CSS externo
def load_external_css():
    css_file = os.path.join(os.path.dirname(__file__), "style.css")
    if not os.path.exists(css_file):
        st.error(f"Arquivo CSS não encontrado: {css_file}")
        return
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def login_user():
    # Carrega CSS externo
    load_external_css()
    
    supabase = init_supabase()
    
    # Título usando a classe do CSS
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
       st.markdown('<div class="azoup-title">Azoup - Business Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<h3 class="login-title">Login</h3>', unsafe_allow_html=True)
    
    with st.form("Login"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            try:
                # Autentica com Supabase Auth
                auth_response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                
                if auth_response.user:
                    # Busca dados do usuário na tabela usuario usando o ID do auth
                    response = supabase.table('usuario').select('*').eq('id', auth_response.user.id).execute()
                    
                    if response.data and len(response.data) > 0:
                        user = response.data[0]
                        
                        # Busca dados da empresa usando o campo "api"
                        cliente_data = supabase.table('clientes').select('*').eq('api', user['api']).execute()
                        
                        if cliente_data.data and len(cliente_data.data) > 0:
                            empresa = cliente_data.data[0]
                            
                            # VERIFICAÇÃO DA DATA DA LICENÇA
                            data_licenca = empresa.get('data_licenca')
                            
                            if data_licenca:
                                # Converte para objeto datetime se for string
                                if isinstance(data_licenca, str):
                                    data_licenca = datetime.strptime(data_licenca, '%Y-%m-%d').date()
                                
                                if data_licenca < datetime.now().date():
                                    st.error("Licença expirada. Entre em contato com o suporte.")
                                    return
                            else:
                                st.error("Data de licença não encontrada")
                                return
                            
                            # Testa conexão com Firebird
                            conn_data = {
                                'host': empresa.get('host', ''),
                                'porta': empresa.get('porta', '3050'),
                                'database': empresa.get('caminho', ''),
                                'user': empresa.get('usuario', ''),
                                'password': empresa.get('senha', '')
                            }
                            
                            if test_firebird_connection(conn_data):
                                st.session_state.user = user
                                st.session_state.empresa = empresa
                                st.session_state.logged_in = True
                                st.rerun()
                            else:
                                st.error("Falha na conexão com o banco de dados da empresa")
                        else:
                            st.error("Empresa não encontrada para este API")
                    else:
                        st.error("Usuário não encontrado na tabela de usuários")
                else:
                    st.error("Falha na autenticação")
            except Exception as e:
                st.error(f"Erro no login: {str(e)}")

def signup_user():
    # Carrega CSS externo
    load_external_css()
    
    supabase = init_supabase()
    
    # Título usando a classe do CSS
    st.markdown('<h3 class="login-title">Criar Nova Conta</h3>', unsafe_allow_html=True)
    
    with st.form("Cadastro"):
        email = st.text_input("Email")
        nome = st.text_input("Nome Completo")
        celular = st.text_input("Celular")
        password = st.text_input("Senha", type="password")
        
        # Busca APENAS a empresa logada
        empresa_logada = supabase.table('clientes').select('nome, api, host, porta').eq('api', st.session_state.user['api']).execute()

        if empresa_logada.data and len(empresa_logada.data) > 0:
            empresa = empresa_logada.data[0]
            
            # Não mostra selectbox, apenas exibe a empresa logada
            st.info(f"Empresa: {empresa['nome']} (API: {empresa['api']})")
            
            perfil = st.selectbox("Perfil", ["Admin Cliente", "Avançado", "Básico", "Visualizador"])
            
            submitted = st.form_submit_button("Cadastrar")
            
            if submitted:
                try:
                    # Verifica se usuário já existe
                    existing_user = supabase.table('usuario').select('*').eq('email_usuario', email).execute()
                    if existing_user.data and len(existing_user.data) > 0:
                        st.error("Email já cadastrado")
                        return
                    
                    # 1. Primeiro cria o usuário na autenticação do Supabase
                    auth_response = supabase.auth.sign_up({
                        "email": email,
                        "password": password,
                        "options": {
                            "data": {
                                "nome": nome,
                                "celular": celular
                            }
                        }
                    })
                    
                    if auth_response.user:
                        # 2. Depois insere na tabela usuario com o mesmo ID
                        insert_response = supabase.table('usuario').insert({
                            "id": auth_response.user.id,  # Usa o ID do usuário criado na autenticação
                            "email_usuario": email,
                            "nome_usuario": nome,
                            "celular": celular,
                            "perfil": perfil,
                            "api": empresa['api'],  # Usa o API da empresa logada
                            "tipo": "BI"
                        }).execute()
                        
                        if insert_response.data:
                            st.success("Conta criada com sucesso! Aguarde aprovação do administrador.")
                        else:
                            st.error("Erro ao cadastrar na tabela usuario")
                    else:
                        st.error("Erro ao criar usuário na autenticação")
                except Exception as e:
                    st.error(f"Erro no cadastro: {str(e)}")
        else:
            st.error("Empresa não encontrada")
