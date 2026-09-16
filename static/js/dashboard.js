const campoMes = iniciarMes();
let sequencia = 0;
async function carregarDashboard() {
  const pedido = ++sequencia;
  if (!campoMes.value) return;
  sessionStorage.setItem('mes',campoMes.value);
  try {
    const d = await api(`/api/dashboard?mes=${campoMes.value}`);
    if (pedido !== sequencia) return; // Não apresenta uma resposta antiga após trocar de mês.
    const cards = [
      ['Saldo do mês',moeda(d.saldo),`Acumulado até o mês: ${moeda(d.saldo_acumulado)}`,''],
      ['Receitas do mês',moeda(d.receitas),'Todas as entradas registradas','positivo'],
      ['Despesas do mês',moeda(d.despesas),'Inclui aportes realizados','negativo'],
      ['Economia disponível',moeda(d.economia),`Taxa de economia: ${porcentagem(d.taxa_economia)}`,'positivo'],
      ['Para investir',moeda(d.investimento_sugerido),'Conforme sua divisão do saldo','positivo'],
      ['Renda comprometida',porcentagem(d.comprometida),'Saídas em relação às receitas','']
    ];
    // Manipular o DOM significa atualizar os elementos da página com a resposta.
    document.querySelector('#cards').innerHTML = cards.map(([nome,valor,nota,classe]) => `<article class="card"><span>${nome}</span><strong class="${classe}">${valor}</strong><small>${nota}</small></article>`).join('');
    grafico('balanco','bar',['Receitas','Despesas','Saldo'],[{label:'Mês selecionado',data:[d.receitas,d.despesas,d.saldo],backgroundColor:['#168364','#c86a72','#a5cdbb']}]);
    grafico('categorias','doughnut',Object.keys(d.categorias),[{data:Object.values(d.categorias)}]);
    document.querySelector('#categorias-texto').textContent = Object.entries(d.categorias).map(([c,v])=>`${c}: ${moeda(v)}`).join(' · ') || 'Nenhuma despesa neste mês.';
    grafico('evolucao','line',d.evolucao.map(m=>new Date(m.mes+'-01T12:00:00').toLocaleDateString('pt-BR',{month:'short'})),[
      {label:'Receitas',data:d.evolucao.map(m=>m.receitas)},
      {label:'Despesas',data:d.evolucao.map(m=>m.despesas),borderColor:'#c86a72',backgroundColor:'#c86a72'}]);
    grafico('distribuicao','doughnut',Object.keys(d.distribuicao),[{data:Object.values(d.distribuicao)}]);
    document.querySelector('#distribuicao-nota').textContent = d.deficit>0 ? `Há um déficit de ${moeda(d.deficit)}. As saídas superam a renda; o gráfico mostra a composição das saídas.` : 'A sobra é o que ficou após todas as saídas. Investimentos aqui são aportes já registrados.';
    document.querySelector('#analises').innerHTML = d.analises.map(a=>`<li>${escapar(a)}</li>`).join('');
    document.querySelector('#sugestoes').innerHTML = d.sugestoes.map(s=>`<div class="sugestao"><div class="entre"><b>${escapar(s.categoria)}</b><span>${moeda(s.gasto)}</span></div><p>Reduzindo ${s.percentual}%, você poderia economizar <strong>${moeda(s.economia)} por mês.</strong></p></div>`).join('') || '<p class="vazio">Cadastre despesas para receber sugestões.</p>';
    renderOrcamentos(d.orcamentos);
  } catch(erro) { aviso(erro.message,true); }
}
campoMes.addEventListener('change',carregarDashboard);
carregarDashboard();
