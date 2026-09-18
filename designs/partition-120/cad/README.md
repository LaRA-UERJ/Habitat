# CAD do Biombo 120 (Partition 120)

Geração headless, por script. Leia [docs/cad-workflow.md](../../../docs/cad-workflow.md)
antes de mexer.

## Regenerar

```bash
cd <raiz do repo>
freecadcmd designs/partition-120/cad/biombo_passo1.py      # passo 1: estrutura
freecadcmd designs/partition-120/cad/biombo_passo1b.py     # passo 1b: base decidida
```

Cada um leva ~15 s. Escrevem em `saida/`.

## Arquivos

| Arquivo | O que é |
|---|---|
| `biombo_passo1.py` | Passo 1: só a estrutura de metal. Aprovado; **não editar** |
| `biombo_passo1b.py` | Passo 1b: base decidida (4 rodízios + chapas soldadas). Reaproveita a construção do passo 1 |
| `saida/passo1_*` | Prancha A3, DXF, STEP, CSV e relatório do passo 1 |
| `saida/passo1b_prancha.pdf` | **Prancha A3 do passo 1b** — 3 colunas × 2 linhas: planta, frente, lateral, isométrica 1:25 e detalhe da base 1:2 |
| `saida/passo1b_prancha.dxf` | Mesma folha em mm para CAD. **Só a geometria** — sem carimbo e sem cota |
| `saida/passo1b_biombo.step` | Sólido do passo 1b |
| `saida/passo1b_lista_corte.csv` | Perfil, comprimento, quantidade (tubo + chapas + rodízios) |
| `saida/passo1b_relatorio.json` | Números medidos, varredura de recuo e resultado das verificações |
| `saida/passo1b_biombo.FCStd` | Modelo FreeCAD (regenerável; não versionado) |

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
- **Peso do painel estofado.** Não entra no CG: só tubo e chapas foram pesados. Os painéis
  (passo 2) vão subir o CG e reduzir a margem de 11,62°.

## Próximos passos

1. Passo 2: painel estofado (compensado + espuma + tecido), espessura, fixação no quadro e
   massa — que realimenta o cálculo de tombamento.
2. Passo 3: detalhe da junção (dobradiça a 120°) e detalhe ampliado da chapa com a furação
   confirmada.
3. Conferir o que acontece com o biombo dobrado: a folha central pendurada, o empilhamento
   contra a parede.
