"""Biombo 120 (Partition 120) - PASSO 1: estrutura basica (so' o metal).

Gera, headless:
  saida/passo1_prancha.pdf   A3, 1:20, 1o diedro: planta + frente + lateral + isometrica
  saida/passo1_prancha.dxf   DXF da prancha (TechDraw)
  saida/passo1_biombo.step   modelo solido (para quem tiver CAD)
  saida/passo1_biombo.FCStd
  saida/passo1_lista_corte.csv

Roda:  freecadcmd designs/partition-120/cad/biombo_passo1.py

NAO inclui: painel de madeira/espuma/tecido, dobradicas, detalhe do rodizio.
Esses entram nos passos seguintes, depois de validar a estrutura.
"""

import csv
import json
import math
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

import cad_lib as cl                      # noqa: E402
import FreeCAD as App                    # noqa: E402
from FreeCAD import Vector               # noqa: E402

SAIDA = os.path.join(os.path.dirname(__file__), "saida")
os.makedirs(SAIDA, exist_ok=True)
LOG = {}

# ============================================================
# 1. PARAMETROS  (do brief quando existia; propostas onde era TBD)
# ============================================================
FOLHA_W = 900.0        # largura externa de cada folha      [brief: 80-100 cm]
FOLHA_H = 1600.0       # altura do quadro                   [brief: total 150-180 cm]
TUBO = 30.0            # metalon quadrado                   [brief: sweet spot 30x30]
PAREDE = 1.5           # 16 ga                              [brief: 1,5 mm p/ colunas]
GIRO = 60.0            # giro por junta -> 120 graus internos

ROD_DIA = 75.0         # roda do rodizio                    [brief: 50-75 mm]
ROD_LARG = 32.0
ROD_ALT = 100.0        # chao -> base do quadro
ROD_RECUO = 100.0      # recuo do rodizio em relacao a ponta da folha
ROD_PLACA = (90.0, 70.0, 4.0)   # chapa soldada sob o montante

Z0 = ROD_ALT                 # base do quadro
Z1 = Z0 + FOLHA_H            # topo do quadro

A = TUBO * TUBO - (TUBO - 2 * PAREDE) ** 2
RHO_ACO = 7.85e-3            # g/mm3

# ============================================================
# 2. GEOMETRIA NO PLANO (planta)
# ============================================================
faltas = []


def rot(v, ang_deg):
    a = math.radians(ang_deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a),
            v[0] * math.sin(a) + v[1] * math.cos(a))


DIR = [rot((1.0, 0.0), i * GIRO) for i in range(3)]
ANG = [i * GIRO for i in range(3)]
P = [(0.0, 0.0)]
for i in range(3):
    P.append((P[i][0] + FOLHA_W * DIR[i][0], P[i][1] + FOLHA_W * DIR[i][1]))

# auditoria do angulo interno entre folhas vizinhas (tem de dar 120)
for i in range(2):
    a1 = math.degrees(math.atan2(DIR[i][1], DIR[i][0]))
    a2 = math.degrees(math.atan2(DIR[i + 1][1], DIR[i + 1][0]))
    interno = 180.0 - (a2 - a1)
    LOG.setdefault("angulos_internos", []).append(round(interno, 2))
    if abs(interno - 120.0) > 0.01:
        faltas.append(f"junta {i + 1}: angulo interno {interno:.2f} != 120")

# ============================================================
# 3. MODELO
# ============================================================
doc = cl.novo_doc("Biombo120")
pecas, cortes, rodizios = [], [], []

for i in range(3):
    ang, di = ANG[i], DIR[i]
    a_pt, b_pt = P[i], P[i + 1]

    def desl(pt, t, di=di):
        return (pt[0] + t * di[0], pt[1] + t * di[1])

    # montantes: eixo a meio tubo da ponta, PARA DENTRO, de modo que a face externa
    # caia exatamente na ponta. O SINAL importa: +TUBO/2 na ponta 'a', -TUBO/2 na 'b'
    # (errar isso joga o montante 30 mm para fora e desconecta as travessas).
    for lado, pt, s in (("a", a_pt, +1.0), ("b", b_pt, -1.0)):
        xy = desl(pt, s * TUBO / 2.0)
        pecas.append(cl.barra(doc, f"folha{i+1}_mont_{lado}", (xy[0], xy[1], Z0),
                              (xy[0], xy[1], Z1), TUBO))
        cortes.append(("montante", FOLHA_H))

    # travessas: entre as faces internas dos montantes
    ta, tb = desl(a_pt, TUBO), desl(b_pt, -TUBO)
    comp_trav = math.dist(ta, tb)
    for nome, zc in (("inf", Z0 + TUBO / 2.0), ("sup", Z1 - TUBO / 2.0)):
        pecas.append(cl.barra(doc, f"folha{i+1}_trav_{nome}",
                              (ta[0], ta[1], zc), (tb[0], tb[1], zc), TUBO))
        cortes.append(("travessa", comp_trav))

    # rodizios: recuados das pontas, para os de folhas vizinhas nao colidirem
    for lado, pt, s in (("a", a_pt, +1.0), ("b", b_pt, -1.0)):
        c = desl(pt, s * ROD_RECUO)
        wh = ROD_DIA / 2.0
        pecas.append(cl.cilindro(doc, f"folha{i+1}_roda_{lado}",
                                 (c[0], c[1], wh), ang, ROD_DIA, ROD_LARG))
        pecas.append(cl.caixa_orientada(doc, f"folha{i+1}_garfo_{lado}", c, ang,
                                        46.0, 36.0, 30.0, wh + 32.5))
        pecas.append(cl.caixa_orientada(doc, f"folha{i+1}_placa_{lado}", c, ang,
                                        ROD_PLACA[0], ROD_PLACA[1], ROD_PLACA[2],
                                        ROD_ALT - ROD_PLACA[2]))
        rodizios.append(c)

doc.recompute()
med = cl.medir(pecas)
LOG["bbox_modelo_mm"] = [round(x, 1) for x in med["min"] + med["max"]]

comp_total = sum(c for _, c in cortes)
LOG["tubo_total_m"] = round(comp_total / 1000.0, 2)
LOG["massa_metal_kg"] = round(A * comp_total * RHO_ACO / 1000.0, 2)
LOG["secao_tubo_mm2"] = A
LOG["n_rodizios"] = len(rodizios)

# --- auditorias MEDIDAS NO MODELO, nunca em formula re-derivada ---
# (a versao anterior recalculava a formula certa enquanto o codigo tinha o sinal
#  trocado; a checagem passava e o desenho saia errado)
import Part                                          # noqa: E402

tubos = [p for p in pecas if "_mont_" in p.Name or "_trav_" in p.Name]
adj = {t.Name: set() for t in tubos}
for ii, a in enumerate(tubos):
    for b in tubos[ii + 1:]:
        if a.Shape.distToShape(b.Shape)[0] < 0.001:
            adj[a.Name].add(b.Name)
            adj[b.Name].add(a.Name)
for nome_t, viz in adj.items():
    if len(viz) < 2:
        faltas.append(f"{nome_t} encosta em {len(viz)} tubo(s) -- quadro desconectado")
    if "_mont_" in nome_t:
        n_trav = sum(1 for v in viz if "_trav_" in v)
        if n_trav != 2:
            faltas.append(f"{nome_t} encosta em {n_trav} travessas, esperado 2")
    if "_trav_" in nome_t:
        n_mont = sum(1 for v in viz if "_mont_" in v)
        if n_mont != 2:
            faltas.append(f"{nome_t} encosta em {n_mont} montantes, esperado 2")
LOG["grafo_do_quadro"] = {k: sorted(v) for k, v in sorted(adj.items())}

# cada chapa de rodizio tem de estar soldada sob um tubo
for p in [x for x in pecas if "_placa_" in x.Name]:
    d = min(t.Shape.distToShape(p.Shape)[0] for t in tubos)
    if d > 0.001:
        faltas.append(f"{p.Name} nao encosta em nenhum tubo (d={d:.1f} mm)")

# rodizios de folhas diferentes nao podem se tocar
rod = [x for x in pecas if "_roda_" in x.Name or "_placa_" in x.Name or "_garfo_" in x.Name]
def dono(o):
    f, resto = o.Name.split("_", 1)
    tipo, lado = resto.rsplit("_", 1)
    return f"{f}_{lado}"
dist_min = 1e9
for ii, a in enumerate(rod):
    for b in rod[ii + 1:]:
        if dono(a) == dono(b):
            continue
        d = a.Shape.distToShape(b.Shape)[0]
        dist_min = min(dist_min, d)
        if d < 0.001:
            faltas.append(f"{a.Name} e {b.Name} se interpenetram (folhas vizinhas)")
LOG["folga_min_rodizios_mm"] = round(dist_min, 1)

# ============================================================
# 4. VISTAS
# ============================================================
prj = cl.Projetor(doc, template="A3")
VS = {}
for nome, chave in (("Frente", "Frente"), ("Planta", "Planta"), ("Lateral", "Lateral")):
    VS[nome] = prj.vista(nome, pecas, *cl.DIRECOES[chave], med["centro"])
    LOG[f"vista_{nome}"] = {"visiveis": len(VS[nome]["vis"]),
                            "ocultas": len(VS[nome]["hid"]),
                            "ext_mm": [round(VS[nome]["w"], 1), round(VS[nome]["h"], 1)]}
Iso = prj.vista("Iso", pecas, *cl.DIRECOES["Iso"], med["centro"])
LOG["vista_Iso"] = {"visiveis": len(Iso["vis"]), "ext_mm": [round(Iso["w"], 1), round(Iso["h"], 1)]}

# ============================================================
# 5. FOLHA A3, 1:20
# ============================================================
ESC = 1 / 20.0
f = cl.Folha(os.path.join(SAIDA, "passo1_prancha.pdf"), "A3")
f.moldura()

vp = f.poe(VS["Planta"], 36.0, 40.0, ESC)
vf = f.poe(VS["Frente"], 36.0, 150.0, ESC)
vl = f.poe(VS["Lateral"], 136.0, 150.0, ESC)
vi = f.poe(Iso, 245.0, 160.0, 1 / 25.0)
f.desenha()
for n in ("Planta", "Frente", "Lateral"):
    f.rotulo_vista(n)
f.texto(vi["px"], vi["py"] - 4.5, "ISOMETRICA (1:25)", 8, negrito=True)

xmin, ymin, zmin = med["min"]
xmax, ymax, zmax = med["max"]

# --- cotas: frente ---
f.cota_h("Frente", (xmin, ymin, zmin), (xmax, ymin, zmin), 7.0, f"{xmax - xmin:.0f} total")
f.cota_v("Frente", (xmin, ymin, zmin), (xmin, ymin, zmax), 9.0, f"{zmax - zmin:.0f} total")
f.cota_v("Frente", (xmin, ymin, Z0), (xmin, ymin, Z1), 22.0, f"{FOLHA_H:.0f} quadro")
f.cota_v("Frente", (xmax, ymin, zmin), (xmax, ymin, Z0), -9.0, f"{Z0:.0f} rodizio")
f.anotacao("Frente", xmax, ymax, Z1, f"{len(rodizios)} rodizios dia {ROD_DIA:.0f}")

# --- cotas: planta (o '900 folha' entra no detalhe da folha, nao no conjunto) ---
f.cota_h("Planta", (xmin, ymax, 0), (xmax, ymax, 0), 7.0, f"{xmax - xmin:.0f} total")
f.cota_v("Planta", (xmin, ymin, 0), (xmin, ymax, 0), 9.0, f"{ymax - ymin:.0f} prof")
for i in (1, 2):
    f.anotacao("Planta", P[i][0], P[i][1], 0, f"{LOG['angulos_internos'][i - 1]:.0f} graus")

# --- cotas: lateral ---
f.cota_h("Lateral", (0, ymin, 0), (0, ymax, 0), 7.0, f"{ymax - ymin:.0f} prof")
f.cota_v("Lateral", (0, ymax, zmin), (0, ymax, zmax), -9.0, f"{zmax - zmin:.0f} total")

# --- lista de corte ---
resumo = {}
for nome, c in cortes:
    resumo.setdefault((nome, round(c)), 0)
    resumo[(nome, round(c))] += 1
linhas = [f"{n:<10s} 30x30x1,5  {c:>6d}      {q}" for (n, c), q in sorted(resumo.items())]
linhas.append(f"{'TOTAL':<10s}            {comp_total:>6.0f}      {len(cortes)}")
linhas.append(f"rodizio     roda dia {ROD_DIA:.0f}   -         {len(rodizios)}")
f.lista_corte("LISTA DE CORTE (quadro)",
              "peca       perfil     comp.(mm)  qtd", linhas, 245.0, 138.0)

# --- carimbo ---
f.carimbo([
    ("Habitat / LaRA-UERJ", 10, True),
    ("BIOMBO 120  -  PASSO 1: ESTRUTURA", 8, True),
    ("Metalon quadrado 30x30x1,5 mm (16 ga) - aco carbono", 6.5, False),
    (f"Escala 1:20   Unidade: mm   A3   1o diedro   Rodizio dia {ROD_DIA:.0f}", 6.5, False),
    (f"Tubo: {LOG['tubo_total_m']} m   Peso aprox.: {LOG['massa_metal_kg']} kg (so metal)", 6.5, False),
    ("Des. A. Calvao   2026-09-18   Rev. 00", 6.5, False),
])

# --- auditoria de sobreposicao na folha ---
caixas = {n: (v["px"], v["py"], v["px"] + v["fw"], v["py"] + v["fh"]) for n, v in f.vistas.items()}
for i, a in enumerate(caixas):
    for b in list(caixas)[i + 1:]:
        A, B = caixas[a], caixas[b]
        if not (A[2] <= B[0] or A[0] >= B[2] or A[3] <= B[1] or A[1] >= B[3]):
            faltas.append(f"{a} e {b} se sobrepoem na folha")
for n, A in caixas.items():
    if not (A[2] <= 273.0 or A[0] >= 408.0 or A[3] <= 54.0 or A[1] >= 54.0):
        faltas.append(f"{n} invade o carimbo")

problemas = f.salva()
LOG["prancha_pdf_bytes"] = os.path.getsize(os.path.join(SAIDA, "passo1_prancha.pdf"))
LOG["caixas_na_folha"] = {n: [round(x, 1) for x in
                              (v["px"], v["py"], v["px"] + v["fw"], v["py"] + v["fh"])]
                          for n, v in f.vistas.items()}
LOG["carimbo_mm"] = [273.0, 12.0, 408.0, 54.0]

# ============================================================
# 6. DXF, STEP, CSV
# ============================================================
# PITFALL: writeDXFPage na MESMA sessao exporta a geometria em escala 1 e ignora
# Scale/X/Y recem-alterados (testado: recompute, touch, getVisibleEdges e
# page.recompute todos falham). Salvar e reabrir o documento resolve.
import TechDraw                                     # noqa: E402
import Import                                       # noqa: E402

for v in f.vistas.values():
    v["v"].Scale = v["escala"]
    v["v"].X = v["px"] + v["fw"] / 2.0
    v["v"].Y = v["py"] + v["fh"] / 2.0
doc.recompute()

fcstd = os.path.join(SAIDA, "passo1_biombo.FCStd")
doc.saveAs(fcstd)
nome_doc = doc.Name
App.closeDocument(nome_doc)
doc2 = App.openDocument(fcstd)

try:
    pg2 = [o for o in doc2.Objects if o.TypeId == "TechDraw::DrawPage"][0]
    dxf = os.path.join(SAIDA, "passo1_prancha.dxf")
    TechDraw.writeDXFPage(pg2, dxf)
    LOG["dxf_bytes"] = os.path.getsize(dxf)
except Exception as e:
    problemas.append("DXF: " + repr(e)[:120])

try:
    pecas2 = [o for o in doc2.Objects if o.TypeId == "Part::Feature"]
    stp = os.path.join(SAIDA, "passo1_biombo.step")
    Import.export(pecas2, stp)
    LOG["step_bytes"] = os.path.getsize(stp)
except Exception as e:
    problemas.append("STEP: " + repr(e)[:120])

with open(os.path.join(SAIDA, "passo1_lista_corte.csv"), "w", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["peca", "perfil", "comprimento_mm", "qtd", "observacao"])
    for (n, c), q in sorted(resumo.items()):
        w.writerow([n, "30x30x1,5", c, q, "ponta 90 graus"])
    w.writerow(["rodizio", f"roda {ROD_DIA:.0f} mm c/ freio", "-", len(rodizios),
                "placa aparafusada em chapa soldada sob o montante"])

LOG["problemas"] = problemas + faltas
LOG["verificacao_ok"] = not (problemas + faltas)
with open(os.path.join(SAIDA, "passo1_relatorio.json"), "w") as fh:
    json.dump(LOG, fh, indent=1, default=str)
print("JSONRES>" + json.dumps(LOG, indent=1, default=str))
