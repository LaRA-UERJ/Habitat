# Pipeline de CAD: FreeCAD headless + reportlab

Como este repositório produz prancha cotada para serralheiro, por código, sem GUI.
Implementação de referência: [`scripts/cad_lib.py`](../scripts/cad_lib.py) e
[`designs/partition-120/cad/biombo_passo1.py`](../designs/partition-120/cad/biombo_passo1.py).

```bash
freecadcmd designs/<modulo>/cad/<script>.py
```

---

## Por que FreeCAD e não OpenSCAD

1. **OpenSCAD não exporta STEP nem IGES** (só STL/DXF/SVG). Sem STEP não há troca com
   quem tem CAD — e é o formato que o mundo metal-mecânico usa.
2. `projection()` do OpenSCAD devolve silhueta achatada, sem aresta oculta. O serralheiro
   lê aresta para saber onde solda; o TechDraw faz HLR do sólido real.
3. Cota no FreeCAD sai do modelo. No OpenSCAD você desenha cada cota como geometria 2D.

OpenSCAD só ganha para DXF de peça plana (chapa ou painel cortado a laser/plasma). Se
precisar, use, mas não troque a cadeia principal.

## Visão geral do fluxo

```
tabela de parâmetros (mm)
  -> sólidos FreeCAD (Part.makeBox / makeCylinder / barra orientada)
  -> projeção TechDraw com HLR (visible + hidden)
  -> segmentos 2D e projectPoint
  -> folha A3 em reportlab, em mm reais, com cotas desenhadas à mão
  -> PDF carimbado + DXF + STEP + CSV + relatório JSON
  -> verificações automáticas
```

## API da biblioteca

`scripts/cad_lib.py` expõe:

```python
doc = cl.novo_doc("Nome")
pecas = [cl.caixa(doc, nome, base_xyz, L, W, H),
         cl.barra(doc, nome, p1_xyz, p2_xyz, sec),            # seção centrada no eixo
         cl.caixa_orientada(doc, nome, centro_xy, ang_deg, L, W, H, z_base),
         cl.cilindro(doc, nome, centro_xyz, ang_deg, dia, comp)]   # eixo horizontal
doc.recompute()
med = cl.medir(pecas)          # min/max/centro/volume

prj = cl.Projetor(doc, template="A3")
v = prj.vista(nome, pecas, *cl.DIRECOES["Frente"], med["centro"])
# v -> vis, hid, w, h, loc (bbox local), pp0, alertas

f = cl.Folha("saida/prancha.pdf", "A3")
f.moldura()
f.poe(v, x_mm, y_mm, escala)
f.desenha(); f.rotulo_vista("Frente")
f.cota_h("Frente", pa_xyz, pb_xyz, off_mm, "1440 total")
f.cota_v("Frente", pa_xyz, pb_xyz, -9.0, "100 rodizio")     # off negativo = à direita
f.anotacao("Planta", x, y, z, "120 graus")
f.lista_corte("LISTA DE CORTE", "cabecalho", linhas, x, y)
f.carimbo([(texto, tamanho, negrito), ...])
problemas = f.salva()          # [] = ok
```

`cl.DIRECOES` traz Frente/Planta/Lateral/Posterior/Iso já na convenção de 1º diedro.

---

## Pitfalls do FreeCAD 1.1 headless

Todos verificados na prática. Nenhum deles dá erro útil — dão desenho errado silencioso.

### O que existe e o que não existe

```
Existe:     writeDXFPage, writeDXFView, projectToDXF, projectToSVG, exportSVGEdges,
            DrawViewDimension, v.projectPoint(), v.getVisibleEdges(), v.getHiddenEdges()
Não existe: writePageAsPdf  ->  o PDF tem que sair do reportlab
Não existe: v.ShowHiddenLines  ->  quem manda é v.HardHidden (padrão False)
```

`projectToDXF`, `projectToSVG`, `exportSVGEdges` e `viewPartAsDxf` **não** recebem a
vista nem a página — recebem `Part.Shape`, ou um argumento só. A assinatura não bate com
o nome. Use `writeDXFPage(page, arquivo)`.

### XDirection é obrigatório e tem que ser perpendicular

Se `XDirection` não for perpendicular a `Direction`, a vista falha com
`failed to create projection CS` e sai vazia (o aviso aparece uma vez por recompute).

```
direita = XDirection normalizado
cima    = Direction x XDirection
```

`Direction` é o vetor do **objeto para o observador**. Conjunto de 1º diedro (ABNT):

| Vista | Direction | XDirection | Resultado |
|---|---|---|---|
| Frente | (0,-1,0) | (1,0,0) | direita=+X, cima=+Z |
| Planta | (0,0,-1) | (1,0,0) | direita=+X, cima=-Y (fica abaixo) |
| Lateral | (1,0,0) | (0,1,0) | direita=+Y, cima=+Z (fica à direita) |

Os dois `-1` são o que produz 1º diedro. Trocar o sinal espelha ou inverte a vista **sem
nenhum erro**. Audite sempre:

```python
pp0 = v.projectPoint(centro_do_bbox_do_modelo)
sig = {k: (round((v.projectPoint(Vector(*p)).x - pp0.x)/100),
           round((v.projectPoint(Vector(*p)).y - pp0.y)/100))
       for k, p in (("x",(100,0,0)), ("y",(0,100,0)), ("z",(0,0,100)))}
# Frente  x:(1,0)  y:(0,0)   z:(0,1)
# Planta  x:(1,0)  y:(0,-1)  z:(0,0)
# Lateral x:(0,0)  y:(1,0)   z:(0,1)
```

### Dois referenciais de coordenada

- `getVisibleEdges()` / `getHiddenEdges()` devolvem 2D **centrado no conteúdo** da vista
  (bbox simétrico em torno de 0), em mm reais — `Scale` não afeta.
- `v.projectPoint(p)` devolve **absoluto** `(p·direita, p·cima)`, sem centrar.

Para desenhar misturando os dois, use o offset `pp0` (já embutido em `Folha.para_folha`):

```
folha_x = X0 + (local_x - local_xmin) * escala                     # dos edges
folha_x = X0 + (pp(p).x - pp0.x - local_xmin) * escala             # do projectPoint
```

**Vista oblíqua precisa de `centrar_no_conteudo=True`.** A conversão acima pressupõe que o
centro do conteúdo projetado seja a projeção do centro do bbox 3D do modelo. Isso vale para
vista alinhada aos eixos (frente/planta/lateral padrão); numa vista perpendicular a uma folha
a 60°, não vale — o conteúdo fica descentrado em relação à projeção do bbox e **toda cota
ancorada em ponto do modelo cai fora da caixa da vista** (o `verificar()` acusa, mas depois de
você já ter desenhado tudo). Passe o parâmetro:

```python
VS["Frente"] = prj.vista("Frente", pecas, direction, xdirection, med["centro"],
                         centrar_no_conteudo=True)
```

Aí o `pp0` é medido amostrando vértices e arestas curvas do modelo, e `para_folha` volta a
fechar. Sem o parâmetro, o comportamento antigo é preservado (é o que mantém o passo 1 do
biombo reproduzível byte a byte).

A vista também é **centrada no próprio conteúdo** na página. Posicionar por canto erra;
ancore sempre pelo bbox do conteúdo.

### Arestas ocultas: ligar explicitamente

```python
v.HardHidden = True      # arestas de sólido
v.SmoothHidden = True    # tangência de cilindro (rodízio, tubo redondo)
v.SeamHidden = False     # costura do cilindro: linha suja, deixe desligada
```

Sem isso `getHiddenEdges()` volta `[]` e você conclui que não há nada escondido.

### writeDXFPage ignora mudanças recentes

Na **mesma sessão**, depois de setar `v.Scale` / `v.X` / `v.Y`, `writeDXFPage` exporta a
geometria em escala 1. Testados e inúteis: `doc.recompute()`, `v.touch()`,
`pg.recompute()`, ler `v.getVisibleEdges()`. **Só resolve salvar e reabrir:**

```python
doc.saveAs(fcstd); App.closeDocument(doc.Name)
doc2 = App.openDocument(fcstd)
pg2 = [o for o in doc2.Objects if o.TypeId == "TechDraw::DrawPage"][0]
TechDraw.writeDXFPage(pg2, dxf)
```

`writeDXFPage` exporta **só as vistas**. Moldura, carimbo e as cotas que você desenhou no
reportlab não vão para o DXF. Se o DXF precisar carregar cota, crie objetos
`TechDraw::DrawViewDimension` (saem como entidade DIMENSION). Confira `$INSUNITS` = 4 (mm).

### Outros

- `Part.cut()` (furo ou rasgo em chapa) devolve **`Compound`**, e Compound não tem
  `CenterOfMass` nem `Volume` útil — o erro é `'Part.Compound' object has no attribute
  'CenterOfMass'`. Passe `shp.removeSplitter()` e, se continuar Compound com um sólido só,
  `shp.Solids[0]`, antes de medir ou de gravar o sólido.
- O FreeCAD **1.1.3** grava um `<nome>.FCBak` ao lado do `.FCStd` (já coberto pelo
  `.gitignore`).
- Conferido nas duas versões: com 1.1.1 e com 1.1.3 o mesmo script gera prancha, DXF e STEP
  byte a byte idênticos. Os pitfalls desta página valem nas duas.
- `v.Scale` tem que ser setado **depois** de `page.addView` + `recompute`, senão volta a 1.
- Texto: use `drawString`/`drawCentredString` do reportlab em mm; `Draft.makeText` não
  tem `Shape` no headless e não vai para o DXF.
- Template do TechDraw: caminho absoluto em `/usr/share/freecad/Mod/TechDraw/Templates/`.
  `App.getResourceDir()` aponta para `/usr/lib/freecad`, onde não há templates.
- `freecadcmd` ignora argumentos próprios ("unrecognised option"). Parametrize por
  variável de ambiente.
- `Part.makeCylinder(r, h, pnt, dir)`: a base fica em `pnt` e o cilindro cresce ao longo
  de `dir`. Para centrar na origem, `pnt = -h/2` no eixo.

## Folha e cotas

- `canvas.Canvas(arquivo, pagesize=(420*mm, 297*mm))` e trabalhe em mm.
- Escala típica: 1 m de peça cabe em A3 a 1:10 (100 mm). Conjunto de 1,5×1,7 m, 1:20.
  **Calcule escala × folha antes de desenhar** — descobrir overflow no fim é retrabalho.
- Cota horizontal se posiciona relativa à **caixa da vista** (`yd = vista_y - off`), nunca
  relativa ao ponto ancorado. Âncora no topo da vista + linha de cota relativa à âncora
  faz a cota cair **dentro** do desenho.
- Seta cheia de 3×1 mm; linhas de chamada do ponto ao pé da cota; texto de 6,5 pt.
- 1º diedro: planta **abaixo** da frente, lateral **à direita**, arestas próximas
  adjacentes à vista principal.

## Massa

Modelar metalon como caixa cheia superestima o volume em ~5×. Calcule analítico:

```
A = lado^2 - (lado - 2*parede)^2        # 30x30x1,5 -> 171 mm2
massa_kg = A * comprimento_total_mm * 7.85e-3 / 1000
```

## Verificação sem enxergar

O agente não é multimodal. Estas seis checagens substituem o olho, nesta ordem:

1. **Assinatura de eixos** por `projectPoint` (acima) — pega vista espelhada.
2. **Contenção cruzada**: a projeção do bbox do modelo tem de conter o bbox local do
   conteúdo. Vale para isométrica também, onde o bbox do conteúdo não é simétrico.
3. **Grafo de solda do quadro**: cada tubo tem de encostar em ≥ 2 outros; montante de
   quadro retangular em exatamente 2 travessas, e vice-versa.
   ```python
   if a.Shape.distToShape(b.Shape)[0] < 0.001: ...   # encostado
   ```
4. **Peça aparafusada/soldada** (chapa do rodízio): `min(distToShape ao tubo) == 0`.
5. **Interferência**: pares de sólidos de **grupos diferentes** exigem `distToShape > 0`.
6. **Tinta**: rastreie todo ponto desenhado (linhas, setas, texto) e valide contra a
   moldura interna; ancore de cota tem de cair na vista correspondente.

   Cuidado: `Folha.verificar()` registra só o **ponto inicial** de cada texto — um texto que
   comece dentro da folha e transborde a borda passa batido. Para fechar esse buraco,
   rasterize e conte pixels escuros nas bandas fora da moldura (a moldura externa fica em
   10 mm; a banda vai de 0 a 9,5 mm). A ferramenta faz isso e mais:

   ```bash
   python3 scripts/auditar_prancha.py --relatorio designs/<modulo>/cad/saida/<passo>_relatorio.json
   ```

   Ela confere, vista por vista, a densidade de tinta (vista em branco e vista borrada
   reprovam), a tinta do carimbo e as quatro bandas fora da moldura, e sai com código 1 se
   qualquer checagem falhar. Rode sempre depois de gerar uma prancha.

E a auditoria visual:

```bash
pdftoppm -r 150 -png -singlefile prancha.pdf pagina
```

Com PIL, meça a fração de pixels escuros por região: cada caixa de vista precisa ter
tinta, o carimbo precisa ter tinta, e as regiões escolhidas vazias devem dar ~0. Cuidado:
região que encosta na moldura conta a linha da moldura — exclua 2 mm da borda. Um mapa
grosso de densidade (grade 30×20) revela coisa fora de lugar de relance.

### Renderizar o modelo em 3D

O `freecadcmd` não tem GUI nem `saveImage`. Para PNG do modelo, rode o FreeCAD **com GUI
num X virtual** (`xvfb-run`: não abre janela na tela de quem está usando o PC):

```bash
RENDER_FCSTD=$PWD/designs/<modulo>/cad/saida/<passo>_biombo.FCStd \
RENDER_NOME=<passo>_render \
  xvfb-run -a freecad $PWD/scripts/render_3d.py
```

Sai `<passo>_render_iso.png` (axonométrica), `<passo>_render_persp.png` (perspectiva) e
`<passo>_render_close.png` (aproximação na primeira peça de base). Pitfalls, todos
verificados:

- **`Gui.doCommand("Std_Quit")` não encerra o processo headless** — o `xvfb-run` fica
  pendurado até o timeout. Termine com `os._exit(0)` depois de salvar.
- **Oriente a câmera ANTES de enquadrar**: enquadrar e depois girar joga o objeto para fora
  do quadro (um close meu ficou com 3/4 de chão).
- Enquadre pela seleção (`Gui.SendMsgToActiveView("ViewSelection")`). `ViewFit` inclui o
  chão e a peça encolhe na imagem.
- No close, selecione só as peças do foco (incluir um montante de 1,6 m arruína o
  enquadramento) e esconda o chão.
- Os `print()` não aparecem no stdout nesse modo: o script grava um `.txt` de log.

### Rasterizar o modelo em ASCII

O melhor substituto de olho para conferir arranjo e conexão. **Amostre 3×3 por célula**,
senão um tubo de 30 mm some numa célula de 40 mm e você entrega uma imagem que mente.

```python
for o in objs:                              # filtre por bbox antes de isInside (rápido)
    b = o.Shape.BoundBox
    if b.XMax < x0 or b.XMin > x0+CX or b.YMax < y0 or b.YMin > y0+CY: continue
    for sx in (-0.33, 0, 0.33):
        for sy in (-0.33, 0, 0.33):
            if o.Shape.isInside(Vector(x0+(0.5+sx)*CX, y0+(0.5+sy)*CY,
                                       (b.ZMin+b.ZMax)/2), 1e-6, True):
                marca(o.Name)     # # montante, = travessa, P placa, o roda
```

Imprima camadas separadas (só o quadro, só os rodízios, tudo sobreposto). Na planta
sobreposta, `###====####` mostra de relance se travessa e montante emendaram.

## Regra que vale mais que todas

**Verifique medindo o modelo construído, nunca com fórmula re-derivada.** Uma versão
anterior conferia o espaçamento entre rodízios com um `math.dist` que reescrevia a fórmula
correta, enquanto o código de construção tinha o sinal trocado: a checagem passou (173 mm)
e o desenho saiu com metade dos rodízios fora da peça. A verificação tem que ler o
artefato, não re-derivar a intenção.

E o irmão dessa regra: **em laço que varre as duas pontas de um elemento, o deslocamento
inverte de sinal na segunda ponta.**

```python
# ERRADO: as duas pontas deslocam para o mesmo lado
for lado, pt in (("a", a_pt), ("b", b_pt)):
    xy = desl(pt, +TUBO/2)

# CERTO
for lado, pt, s in (("a", a_pt, +1.0), ("b", b_pt, -1.0)):
    xy = desl(pt, s * TUBO/2)
```

Sintoma: `bbox` do conjunto maior que o nominal, e uma travessa de comprimento certo que
não encosta no montante do lado `b`.

## Geometria de junta a 120 graus

Duas folhas planas com 120° internos: defina cada folha pelo eixo do seu painel e ponha os
montantes a `lado_tubo/2` **para dentro** da ponta, de modo que a face externa caia
exatamente na ponta. As duas faces de topo então se cruzam na aresta vertical comum — é ali
que a dobradiça de piano (aberta a 120°) trava. A folha `i` tem direção `i × 60°`; o
ângulo interno sai `180 − (ang2 − ang1)`.
