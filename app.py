"""Servidor local: páginas HTML e API JSON consumida pelo fetch do navegador."""
from datetime import date
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from repositorio import Repositorio
from financeiro import (CATEGORIAS, DIVISAO, comparar, dashboard, dinheiro,
                        mes_valido, percentual, reais, texto, validar_transacao)


def criar_app(caminho=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    repo = Repositorio(caminho or Path(__file__).with_name("dados.json"))

    @app.before_request
    def proteger_api():
        # Rejeita escritas feitas por outros sites. Aplicação destinada ao localhost.
        if request.method in {"POST", "PUT", "DELETE"}:
            origem = request.headers.get("Origin")
            if origem and urlparse(origem).netloc != request.host:
                return jsonify(erro="Origem não permitida."), 403
            if request.method != "DELETE" and not request.is_json:
                return jsonify(erro="Envie um corpo JSON."), 415

    @app.after_request
    def cabecalhos(resposta):
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["Cache-Control"] = "no-store"
        return resposta

    @app.errorhandler(ValueError)
    def erro_validacao(erro):
        return jsonify(erro=str(erro)), 400

    @app.errorhandler(Exception)
    def erro_geral(erro):
        if isinstance(erro, HTTPException):
            return jsonify(erro=erro.description), erro.code
        app.logger.exception("Falha na operação")
        return jsonify(erro="Não foi possível acessar os dados. Confira o terminal e preserve seu JSON."), 500

    def corpo():
        dados = request.get_json()
        if not isinstance(dados, dict):
            raise ValueError("O corpo da requisição deve ser um objeto JSON.")
        return dados

    def mes():
        return mes_valido(request.args.get("mes", date.today().strftime("%Y-%m")))

    @app.get("/")
    def inicio():
        return render_template("dashboard.html", pagina="dashboard")

    @app.get("/<pagina>")
    def pagina(pagina):
        if pagina not in {"transacoes", "metas", "planejamento", "relatorios", "configuracoes"}:
            return jsonify(erro="Página não encontrada."), 404
        return render_template(pagina + ".html", pagina=pagina)

    @app.get("/api/categorias")
    def categorias():
        return jsonify(CATEGORIAS)

    # GET consulta sem alterar; POST cadastra; PUT substitui; DELETE exclui.
    @app.get("/api/transacoes")
    def transacoes():
        itens = repo.ler()["transacoes"]
        referencia, ano = request.args.get("mes"), request.args.get("ano")
        if referencia:
            mes_valido(referencia)
            itens = [t for t in itens if t["data"].startswith(referencia)]
        if ano:
            if not ano.isdigit() or len(ano) != 4 or not 1 <= int(ano) <= 9999:
                raise ValueError("Ano inválido.")
            itens = [t for t in itens if t["data"][:4] == ano]
        for campo in ("tipo", "categoria"):
            filtro = request.args.get(campo)
            if filtro:
                itens = [t for t in itens if t[campo] == filtro]
        return jsonify([{**t, "valor": reais(t["valor_centavos"])}
                        for t in sorted(itens, key=lambda t: t["data"], reverse=True)])

    @app.post("/api/transacoes")
    def cadastrar():
        item = {"id": uuid4().hex, **validar_transacao(corpo())}
        repo.alterar(lambda d: d["transacoes"].append(item))
        return jsonify(item), 201

    @app.route("/api/transacoes/<identificador>", methods=["PUT", "DELETE"])
    def alterar_transacao(identificador):
        novo = validar_transacao(corpo()) if request.method == "PUT" else None
        def operacao(dados):
            for indice, item in enumerate(dados["transacoes"]):
                if item["id"] == identificador:
                    if novo is None:
                        dados["transacoes"].pop(indice)
                    else:
                        dados["transacoes"][indice] = {"id": identificador, **novo}
                    return True
            return False
        if not repo.alterar(operacao):
            return jsonify(erro="Transação não encontrada."), 404
        return jsonify(ok=True)

    @app.get("/api/dashboard")
    def painel():
        return jsonify(dashboard(repo.ler(), mes()))

    @app.get("/api/analise")
    def analise():
        resultado = dashboard(repo.ler(), mes())
        return jsonify(analises=resultado["analises"], sugestoes=resultado["sugestoes"])

    @app.get("/api/comparacao")
    def comparacao():
        a = mes_valido(request.args.get("primeiro"))
        b = mes_valido(request.args.get("segundo"))
        return jsonify(comparar(repo.ler(), a, b))

    @app.route("/api/metas", methods=["GET", "POST"])
    def metas():
        if request.method == "GET":
            return jsonify([{**m, "valor": reais(m["valor_centavos"]),
                             "guardado": reais(m["guardado_centavos"]),
                             "faltam": reais(max(0, m["valor_centavos"] - m["guardado_centavos"])),
                             "percentual": percentual(m["guardado_centavos"], m["valor_centavos"])}
                            for m in repo.ler()["metas"]])
        m = validar_meta(corpo())
        m["id"] = uuid4().hex
        repo.alterar(lambda d: d["metas"].append(m))
        return jsonify(m), 201

    def validar_meta(dados):
        return {"nome": texto(dados.get("nome"), "Nome"), "valor_centavos": dinheiro(dados.get("valor")),
                "guardado_centavos": dinheiro(dados.get("guardado"), zero=True)}

    @app.route("/api/metas/<identificador>", methods=["PUT", "DELETE"])
    def alterar_meta(identificador):
        nova = validar_meta(corpo()) if request.method == "PUT" else None
        def operacao(dados):
            for indice, item in enumerate(dados["metas"]):
                if item["id"] == identificador:
                    if nova is None:
                        dados["metas"].pop(indice)
                    else:
                        dados["metas"][indice] = {"id": identificador, **nova}
                    return True
            return False
        if not repo.alterar(operacao):
            return jsonify(erro="Meta não encontrada."), 404
        return jsonify(ok=True)

    @app.put("/api/planejamento")
    def planejamento():
        dados = corpo()
        referencia = mes_valido(dados.get("mes"))
        divisao = dados.get("percentuais")
        if (not isinstance(divisao, dict) or set(divisao) != set(DIVISAO)
                or any(type(v) is not int or not 0 <= v <= 100 for v in divisao.values())
                or sum(divisao.values()) != 100):
            raise ValueError("Os quatro percentuais devem ser inteiros e somar 100%.")
        repo.alterar(lambda d: d["planos"].update({referencia: divisao}))
        return jsonify(ok=True)

    @app.route("/api/orcamentos", methods=["PUT", "DELETE"])
    def orcamentos():
        dados = corpo()
        referencia = mes_valido(dados.get("mes"))
        categoria = dados.get("categoria")
        if categoria not in CATEGORIAS["despesa"]:
            raise ValueError("Categoria inválida.")
        limite = dinheiro(dados.get("limite")) if request.method == "PUT" else None
        def operacao(d):
            limites = d["orcamentos"].setdefault(referencia, {})
            if limite is None:
                limites.pop(categoria, None)
            else:
                limites[categoria] = limite
        repo.alterar(operacao)
        return jsonify(ok=True)

    @app.get("/api/exportar")
    def exportar():
        resposta = jsonify(repo.ler())
        resposta.headers["Content-Disposition"] = 'attachment; filename="backup-financeiro.json"'
        return resposta

    return app


if __name__ == "__main__":
    # Um processo local. Não exponha este servidor pessoal à internet.
    criar_app().run(host="127.0.0.1", port=5000, debug=False)
