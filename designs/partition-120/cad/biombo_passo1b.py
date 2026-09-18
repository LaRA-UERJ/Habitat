"""Biombo 120 (Partition 120) - PASSO 1B: base revisada.

Muda em relacao ao passo 1 (que fica intacto, aprovado):
  - rodizio comercial: moveleiro dia 75 com freio, altura total 102 mm, placa 91,5 x 60 mm,
    carga 70 kg/un (referencia: Leroy Merlin 1567099890 / IPC Comercial). Antes: envelope
    generico de 100 mm de altura.
  - 4 rodizios em vez de 6: 2 por folha, so' nas folhas das pontas (1 e 3). A folha central
    fica pendurada nas duas juntas.
  - chapa soldada 100 x 70 x 4 sob o pe do montante, com 4 rasgos oblongos 25 x 9, entre o
    tubo e o rodizio (substituivel sem desmontar o quadro).

O pe em L foi descartado pelo usuario: perna de 150 mm no chao e' risco de tropeco no lab.

Cadeia de alturas: chao -> 102 (rodizio) -> 106 (topo da chapa) -> 1706 (topo do quadro).
O passo 1 tinha 100 -> 1700.

Verificacoes: todas medidas nos solidos (distToShape / CenterOfMass), nunca por formula
re-derivada. Ver docs/cad-workflow.md.

Roda:  freecadcmd designs/partition-120/cad/biombo_passo1b.py
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
import Part                              # noqa: E402
from FreeCAD import Vector               # noqa: E402

SAIDA = os.path.join(os.path.dirname(__file__), "saida")
os.makedirs(SAIDA, exist_ok=True)
LOG = {}
faltas = []

# ============================================================
# 1. PARAMETROS
# ============================================================
FOLHA_W = 900.0        # largura externa da folha            [brief 80-100 cm]
FOLHA_H = 1600.0       # altura do quadro                     [brief]
TUBO = 30.0            # metalon 30x30                        [brief]
PAREDE = 1.5           # 16 ga                                [brief]
GIRO = 60.0            # giro por junta -> 120 graus internos

ROD_DIA = 75.0         # roda do rodizio (3 pol)              [comercial]
ROD_LARG = 32.0        # largura da banda                     [comercial: 32 mm]
ROD_ALT = 102.0        # chao -> topo da placa do rodizio     [comercial: 102 mm]
ROD_CARGA = 70.0       # kg por rodizio                       [comercial]
PLACA_ROD = (91.5, 60.0, 4.0)      # placa do rodizio comprado [comercial]
ROD_RECUO = 100.0      # ponta da folha -> centro do rodizio  [P]
ROD_FOLHAS = (0, 2)    # indices das folhas com rodizio (1 e 3) -- 4 rodizios no total

CHAPA = (100.0, 70.0, 4.0)         # chapa soldada sob o montante [P]
FURO_OBL = 25.0        # rasgo oblongo: comprimento na direcao da folha   [P]
FURO_LARG = 9.0        # rasgo oblongo: largura (M8)                      [P]
FURO_PASSO_L = 70.0    # passo dos rasgos na direcao da folha             [P] A CONFERIR
FURO_PASSO_W = 40.0    # passo dos rasgos na direcao perpendicular        [P] A CONFERIR

Z0 = ROD_ALT + CHAPA[2]           # 106 = base do quadro (topo da chapa soldada)
Z1 = Z0 + FOLHA_H                 # 1706 = topo do quadro
A_VAZADA = TUBO ** 2 - (TUBO - 2 * PAREDE) ** 2      # 171 mm2
RHO_ACO = 7.85e-3                 # g/mm3

LOG["cadeia_alturas_mm"] = {"rodizio": ROD_ALT, "chapa": CHAPA[2],
                            "base_quadro": Z0, "topo": Z1}
LOG["rodizio_ref"] = (f"dia {ROD_DIA:.0f} com freio, altura {ROD_ALT:.0f}, "
                      f"placa {PLACA_ROD[0]:.1f}x{PLACA_ROD[1]:.0f}, carga {ROD_CARGA:.0f} kg/un")
LOG["rodizios_por_folha"] = {f"folha{i+1}": (2 if i in ROD_FOLHAS else 0)
                             for i in range(3)}
LOG["recuo_rodizio_mm"] = ROD_RECUO

# ============================================================
# 2. GEOMETRIA NO PLANO (planta)
# ============================================================


def rot(v, ang_deg):
    a = math.radians(ang_deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a),
            v[0] * math.sin(a) + v[1] * math.cos(a))


DIR = [rot((1.0, 0.0), i * GIRO) for i in range(3)]
ANG = [i * GIRO for i in range(3)]
P = [(0.0, 0.0)]
for i in range(3):
    P.append((P[i][0] + FOLHA_W * DIR[i][0], P[i][1] + FOLHA_W * DIR[i][1]))

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
doc = cl.novo_doc("Biombo120_p1b")
pecas, cortes, rodizios, pontos = [], [], [], {}


def chapa_com_rasgos(doc_alvo, nome, centro_xy, ang_deg, z_base):
    """Chapa com 4 rasgos oblongos, montada no referencial local e depois orientada.

    Recebe o documento alvo porque a varredura de recuo constroi em outro documento.
    """
    shp = Part.makeBox(CHAPA[0], CHAPA[1], CHAPA[2],
                       Vector(-CHAPA[0] / 2.0, -CHAPA[1] / 2.0, 0.0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            furo = Part.makeBox(FURO_OBL, FURO_LARG, CHAPA[2] + 2.0,
                                Vector(sx * FURO_PASSO_L / 2.0 - FURO_OBL / 2.0,
                                       sy * FURO_PASSO_W / 2.0 - FURO_LARG / 2.0,
                                       -1.0))
            shp = shp.cut(furo)
    # o cut devolve Compound: sem isso nao ha CenterOfMass/Volume (ver cad-workflow.md)
    if shp.ShapeType == "Compound":
        try:
            shp = shp.removeSplitter()
        except Exception:
            pass
    if shp.ShapeType == "Compound" and len(shp.Solids) == 1:
        shp = shp.Solids[0]
    shp.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang_deg)
    shp.translate(Vector(centro_xy[0], centro_xy[1], z_base))
    return cl.solido(doc_alvo, nome, shp)


def conjunto_rodizio(nome, c, ang):
    """chapa soldada + rodizio (roda, garfo, placa do produto) sob o pe do montante."""
    pecas.append(chapa_com_rasgos(doc, f"{nome}_chapa", c, ang, Z0 - CHAPA[2]))
    wh = ROD_DIA / 2.0
    pecas.append(cl.cilindro(doc, f"{nome}_roda", (c[0], c[1], wh), ang,
                             ROD_DIA, ROD_LARG))
    pecas.append(cl.caixa_orientada(doc, f"{nome}_garfo", c, ang, 46.0, 36.0, 23.0,
                                    ROD_DIA))
    pecas.append(cl.caixa_orientada(doc, f"{nome}_placa", c, ang,
                                    PLACA_ROD[0], PLACA_ROD[1], PLACA_ROD[2],
                                    ROD_ALT - PLACA_ROD[2]))


for i in range(3):
    ang, di = ANG[i], DIR[i]
    a_pt, b_pt = P[i], P[i + 1]

    def desl(pt, t, di=di):
        return (pt[0] + t * di[0], pt[1] + t * di[1])

    for lado, pt, s in (("a", a_pt, +1.0), ("b", b_pt, -1.0)):
        xy = desl(pt, s * TUBO / 2.0)
        pecas.append(cl.barra(doc, f"folha{i+1}_mont_{lado}", (xy[0], xy[1], Z0),
                              (xy[0], xy[1], Z1), TUBO))
        cortes.append(("montante", FOLHA_H))

    ta, tb = desl(a_pt, TUBO), desl(b_pt, -TUBO)
    comp_trav = math.dist(ta, tb)
    for nome, zc in (("inf", Z0 + TUBO / 2.0), ("sup", Z1 - TUBO / 2.0)):
        pecas.append(cl.barra(doc, f"folha{i+1}_trav_{nome}",
                              (ta[0], ta[1], zc), (tb[0], tb[1], zc), TUBO))
        cortes.append(("travessa", comp_trav))

    if i in ROD_FOLHAS:
        # recuado da ponta, DENTRO do plano da folha (sem pe em L, sem risco de tropeco)
        for lado, pt, s in (("a", a_pt, +1.0), ("b", b_pt, -1.0)):
            c = desl(pt, s * ROD_RECUO)
            conjunto_rodizio(f"folha{i+1}_{lado}", c, ang)
            rodizios.append(c)
            pontos[f"folha{i+1}_{lado}"] = {"ponta": pt, "centro": c}

doc.recompute()
med = cl.medir(pecas)
LOG["bbox_modelo_mm"] = [round(x, 1) for x in med["min"] + med["max"]]

comp_total = sum(c for _, c in cortes)
LOG["tubo_total_m"] = round(comp_total / 1000.0, 2)
LOG["massa_tubo_kg"] = round(A_VAZADA * comp_total * RHO_ACO / 1000.0, 2)
n_chapas = len([p for p in pecas if "_chapa" in p.Name])
LOG["n_chapas"] = n_chapas
LOG["massa_chapas_kg"] = round(n_chapas * CHAPA[0] * CHAPA[1] * CHAPA[2] * RHO_ACO / 1000.0, 2)
LOG["n_rodizios"] = len(rodizios)

# ============================================================
# 4. AUDITORIAS MEDIDAS NO MODELO
# ============================================================
tubos = [p for p in pecas if any(k in p.Name for k in ("_mont_", "_trav_"))]
adj = {t.Name: set() for t in tubos}
for ii, a in enumerate(tubos):
    for b in tubos[ii + 1:]:
        if a.Shape.distToShape(b.Shape)[0] < 0.001:
            adj[a.Name].add(b.Name)
            adj[b.Name].add(a.Name)
LOG["grafo_do_quadro"] = {k: sorted(v) for k, v in sorted(adj.items())}
for nome_t, viz in adj.items():
    n_trav = sum(1 for v in viz if "_trav_" in v)
    n_mont = sum(1 for v in viz if "_mont_" in v)
    if "_mont_" in nome_t and n_trav != 2:
        faltas.append(f"{nome_t}: {n_trav} travessas, esperado 2")
    if "_trav_" in nome_t and n_mont != 2:
        faltas.append(f"{nome_t}: {n_mont} montantes, esperado 2")

# chapa soldada: tem de estar em contato com algum tubo do quadro (na pratica solda
# sob a travessa inferior, que fica 20 mm adiante do montante)
for i in ROD_FOLHAS:
    for lado in ("a", "b"):
        nome = f"folha{i+1}_{lado}"
        ch = [p for p in pecas if p.Name == f"{nome}_chapa"][0]
        pl = [p for p in pecas if p.Name == f"{nome}_placa"][0]
        toca = [(round(ch.Shape.distToShape(t.Shape)[0], 3), t.Name) for t in tubos]
        toca.sort()
        if toca[0][0] > 0.001:
            faltas.append(f"{nome}: chapa nao encosta em nenhum tubo (min={toca[0][0]})")
        LOG.setdefault("chapa_soldada_em", {})[f"{nome}_chapa"] = {
            t: d for d, t in toca[:3]}
        d2 = pl.Shape.distToShape(ch.Shape)[0]
        if d2 > 0.001:
            faltas.append(f"{nome}: placa do rodizio nao encosta na chapa (d={d2:.1f})")
        if abs(ch.Shape.BoundBox.ZMax - Z0) > 0.001:
            faltas.append(f"{nome}: topo da chapa em {ch.Shape.BoundBox.ZMax:.1f}, esperado {Z0:.1f}")
        vol_esp = CHAPA[0] * CHAPA[1] * CHAPA[2] - 4 * FURO_OBL * FURO_LARG * CHAPA[2]
        if abs(ch.Shape.Volume - vol_esp) > 1.0:
            faltas.append(f"{nome}: volume da chapa {ch.Shape.Volume:.0f} != {vol_esp:.0f}")

rodas = [p for p in pecas if "_roda" in p.Name]
z_min = min(p.Shape.BoundBox.ZMin for p in rodas)
LOG["rodizio_toca_chao_mm"] = round(z_min, 3)
if abs(z_min) > 0.001:
    faltas.append(f"roda nao toca o chao (Zmin={z_min:.1f})")


def dono(o):
    """dono = folha + lado ('folha1_a'). Nomes: folha{i}_{lado}_{tipo} e, na varredura,
    varredura{i}_{lado}_{tipo}. Contato entre pecas do MESMO dono e' montagem, nao erro."""
    return "_".join(o.Name.split("_")[:2])


def interferencia(a, b):
    """volume de interseccao: distToShape devolve 0 tanto para contato quanto para
    sobreposicao, entao a unica medida honesta e' o volume do solido comum."""
    try:
        return a.Shape.common(b.Shape).Volume
    except Exception:
        return 0.0


base = [p for p in pecas if any(k in p.Name for k in
                                ("_roda", "_garfo", "_placa", "_chapa"))]
dist_min, par_min, vol_max, par_vol = 1e9, None, 0.0, None
for ii, a in enumerate(base):
    for b in base[ii + 1:]:
        if dono(a) == dono(b):
            continue
        d = a.Shape.distToShape(b.Shape)[0]
        if d < dist_min:
            dist_min, par_min = d, f"{a.Name} x {b.Name}"
        v = interferencia(a, b)
        if v > vol_max:
            vol_max, par_vol = v, f"{a.Name} x {b.Name}"
        if v > 1.0:
            faltas.append(f"{a.Name} e {b.Name} se interpenetram ({v:.0f} mm3)")
LOG["folga_min_base_mm"] = round(dist_min, 1)
LOG["par_mais_apertado"] = par_min
LOG["interferencia_max_base_mm3"] = round(vol_max, 3)
LOG["par_com_interferencia"] = par_vol

d_roda = 1e9
for ii, a in enumerate(rodas):
    for b in rodas[ii + 1:]:
        if dono(a) == dono(b):
            continue
        d_roda = min(d_roda, a.Shape.distToShape(b.Shape)[0])
LOG["folga_min_rodas_mm"] = round(d_roda, 1)

# ---- CG das pecas fabricadas (tubo analitico + chapas) ----
mt = mx = my = mz = 0.0
for p in pecas:
    b = p.Shape.BoundBox
    c = p.Shape.CenterOfMass
    if "_chapa" in p.Name:
        m = p.Shape.Volume * RHO_ACO
    elif any(k in p.Name for k in ("_mont_", "_trav_")):
        m = A_VAZADA * max(b.XLength, b.YLength, b.ZLength) * RHO_ACO
    else:
        continue                       # rodizio comprado: fora do CG (conservador)
    mt += m
    mx += m * c.x
    my += m * c.y
    mz += m * c.z
cg = (mx / mt, my / mt, mz / mt)
LOG["massa_fabricada_kg"] = round(mt / 1000.0, 2)
LOG["cg_fabricado_mm"] = [round(v, 1) for v in cg]


def hull(p):
    p = sorted(set((round(x, 3), round(y, 3)) for x, y in p))

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def estabilidade(pontos_apoio, cg_):
    """margem e angulo de tombamento a partir dos apoios (hull) e do CG medidos."""
    h = hull(pontos_apoio)
    dmin, dentro = 1e9, True
    for i in range(len(h)):
        a, b = h[i], h[(i + 1) % len(h)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        cruz = ex * (cg_[1] - a[1]) - ey * (cg_[0] - a[0])
        if cruz < 0:
            dentro = False
        dmin = min(dmin, abs(cruz) / L)
    return h, dmin, math.degrees(math.atan2(dmin, cg_[2])), dentro


h, dmin, ang_tomb, dentro = estabilidade(rodizios, cg)
LOG["poligono_apoio"] = [[round(x, 1), round(y, 1)] for x, y in h]
LOG["cg_dentro_do_poligono"] = dentro
LOG["margem_tombamento_mm"] = round(dmin, 1)
LOG["tombamento_graus"] = round(ang_tomb, 2)
LOG["tombamento_passo1_graus"] = 16.7      # medido no modelo do passo 1 (6 rodizios)

# ---- varredura de recuo: constroi os rodizios de verdade e mede ----
print("varredura de recuo do rodizio (margem de tombamento e folga ao montante vizinho):")
LOG["varredura_recuo"] = []
for R in (80.0, 90.0, 100.0, 110.0, 120.0):
    d2 = cl.novo_doc("varre%d" % int(R))
    centros, viz = [], []
    for i in ROD_FOLHAS:
        for k, (lado, pt, s) in enumerate((("a", P[i], +1.0), ("b", P[i + 1], -1.0))):
            di = DIR[i]
            c = (pt[0] + s * R * di[0], pt[1] + s * R * di[1])
            wh = ROD_DIA / 2.0
            cl.cilindro(d2, f"f{i}_{lado}_roda", (c[0], c[1], wh), ANG[i], ROD_DIA, ROD_LARG)
            cl.caixa_orientada(d2, f"f{i}_{lado}_garfo", c, ANG[i], 46.0, 36.0, 23.0, ROD_DIA)
            cl.caixa_orientada(d2, f"f{i}_{lado}_placa", c, ANG[i], PLACA_ROD[0],
                               PLACA_ROD[1], PLACA_ROD[2], ROD_ALT - PLACA_ROD[2])
            chapa_com_rasgos(d2, f"f{i}_{lado}_chapa", c, ANG[i], Z0 - CHAPA[2])
            centros.append(c)
    # montantes de TODAS as folhas (os vizinhos sao o que limita)
    for i in range(3):
        for lado, pt, s in (("a", P[i], +1.0), ("b", P[i + 1], -1.0)):
            di = DIR[i]
            xy = (pt[0] + s * TUBO / 2 * di[0], pt[1] + s * TUBO / 2 * di[1])
            viz.append(cl.barra(d2, f"m{i}_{lado}", (xy[0], xy[1], Z0),
                                (xy[0], xy[1], Z1), TUBO))
    d2.recompute()
    objs = [o for o in d2.Objects if o.TypeId == "Part::Feature"]
    base2 = [o for o in objs if any(k in o.Name for k in
                                    ("_roda", "_garfo", "_placa", "_chapa"))]
    tub2 = [o for o in objs if "_mont" not in o.Name and o.Name.startswith("m")]
    dmin2, par2 = 1e9, None
    for ii, a in enumerate(base2):
        for b in base2[ii + 1:]:
            if dono(a) == dono(b):
                continue
            d = a.Shape.distToShape(b.Shape)[0]
            if d < dmin2:
                dmin2, par2 = d, f"{a.Name} x {b.Name}"
    toca = 1e9
    for a in base2:
        for m in tub2:
            toca = min(toca, a.Shape.distToShape(m.Shape)[0])
    cc = [o.Shape.CenterOfMass for o in objs if "_roda" in o.Name]
    hp, dp, ap, dentro_p = estabilidade([(c.x, c.y) for c in cc], cg)
    linha = {"recuo": R, "folga_base_mm": round(dmin2, 1), "par": par2,
             "folga_ao_montante_mm": round(toca, 1),
             "margem_mm": round(dp, 1), "tombamento_graus": round(ap, 2),
             "cg_dentro": dentro_p}
    LOG["varredura_recuo"].append(linha)
    print("  recuo %5.0f: folga base %6.1f | folga ao montante %6.1f | margem %6.1f "
          "(tomba a %5.2f graus)%s"
          % (R, dmin2, toca, dp, ap, "" if dentro_p else "  CG FORA DO POLIGONO"))
    App.closeDocument(d2.Name)

# ============================================================
# 5. VISTAS
#   Frente: perpendicular a' folha CENTRAL (a placa do meio), do lado concavo, para a
#     vista sair simetrica. DIR2 esta a 60 graus -> observador em (-sin60, cos60);
#     direita = -DIR2; cima = +z (conferido: Direction x XDirection = +z).
#   Lateral: paralela a's folhas das pontas -- e' a "frente" do passo 1, renomeada.
#   Planta: de cima, com a mesma direita da frente (1o diedro).
# ============================================================
prj = cl.Projetor(doc, template="A3")
DIRF = (-math.sin(math.radians(GIRO)), math.cos(math.radians(GIRO)), 0.0)
XF = (-math.cos(math.radians(GIRO)), -math.sin(math.radians(GIRO)), 0.0)
VS = {}
VS["Frente"] = prj.vista("Frente", pecas, DIRF, XF, med["centro"], centrar_no_conteudo=True)
VS["Lateral"] = prj.vista("Lateral", pecas, *cl.DIRECOES["Frente"], med["centro"],
                          centrar_no_conteudo=True)
VS["Planta"] = prj.vista("Planta", pecas, cl.DIRECOES["Planta"][0], XF, med["centro"],
                         centrar_no_conteudo=True)
for nome in ("Frente", "Lateral", "Planta"):
    LOG[f"vista_{nome}"] = {"visiveis": len(VS[nome]["vis"]),
                            "ocultas": len(VS[nome]["hid"]),
                            "ext_mm": [round(VS[nome]["w"], 1), round(VS[nome]["h"], 1)]}
LOG["vistas_direcoes"] = {
    "Frente": {"Direction": [round(x, 4) for x in DIRF],
               "XDirection": [round(x, 4) for x in XF],
               "nota": "perpendicular a folha central (placa do meio), lado concavo"},
    "Lateral": {"Direction": list(cl.DIRECOES["Frente"][0]),
                "XDirection": list(cl.DIRECOES["Frente"][1]),
                "nota": "paralela as folhas das pontas"},
    "Planta": {"Direction": list(cl.DIRECOES["Planta"][0]),
               "XDirection": [round(x, 4) for x in XF],
               "nota": "de cima, com a mesma direita da frente (1o diedro)"},
}
Iso = prj.vista("Iso", pecas, *cl.DIRECOES["Iso"], med["centro"], centrar_no_conteudo=True)
LOG["vista_Iso"] = {"visiveis": len(Iso["vis"]), "ext_mm": [round(Iso["w"], 1),
                                                            round(Iso["h"], 1)]}

detalhe = [p for p in pecas if p.Name in
           ("folha1_mont_a", "folha1_a_chapa", "folha1_a_roda", "folha1_a_garfo",
            "folha1_a_placa")]
md = cl.medir(detalhe)
Det = prj.vista("Detalhe", detalhe, *cl.DIRECOES["Planta"], md["centro"],
                centrar_no_conteudo=True)
LOG["vista_Detalhe"] = {"visiveis": len(Det["vis"]), "ext_mm": [round(Det["w"], 1),
                                                                round(Det["h"], 1)]}

# ============================================================
# 6. FOLHA A3 -- grade de 3 colunas x 2 linhas, carimbo no canto
# ============================================================
ESC = 1 / 20.0
f = cl.Folha(os.path.join(SAIDA, "passo1b_prancha.pdf"), "A3")
f.moldura()

COL = (38.0, 165.0, 292.0)          # x dos cantos esquerdos das colunas
LIN = {"sup": 172.0, "inf": 48.0}   # y dos cantos inferiores das linhas

vp = f.poe(VS["Planta"], COL[0], LIN["inf"], ESC)
vf = f.poe(VS["Frente"], COL[0], LIN["sup"], ESC)
vl = f.poe(VS["Lateral"], COL[1], LIN["sup"], ESC)
vi = f.poe(Iso, COL[2], LIN["sup"], 1 / 25.0)
vd = f.poe(Det, COL[1], LIN["inf"], 1 / 2.0)
f.desenha()
for n in ("Planta", "Frente", "Lateral"):
    f.rotulo_vista(n)
f.texto(vi["px"], vi["py"] - 4.5, "ISOMETRICA (1:25)", 8, negrito=True)
# o detalhe fica na linha de baixo: rotulo e notas ACIMA dele, cotas abaixo
f.texto(vd["px"], vd["py"] + vd["fh"] + 4.5, "DETALHE BASE (1:2)", 8, negrito=True)
f.texto(vd["px"], vd["py"] + vd["fh"] + 9.5,
        f"chapa {CHAPA[0]:.0f}x{CHAPA[1]:.0f}x{CHAPA[2]:.0f} soldada sob a travessa inferior, "
        f"entre o tubo e o rodizio", 6.5)
f.texto(vd["px"], vd["py"] + vd["fh"] + 13.5,
        f"4 rasgos {FURO_OBL:.0f}x{FURO_LARG:.0f} passo {FURO_PASSO_L:.0f}x{FURO_PASSO_W:.0f}: "
        "CONFERIR com o rodizio comprado", 6.5)

xmin, ymin, zmin = med["min"]
xmax, ymax, zmax = med["max"]

# --- cotas: frente (perpendicular a' folha central) ---
f.cota_h("Frente", (P[0][0], P[0][1], zmin), (P[3][0], P[3][1], zmin), 7.0,
         f"{VS['Frente']['w']:.0f} total")
f.cota_v("Frente", (P[0][0], P[0][1], zmin), (P[0][0], P[0][1], zmax), 9.0,
         f"{zmax - zmin:.0f} total")
f.cota_v("Frente", (P[0][0], P[0][1], Z0), (P[0][0], P[0][1], Z1), 22.0, f"{FOLHA_H:.0f} quadro")
f.cota_v("Frente", (P[3][0], P[3][1], zmin), (P[3][0], P[3][1], Z0), -9.0,
         f"{Z0:.0f} rodizio+chapa")
# texto curto: anotacao longa aqui ja' saiu da folha uma vez (terminava em x=30 mm)
f.anotacao("Frente", P[3][0], P[3][1], Z1, f"{len(rodizios)} rodizios dia {ROD_DIA:.0f}")

# --- cotas: lateral (paralela a's folhas das pontas) ---
f.cota_h("Lateral", (0, ymin, zmin), (0, ymax, zmin), 7.0, f"{VS['Lateral']['w']:.0f} prof")
f.cota_v("Lateral", (0, ymax, zmin), (0, ymax, zmax), -9.0, f"{zmax - zmin:.0f} total")

# --- cotas: planta ---
f.cota_h("Planta", (P[0][0], P[0][1], 0), (P[3][0], P[3][1], 0), 7.0,
         f"{VS['Planta']['w']:.0f} total")
f.cota_v("Planta", (P[0][0], P[0][1], 0), (P[2][0], P[2][1], 0), 9.0,
         f"{VS['Planta']['h']:.0f} raio")
for i in (1, 2):
    f.anotacao("Planta", P[i][0], P[i][1], 0, f"{LOG['angulos_internos'][i - 1]:.0f} graus")

# --- cotas: detalhe da base (folha 1, lado a) ---
pt = pontos["folha1_a"]
z_face = Z0 - CHAPA[2] / 2.0
f.cota_h("Detalhe", (pt["ponta"][0], pt["ponta"][1], z_face),
         (pt["centro"][0], pt["centro"][1], z_face), 6.0, f"{ROD_RECUO:.0f} recuo")
dx, dy = DIR[0]
f.cota_h("Detalhe", (pt["centro"][0] + CHAPA[1] / 2 * dy, pt["centro"][1] - CHAPA[1] / 2 * dx,
                     z_face),
         (pt["centro"][0] - CHAPA[1] / 2 * dy, pt["centro"][1] + CHAPA[1] / 2 * dx, z_face),
         14.0, f"chapa {CHAPA[1]:.0f} larg")
f.anotacao("Detalhe", pt["centro"][0], pt["centro"][1], z_face,
           f"chapa {CHAPA[0]:.0f} comp, rodizio dia {ROD_DIA:.0f} h {ROD_ALT:.0f}",
           dist=10.0)

# --- lista de corte ---
resumo = {}
for nome, c in cortes:
    resumo.setdefault((nome, round(c)), 0)
    resumo[(nome, round(c))] += 1
linhas = [f"{n:<10s} 30x30x1,5  {c:>6d}      {q}" for (n, c), q in sorted(resumo.items())]
linhas.append(f"{'TOTAL':<10s} {'':<10s} {comp_total:>6.0f}      {len(cortes)}")
linhas.append(f"{'chapa base':<10s} {'100x70x4':<10s} {CHAPA[0]:>6.0f}      {n_chapas}")
linhas.append(f"{'rodizio':<10s} {'dia 75':<10s} {'':>6s}      {len(rodizios)}")
f.lista_corte("LISTA DE CORTE (quadro)", "peca       perfil     comp.(mm)  qtd",
              linhas + [f"2 rodizios por folha, so' nas folhas das pontas ({len(rodizios)} un.)"],
              COL[2], 140.0)

# --- carimbo ---
f.carimbo([
    ("Habitat / LaRA-UERJ", 10, True),
    ("BIOMBO 120  -  PASSO 1B: BASE (4 RODIZIOS)", 8, True),
    (f"Metalon 30x30x1,5: tubo {LOG['tubo_total_m']} m + {n_chapas} chapas 100x70x4 "
     f"({LOG['massa_tubo_kg']} + {LOG['massa_chapas_kg']} kg)", 6.5, False),
    ("FRENTE = folha central de frente; LATERAL = paralela as folhas das pontas", 6.5, False),
    (f"Escala 1:20 (detalhe 1:2)  mm  A3  1o diedro   Rodizio dia {ROD_DIA:.0f} "
     f"h {ROD_ALT:.0f} c/ freio, {len(rodizios)} un.", 6.5, False),
    ("Des. A. Calvao   2026-09-18   Rev. 02", 6.5, False),
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
LOG["caixas_na_folha"] = {n: [round(x, 1) for x in
                              (v["px"], v["py"], v["px"] + v["fw"], v["py"] + v["fh"])]
                          for n, v in f.vistas.items()}
LOG["area_util_ocupada_pct"] = round(
    100.0 * sum((c[2] - c[0]) * (c[3] - c[1]) for c in caixas.values())
    / ((408.0 - 12.0) * (287.0 - 12.0)), 1)

problemas = f.salva()
LOG["prancha_pdf_bytes"] = os.path.getsize(os.path.join(SAIDA, "passo1b_prancha.pdf"))

# ============================================================
# 7. DXF, STEP, CSV
# ============================================================
import TechDraw                                     # noqa: E402
import Import                                       # noqa: E402

for v in f.vistas.values():
    v["v"].Scale = v["escala"]
    v["v"].X = v["px"] + v["fw"] / 2.0
    v["v"].Y = v["py"] + v["fh"] / 2.0
doc.recompute()

fcstd = os.path.join(SAIDA, "passo1b_biombo.FCStd")
doc.saveAs(fcstd)
nome_doc = doc.Name
App.closeDocument(nome_doc)
doc2 = App.openDocument(fcstd)

try:
    pg2 = [o for o in doc2.Objects if o.TypeId == "TechDraw::DrawPage"][0]
    dxf = os.path.join(SAIDA, "passo1b_prancha.dxf")
    TechDraw.writeDXFPage(pg2, dxf)
    LOG["dxf_bytes"] = os.path.getsize(dxf)
except Exception as e:
    problemas.append("DXF: " + repr(e)[:120])

try:
    pecas2 = [o for o in doc2.Objects if o.TypeId == "Part::Feature"]
    stp = os.path.join(SAIDA, "passo1b_biombo.step")
    Import.export(pecas2, stp)
    LOG["step_bytes"] = os.path.getsize(stp)
except Exception as e:
    problemas.append("STEP: " + repr(e)[:120])

with open(os.path.join(SAIDA, "passo1b_lista_corte.csv"), "w", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["peca", "perfil", "comprimento_mm", "qtd", "observacao"])
    for (n, c), q in sorted(resumo.items()):
        w.writerow([n, "30x30x1,5", c, q, "ponta 90 graus"])
    w.writerow(["chapa_base", "chapa aco", CHAPA[0], n_chapas,
                f"{CHAPA[0]:.0f}x{CHAPA[1]:.0f}x{CHAPA[2]:.0f} mm; 4 rasgos oblongos "
                f"{FURO_OBL:.0f}x{FURO_LARG:.0f} passo {FURO_PASSO_L:.0f}x{FURO_PASSO_W:.0f} "
                "(conferir com o rodizio comprado); soldada sob a travessa inferior"])
    w.writerow(["rodizio", f"roda {ROD_DIA:.0f} mm c/ freio, altura {ROD_ALT:.0f}",
                "-", len(rodizios), "parafusado na chapa soldada sob a travessa inferior"])

LOG["problemas"] = problemas + faltas
LOG["verificacao_ok"] = not (problemas + faltas)
with open(os.path.join(SAIDA, "passo1b_relatorio.json"), "w") as fh:
    json.dump(LOG, fh, indent=1, default=str)
print("JSONRES>" + json.dumps(LOG, indent=1, default=str))
