"""Único módulo que conhece o JSON. Pode ser substituído por SQLite depois."""
import json
import os
from copy import deepcopy
from pathlib import Path
from threading import RLock

VAZIO = {"transacoes": [], "metas": [], "orcamentos": {}, "planos": {}}


class Repositorio:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self.lock = RLock()

    def ler(self):
        # O lock impede duas requisições de escreverem ao mesmo tempo neste processo.
        with self.lock:
            if not self.caminho.exists():
                self._salvar(deepcopy(VAZIO))
            with self.caminho.open(encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            if not isinstance(dados, dict) or not all(k in dados for k in VAZIO):
                raise ValueError("Estrutura do arquivo de dados inválida.")
            return dados

    def _salvar(self, dados):
        # Grava um temporário e troca o original só quando a escrita termina.
        temporario = self.caminho.with_suffix(".tmp")
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, self.caminho)

    def alterar(self, operacao):
        with self.lock:
            dados = self.ler()
            resultado = operacao(dados)
            self._salvar(dados)
            return resultado
