"""Testes com arquivo temporário: seus dados pessoais nunca são alterados."""
import json
from pathlib import Path
import tempfile
import unittest
from app import criar_app
from financeiro import anterior, dashboard, dinheiro
from repositorio import VAZIO


class TesteFinanceiro(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = Path(self.pasta.name) / "dados.json"
        self.caminho.write_text(json.dumps(VAZIO), encoding="utf-8")
        self.client = criar_app(self.caminho).test_client()

    def tearDown(self):
        self.pasta.cleanup()

    def inserir(self, valor, tipo="receita", categoria="Salário", data="2026-09-10"):
        r = self.client.post("/api/transacoes", json={"descricao": "Teste", "valor": valor,
            "categoria": categoria, "tipo": tipo, "data": data})
        self.assertEqual(r.status_code, 201)
        return r.json["id"]

    def test_crud_e_persistencia(self):
        identificador = self.inserir("2500.00")
        self.inserir("1500.00", "despesa", "Alimentação")
        d = self.client.get("/api/dashboard?mes=2026-09").json
        self.assertEqual((d["saldo"], d["comprometida"], d["economia"]), (1000, 60, 1000))
        self.assertEqual(d["investimento_sugerido"], 300)
        self.assertEqual(sum(d["distribuicao"].values()), 2500)
        novo = {"descricao": "Alterado", "valor": "3000", "tipo": "receita", "categoria": "Salário", "data": "2026-09-10"}
        self.assertEqual(self.client.put(f"/api/transacoes/{identificador}", json=novo).status_code, 200)
        cliente_novo = criar_app(self.caminho).test_client()
        self.assertEqual(cliente_novo.get("/api/dashboard?mes=2026-09").json["receitas"], 3000)
        self.assertEqual(self.client.delete(f"/api/transacoes/{identificador}").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/transacoes/{identificador}").status_code, 404)

    def test_validacoes(self):
        for valor in ("-1", "0", "abc", "NaN", "Infinity", "1.001", True, None):
            r = self.client.post("/api/transacoes", json={"descricao": "X", "valor": valor, "tipo": "receita", "categoria": "Salário", "data": "2026-09-10"})
            self.assertEqual(r.status_code, 400, valor)
        for campo, valor in [("descricao", " "), ("data", "2026-02-30"), ("tipo", "outro"), ("categoria", "Inválida")]:
            dado = {"descricao": "Teste", "valor": "10", "tipo": "receita", "categoria": "Salário", "data": "2026-09-10"}
            dado[campo] = valor
            self.assertEqual(self.client.post("/api/transacoes", json=dado).status_code, 400)
        self.assertEqual(self.client.get("/api/dashboard?mes=2026-13").status_code, 400)
        self.assertEqual(self.client.post("/api/transacoes", json=[]).status_code, 400)

    def test_zero_deficit_centavos_e_virada_ano(self):
        self.assertEqual(anterior("2026-01"), "2025-12")
        self.assertEqual(dinheiro("0.29"), 29)
        d = dashboard(VAZIO, "2026-09")
        self.assertIsNone(d["comprometida"])
        self.assertEqual(d["plano"]["disponivel"], 0)
        self.inserir("10", "despesa", "Investimentos")
        d = self.client.get("/api/dashboard?mes=2026-09").json
        self.assertEqual((d["deficit"], d["economia"], d["investimento_sugerido"]), (10, 0, 0))
        self.assertEqual(d["distribuicao"]["Não essenciais"], 0)
        self.inserir("10.01")
        d = self.client.get("/api/dashboard?mes=2026-09").json
        self.assertEqual(d["plano"]["valores"]["Reserva"], .01)

    def test_metas_orcamentos_planos(self):
        m = self.client.post("/api/metas", json={"nome": "PC", "valor": "6000", "guardado": "1500"})
        self.assertEqual(m.status_code, 201)
        self.assertEqual(self.client.get("/api/metas").json[0]["percentual"], 25)
        self.assertEqual(self.client.put('/api/metas/'+m.json['id'], json={"nome":"PC", "valor":"6000", "guardado":"7000"}).status_code, 200)
        self.assertEqual(self.client.get("/api/metas").json[0]["faltam"], 0)
        self.assertEqual(self.client.delete('/api/metas/'+m.json['id']).status_code, 200)
        self.inserir("570", "despesa", "Alimentação")
        o = {"mes": "2026-09", "categoria": "Alimentação", "limite": "500"}
        self.assertEqual(self.client.put("/api/orcamentos", json=o).status_code, 200)
        self.assertEqual(self.client.get("/api/dashboard?mes=2026-09").json["orcamentos"][0]["excesso"], 70)
        self.assertEqual(self.client.delete("/api/orcamentos", json=o).status_code, 200)
        p = {"mes":"2026-09", "percentuais":{"Reserva":40,"Investimentos":30,"Meta financeira":20,"Lazer":9}}
        self.assertEqual(self.client.put("/api/planejamento", json=p).status_code, 400)
        p["percentuais"]["Lazer"] = 10
        self.assertEqual(self.client.put("/api/planejamento", json=p).status_code, 200)

    def test_filtros_e_comparacao(self):
        self.inserir("100", "despesa", "Lazer", "2026-08-10")
        self.inserir("150", "despesa", "Lazer")
        self.inserir("200")
        itens = self.client.get("/api/transacoes?mes=2026-09&ano=2026&tipo=despesa&categoria=Lazer").json
        self.assertEqual(len(itens), 1)
        d = self.client.get("/api/comparacao?primeiro=2026-08&segundo=2026-09").json
        self.assertEqual(d["variacao_despesas"], 50)
        self.assertEqual(d["maior_aumento"], {"categoria":"Lazer", "variacao":50})
        self.assertIsNone(d["maior_reducao"])

    def test_paginas_e_origem(self):
        for pagina in ["/", "/transacoes", "/metas", "/planejamento", "/relatorios", "/configuracoes", "/api/categorias", "/api/exportar"]:
            self.assertEqual(self.client.get(pagina).status_code, 200, pagina)
        self.assertEqual(self.client.post("/api/transacoes", json={}, headers={"Origin":"https://outro.example"}).status_code, 403)
        self.assertEqual(self.client.post("/api/transacoes", data="x").status_code, 415)


if __name__ == "__main__":
    unittest.main(verbosity=2)
