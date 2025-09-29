import streamlit as st
from supabase import create_client
import fdb
import os
import sys

# Configurações do Supabase
@st.cache_resource

def init_supabase():
    # Inicializa e retorna o cliente Supabase
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["key"]
    return create_client(supabase_url, supabase_key)

# Conexão dinâmica com Firebird usando fdb
def get_firebird_connection(conn_data):
    try:
        # Verifica se o host está vazio (conexão local)
        if not conn_data['host'] or conn_data['host'].strip() == '':
            # Conexão local - usa apenas o caminho do banco
            dsn = conn_data['database']
        else:
            # Conexão remota - formata host/porta:caminho
            porta = conn_data.get('porta', '3050')  # Porta padrão do Firebird
            dsn = f"{conn_data['host']}/{porta}:{conn_data['database']}"
        
        conn = fdb.connect(
            dsn=dsn,
            user=conn_data['user'],
            password=conn_data['password'],
            charset='UTF8'
        )
        return conn
    except Exception as e:
        st.error(f"Erro na conexão Firebird: {str(e)}")
        return None

# Função para testar conexão com Firebird
def test_firebird_connection(conn_data):
    try:
        conn = get_firebird_connection(conn_data)
        if conn:
            conn.close()
            return True
        return False
    except Exception as e:
        st.error(f"Falha no teste de conexão: {str(e)}")
        return False