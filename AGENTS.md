# AGENTS.md

Instruções para agentes de IA trabalhando neste repositório.
Se você é humano, leia o [README.md](README.md) — este arquivo é sobre *como trabalhar aqui*.

---

## O que é este repositório

Projeto **Habitat** / LaRA-UERJ: mobiliário e infraestrutura de laboratório em hardware
aberto, para o lab de 7×7 m do LaRA. Cinco módulos, todos ainda em projeto.

- Hardware: licença **CERN-OHL-S v2** ([LICENSE](LICENSE))
- Texto e documentação: **CC BY-SA 4.0**
- Idioma: o repositório é bilíngue e herdado — os briefs em `designs/` estão em inglês,
  boa parte de `docs/` também. **Siga o idioma do arquivo que você está editando**; não
  traduza em massa. Documentação operacional nova (este arquivo, `docs/cad-workflow.md`)
  fica em português.

## Onde está cada coisa

| Caminho | O que tem |
|---|---|
| `designs/<modulo>/README.md` | Brief: requisitos, opções em avaliação, dimensões, questões abertas |
| `designs/<modulo>/cad/` | Script de CAD do módulo + `saida/` com os artefatos |
| `designs/<modulo>/assets/` | Referências visuais e renders |
| `docs/` | Conceitos, princípios de projeto, ergonomia, layout, referências |
| `docs/cad-workflow.md` | **Leia antes de mexer em CAD.** Pipeline headless e pitfalls |
| `scripts/cad_lib.py` | Biblioteca de desenho (projeção TechDraw + folha reportlab) |

## Método de trabalho neste projeto

O usuário conduz **baby steps com checkpoint**. Cada passo termina num artefato que ele
abre e aprova antes de começar o próximo. Há uma exceção à preferência geral dele por
ação direta: neste projeto, planeje primeiro, execute depois.

1. Proponha a tabela de parâmetros e deixe ele validar **antes** de modelar.
2. Modele e gere o artefato.
3. Rode as verificações (abaixo) e reporte os números medidos.
4. **Pare** e diga onde está o arquivo. Não emende no passo seguinte sem o aval dele.
5. Não commite nem faça push sem pedido explícito.

Exemplo de recorte de passos (biombo): passo 1 = só a estrutura de metal. Painéis
estofados, dobradiças e detalhe do rodízio são passos **separados**, nesta ordem.

## CAD: como é feito aqui

FreeCAD 1.1 headless, dirigido por script Python, com a folha em PDF gerada por
reportlab. **Não invente outro caminho** — a escolha está justificada e as armadilhas
já foram pagas. Ver [docs/cad-workflow.md](docs/cad-workflow.md) para o detalhe.

```bash
freecadcmd designs/<modulo>/cad/<script>.py
```

Saída esperada de um passo de CAD, em `designs/<modulo>/cad/saida/`:

- `<passo>_prancha.pdf` — A3, 1º diedro, escalado, cotado, com carimbo e lista de corte
- `<passo>_prancha.dxf` — mesma folha, em mm, para quem tiver CAD
- `<passo>_<peca>.step` — sólido, para troca com CAD
- `<passo>_lista_corte.csv` — perfil, comprimento, quantidade
- `<passo>_relatorio.json` — números medidos e resultado das verificações

## Regras duras

Cada uma destas custou tempo e um desenho errado na mão do usuário.
O detalhe técnico está em [docs/cad-workflow.md](docs/cad-workflow.md).

1. **Verifique medindo o modelo construído, nunca com uma fórmula re-derivada.**
   Uma checagem que recalculava a fórmula correta *passou* enquanto o código de
   construção tinha o sinal trocado, e o desenho saiu com metade dos rodízios fora da
   peça. Use `Shape.distToShape` nos sólidos reais.

2. **Em laço que varre as duas pontas de um elemento, o deslocamento inverte de sinal
   na segunda ponta.** Errar não dá exceção: dá uma peça 30 mm fora do lugar e um vão
   invisível. Se o `bbox` do conjunto saiu maior que o nominal, suspeite disso primeiro.

3. **Você não enxerga imagem.** Audite o desenho por densidade de tinta
   (`pdftoppm` + PIL) e rasterize o modelo em ASCII varrendo o sólido. As duas técnicas
   estão descritas em `docs/cad-workflow.md`. Vista em branco e cota dentro do desenho
   aparecem nesses dois testes.

4. **Massa de tubo é seção vazada × comprimento**, não volume do sólido. Modelar metalon
   como caixa cheia superestima a massa em ~5×.

5. **Toda verificação numérica que você afirmar tem que sair do artefato gerado**, e o
   número vai no relatório. "Deve estar certo" não vale.

6. **Nunca aceite o relatório de um subagente como prova.** Exija caminho absoluto do
   artefato e os números medidos; confira você mesmo antes de repassar ao usuário.

## Estado dos módulos

Atualize esta tabela quando fechar um passo.

| Módulo | O que existe | Próximo passo |
|---|---|---|
| [partition-120](designs/partition-120/) (biombo) | CAD passo 1 (estrutura) e passo 1b (base decidida: 4 rodízios Ø75/102 mm nas folhas das pontas, chapa soldada 100×70×4). Pranchas A3, DXF, STEP, listas de corte, relatórios | Passo 2: painel estofado (compensado + espuma + tecido), fixação e massa; depois dobradiça |
| [soldering-bench](designs/soldering-bench/) | Brief + render | Tabela de parâmetros |
| [workstation-120](designs/workstation-120/) | Brief + render | Tabela de parâmetros |
| [focus-pod](designs/focus-pod/) | Brief + render | Tabela de parâmetros |
| [break-pod](designs/break-pod/) | Brief + render | Tabela de parâmetros |

## Delegar para subagente

O usuário prefere que trabalho longo vá para subagente, para não estourar a sessão
principal. Delegue quando a tarefa for **executável a partir de uma especificação
escrita** — é por isso que `docs/cad-workflow.md` existe.

Delegue:
- "Monte o CAD do módulo X do passo 1 seguindo docs/cad-workflow.md. Parâmetros: <tabela
  fechada>. Entregue PDF/DXF/STEP/CSV em designs/X/cad/saida/ e reporte os números
  medidos pelo relatório JSON."

Não delegue:
- Fechar parâmetros de projeto (decisão de engenharia, é do usuário com você).
- Redação deste arquivo ou de docs que dependem do contexto da conversa.
- Qualquer coisa que exija pergunta ao usuário — subagente não pergunta.

Ao receber o resultado do filho: exija caminho absoluto e uma medida verificável,
abra o arquivo e confira. Um filho já devolveu tabela de números bonita e nenhum
arquivo no disco.

## Convenções

- Não commit nem push sem pedido explícito.
- Sem emoji em arquivo do repositório.
- Números sempre com unidade e sempre que possível lidos do artefato, não digitados.
- Ao mudar um parâmetro de projeto, atualize a seção "Dimensions" do README do módulo
  e a tabela de estado acima.
- Se um documento de referência (`docs/*.md`) citar um valor que você mudou, atualize.
