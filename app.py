from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_simplelogin import SimpleLogin, login_required
import os

# ───────────────────────────────
# Configuração da aplicação
# ───────────────────────────────
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///padaria.db"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "MinhaChave10000#")  # troque em produção

# ───────────────────────────────
# Banco de dados
# ───────────────────────────────
db = SQLAlchemy(app)          # ✔️  única inicialização

# ───────────────────────────────
# Autenticação (Flask-SimpleLogin)
# ───────────────────────────────
def checker(user):
    """Valida usuário/senha contra variáveis de ambiente ou valores-padrão."""
    expected_user = os.getenv("SL_USER", "tulio")
    expected_pass = os.getenv("SL_PASS", "7410git")
    return (
        user.get("username") == expected_user
        and user.get("password") == expected_pass
    )

SimpleLogin(app, login_checker=checker)   # ✔️  única chamada

# ───────────────────────────────
# Modelos
# ───────────────────────────────
class Product(db.Model):
    __tablename__ = "produto"

    id          = db.Column(db.Integer, primary_key=True)
    nome        = db.Column(db.String(100),  nullable=False)
    descricao   = db.Column(db.String(500))
    ingredientes= db.Column(db.String(500))
    origem      = db.Column(db.String(100))
    imagem      = db.Column(db.String(100))

    def __init__(self, nome, descricao, ingredientes, origem, imagem):
        self.nome         = nome
        self.descricao    = descricao
        self.ingredientes = ingredientes
        self.origem       = origem
        self.imagem       = imagem

# ───────────────────────────────
# Rotas
# ───────────────────────────────
@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/listar_produtos", methods=["GET", "POST"])
@login_required
def listar_produtos():
    if request.method == "POST":
        termo = request.form["pesquisa"]
        produtos = (
            db.session.execute(
                db.select(Product).filter(Product.nome.like(f"%{termo}%"))
            ).scalars()
        )
    else:
        produtos = db.session.execute(db.select(Product)).scalars()
    return render_template("produtos.html", produtos=produtos)


@app.route("/cadastrar_produto", methods=["GET", "POST"])
@login_required
def cadastrar_produto():
    if request.method == "POST":
        status  = {"type": "sucesso", "message": "Produto cadastrado com sucesso!"}
        dados   = request.form
        imagem  = request.files["imagem"]
        try:
            produto = Product(
                dados["nome"],
                dados["descricao"],
                dados["ingredientes"],
                dados["origem"],
                imagem.filename,
            )
            imagem.save(os.path.join("static/imagens", imagem.filename))
            db.session.add(produto)
            db.session.commit()
        except Exception as e:
            status = {
                "type": "erro",
                "message": f"Problema ao cadastrar {dados['nome']}! - {e}",
            }
        return render_template("cadastrar.html", status=status)

    return render_template("cadastrar.html")


@app.route("/editar_produtos/<int:id>", methods=["GET", "POST"])
@login_required
def editar_produto(id):
    produto = db.get_or_404(Product, id)

    if request.method == "POST":
        dados   = request.form
        imagem  = request.files["imagem"]

        produto.nome         = dados["nome"]
        produto.descricao    = dados["descricao"]
        produto.ingredientes = dados["ingredientes"]
        produto.origem       = dados["origem"]

        if imagem.filename:
            produto.imagem = imagem.filename
            imagem.save(os.path.join("static/imagens", imagem.filename))

        db.session.commit()
        return redirect("/listar_produtos")

    return render_template("editar.html", produto=produto)


@app.route("/deletar_produto/<int:id>")
@login_required
def deletar_produto(id):
    produto = db.get_or_404(Product, id)
    db.session.delete(produto)
    db.session.commit()
    return redirect("/listar_produtos")

# ───────────────────────────────
# Bootstrap
# ───────────────────────────────
if __name__ == "__main__":          # executado só localmente
    with app.app_context():
        db.create_all()
#    app.run(debug=True)
