# CAD do Biombo 120 (Partition 120)

Geração headless, por script. Leia [docs/cad-workflow.md](../../../docs/cad-workflow.md)
antes de mexer.

## Regenerar

```bash
cd <raiz do repo>
freecadcmd designs/partition-120/cad/biombo_passo1.py      # passo 1: estrutura
freecadcmd designs/partition-120/cad/biombo_passo1b.py     # passo 1b: base decidida
freecadcmd designs/partition-120/cad/biombo_passo2.py      # passo 2: placa e fixacao

# render 3D em PNG (FreeCAD GUI num X virtual: nao abre janela na sua tela)
RENDER_FCSTD=$PWD/designs/partition-120/cad/saida/passo1b_biombo.FCStd \
RENDER_NOME=passo1b_render \
  xvfb-run -a freecad $PWD/scripts/render_3d.py

# passo 2: o close e' em UMA fixacao (aba + parafuso + cabeca), nao no rodizio
RENDER_FCSTD=$PWD/designs/partition-120/cad/saida/passo2_biombo.FCStd \
RENDER_NOME=passo2_render RENDER_CLOSE=folha1_a_aba \
  xvfb-run -a freecad $PWD/scripts/render_3d.py

# auditoria da prancha: vista sem tinta, tinta fora da moldura, texto sobreposto
python3 scripts/auditar_prancha.py --relatorio \
  designs/partition-120/cad/saida/passo2_relatorio.json
```

O passo 1 leva ~15 s, o 1b ~30 s (inclui a varredura de recuo), o 2 ~10 s e o render ~5 s.
Escrevem em `saida/`.

## Arquivos

| Arquivo | O que é |
|---|---|
| `biombo_passo1.py` | Passo 1: só a estrutura de metal. Aprovado; **não editar** |
| `biombo_passo1b.py` | Passo 1b: base decidida (4 rodízios + chapas soldadas). Reaproveita a construção do passo 1 |
| `saida/passo1_*` | Prancha A3 (PDF), lista de corte (CSV) e relatório do passo 1. O DXF e o STEP são gerados mas **não versionados** |
| `saida/passo1b_prancha.pdf` | **Prancha A3 do passo 1b** — 3 colunas × 2 linhas: planta, frente, lateral, isométrica 1:25 e detalhe da base 1:2 |
| `saida/passo1b_prancha.dxf` | Mesma folha em mm para CAD — **não versionado**: regenere com o script |
| `saida/passo1b_biombo.step` | Sólido do passo 1b — **não versionado**: regenere com o script |
| `saida/passo1b_lista_corte.csv` | Perfil, comprimento, quantidade (tubo + chapas + rodízios) |
| `saida/passo1b_relatorio.json` | Números medidos, varredura de recuo e resultado das verificações |
| `saida/passo1b_render_iso.png` | Render 3D isométrico (1920×1200) |
| `saida/passo1b_render_persp.png` | Render 3D em perspectiva (1920×1200) |
| `saida/passo1b_render_close.png` | Render 3D do close na base (1600×1200) |
| `saida/passo1b_render.txt` | Log do render (o `print` do script não sai no stdout nesse modo) |
| `saida/passo1b_biombo.FCStd` | Modelo FreeCAD (regenerável; não versionado) |
| `saida/passo2_prancha.pdf` | **Prancha A3 do passo 2** — duas faixas: as 4 vistas em cima; embaixo a placa decorada 1:20, a lista de material e as notas de fixação e montagem |
| `saida/passo2_prancha.dxf` | Mesma folha em mm para CAD — **não versionado** |
| `saida/passo2_biombo.step` | Sólido do passo 2 (67 peças) — **não versionado** |
| `saida/passo2_lista_corte.csv` | Tubo, chapa do rodízio, cantoneiras e placa |
| `saida/passo2_lista_compras.csv` | Compensado, parafusos e o acabamento opcional |
| `saida/passo2_relatorio.json` | Números medidos, verificações e o resultado da auditoria da prancha |
| `saida/passo2_render_iso.png`, `passo2_render_persp.png` | Renders 3D do conjunto montado (1920×1200) |
| `saida/passo2_render_close.png` | Render 3D do close em uma fixação (1600×1200) |
| `saida/passo2_biombo.FCStd` | Modelo FreeCAD do passo 2 (regenerável; não versionado) |

## Parâmetros do passo 1 (estrutura) — aprovado

Origem de cada número: `[B]` = veio do brief, `[P]` = proposta do agente.

| Parâmetro | Valor | Origem |
|---|---|---|
| Folha (largura × altura) | 900 × 1600 mm | [B] faixa 80–100 cm / total 150–180 cm |
| Perfil | metalon quadrado 30×30×1,5 mm | [B] "sweet spot" |
| Giro por junta | 60° → 120° internos | [B] núcleo do projeto |
| Travessa | 840 mm entre as faces internas dos montantes | [P] |

## Parâmetros do passo 1b (base decidida)

| Parâmetro | Valor | Origem |
|---|---|---|
| Rodízio | moveleiro Ø75 (3") com freio de ação total, roda de borracha, **altura total 102 mm**, placa 91,5 × 60 mm, carga 70 kg/un | [comercial] Leroy Merlin 1567099890 / IPC Comercial |
| Quantidade | **4 rodízios**: 2 na folha 1 e 2 na folha 3. A folha central fica pendurada nas juntas | [P] decisão do usuário |
| Cadeia de alturas | 102 (rodízio) + 4 (chapa) = **106 mm** até a base do quadro; topo em **1706 mm** | [P] medido do produto |
| Recuo do rodízio | 100 mm da ponta da folha, **dentro do plano da folha** | [P] ver varredura abaixo |
| Chapa soldada | 100 × 70 × 4 mm sob o pé do montante (na prática solda sob a travessa inferior), 4 rasgos oblongos 25 × 9 mm, passo 70 × 40 mm | [P] **passo dos furos a conferir** |

O pé em L de 150 mm chegou a ser projetado e foi **descartado**: perna no chão é risco de
tropeço no laboratório.

## Varredura do recuo (medida, não calculada)

Cada linha foi obtida construindo os sólidos dos rodízios e os montantes vizinhos e medindo
com `distToShape`. "Folga ao montante" é a menor distância entre qualquer peça do rodízio
(chapa, garfo, placa, roda) e o montante da folha vizinha, que é o que limita a aproximação.

| Recuo | Folga ao montante vizinho | Margem de tombamento | Tomba a |
|---|---|---|---|
| 80 mm | 0,0 mm (colide) | 197,2 mm | 12,70° |
| 90 mm | 4,5 mm | 188,6 mm | 12,16° |
| **100 mm** | **14,5 mm** | **179,9 mm** | **11,62°** |
| 110 mm | 24,5 mm | 171,3 mm | 11,07° |
| 120 mm | 34,5 mm | 162,6 mm | 10,53° |

Ficou em 100 mm: é o primeiro recuo com folga confortável ao montante vizinho. Aproximar mais
ganha pouca margem de tombamento (12,70° no limite, e colidindo) e encolher a folha de corte.

## Medições do passo 1b (saída do relatório JSON)

| Grandeza | Valor |
|---|---|
| Envoltória do conjunto | x 0,0…1357,5 · y −35,0…1560,9 · z 0…1706 mm |
| Tubo total | 14,64 m (igual ao passo 1) |
| Massa do tubo (seção vazada × comprimento) | 19,65 kg |
| Chapas soldadas | 4 × 100×70×4 → 0,88 kg |
| Massa fabricada (tubo + chapas) | 19,89 kg |
| Rodízios | 4 × Ø75, todos com Zmin = 0,000 mm (tocando o chão) |
| Folga mínima entre peças da base | 600,0 mm (`folha1_a_chapa` × `folha1_b_chapa`) |
| Interferência máxima entre peças de folhas diferentes | 0,000 mm³ |
| Folga mínima entre rodas | 625,0 mm |
| CG das peças fabricadas | (889,7 · 515,3 · 875,1) mm |
| CG dentro do polígono de apoio | sim |
| Margem de tombamento | 179,9 mm → tomba a **11,62°** |

Comparação de estabilidade medida no mesmo modelo: 6 rodízios recuados 100 mm → 16,7°;
4 rodízios (atual) → 11,62°; com o pé em L (descartado) → 24,24°.

A chapa soldada encosta na travessa inferior em todas as quatro posições (distância 0,000 mm),
e a 20 mm do montante — é sob a travessa que ela solda, não sob o montante.

## Parâmetros do passo 2 (placa de compensado decorado) — aprovado

Origem: `[U]` = decisão do usuário em 2026-09-18, `[P]` = proposta do agente derivada da
geometria e medida no sólido.

| Parâmetro | Valor | Origem |
|---|---|---|
| Painel | compensado decorado 15 mm, **834 × 1534 mm** | [U] placa de 15 mm; o recorte vem do vão de 840 × 1540 |
| Folga ao tubo | 3,0 mm em todo o contorno | [P] é o vão ocupado pela perna A da cantoneira |
| Posição | centrado na profundidade do tubo: −7,5 a +7,5 mm do plano médio da folha | [P] |
| Altura do painel | 139 a 1673 mm (Z0+33 até Z1−33) | [P] medido no modelo |
| Cantoneira | chapa dobrada em L, 25 × 25 × 3 mm, altura 25 mm | [U] |
| Cantoneira — perna A | 22,5 × 25 mm, soldada **de face** na face interna do montante | [U] |
| Cantoneira — perna B | 25 × 25 mm, deitada **sobre** a face do compensado | [U] |
| Cantoneira — quantidade | 4 por folha, 12 no total, em Z0+200 (306 mm) e Z0+1340 (1446 mm) | [P] |
| Furo da aba | Ø4,2 mm, a 15 mm da face interna do montante | [P] |
| Parafuso | madeira Ø4 × 16 mm, cabeça panela Ø8 mm, furo piloto Ø2,5 mm, 12 unidades | [P] |
| Acabamento (espuma + tecido) | **em aberto, e não modelado** | [U] em 2026-09-18: a prancha mostra só a placa decorada |
| Acabamento, se houver | espuma 3 mm + tecido <1 mm por face | [U] desloca a cantoneira 4 mm e pede parafuso Ø4 × 20 |

### Fixação: cantoneira em L, e por que assim

O parafuso de madeira só é acionável na direção da normal do painel — é a única em que a chave
chega ao vão entre o tubo e a placa. Logo a peça soldada tem de apresentar uma face
perpendicular a essa normal sobre a placa, e é isso que a perna B faz.

- soldar **de face** (perna A encostada na face interna do montante) dá 22,5 × 25 mm de contato
  na parede do tubo, e o gabarito de solda vira só encostar a perna A na face interna;
- a perna A tem 3 mm de espessura e é ela que define a folga de 3 mm entre a placa e o tubo: a
  placa apoia na perna A e o parafuso aperta contra ela. Não mude uma coisa sem mudar a outra;
- a cabeça Ø8 fica entre 10,5 e 12,1 mm do plano médio — abaixo da face do tubo (15 mm) e fora
  da pegada do estofamento, que começa a 30 mm da borda: não briga com o acabamento;
- o parafuso de 16 mm são 3 mm na perna B + 13 mm na placa, com 2 mm de fundo. Não atravessa.

### Ordem de fabricação (está na prancha)

1. Soldar as 4 cantoneiras de cada folha no gabarito, nas alturas Z0+200 e Z0+1340, centradas na
   profundidade do tubo.
2. Parafusar a placa **nua** nas cantoneiras: 4 parafusos Ø4 × 16 por folha, furo piloto Ø2,5
   feito pelo furo da aba.
3. Se houver acabamento: colar a espuma nas duas faces e grampear o tecido na borda de 20 mm da placa.
4. Com acabamento, a cantoneira solda com o painel já estofado e o parafuso passa a Ø4 × 20.

Depois do passo 2 não há mais acesso aos parafusos: é a ordem acima ou nada.

## Medições do passo 2 (saída do relatório JSON)

| Grandeza | Valor |
|---|---|
| Peças do conjunto | 67 (28 do quadro e da base + 3 placas + 12 cantoneiras + 24 parafuso e cabeça) |
| Massa fabricada | **55,32 kg** = tubo 19,652 + placa 34,543 + chapas 0,766 + cantoneiras 0,332 + parafusos 0,026 |
| Massa do painel por folha | 11,51 kg |
| Carga por rodízio | 13,8 kg (limite 70 kg/un) |
| CG do conjunto | (898,4 · 520,5 · 894,7) mm |
| Margem de tombamento | **175,0 mm → tomba a 11,07°** (passo 1b: 179,9 mm / 11,62°) |
| Sensibilidade do compensado | 550 kg/m³ → 52,44 kg / 11,08°; 600 → 55,32 kg / 11,07°; 650 → 58,20 kg / 11,06° |
| Espessura do painel | 15,0 mm (só a placa: o acabamento não entra no modelo) |
| Folga da placa aos tubos | 3,0 mm, a mínima, nos 4 tubos de cada folha |
| Contato das cantoneiras | 0,000 mm nas 12, nas duas pernas (perna A no montante, perna B na placa) |
| Volume da cantoneira | 3.520,9 mm³ por peça, medido; o nominal 3.337,5 do primeiro rascunho estava errado (descontava o canto do L duas vezes) |
| Parafuso dentro da placa | 163,363 mm³ por par — 13 mm de rosca, por projeto |
| Interferência entre montantes vizinhos | 207.846,097 mm³ em cada uma das duas juntas — **herdada do passo 1b**: é o canto do encontro a 120°. O detalhe da junta é o passo 3 |
| Altura total | 1706 mm; o painel para em 1673 mm, dentro do quadro |
| Área útil da prancha ocupada | 17,9 % |
| Auditoria da prancha | 47 textos, nenhum sobreposto, nenhum fora da moldura; nenhuma vista sem tinta |

## Vistas da prancha

`Frente` é a vista perpendicular à **folha central** (a placa do meio), do lado côncavo — a
vista simétrica do biombo. `Lateral` é a paralela às **folhas das pontas**. Isso está invertido
em relação ao passo 1, onde a "frente" era a vista paralela às folhas das pontas.

| Vista | Direction | XDirection | Extensão medida |
|---|---|---|---|
| Frente (folha central de frente) | (−0,866 · 0,500 · 0) | (−0,500 · −0,866 · 0) | 1826 × 1706 mm |
| Lateral (paralela às folhas das pontas) | (0 · −1 · 0) | (1 · 0 · 0) | 1357,5 × 1706 mm |
| Planta (de cima, mesma direita da frente) | (0 · 0 · −1) | (−0,500 · −0,866 · 0) | 1826 × 807,4 mm |
| Isométrica 1:25 | (1 · −1 · 1) | (1 · 1 · 0) | 1770 × 2001 mm |
| Detalhe da base 1:2 | (0 · 0 · −1) | (1 · 0 · 0) | 150 × 70 mm |

A vista oblíqua é o caso que exige `centrar_no_conteudo=True` no `Projetor.vista` — sem isso
as cotas ancoradas em ponto do modelo caem fora da caixa da vista. Ver
[docs/cad-workflow.md](../../../docs/cad-workflow.md).

Folha A3 em grade de 3 colunas (`x` = 38 / 165 / 292 mm) por 2 linhas (`y` = 172 / 48 mm), com
o carimbo no canto inferior direito. Área útil ocupada pelas vistas: 23,5 % (a folga entre
colunas é o que as cotas verticais usam).

### Folha do passo 2

Duas faixas, separadas por uma linha horizontal imaginária no meio da folha. Em cima, as quatro
vistas na escala do 1b: `Iso` (1:25), `Frente` (1:25, perpendicular à folha central), `Lateral`
(1:25) e `Topo` (1:25, a que mostra o ângulo de 120°). Embaixo, três blocos: `Compensado`
(1:20 — a placa de 834 × 1534 cotada, com a posição dos 4 furos de parafuso), a lista de
material e as notas de fixação e montagem. Carimbo no canto inferior direito:
`BIOMBO 120 - PASSO 2: PLACA DE COMPENSADO DECORADO`.

## Correção de um número errado do passo 1

A primeira versão deste arquivo dizia que, nas pontas, "os rodízios de folhas vizinhas caem a
26 mm um do outro e a roda tem 75 mm — colidem". Medido nos sólidos do passo 1:

| Par | Distância |
|---|---|
| centros das rodas | 173,2 mm |
| roda × roda | 92,3 mm |
| garfo × garfo | 115,4 mm |
| placa × placa | 60,3 mm |
| **placa × montante da folha vizinha** | **19,5 mm** ← é este que limita |

Nada colide: o que limita a aproximação é a chapa do rodízio contra o montante da folha
vizinha.

## Decisões fechadas no passo 1b

- **Rodízio comercial.** Linha moveleira Ø75 com freio, altura 102 mm, carga 70 kg/un. A linha
  industrial (Schioppa 3", 200 kg, R$ 149,95) foi descartada: altura de 154 mm e roda de ferro
  fundido, que o anúncio diz não servir para piso sensível nem para baixo ruído.
- **Quantidade e posição.** 4 rodízios, 2 por folha, só nas folhas das pontas, recuados
  100 mm dentro do plano da folha. Sem pé em L.
- **Chapa de base.** 100 × 70 × 4 mm soldada sob a travessa inferior, com 4 rasgos oblongos.

## Pendências

- **Furação da chapa.** Nenhuma fonte consultada publica o passo entre os 4 furos da placa do
  rodízio (a Leroy dá altura 102, banda 32, cubo 40, raio de giro 65, carga 70; a IPC dá a
  placa 60 × 91,5 "4 furos oblongos"). O desenho usa rasgo oblongo 25 × 9 com passo 70 × 40,
  que tolera variação entre modelos, e a prancha diz **CONFERIR com o rodízio comprado**.
- **Folha central sem apoio.** Com 4 rodízios, a folha 2 fica pendurada nas duas juntas e o pé
  dela permanece 106 mm acima do chão. Ao mover ou dobrar o biombo, o peso dela (≈6,5 kg de
  estrutura, mais o painel) passa pelas dobradiças — o passo 3 precisa confirmar que a
  dobradiça aguenta e que não há folga que deixe a folha central raspar o piso.
- **Peso do painel.** Resolvido no passo 2: 11,51 kg por folha, medidos, derrubaram a margem de
  179,9 mm (11,62°) para 175,0 mm (11,07°). O acabamento (espuma + tecido) não está modelado:
  se existir, o CG sobe um pouco mais.
- **Acabamento do painel em aberto.** Qual espuma, qual tecido, e se existem. O modelo trata
  como opcional (3 + 1 mm por face) e não desenha. A decisão muda a cantoneira (4 mm de
  deslocamento para fora) e o parafuso (passa a Ø4 × 20).
- **Interferência na junta.** Os montantes vizinhos se sobrepõem 207.846 mm³ (207,8 cm³) no
  encontro a 120°, nas duas juntas — geometria herdada do passo 1b. O corte das pontas e a
  dobradiça são o passo 3.

## Próximos passos

1. Acabamento do painel: decidir espuma e tecido, ou decidir não fazer. Se fizer, a cantoneira
   desloca 4 mm para fora e o parafuso vira Ø4 × 20 — só essa parte do passo 2 precisa ser
   refeita.
2. Passo 3: dobradiça no encontro a 120°, onde os montantes vizinhos hoje se sobrepõem
   207,8 cm³, e detalhe ampliado da chapa com a furação confirmada contra o rodízio comprado.
3. Conferir o que acontece com o biombo dobrado: a folha central pendurada (o painel dela, de
   11,51 kg, pende só das juntas), o empilhamento contra a parede.
