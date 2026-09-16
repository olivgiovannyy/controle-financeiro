"""Cria dados FICTÍCIOS apenas se dados.json não existir. Nunca sobrescreve dados."""
from datetime import date
from pathlib import Path
import json
from financeiro import anterior


def gerar(caminho):
    atual = date.today().strftime("%Y-%m")
    passado = anterior(atual)
    transacoes = []
    for mes, itens in [(passado, [("Salário", 250000, "Salário", "receita"),
                                  ("Mercado", 60000, "Alimentação", "despesa"),
                                  ("Aluguel", 70000, "Moradia", "despesa"),
                                  ("Passeios", 25000, "Lazer", "despesa")]),
                       (atual, [("Salário", 250000, "Salário", "receita"),
                                ("Projeto freelance", 45000, "Freelance", "receita"),
                                ("Mercado", 42000, "Alimentação", "despesa"),
                                ("Aluguel", 70000, "Moradia", "despesa"),
                                ("Bilhete transporte", 18000, "Transporte", "despesa"),
                                ("Cinema e passeios", 18000, "Lazer", "despesa"),
                                ("Streaming", 4490, "Assinaturas", "despesa"),
                                ("Roupas", 15000, "Compras", "despesa"),
                                ("Aporte realizado", 10000, "Investimentos", "despesa")])]:
        for i, (descricao, valor, categoria, tipo) in enumerate(itens):
            transacoes.append({"id": f"demo-{mes}-{i}", "descricao": descricao,
                               "valor_centavos": valor, "categoria": categoria,
                               "tipo": tipo, "data": f"{mes}-{i + 1:02d}"})
    dados = {"transacoes": transacoes,
             "metas": [{"id": "demo-meta", "nome": "Meu novo computador", "valor_centavos": 600000, "guardado_centavos": 150000}],
             "orcamentos": {atual: {"Alimentação": 50000, "Lazer": 15000, "Compras": 25000}}, "planos": {}}
    with Path(caminho).open("x", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    destino = Path(__file__).with_name("dados.json")
    if destino.exists():
        print("dados.json já existe; nada foi alterado.")
    else:
        gerar(destino)
        print("Dados fictícios criados. Veja no README como começar do zero.")
