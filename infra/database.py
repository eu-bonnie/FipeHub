import pandas as pd
from sqlalchemy import create_engine, text

# Conexão via Docker
DB_URL = "postgresql://user_fipe:password_fipe@localhost:5432/fipe_db"
engine = create_engine(DB_URL)

def init_db():
    """Cria as tabelas iniciais e de geolocalização se não existirem."""
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