import streamlit as st
from datetime import datetime
from database import init_supabase
from streamlit_modal import Modal


# =========================
# Funções auxiliares
# =========================

def load_external_css():
    css_file = "style.css"
    try:
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo CSS não encontrado, usando estilo padrão.")


def show_header():
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image("logo.png", width=120)
    with col2:
        st.markdown(
            "<h1 style='text-align: left; margin-top: 20px;'>AZOUP - Business Intelligence</h1>",
            unsafe_allow_html=True
        )
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader('Modulo Administrativo')
    st.markdown("---")


# =========================
# Login
# =========================

def login_page():
    load_external_css()
    show_header()

    st.markdown("<h3 style='text-align: center;'>🔑 Login Administrativo</h3>", unsafe_allow_html=True)

    supabase = init_supabase()

    with st.form("Login"):
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            try:
                auth_response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })

                if auth_response.user:
                    response = supabase.table('usuario').select('*').eq('id', auth_response.user.id).execute()
                    if response.data:
                        st.session_state.user = response.data[0]
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Usuário não encontrado na tabela de usuários")
                else:
                    st.error("Falha na autenticação")
            except Exception as e:
                st.error(f"Erro no login: {str(e)}")


# =========================
# Cadastro Super Admin
# =========================

def cadastro_super_admin():
    load_external_css()
    show_header()

    st.markdown("<h3 style='text-align: center;'>👑 Cadastro Super Admin</h3>", unsafe_allow_html=True)

    supabase = init_supabase()
    clientes = supabase.table("clientes").select("id, nome, api").execute().data

    if not clientes:
        st.warning("Nenhuma empresa encontrada no cadastro de clientes.")
        return

    with st.form("cadastro_admin"):
        empresa = st.selectbox("Selecione a Empresa", clientes, format_func=lambda x: f"{x['nome']} ({x['api']})")
        nome = st.text_input("Nome Completo")
        email = st.text_input("Email")
        celular = st.text_input("Celular")
        senha = st.text_input("Senha", type="password")

        submitted = st.form_submit_button("Cadastrar Super Admin")

        if submitted:
            try:
                existing_user = supabase.table("usuario").select("*").eq("email_usuario", email).execute()
                if existing_user.data:
                    st.error("Email já cadastrado")
                    return

                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": senha,
                    "options": {
                        "data": {
                            "nome": nome,
                            "celular": celular
                        }
                    }
                })

                if auth_response.user:
                    supabase.table("usuario").insert({
                        "id": auth_response.user.id,
                        "nome_usuario": nome,
                        "email_usuario": email,
                        "celular": celular,
                        "perfil": "Super Admin",
                        "api": empresa["api"],
                        "tipo": "BI",
                        "senha": senha
                    }).execute()

                    st.success("Super Admin cadastrado com sucesso! Agora já pode acessar o sistema.")
                else:
                    st.error("Erro ao criar usuário no Supabase Auth")
            except Exception as e:
                st.error(f"Erro ao cadastrar: {str(e)}")


# =========================
# CRUD Clientes com Modal
# =========================

def crud_clientes():
    supabase = init_supabase()
    load_external_css()
    show_header()

    st.markdown("<h3 style='text-align: center;'>🏢 Gerenciamento de Clientes</h3>", unsafe_allow_html=True)

    # ----- Filtro de empresa -----
    nomes_clientes = supabase.table("clientes").select("nome", count="distinct").execute().data
    empresa_opcoes = [c["nome"] for c in nomes_clientes] if nomes_clientes else []
    empresa_selecionada = st.selectbox("Filtrar por Cliente (Empresa)", empresa_opcoes)

    # Busca clientes filtrados
    clientes = supabase.table("clientes").select("*").eq("nome", empresa_selecionada).execute().data

    modal = Modal("✏️ Alterar Cliente", key="edit_cliente_modal")

    # ----- Listagem de clientes -----
    if clientes:
        for cliente in clientes:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{cliente['nome']}** - {cliente['cnpj']} ({cliente['cidade']}/{cliente['estado']})")
            with col2:
                if st.button("✏️ Alterar", key=f"alt_{cliente['id']}"):
                    st.session_state["edit_cliente"] = cliente
                    modal.open()
            with col3:
                if st.button("🗑️ Excluir", key=f"exc_{cliente['id']}"):
                    supabase.table("clientes").delete().eq("id", cliente["id"]).execute()
                    st.success("Cliente excluído com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhum cliente cadastrado para este cliente/empresa.")

    # ----- Modal de edição -----
    if modal.is_open():
        cliente_edit = st.session_state.get("edit_cliente")
        if cliente_edit:
            with modal.container():
                st.markdown("### ✏️ Editar Cliente")
                with st.form("editar_cliente"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome = st.text_input("Nome", value=cliente_edit.get("nome", ""))
                        nome_fantasia = st.text_input("Nome Fantasia", value=cliente_edit.get("nome_fantasia", ""))
                        cnpj = st.text_input("CNPJ", value=cliente_edit.get("cnpj", ""))
                        cidade = st.text_input("Cidade", value=cliente_edit.get("cidade", ""))
                        estado = st.text_input("Estado", value=cliente_edit.get("estado", ""))
                        celular = st.text_input("Celular", value=cliente_edit.get("celular", ""))
                        mensalidade = st.text_input("Mensalidade", value=cliente_edit.get("mensalidade", ""))
                        api = st.text_input("API", value=cliente_edit.get("api", ""))
                        codcliente_azoup = st.text_input("Código Cliente Azoup", value=cliente_edit.get("codcliente_azoup", ""))
                    with col2:
                        data_inicio = st.date_input(
                            "Data Início",
                            value=datetime.fromisoformat(cliente_edit.get("data_inicio")) if cliente_edit.get("data_inicio") else datetime.now()
                        )
                        data_licenca = st.date_input(
                            "Data Licença",
                            value=datetime.fromisoformat(cliente_edit.get("data_licenca")) if cliente_edit.get("data_licenca") else datetime.now()
                        )
                        data_cancelamento = st.date_input(
                            "Data Cancelamento",
                            value=datetime.fromisoformat(cliente_edit.get("data_cancelamento")) if cliente_edit.get("data_cancelamento") else datetime.now()
                        )
                        caminho = st.text_input("Caminho", value=cliente_edit.get("caminho", ""))
                        usuario = st.text_input("Usuário", value=cliente_edit.get("usuario", ""))
                        senha = st.text_input("Senha", value=cliente_edit.get("senha", ""))
                        email = st.text_input("Email", value=cliente_edit.get("email", ""))
                        host = st.text_input("Host", value=cliente_edit.get("host", "azoupfb5.sp1.br.saveincloud.net.br"))
                        porta = st.text_input("Porta", value=cliente_edit.get("porta", "15421"))
                        ativo = st.selectbox("Ativo", ["S", "N"], index=0 if cliente_edit.get("ativo") == "S" else 1)

                    submitted = st.form_submit_button("💾 Salvar Alterações")

                    if submitted:
                        update_data = {
                            "nome": nome,
                            "nome_fantasia": nome_fantasia,
                            "cnpj": cnpj,
                            "cidade": cidade,
                            "estado": estado,
                            "celular": celular,
                            "mensalidade": mensalidade,
                            "api": api,
                            "codcliente_azoup": codcliente_azoup,
                            "data_inicio": str(data_inicio),
                            "data_licenca": str(data_licenca),
                            "data_cancelamento": str(data_cancelamento),
                            "caminho": caminho,
                            "usuario": usuario,
                            "senha": senha,
                            "email": email,
                            "host": host,
                            "porta": porta,
                            "ativo": ativo
                        }
                        supabase.table("clientes").update(update_data).eq("id", cliente_edit["id"]).execute()
                        st.success("Cliente atualizado com sucesso!")
                        modal.close()
                        st.rerun()



# =========================
# Main
# =========================

def main():
    st.set_page_config(page_title="Azoup - Administração", layout="wide")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        menu = ["Cadastro Super Admin", "Gerenciar Clientes", "Sair"]
        escolha = st.sidebar.selectbox("Menu", menu)

        if escolha == "Cadastro Super Admin":
            cadastro_super_admin()
        elif escolha == "Gerenciar Clientes":
            crud_clientes()
        elif escolha == "Sair":
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()


if __name__ == "__main__":
    main()
