[README(1).md](https://github.com/user-attachments/files/32308671/README.1.md)
# Clareza — Controle Financeiro Pessoal

Aplicação web para organizar receitas e despesas, acompanhar o saldo mensal e planejar objetivos financeiros em uma interface visual.

O **Clareza** combina um backend em **Python e Flask** com um frontend em **HTML, CSS e JavaScript**, utilizando **Chart.js** para exibir gráficos. Os dados são armazenados em **JSON**, sem necessidade de configurar um banco de dados.

## Objetivo

Facilitar o acompanhamento das finanças pessoais e ajudar a responder perguntas como:

- Quanto recebi e quanto gastei neste mês?
- Quais categorias concentram minhas despesas?
- Quanto sobrou e como posso distribuir esse dinheiro?
- Onde posso tentar economizar?
- Como estou avançando nas minhas metas?

O projeto também serve como exercício prático de desenvolvimento full stack, conectando uma interface web às regras e ao armazenamento implementados em Python.

## Funcionalidades

### Dashboard financeiro

- Indicadores de receitas, despesas, saldo do mês e saldo acumulado.
- Economia disponível e percentual da renda comprometida.
- Valor planejado para investimentos conforme a divisão escolhida.
- Gráficos de gastos por categoria, receitas × despesas, evolução mensal e distribuição da renda.

### Gerenciamento de transações

- Cadastro, edição e exclusão de receitas e despesas.
- Registro de descrição, valor, categoria e data.
- Filtros por mês, ano, categoria e tipo de movimentação.

### Metas e planejamento

- Criação de metas com valor desejado e valor já guardado.
- Barras de progresso para acompanhar cada objetivo.
- Divisão do saldo disponível entre reserva, investimentos, lazer e meta financeira.
- Limites mensais por categoria, com indicação de uso e alertas de excesso.

### Análises e relatórios

- Comparação entre dois meses.
- Identificação das categorias com maior aumento e maior redução de gastos.
- Sugestões de economia calculadas a partir das despesas cadastradas.
- Exportação de backup em JSON.

A interface se adapta a diferentes tamanhos de tela e apresenta valores e datas no formato brasileiro.

## 🛠️ Tecnologias

| Tecnologia | Papel no projeto |
|---|---|
| Python | Validação, cálculos e regras financeiras |
| Flask | Servidor web, páginas e API |
| HTML5 | Estrutura das telas |
| CSS3 | Estilização e responsividade |
| JavaScript | Interações e comunicação com a API via `fetch()` |
| Chart.js | Visualização dos dados em gráficos |
| JSON | Armazenamento local dos registros |
| unittest | Testes automatizados do backend |

## Como funciona

Ao salvar uma transação, o JavaScript envia os campos do formulário à API Flask usando `fetch()`. O Python valida os dados e grava a movimentação no arquivo `dados.json`.

Quando o dashboard é consultado, o backend lê os registros, calcula os indicadores e devolve uma resposta JSON. O JavaScript utiliza essa resposta para atualizar os cards e os gráficos.

**Os cálculos financeiros ficam no Python.** O frontend cuida da interação e da apresentação dos resultados.

Os valores são armazenados em centavos inteiros, com validação usando `Decimal`, para evitar imprecisões nas operações com dinheiro. A leitura e a escrita ficam isoladas em `repositorio.py`, facilitando uma futura migração para outro tipo de armazenamento.

## Estrutura do projeto

```text
controle-financeiro/
├── app.py
├── financeiro.py
├── repositorio.py
├── gerar_demo.py
├── requirements.txt
├── .gitignore
├── README.md
├── testes.py
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   ├── transacoes.html
│   ├── metas.html
│   ├── planejamento.html
│   ├── relatorios.html
│   └── configuracoes.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        ├── comum.js
        ├── dashboard.js
        ├── transacoes.js
        └── planejamento.js
```

O arquivo **`dados.json`** fica na raiz do projeto durante o uso, mas é ignorado pelo Git para evitar o envio de informações financeiras pessoais. Ao iniciar sem esse arquivo, a aplicação cria uma estrutura vazia.

| Arquivo ou pasta | Responsabilidade |
|---|---|
| `app.py` | Define as rotas e inicia o servidor Flask |
| `financeiro.py` | Concentra cálculos, validações e análises |
| `repositorio.py` | Lê e salva os dados em JSON |
| `gerar_demo.py` | Gera movimentações fictícias para demonstração |
| `templates/` | Contém as páginas HTML |
| `static/` | Contém CSS e JavaScript |
| `testes.py` | Verifica regras e operações da API |

## Como executar

### 1. Pré-requisitos

- Python 3.11 ou superior.
- Git, caso escolha clonar o repositório.
- Navegador atualizado.

Você pode instalar o Python pelo [site oficial](https://www.python.org/downloads/). No Windows, marque a opção **Add Python to PATH** durante a instalação.

### 2. Baixe o projeto

Neste repositório, clique em **Code → Download ZIP**, extraia os arquivos e abra a pasta no VS Code.

Se preferir clonar, copie a URL HTTPS no botão **Code** e use `git clone` seguido dessa URL. Depois, abra a pasta baixada.

### 3. Crie um ambiente virtual

No terminal, dentro da pasta que contém `app.py`:

```bash
python -m venv .venv
```

### 4. Instale as dependências e inicie

**Windows:**

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

**Linux e macOS:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

### 5. Abra no navegador

Acesse **http://127.0.0.1:5000** e mantenha o terminal aberto durante o uso.

As páginas devem ser acessadas pelo servidor Flask. Abrir o HTML diretamente ou usar o Live Server não conecta a interface ao backend.

O Chart.js é carregado por CDN e precisa de conexão com a internet para carregar os gráficos.

## Dados de demonstração

Para experimentar o sistema com movimentações fictícias, execute antes de iniciar o servidor:

**Windows:**

```powershell
.venv\Scripts\python.exe gerar_demo.py
```

**Linux e macOS:**

```bash
.venv/bin/python gerar_demo.py
```

O script só cria os exemplos se `dados.json` ainda não existir; ele não sobrescreve registros existentes. Os exemplos são gerados para o mês atual e o anterior.

### Começar com seus próprios dados

Se você estiver usando os exemplos, faça um backup, pare o servidor e substitua o conteúdo de `dados.json` por:

```json
{
  "transacoes": [],
  "metas": [],
  "orcamentos": {},
  "planos": {}
}
```

Depois, inicie o servidor novamente e cadastre suas movimentações na tela **Transações**.

## Testes

Os testes utilizam um arquivo temporário e não alteram seus registros pessoais.

**Windows:**

```powershell
.venv\Scripts\python.exe testes.py
```

**Linux e macOS:**

```bash
.venv/bin/python testes.py
```

A cobertura inclui cadastro, edição, exclusão, persistência, filtros, comparações, metas, orçamentos, planejamento e validações. Também são verificados casos como ausência de receitas, saldo negativo, divisão de centavos e mudança de ano.

## Critérios dos cálculos

- **Saldo do mês:** receitas menos todas as saídas registradas no mês.
- **Economia disponível:** sobra positiva após as saídas; não representa uma transferência automática para uma reserva.
- **Renda comprometida:** proporção das saídas em relação às receitas. Sem receita, o percentual não se aplica.
- **Investimentos realizados:** aportes registrados como saídas, reduzindo o saldo disponível.
- **Valor planejado para investir:** parcela da sobra definida no planejamento, separada dos aportes já realizados.
- **Metas:** o valor já guardado é atualizado manualmente pelo usuário.

A divisão do saldo não cria transações nem atualiza automaticamente as metas. As sugestões de economia usam regras simples em Python, sem IA externa ou recomendação de ativos financeiros.

## Uso e armazenamento

Esta versão foi desenvolvida para **uso pessoal e local**, sem autenticação ou integração bancária. O servidor atende em `127.0.0.1` e deve ser utilizado em um único processo para preservar a consistência das escritas no JSON.

Mantenha cópias de segurança pela tela **Configurações** e não envie dados financeiros pessoais ao GitHub. Para restaurar um backup, pare o servidor e copie o conteúdo do backup para `dados.json`.

Hospedar o código no GitHub não coloca o sistema em funcionamento na internet. Uma versão pública precisaria de autenticação e adaptações de armazenamento e infraestrutura.
