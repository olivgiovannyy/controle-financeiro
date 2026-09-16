"""Regras financeiras puras: não dependem do Flask nem do arquivo JSON."""
from datetime import date
from decimal import Decimal, InvalidOperation
import re

CATEGORIAS = {
    "receita": ["Salário", "Freelance", "Rendimentos", "Outros"],
    "despesa": ["Alimentação", "Transporte", "Moradia", "Lazer", "Compras",
                "Assinaturas", "Educação", "Saúde", "Investimentos", "Outros"],
}
ESSENCIAIS = {"Alimentação", "Transporte", "Moradia", "Educação", "Saúde"}
DIVISAO = {"Reserva": 40, "Investimentos": 30, "Meta financeira": 20, "Lazer": 10}


def dinheiro(valor, zero=False):
    """Converte reais para centavos inteiros, evitando erros de ponto flutuante."""
    try:
        n = Decimal(str(valor))
        if not n.is_finite() or n < 0 or (not zero and n == 0) or n > 999999999:
            raise ValueError()
        if n != n.quantize(Decimal("0.01")):
            raise ValueError()
        return int(n * 100)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Informe um valor válido, com até duas casas decimais.")


def texto(valor, nome):
    if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > 120:
        raise ValueError(f"{nome}: preencha entre 1 e 120 caracteres.")
    return valor.strip()


def mes_valido(mes):
    if not isinstance(mes, str) or not re.fullmatch(r"\d{4}-\d{2}", mes):
        raise ValueError("Mês inválido. Use AAAA-MM.")
    date.fromisoformat(mes + "-01")
    return mes


def anterior(mes):
    ano, numero = map(int, mes.split("-"))
    return f"{ano - (numero == 1):04d}-{12 if numero == 1 else numero - 1:02d}"


def validar_transacao(dados):
    tipo = dados.get("tipo")
    if tipo not in CATEGORIAS or dados.get("categoria") not in CATEGORIAS[tipo]:
        raise ValueError("Tipo ou categoria inválida.")
    data = dados.get("data", "")
    if not isinstance(data, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
        raise ValueError("Data inválida.")
    date.fromisoformat(data)
    return {"descricao": texto(dados.get("descricao"), "Descrição"),
            "valor_centavos": dinheiro(dados.get("valor")), "tipo": tipo,
            "categoria": dados["categoria"], "data": data}


def reais(centavos):
    return centavos / 100


def brl(centavos):
    return "R$ " + f"{reais(centavos):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def percentual(parte, total):
    return round(parte / total * 100, 2) if total else None


def resumo(dados, mes):
    itens = [t for t in dados["transacoes"] if t["data"][:7] == mes]
    receita = sum(t["valor_centavos"] for t in itens if t["tipo"] == "receita")
    categorias = {c: sum(t["valor_centavos"] for t in itens
                        if t["tipo"] == "despesa" and t["categoria"] == c)
                  for c in CATEGORIAS["despesa"]}
    despesa = sum(categorias.values())
    saldo = receita - despesa
    return {"receitas": receita, "despesas": despesa, "saldo": saldo,
            "economia": max(saldo, 0), "categorias": categorias,
            "comprometida": percentual(despesa, receita),
            "taxa_economia": percentual(saldo, receita)}


def planejar(dados, mes, saldo):
    percentuais = dados["planos"].get(mes, DIVISAO)
    disponivel = max(0, saldo)
    valores = {k: disponivel * p // 100 for k, p in percentuais.items()}
    # O resto dos centavos vai para a reserva, garantindo soma exata.
    valores["Reserva"] += disponivel - sum(valores.values())
    return {"percentuais": percentuais, "valores": {k: reais(v) for k, v in valores.items()},
            "disponivel": reais(disponivel)}


def dashboard(dados, mes):
    atual, antes = resumo(dados, mes), resumo(dados, anterior(mes))
    cats = atual["categorias"]
    plano = planejar(dados, mes, atual["saldo"])
    analises = []
    if atual["receitas"]:
        analises.append(f"Alimentação consumiu {percentual(cats['Alimentação'], atual['receitas']):.1f}% da renda do mês.".replace(".", "," ,1))
    else:
        analises.append("Sem receitas neste mês: percentuais da renda não se aplicam.")
    diferenca = atual["despesas"] - antes["despesas"]
    analises.append(f"Suas despesas ficaram {brl(abs(diferenca))} {'maiores' if diferenca >= 0 else 'menores'} que no mês anterior.")
    if antes["categorias"]["Lazer"]:
        variacao = (cats["Lazer"] - antes["categorias"]["Lazer"]) / antes["categorias"]["Lazer"] * 100
        analises.append(f"Lazer variou {variacao:+.1f}% em relação ao mês anterior.".replace(".", ",", 1))
    if atual["despesas"]:
        analises.append(f"Assinaturas representam {percentual(cats['Assinaturas'], atual['despesas']):.1f}% das saídas.".replace(".", ",", 1))
    analises.append(f"Você tem {brl(atual['economia'])} disponíveis após as saídas do mês." if atual["saldo"] >= 0
                    else f"As saídas ultrapassam as receitas em {brl(-atual['saldo'])}.")
    sugestoes = []
    for categoria, valor in sorted(cats.items(), key=lambda item: item[1], reverse=True):
        taxa = {"Lazer": 20, "Compras": 15, "Assinaturas": 20, "Alimentação": 10, "Outros": 10}.get(categoria)
        if valor and taxa:
            sugestoes.append({"categoria": categoria, "gasto": reais(valor), "percentual": taxa,
                             "economia": reais(valor * taxa // 100)})
    orcamentos = []
    for categoria, limite in dados["orcamentos"].get(mes, {}).items():
        gasto = cats[categoria]
        orcamentos.append({"categoria": categoria, "limite": reais(limite), "gasto": reais(gasto),
                           "percentual": percentual(gasto, limite), "excesso": reais(max(0, gasto - limite))})
    evolucao = []
    for numero in range(1, 13):
        referencia = f"{mes[:4]}-{numero:02d}"
        r = resumo(dados, referencia)
        evolucao.append({"mes": referencia, "receitas": reais(r["receitas"]), "despesas": reais(r["despesas"])})
    essenciais = sum(v for c, v in cats.items() if c in ESSENCIAIS)
    investimentos = cats["Investimentos"]
    saldo_acumulado = sum((1 if t["tipo"] == "receita" else -1) * t["valor_centavos"]
                         for t in dados["transacoes"] if t["data"][:7] <= mes)
    return {**{k: reais(atual[k]) for k in ["receitas", "despesas", "saldo", "economia"]},
            "saldo_acumulado": reais(saldo_acumulado), "comprometida": atual["comprometida"],
            "taxa_economia": atual["taxa_economia"], "investimento_sugerido": plano["valores"]["Investimentos"],
            "categorias": {k: reais(v) for k, v in cats.items() if v},
            "distribuicao": {"Essenciais": reais(essenciais),
                             "Não essenciais": reais(atual["despesas"] - essenciais - investimentos),
                             "Investimentos realizados": reais(investimentos), "Sobra do mês": reais(atual["economia"])},
            "deficit": reais(max(0, -atual["saldo"])), "evolucao": evolucao, "analises": analises,
            "sugestoes": sugestoes[:3], "orcamentos": orcamentos, "plano": plano}


def comparar(dados, primeiro, segundo):
    a, b = resumo(dados, primeiro), resumo(dados, segundo)
    deltas = {c: b["categorias"][c] - a["categorias"][c] for c in CATEGORIAS["despesa"]}
    maiores = [(c, v) for c, v in deltas.items() if v > 0]
    menores = [(c, v) for c, v in deltas.items() if v < 0]
    def extremo(itens, func):
        if not itens:
            return None
        c, v = func(itens, key=lambda item: item[1])
        return {"categoria": c, "variacao": reais(v)}
    return {"primeiro": {k: reais(a[k]) for k in ["receitas", "despesas", "saldo", "economia"]},
            "segundo": {k: reais(b[k]) for k in ["receitas", "despesas", "saldo", "economia"]},
            "variacao_despesas": percentual(b["despesas"] - a["despesas"], a["despesas"]),
            "maior_aumento": extremo(maiores, max), "maior_reducao": extremo(menores, min)}
