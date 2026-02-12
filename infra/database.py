import pandas as pd
from sqlalchemy import create_engine, text

# Conexão via Docker
DB_URL = "postgresql://user_fipe:password_fipe@localhost:5432/fipe_db"
engine = create_engine(DB_URL)

def init_db():
    """Cria as tabelas iniciais, geolocalização e usuários se não existirem."""
    with engine.connect() as conn:
        # 1. Tabela de Logs de Consulta (Home)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS buscas_log (
                id SERIAL PRIMARY KEY,
                marca VARCHAR(100),
                modelo VARCHAR(100),
                ano VARCHAR(20),
                preco VARCHAR(50),
                data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 2. Tabela de Áreas Delimitadas pelo Coordenador (O Quadrado)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS areas_pesquisa (
                id SERIAL PRIMARY KEY,
                municipio VARCHAR(100),
                lat_min DOUBLE PRECISION,
                lat_max DOUBLE PRECISION,
                lon_min DOUBLE PRECISION,
                lon_max DOUBLE PRECISION,
                mes_referencia VARCHAR(20),
                status VARCHAR(20) DEFAULT 'Pendente',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 3. Tabela de Lojas
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lojas (
                id SERIAL PRIMARY KEY,
                nome_loja VARCHAR(150),
                endereco VARCHAR(255),
                cnpj VARCHAR(20),
                status VARCHAR(20) DEFAULT 'Pendente' -- Pendente, Aprovada, Rejeitada
            );
        """))

        # 4. Tabela de Coletas do Pesquisador
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS coletas_campo (
                id SERIAL PRIMARY KEY,
                area_id INTEGER REFERENCES areas_pesquisa(id),
                loja_id INTEGER, -- Pode ser ID da tabela lojas ou NULL se for "Outros"
                loja_nome_manual VARCHAR(150), -- Se for "Outros"
                marca VARCHAR(100),
                modelo VARCHAR(100),
                ano VARCHAR(20),
                preco_anunciado VARCHAR(50),
                status VARCHAR(20) DEFAULT 'Aguardando Aprovação',
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 5. Tabela de Usuários e Controle de Acesso
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                codigo VARCHAR(20) NOT NULL,
                perfil VARCHAR(20) NOT NULL -- Admin, Coordenador, Pesquisador, Lojista
            );
        """))

        # 6. Criar Admin Inicial (caso não exista) para permitir o primeiro acesso
        conn.execute(text("""
            INSERT INTO usuarios (username, codigo, perfil) 
            VALUES ('admin', '1234', 'Admin') 
            ON CONFLICT (username) DO NOTHING;
        """))

        # Tabela para Marcas Manuais
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS marcas_custom (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) UNIQUE NOT NULL
            );
        """))
        
        # Tabela para Modelos Manuais
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS modelos_custom (
                id SERIAL PRIMARY KEY,
                marca_nome VARCHAR(100) NOT NULL,
                nome VARCHAR(100) NOT NULL,
                UNIQUE(marca_nome, nome)
            );
        """))

        conn.commit()

def salvar_consulta(dados):
    """Registra logs de uso da tabela FIPE no banco."""
    df = pd.DataFrame([dados])
    df.to_sql('buscas_log', engine, if_exists='append', index=False)

def salvar_area_pesquisa(dados):
    """Salva o quadrado/área definido pelo coordenador."""
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO areas_pesquisa (municipio, lat_min, lat_max, lon_min, lon_max, mes_referencia)
            VALUES (:municipio, :lat_min, :lat_max, :lon_min, :lon_max, :mes_referencia)
        """), dados)
        conn.commit()

def listar_areas_pendentes():
    """Busca áreas que o pesquisador ainda precisa trabalhar."""
    query = "SELECT * FROM areas_pesquisa WHERE status = 'Pendente' ORDER BY data_criacao DESC"
    return pd.read_sql(query, engine)