from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, Session

Base = declarative_base()
DB_PATH = "cesta_basica.db"

class IPCA(Base):
    __tablename__ = "ipca"
    id    = Column(Integer, primary_key=True, autoincrement=True)
    data  = Column(Date, nullable=False, unique=True)
    valor = Column(Float, nullable=False)

class Categoria(Base):
    __tablename__ = "categoria"
    id                    = Column(Integer, primary_key=True, autoincrement=True)
    nome                  = Column(String, nullable=False, unique=True)
    quantidade_necessaria = Column(Float, nullable=False)
    unidade               = Column(String, nullable=False)
    complemento           = Column(Integer, nullable=False, default=0)
    produtos = relationship("Produto", back_populates="categoria")

class Produto(Base):
    __tablename__ = "produto"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    categoria_id   = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    nome           = Column(String, nullable=False)
    marca          = Column(String)
    preco          = Column(Float, nullable=False)
    unidade_volume = Column(String)
    preco_por_kg   = Column(Float)
    url            = Column(String)
    __table_args__ = (UniqueConstraint("nome", "marca", name="uq_produto_nome_marca"),)
    categoria = relationship("Categoria", back_populates="produtos")

def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}", echo=False)

def criar_banco():
    engine = get_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        if session.query(Categoria).count() > 0: return
        session.add_all([
            Categoria(nome="Arroz", quantidade_necessaria=5, unidade="kg", complemento=0),
            Categoria(nome="Feijão", quantidade_necessaria=2, unidade="kg", complemento=0),
            Categoria(nome="Óleo de Soja", quantidade_necessaria=0.9, unidade="L", complemento=0),
            Categoria(nome="Açúcar", quantidade_necessaria=1, unidade="kg", complemento=0),
            Categoria(nome="Café", quantidade_necessaria=0.5, unidade="kg", complemento=0),
            Categoria(nome="Macarrão", quantidade_necessaria=1, unidade="kg", complemento=1),
            Categoria(nome="Sal", quantidade_necessaria=1, unidade="kg", complemento=1)
        ])
        session.commit()