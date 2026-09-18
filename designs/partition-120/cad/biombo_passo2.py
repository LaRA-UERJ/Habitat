"""Biombo 120 (Partition 120) - PASSO 2: painel estofado.

Sobre a base congelada do passo 1b (reproduzida aqui, sem editar aquele arquivo):
  - compensado 15 mm dentro da abertura das 3 folhas (834 x 1534), 3 mm de folga;
  - espuma 30 mm colada nas DUAS faces (2 x 774 x 1474 x 30), recuada 30 mm da borda;
  - tecido 1 mm modelado por face (peca crua 874 x 1574, dobra de 20 mm grampeada);
  - fixacao do compensado por 4 abas 3 x 25 x 25 mm soldadas na face interna dos
    montantes, furo dia 4,2 e parafuso de madeira dia 4 x 16 (furo piloto dia 2,5).
  - massa dos paineis, CG do conjunto e nova margem de tombamento.

Tudo verificado MEDINDO o modelo construido (distToShape / common().Volume), nunca por
formula re-derivada. Ver docs/cad-workflow.md e a spec-passo2.md.

Roda:  freecadcmd designs/partition-120/cad/biombo_passo2.py
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
FOLHA_W = 900.0
FOLHA_H = 1600.0
TUBO = 30.0
PAREDE = 1.5
GIRO = 60.0

ROD_DIA = 75.0
ROD_LARG = 32.0
ROD_ALT = 102.0
ROD_CARGA = 70.0
PLACA_ROD = (91.5, 60.0, 4.0)
ROD_RECUO = 100.0
ROD_FOLHAS = (0, 2)

CHAPA = (100.0, 70.0, 4.0)
FURO_OBL = 25.0
FURO_LARG = 9.0
FURO_PASSO_L = 70.0
FURO_PASSO_W = 40.0

Z0 = ROD_ALT + CHAPA[2]
Z1 = Z0 + FOLHA_H
A_VAZADA = TUBO ** 2 - (TUBO - 2 * PAREDE) ** 2
RHO_ACO = 7.85e-3

# --- passo 2: painel estofado ---
COMP_T = 15.0
COMP_L = 834.0
COMP_H = 1534.0
FOLGA_COMP = 3.0
# Acabamento (espuma + tecido) e' OPCIONAL e fino, e o usuario ainda nao decidiu se existe.
# Nao entra no modelo: o que muda com acabamento e' o deslocamento da aba (ACAB_T) e o
# comprimento do parafuso. A aba solda encostada na face do painel JA montado.
ACAB_T = 4.0                                    # espuma 3 + tecido 1, por face (teto de 4 mm)
ACAB_ESPUMA_T = 3.0
ACAB_TECIDO_T = 1.0
RHO_ESPUMA = 25.0                               # kg/m3 (so' se o acabamento existir)
TECIDO_KGM2 = 0.35

ABA_T = 3.0                                     # chapa da cantoneira
ABA_H = 25.0                                    # altura (Z)
ABA_U_A = (-15.0, 7.5)                          # u da perna A (solda de face)
ABA_V_A = (0.0, 3.0)                            # v da perna A
ABA_U_B = (7.5, 10.5)                           # u da perna B (sobre o compensado)
ABA_V_B = (0.0, 25.0)                           # v da perna B
ABA_POR_MONTANTE = 2
ABA_ALTURAS = (Z0 + 200.0, Z0 + 1340.0)
ABA_FURO_D = 4.2
ABA_FURO_ATE_FACE = 15.0                        # v do eixo do parafuso

PARAF_D = 4.0
PARAF_COMP = 16.0
PARAF_CABECA_D = 8.0
PARAF_CABECA_T = 1.6
PARAF_PILOTO_D = 2.5
PARAF_MASSA = 2.2                               # g
PARAF_COMP_COM_ACAB = PARAF_COMP + ACAB_T       # 20 mm se houver acabamento

RHO_COMP = 600.0                                # kg/m3
RHO_COMP_SENS = (550.0, 600.0, 650.0)

# coordenadas locais (do plano medio da folha), seguindo a spec
NI_COMP = (-COMP_T / 2.0, +COMP_T / 2.0)        # -7,5 .. +7,5
NI_ABA = (COMP_T / 2.0, COMP_T / 2.0 + ABA_T)                 # 7,5 .. 10,5

LOG["cadeia_alturas_mm"] = {"rodizio": ROD_ALT, "chapa": CHAPA[2],
                            "base_quadro": Z0, "topo": Z1}
LOG["rodizio_ref"] = (f"dia {ROD_DIA:.0f} com freio, altura {ROD_ALT:.0f}, "
                      f"placa {PLACA_ROD[0]:.1f}x{PLACA_ROD[1]:.0f}, carga {ROD_CARGA:.0f} kg/un")
LOG["rodizios_por_folha"] = {f"folha{i+1}": (2 if i in ROD_FOLHAS else 0)
                             for i in range(3)}
LOG["recuo_rodizio_mm"] = ROD_RECUO
LOG["parametros_painel_mm"] = {
    "compensado": [COMP_L, COMP_H, COMP_T],
    "acabamento_opcional_por_face_mm": ACAB_T,
    "acabamento_detalhe": {"espuma": ACAB_ESPUMA_T, "tecido": ACAB_TECIDO_T,
                           "nota": "opcional, nao modelado"},
    "cantoneira": {"chapa": ABA_T, "altura": ABA_H,
                   "perna_A": {"u": list(ABA_U_A), "v": list(ABA_V_A),
                               "contato_solda_mm": [ABA_U_A[1] - ABA_U_A[0], ABA_H]},
                   "perna_B": {"u": list(ABA_U_B), "v": list(ABA_V_B)},
                   "furo": [ABA_FURO_D, ABA_FURO_ATE_FACE],
                   "volume_nominal_spec_mm3": 3337.5},
    "parafuso": [PARAF_D, PARAF_COMP, PARAF_CABECA_D, PARAF_CABECA_T, PARAF_PILOTO_D],
    "parafuso_com_acabamento": PARAF_COMP_COM_ACAB,
    "folga_compensado_tubo": FOLGA_COMP,
    "espessura_total_nominal": COMP_T,
    "densidades": {"compensado": RHO_COMP},
}

# ============================================================
# 2. GEOMETRIA NO PLANO (planta) - identica ao passo 1b
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


def desl(pt, t, di):
    """Deslocamento de 'pt' ao longo da direcao 'di' da FOLHA daquele ponto."""
    return (pt[0] + t * di[0], pt[1] + t * di[1])


def normal(p):                                  # ni = rot(di, +90) = (-dy, dx)
    return (-p[1], p[0])


NI = [normal(DIR[i]) for i in range(3)]
BISSETRIZ = []
for i in range(3):
    if i == 0:
        v = rot(NI[0], +GIRO / 2.0)             # concavo da folha 1 = bissetriz para dentro
    elif i == 2:
        v = rot(NI[2], -GIRO / 2.0)
    else:
        v = NI[1]
    BISSETRIZ.append(v)

for i in range(2):
    interno = 180.0 - (math.degrees(math.atan2(DIR[i + 1][1], DIR[i + 1][0]))
                       - math.degrees(math.atan2(DIR[i][1], DIR[i][0])))
    LOG.setdefault("angulos_internos", []).append(round(interno, 2))
    if abs(interno - 120.0) > 0.01:
        faltas.append(f"junta {i + 1}: angulo interno {interno:.2f} != 120")

# ============================================================
# 3. MODELO
# ============================================================
doc = cl.novo_doc("Biombo120_p2")
pecas, cortes, rodizios, pontos = [], [], [], {}
comp_peca = {}                     # nome do tubo -> comprimento real (para a massa)
painel, abas, parafusos = [], [], []


def chapa_com_rasgos(doc_alvo, nome, centro_xy, ang_deg, z_base):
    """Chapa do rodizio com 4 rasgos oblongos (identica ao passo 1b)."""
    shp = Part.makeBox(CHAPA[0], CHAPA[1], CHAPA[2],
                       Vector(-CHAPA[0] / 2.0, -CHAPA[1] / 2.0, 0.0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            furo = Part.makeBox(FURO_OBL, FURO_LARG, CHAPA[2] + 2.0,
                                Vector(sx * FURO_PASSO_L / 2.0 - FURO_OBL / 2.0,
                                       sy * FURO_PASSO_W / 2.0 - FURO_LARG / 2.0,
                                       -1.0))
            shp = shp.cut(furo)
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
    pecas.append(chapa_com_rasgos(doc, f"{nome}_chapa", c, ang, Z0 - CHAPA[2]))
    wh = ROD_DIA / 2.0
    pecas.append(cl.cilindro(doc, f"{nome}_roda", (c[0], c[1], wh), ang,
                             ROD_DIA, ROD_LARG))
    pecas.append(cl.caixa_orientada(doc, f"{nome}_garfo", c, ang, 46.0, 36.0, 23.0,
                                    ROD_DIA))
    pecas.append(cl.caixa_orientada(doc, f"{nome}_placa", c, ang,
                                    PLACA_ROD[0], PLACA_ROD[1], PLACA_ROD[2],
                                    ROD_ALT - PLACA_ROD[2]))


def montante(nome, centro_xy, ang, z0, z1, sec):
    """Montante com secao 30x30 GIRADA por 'ang'.

    cl.barra constroi barra vertical como caixa alinhada aos eixos (ignora a
    rotacao da folha) -- para as folhas 2 e 3 (60 e 120 graus) isso deixa a secao
    de fora do plano da folha. Medido: o compensado a 3 mm da face interna
    colidia com esse prisma (10.986 mm3) e a travessa penetrava 1.044 mm3 no
    montante. Aqui a secao e' girada por ANG[i]; para a folha 1 (ang = 0) o
    resultado e' identico ao cl.barra.
    """
    return cl.caixa_orientada(doc, nome, centro_xy, ang, sec, sec, z1 - z0, z0)


# ---- quadro: 3 folhas (montantes + travessas + rodizios) ----
for i in range(3):
    ang, di = ANG[i], DIR[i]
    a_pt, b_pt = P[i], P[i + 1]

    for lado, pt, s in (("a", a_pt, +1.0), ("b", b_pt, -1.0)):
        xy = desl(pt, s * TUBO / 2.0, di)
        pecas.append(montante(f"folha{i+1}_mont_{lado}", xy, ang, Z0, Z1, TUBO))
        cortes.append(("montante", FOLHA_H))
        comp_peca[f"folha{i+1}_mont_{lado}"] = FOLHA_H

    ta, tb = desl(a_pt, TUBO, di), desl(b_pt, -TUBO, di)
    comp_trav = math.dist(ta, tb)
    for nome, zc in (("inf", Z0 + TUBO / 2.0), ("sup", Z1 - TUBO / 2.0)):
        pecas.append(cl.barra(doc, f"folha{i+1}_trav_{nome}",
                              (ta[0], ta[1], zc), (tb[0], tb[1], zc), TUBO))
        cortes.append(("travessa", comp_trav))
        comp_peca[f"folha{i+1}_trav_{nome}"] = comp_trav

    if i in ROD_FOLHAS:
        for lado, pt, s in (("a", a_pt, +1.0), ("b", b_pt, -1.0)):
            c = desl(pt, s * ROD_RECUO, di)
            conjunto_rodizio(f"folha{i+1}_{lado}", c, ang)
            rodizios.append(c)
            pontos[f"folha{i+1}_{lado}"] = {"ponta": pt, "centro": c}


def cantoneira(nome, ref, di, ni, ang, z_base, s_v):
    """Aba de fixacao: CANTONEIRA dobrada em L, chapa 3 mm, 25 mm de altura.

    Construida no referencial local da folha (x = v ao longo de di, y = u ao longo
    de ni, z na vertical), depois girada por 'ang' e levada para 'ref' (o ponto da
    face interna do montante sobre o plano medio do painel):

      perna A: u -15,0 a +7,5 | v 0 a 3,0  -> soldada DE FACE na face interna do
               montante (22,5 x 25 mm de contato)
      perna B: u +7,5 a +10,5 | v 0 a 25,0 -> deitada sobre a face concava do
               compensado
      furo    : dia 4,2 passante em u, centro em v = 15,0, centrado na altura

    s_v = +1 (montante a): v cresce em +di, que e' o lado da abertura daquele
    montante. s_v = -1 (montante b): v cresce em -di, porque a abertura do
    montante b fica no sentido OPOSTO (a folha corre de a para b, logo o vao
    entre os dois montantes esta' a' esquerda de b_pt - TUBO*di). Com +1 nos dois
    lados a cantoneira de b cai DENTRO do tubo (medido: 3.521 mm3 de intersecao,
    a peca inteira) e a perna B fica a 3,0 mm do compensado.

    fuse() + removeSplitter(): sem unir as pernas sobram duas pecas soltas (ou um
    Compound) e tanto o volume quanto a interferencia mentem.
    """
    x_a = 0.0 if s_v > 0 else -ABA_T
    x_b = 0.0 if s_v > 0 else -(ABA_V_B[1] - ABA_V_B[0])
    perna_a = Part.makeBox(ABA_T, ABA_U_A[1] - ABA_U_A[0], ABA_H,
                           Vector(x_a, ABA_U_A[0], 0.0))
    perna_b = Part.makeBox(ABA_V_B[1] - ABA_V_B[0], ABA_T, ABA_H,
                           Vector(x_b, ABA_U_B[0], 0.0))
    shp = perna_a.fuse(perna_b)
    furo = Part.makeCylinder(ABA_FURO_D / 2.0, ABA_T + 2.0,
                             Vector(s_v * ABA_FURO_ATE_FACE, ABA_U_B[0] - 1.0,
                                    ABA_H / 2.0),
                             Vector(0, 1, 0))
    shp = shp.cut(furo)
    if shp.ShapeType == "Compound":
        try:
            shp = shp.removeSplitter()
        except Exception:
            pass
    if shp.ShapeType == "Compound" and len(shp.Solids) == 1:
        shp = shp.Solids[0]
    if shp.ShapeType != "Solid":
        faltas.append(f"{nome}: cantoneira nao e' um solido unico ({shp.ShapeType})")
    shp.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang)
    shp.translate(Vector(ref[0], ref[1], z_base))
    return cl.solido(doc, nome, shp)


# ---- painel: so' a placa de compensado, por folha ----
def caixa_plana(nome, ref, di, ni, di_ini, t_di, ni_a, ni_b, z0, z1, ang):
    """Chapa plana de 't_di' mm em di a partir de 'di_ini' medido de 'ref' (a face
    interna do montante), e de 'ni_a' a 'ni_b' mm do plano medio do painel.

    Em ni a caixa ATRAVESSA o plano medio: o deslocamento nao inverte de sinal.
    """
    mid = ((ni_a + ni_b) / 2.0)
    cxy = (ref[0] + (di_ini + t_di / 2.0) * di[0] + mid * ni[0],
           ref[1] + (di_ini + t_di / 2.0) * di[1] + mid * ni[1])
    return cl.caixa_orientada(doc, nome, cxy, ang, t_di, abs(ni_b - ni_a),
                              z1 - z0, z0)


for i in range(3):
    di, ni, ang = DIR[i], NI[i], ANG[i]
    a_pt, b_pt = P[i], P[i + 1]
    face_a = desl(a_pt, TUBO, di)               # face interna do montante a
    face_b = desl(b_pt, -TUBO, di)              # face interna do montante b
    vao = math.dist(face_a, face_b)
    meio = ((face_a[0] + face_b[0]) / 2.0, (face_a[1] + face_b[1]) / 2.0)
    if abs(vao - (FOLHA_W - 2 * TUBO)) > 0.01:
        faltas.append(f"folha{i+1}: vao entre faces internas {vao:.2f}")

    # compensado: 3 mm de folga a cada face interna de tubo (vao da perna A)
    ZC0 = Z0 + TUBO + FOLGA_COMP                # base do compensado: Z0 + 33
    comp = caixa_plana(f"folha{i+1}_compensado", face_a, di, ni, FOLGA_COMP,
                       COMP_L, NI_COMP[0], NI_COMP[1], ZC0, ZC0 + COMP_H, ang)
    painel.append(comp)
    pecas.append(comp)

    # abas: cantoneiras em L, 4 por folha, nas faces internas dos 2 montantes.
    # v e' medido da face interna do montante e cresce PARA DENTRO DA ABERTURA:
    # +di no montante a, -di no montante b (s_v).
    for lado, ref, s_v in (("a", face_a, +1.0), ("b", face_b, -1.0)):
        for k, z_aba in enumerate(ABA_ALTURAS):
            nome = f"folha{i+1}_{lado}_aba_{k+1}"
            o = cantoneira(nome, ref, di, ni, ang, z_aba - ABA_H / 2.0, s_v)
            abas.append(o)
            pecas.append(o)
            # parafuso: eixo em v = 15,0 (da face interna), centro em u = 2,5
            u_par = 10.5 - PARAF_COMP / 2.0                               # 2,5
            x_f = (ref[0] + s_v * ABA_FURO_ATE_FACE * di[0] + u_par * ni[0],
                   ref[1] + s_v * ABA_FURO_ATE_FACE * di[1] + u_par * ni[1])
            p = cl.cilindro(doc, f"folha{i+1}_{lado}_paraf_{k+1}",
                            (x_f[0], x_f[1], z_aba), ang, PARAF_D, PARAF_COMP)
            parafusos.append(p)
            pecas.append(p)
            # cabeca: u de 10,5 a 12,1 -> centro 11,3
            u_cab = NI_ABA[1] + PARAF_CABECA_T / 2.0
            x_cab = (ref[0] + s_v * ABA_FURO_ATE_FACE * di[0] + u_cab * ni[0],
                     ref[1] + s_v * ABA_FURO_ATE_FACE * di[1] + u_cab * ni[1])
            cab = cl.cilindro(doc, f"folha{i+1}_{lado}_cabeca_{k+1}",
                              (x_cab[0], x_cab[1], z_aba), ang,
                              PARAF_CABECA_D, PARAF_CABECA_T)
            pecas.append(cab)

doc.recompute()
med = cl.medir(pecas)
LOG["bbox_modelo_mm"] = [round(x, 1) for x in med["min"] + med["max"]]
LOG["n_pecas"] = len(pecas)
LOG["n_abas"] = len(abas)
LOG["aba_alturas_z_medidas"] = [round(a.Shape.BoundBox.ZMin + ABA_H / 2.0, 1)
                                for a in abas[:2]]
LOG["volume_cantoneira_medido_mm3"] = round(abas[0].Shape.Volume, 1)
LOG["volume_cantoneira_nominal_spec_mm3"] = 3337.5
LOG["desvio_volume_cantoneira_mm3"] = round(abas[0].Shape.Volume - 3337.5, 1)

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

# ---- 1/2. cantoneira: perna A solda de face no montante, perna B apoia no compensado ----
LOG["aba_contatos"] = {}
for o in abas:
    partes = o.Name.split("_")               # folhaN_lado_aba_k
    folha, lado = partes[0], partes[1]
    mont = [p for p in pecas if p.Name == f"{folha}_mont_{lado}"][0]
    comp = [p for p in pecas if p.Name == f"{folha}_compensado"][0]
    d_mont = o.Shape.distToShape(mont.Shape)[0]
    d_comp = o.Shape.distToShape(comp.Shape)[0]
    LOG["aba_contatos"][o.Name] = {"perna_A_montante_mm": round(d_mont, 3),
                                   "perna_B_compensado_mm": round(d_comp, 3)}
    if d_mont > 0.001:
        faltas.append(f"{o.Name}: perna A nao encosta no montante (d={d_mont:.3f})")
    if d_comp > 0.001:
        faltas.append(f"{o.Name}: perna B nao encosta no compensado (d={d_comp:.3f})")

# geometria local medida: u ao longo de ni, v ao longo de di, do ref (face interna)
LOG["aba_uv_medido_mm"] = {}
for i in range(3):
    di, ni = DIR[i], NI[i]
    face_a = desl(P[i], TUBO, di)
    for o in [a for a in abas if a.Name.startswith(f"folha{i+1}_a_")][:1]:
        us, vs = [], []
        for vtx in o.Shape.Vertexes:
            p = (vtx.Point.x - face_a[0], vtx.Point.y - face_a[1])
            us.append(p[0] * ni[0] + p[1] * ni[1])
            vs.append(p[0] * di[0] + p[1] * di[1])
        LOG["aba_uv_medido_mm"][o.Name] = {
            "u": [round(min(us), 2), round(max(us), 2)],
            "v": [round(min(vs), 2), round(max(vs), 2)]}

# ---- 3. folga do compensado aos 4 tubos do quadro da propria folha ----
LOG["folga_compensado_tubo_mm"] = {}
d_min_geral, par_geral = 1e9, None
for i in range(3):
    comp = [p for p in pecas if p.Name == f"folha{i+1}_compensado"][0]
    viz = [t for t in tubos if t.Name.startswith(f"folha{i+1}_")]
    pior = (1e9, None)
    for t in viz:
        d = comp.Shape.distToShape(t.Shape)[0]
        LOG["folga_compensado_tubo_mm"][f"{comp.Name}_x_{t.Name}"] = round(d, 2)
        if d < pior[0]:
            pior = (d, t.Name)
    if pior[0] < 2.9:
        faltas.append(f"{comp.Name}: folga ao tubo {pior[0]:.2f} mm < 2.9")
    if pior[0] < d_min_geral:
        d_min_geral, par_geral = pior[0], f"{comp.Name} x {pior[1]}"
LOG["folga_min_compensado_tubo_mm"] = round(d_min_geral, 2)
LOG["par_folga_min_compensado"] = par_geral
LOG["folga_compensado_travessa_V_mm"] = round(
    (Z0 + TUBO + FOLGA_COMP) - (Z0 + TUBO), 2)
LOG["folga_compensado_travessa_S_mm"] = round(
    (Z1 - TUBO) - (Z0 + TUBO + FOLGA_COMP + COMP_H), 2)


def dono(o):
    return "_".join(o.Name.split("_")[:2])


def interferencia(a, b, filtro_bbox=True):
    """volume de interseccao dos solidos REAIS; bbox que nao se cruza -> 0."""
    if filtro_bbox:
        ba, bb = a.Shape.BoundBox, b.Shape.BoundBox
        if (ba.XMax < bb.XMin or ba.XMin > bb.XMax or ba.YMax < bb.YMin or
                ba.YMin > bb.YMax or ba.ZMax < bb.ZMin or ba.ZMin > bb.ZMax):
            return 0.0, False
    try:
        return a.Shape.common(b.Shape).Volume, True
    except Exception:
        return 0.0, True


# ---- 4/5. interferecias ----
grupo = {}
for p in pecas:
    n = p.Name
    if any(k in n for k in ("_mont_", "_trav_", "_roda", "_garfo", "_placa", "_chapa")):
        grupo[n] = "quadro"
    elif "_compensado" in n:
        grupo[n] = "painel"
    elif "_espuma" in n or "_tecido" in n:
        grupo[n] = "painel"
    elif "_aba" in n:
        grupo[n] = "aba"
    else:
        grupo[n] = "parafuso"      # parafuso e cabeca: entram NO compensado de proposito

vol_max, par_vol = 0.0, None
pares_testados, pares_por_bbox = 0, 0
interf_por_tipo = {}
interf_herdada = {}
for ii, a in enumerate(pecas):
    for b in pecas[ii + 1:]:
        ga, gb = grupo[a.Name], grupo[b.Name]
        if ga == gb == "quadro" and dono(a) == dono(b):
            continue
        if ga == gb and ga in ("painel", "aba", "parafuso") and dono(a) == dono(b):
            continue
        if {ga, gb} == {"parafuso", "quadro"}:
            continue
        v, medido = interferencia(a, b)
        if medido:
            pares_testados += 1
        else:
            pares_por_bbox += 1
        chave = " x ".join(sorted((ga, gb)))
        interf_por_tipo[chave] = max(interf_por_tipo.get(chave, 0.0), v)
        if v > vol_max:
            vol_max, par_vol = v, f"{a.Name} x {b.Name}"
        # parafuso/cabeca dentro do compensado: projeto (13 mm no compensado)
        esperado = (ga == "parafuso" and gb == "painel") or (gb == "parafuso" and ga == "painel")
        # quadro x quadro: caracteristica herdada do passo 1b (junta a 120 graus, o
        # montante b de uma folha e o montante a da vizinha dividem o canto) --
        # medida e reportada, mas nao e' falha do passo 2.
        herdado = (ga == "quadro" and gb == "quadro")
        if v > 1.0 and herdado:
            interf_herdada[chave] = max(interf_herdada.get(chave, 0.0), v)
        elif v > 1.0 and not esperado:
            faltas.append(f"{a.Name} e {b.Name} se interpenetram ({v:.0f} mm3)")
LOG["interferencia_max_mm3"] = round(vol_max, 3)
LOG["par_com_interferencia"] = par_vol
LOG["interferencia_max_por_tipo_mm3"] = {k: round(v, 3) for k, v in
                                         sorted(interf_por_tipo.items())}
LOG["interferencia_herdada_do_1b_mm3"] = {k: round(v, 1) for k, v in
                                          sorted(interf_herdada.items())}
LOG["pares_interferencia_testados"] = pares_testados
LOG["pares_descartados_por_bbox"] = pares_por_bbox

paraf = [p for p in pecas if "_paraf_" in p.Name]
cabecas = [p for p in pecas if "_cabeca_" in p.Name]
LOG["parafuso_no_compensado_mm3"] = round(
    paraf[0].Shape.common(
        [p for p in pecas if p.Name == "folha1_compensado"][0].Shape).Volume, 1)
LOG["parafuso_x_aba_mm3"] = round(
    paraf[0].Shape.common([a for a in abas if a.Name == "folha1_a_aba_1"][0].Shape).Volume, 3)
LOG["cabeca_x_aba_mm3"] = round(
    cabecas[0].Shape.common([a for a in abas if a.Name == "folha1_a_aba_1"][0].Shape).Volume, 3)

# ---- 6. rodizios no chao ----
rodas = [p for p in pecas if "_roda" in p.Name]
z_min = min(p.Shape.BoundBox.ZMin for p in rodas)
LOG["rodizio_toca_chao_mm"] = round(z_min, 3)
if abs(z_min) > 0.001:
    faltas.append(f"roda nao toca o chao (Zmin={z_min:.1f})")

# ---- 7. espessura do painel medida no bbox (folha 1: ni = +Y) ----
pn1 = [p for p in painel if p.Name.startswith("folha1_")]
b1 = cl.medir(pn1)
LOG["painel_espessura_medida_mm"] = round(b1["max"][1] - b1["min"][1], 2)
LOG["painel_espessura_nominal_mm"] = COMP_T
LOG["painel_faixa_ni_mm"] = [round(b1["min"][1], 2), round(b1["max"][1], 2)]
LOG["painel_bbox_folha1_mm"] = [round(x, 1) for x in b1["min"] + b1["max"]]
if abs(LOG["painel_espessura_medida_mm"] - COMP_T) > 0.1:
    faltas.append(f"espessura da placa {LOG['painel_espessura_medida_mm']:.2f} != {COMP_T:.1f}")
if b1["max"][0] - b1["min"][0] < COMP_L:
    faltas.append("compensado com comprimento menor que 834 mm")

# ---- 8. altura total ----
LOG["altura_total_mm"] = round(med["max"][2] - med["min"][2], 1)
if abs(LOG["altura_total_mm"] - 1706.0) > 0.01:
    faltas.append(f"altura total {LOG['altura_total_mm']} != 1706")
z_topo_painel = max(p.Shape.BoundBox.ZMax for p in painel)
LOG["topo_do_painel_mm"] = round(z_topo_painel, 1)
if z_topo_painel > Z1 - 3.0 + 0.001:
    faltas.append("painel passa do quadro por cima")
if min(p.Shape.BoundBox.ZMin for p in painel) < Z0 + 3.0 - 0.001:
    faltas.append("painel passa do quadro por baixo")

# ============================================================
# 5. MASSA, CG E TOMBAMENTO
# ============================================================
RHO_TECIDO_G_MM2 = TECIDO_KGM2 * 1000.0 / 1e6      # 0,35 kg/m2 -> g/mm2 (acabamento opcional)
logos = []
for p in pecas:
    n = p.Name
    c = p.Shape.CenterOfMass
    if "_cabeca_" in n:
        continue                       # a cabeca faz parte dos 2,2 g do parafuso
    if "_chapa" in n:
        m = p.Shape.Volume * RHO_ACO
        k = "chapas_rodizio"
    elif any(k2 in n for k2 in ("_mont_", "_trav_")):
        # comprimento REAL da peca (nao o bbox: uma travessa a 60 graus tem bbox
        # menor que o comprimento e a massa sairia subestimada em 12%)
        m = A_VAZADA * comp_peca[n] * RHO_ACO
        k = "tubo"
    elif "_aba" in n:
        m = p.Shape.Volume * RHO_ACO
        k = "abas"
    elif "_compensado" in n:
        m = p.Shape.Volume * 1e-9 * RHO_COMP * 1000.0
        k = "compensado"
    elif "_paraf_" in n:
        m = PARAF_MASSA
        k = "parafusos"
    else:
        continue                       # rodizio comprado: fora do CG (conservador)
    logos.append({"nome": n, "tipo": k, "m_g": m, "com": (c.x, c.y, c.z),
                  "vol_mm3": p.Shape.Volume})

kit = {}
for lg in logos:
    kit[lg["tipo"]] = kit.get(lg["tipo"], 0.0) + lg["m_g"]
LOG["massa_por_kit_kg"] = {k: round(v / 1000.0, 3) for k, v in sorted(kit.items())}
LOG["metodo_tubo"] = "secao vazada x comprimento (171 mm2)"

massa_painel_folha = {}
massa_folha_total = {}
massa_aba_paraf_folha = {}
for i in range(3):
    sel = [lg for lg in logos if lg["nome"].startswith(f"folha{i+1}_")]
    pain = sum(lg["m_g"] for lg in sel if lg["tipo"] == "compensado")
    fix = sum(lg["m_g"] for lg in sel if lg["tipo"] in ("abas", "parafusos"))
    massa_painel_folha[f"folha{i+1}"] = round(pain / 1000.0, 2)
    massa_aba_paraf_folha[f"folha{i+1}"] = round(fix / 1000.0, 3)
    massa_folha_total[f"folha{i+1}"] = round(sum(lg["m_g"] for lg in sel) / 1000.0, 2)
LOG["massa_painel_por_folha_kg"] = massa_painel_folha
LOG["massa_abas_parafusos_por_folha_kg"] = massa_aba_paraf_folha
LOG["massa_folha_completa_kg"] = massa_folha_total
LOG["massa_painel_folha_central_kg"] = massa_painel_folha["folha2"]
LOG["n_paineis"] = 3
massa_total = sum(lg["m_g"] for lg in logos)
LOG["massa_total_fabricada_kg"] = round(massa_total / 1000.0, 2)
LOG["carga_por_rodizio_kg"] = round(massa_total / 1000.0 / len(rodizios), 1)
LOG["limite_rodizio_kg"] = ROD_CARGA
LOG["folga_limite_rodizio_kg"] = round(ROD_CARGA - massa_total / 1000.0 / len(rodizios), 1)
if massa_total / 1000.0 / len(rodizios) > ROD_CARGA:
    faltas.append("carga por rodizio acima do limite")


def cg_com(rho_comp):
    """CG do conjunto fabricado, com o compensado a 'rho_comp' kg/m3."""
    mt = mx = my = mz = 0.0
    for lg in logos:
        m = lg["m_g"]
        if lg["tipo"] == "compensado":
            m = lg["vol_mm3"] * 1e-9 * rho_comp * 1000.0
        mt += m
        mx += m * lg["com"][0]
        my += m * lg["com"][1]
        mz += m * lg["com"][2]
    return (mx / mt, my / mt, mz / mt), mt / 1000.0


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


cg, massa_cg = cg_com(RHO_COMP)
LOG["cg_conjunto_mm"] = [round(v, 1) for v in cg]
LOG["massa_conjunto_cg_kg"] = round(massa_cg, 2)
h, dmin, ang_tomb, dentro = estabilidade(rodizios, cg)
LOG["poligono_apoio"] = [[round(x, 1), round(y, 1)] for x, y in h]
LOG["cg_dentro_do_poligono"] = dentro
LOG["margem_tombamento_mm"] = round(dmin, 1)
LOG["tombamento_graus"] = round(ang_tomb, 2)
LOG["comparacao_passo1b"] = {"margem_mm": 179.9, "graus": 11.62}
LOG["perda_margem_mm"] = round(179.9 - dmin, 1)
LOG["perda_angulo_graus"] = round(11.62 - ang_tomb, 2)
if not dentro:
    faltas.append("CG fora do poligono de apoio")

LOG["sensibilidade_compensado"] = []
for r in RHO_COMP_SENS:
    cgs, ms = cg_com(r)
    _, dm, ag, dn = estabilidade(rodizios, cgs)
    LOG["sensibilidade_compensado"].append({
        "rho_kg_m3": r, "massa_total_kg": round(ms, 2),
        "cg_z_mm": round(cgs[2], 1), "margem_mm": round(dm, 1),
        "tombamento_graus": round(ag, 2), "cg_dentro": dn})

LOG["faltas_ate_aqui"] = list(faltas)

# ============================================================
# 6. GRUPOS AUXILIARES (so' entram nas vistas deles: fora da massa, do CG,
#    das verificacoes de interferencia e do STEP)
# ============================================================
import TechDraw                                     # noqa: E402
import Import                                       # noqa: E402

aux = []
di1, ni1 = DIR[0], NI[0]                            # folha 1: di = +X, ni = +Y
face_a1 = desl(P[0], TUBO, di1)
z_aba1 = ABA_ALTURAS[0]

# --- placa do painel (peca plana), no plano XZ, para a vista "Compensado" ---
aux.append(cl.caixa(doc, "plano_compensado", (0.0, 0.0, 0.0), COMP_L, COMP_T, COMP_H))
doc.recompute()

# ============================================================
# 7. VISTAS
# ============================================================
prj = cl.Projetor(doc, template="A3")
DIRF = (-math.sin(math.radians(GIRO)), math.cos(math.radians(GIRO)), 0.0)
XF = (-math.cos(math.radians(GIRO)), -math.sin(math.radians(GIRO)), 0.0)

VS = {}
# Frente: perpendicular a' folha central, do lado concavo (vista simetrica do conjunto)
VS["Frente"] = prj.vista("Frente", pecas, DIRF, XF, med["centro"], centrar_no_conteudo=True)
# Lateral: paralela a's folhas das pontas. Mesma definicao de direcao do passo 1b, que fecha
# 1357,5 x 1706 (a vista pelo lado +Y nao devolve aresta da roda, ver relatorio do 1b).
VS["Lateral"] = prj.vista("Lateral", pecas, (0.0, -1.0, 0.0), (1.0, 0.0, 0.0),
                          med["centro"], centrar_no_conteudo=True)
# Placa do painel (peca plana), vista de frente para o desenho de corte da placa
VS["Compensado"] = prj.vista("Compensado", [a for a in aux if a.Name.startswith("plano_")],
                             (0.0, -1.0, 0.0), (1.0, 0.0, 0.0),
                             (COMP_L / 2.0, COMP_T / 2.0, COMP_H / 2.0),
                             centrar_no_conteudo=True)
# assinatura da vista da placa: X para a direita, Z para cima (auditoria de vista espelhada)
base_cp = Vector(COMP_L / 2.0, COMP_T / 2.0, COMP_H / 2.0)
vcp = VS["Compensado"]["v"]
pp0cp = vcp.projectPoint(base_cp)
sig_cp = {}
for k, ax in (("x", Vector(1, 0, 0)), ("y", Vector(0, 1, 0)), ("z", Vector(0, 0, 1))):
    q = vcp.projectPoint(base_cp + ax * 100.0)
    sig_cp[k] = (round((q.x - pp0cp.x) / 100.0), round((q.y - pp0cp.y) / 100.0))
LOG["assinatura_compensado"] = {k: list(v) for k, v in sig_cp.items()}
if sig_cp["x"] != (1, 0) or sig_cp["z"] != (0, 1):
    faltas.append(f"Compensado com eixos trocados: {sig_cp}")
# Topo (planta): vista de cima, para destacar o angulo de 120 graus entre as folhas
VS["Topo"] = prj.vista("Topo", pecas, (0.0, 0.0, -1.0), (1.0, 0.0, 0.0), med["centro"],
                       centrar_no_conteudo=True)
for nome, v in VS.items():
    LOG[f"vista_{nome}"] = {"visiveis": len(v["vis"]), "ocultas": len(v["hid"]),
                            "ext_mm": [round(v["w"], 1), round(v["h"], 1)],
                            "alertas": v["alertas"]}
    faltas += [f"{nome}: {al}" for al in v["alertas"]]
    if len(v["vis"]) < 4:
        faltas.append(f"{nome}: poucas arestas visiveis ({len(v['vis'])})")

# ============================================================
# 8. FOLHA A3 — duas linhas: (isometrica, frente, lateral) e (compensado decorado, lista)
#
# Texto curto e zona fixa para cada bloco: f.colisoes() reprova texto sobre texto, que e'
# o defeito que a auditoria por tinta nao ve.
# ============================================================
ESC_FR, ESC_LA, ESC_CP, ESC_TP = 1 / 25.0, 1 / 25.0, 1 / 20.0, 1 / 25.0
f = cl.Folha(os.path.join(SAIDA, "passo2_prancha.pdf"), "A3")
f.moldura()

# cores de material: as mesmas do render isometrico e da legenda
COR_METAL = (0.84, 0.86, 0.88)      # metalon, cinza claro
COR_COMP = (0.98, 0.94, 0.62)       # compensado, amarelo claro
COR_ABA = (0.68, 0.80, 0.95)        # cantoneira, azul claro


def preenche(pts, cor):
    """Preenche um poligono em mm de folha, ANTES de Folha.desenha(): aresta fica por cima."""
    p = f.c.beginPath()
    p.moveTo(pts[0][0] * f.MM, pts[0][1] * f.MM)
    for q in pts[1:]:
        p.lineTo(q[0] * f.MM, q[1] * f.MM)
    p.close()
    f.c.setFillColorRGB(*cor)
    f.c.drawPath(p, stroke=0, fill=1)


V = {}
# ordem e espacamento: 4 vistas na metade de cima, com FOLGA IGUAL entre elas (o vazio todo
# a' esquerda era o defeito de distribuicao); 3 blocos na metade de baixo.
V["Iso"] = None                                                 # definida mais abaixo (recorte)
V["Frente"] = f.poe(VS["Frente"], 124.2, 205.0, ESC_FR)          # 124,2..197,2 x 205..273,2
V["Lateral"] = f.poe(VS["Lateral"], 240.6, 205.0, ESC_LA)        # 240,6..295,1 x 205..273,2
V["Topo"] = f.poe(VS["Topo"], 338.5, 205.0, ESC_TP)              # 338,5..393,0 x 205..269,1
V["Compensado"] = f.poe(VS["Compensado"], 28.0, 100.0, ESC_CP)   # 28..69,7   x 100..176,7
# --- isometrica: recorta o modelo no render e alinha a BASE dele com a base das vistas ---
# O render vem com margem de fundo e chao, entao o modelo flutuava alto dentro da moldura.
# O recorte usa as cores do render: fundo (canto) e chao (cor mais comum que nao o fundo).
ISO_PNG = os.path.join(SAIDA, "passo2_render_iso.png")
ISO_DESENHO = ISO_PNG
ISO_H = (Z1 - med["min"][2]) / 25.0                 # altura do modelo em 1:25 = 68,24 mm
ISO_W = 108.0
try:
    import tempfile
    from PIL import Image as _Im
    _im = _Im.open(ISO_PNG).convert("RGB")
    _w, _h = _im.size
    _px = _im.load()
    _fundo = _px[2, 2]
    _conta = {}
    for _j in range(0, _h, 4):
        for _i in range(0, _w, 4):
            _conta[_px[_i, _j]] = _conta.get(_px[_i, _j], 0) + 1
    _chao = max((c for c in _conta if sum(abs(c[k] - _fundo[k]) for k in range(3)) > 24),
                key=lambda c: _conta[c])

    def _obj(_p):
        return (sum(abs(_p[k] - _fundo[k]) for k in range(3)) > 30
                and sum(abs(_p[k] - _chao[k]) for k in range(3)) > 30)

    _lin = [_j for _j in range(_h) if any(_obj(_px[_i, _j]) for _i in range(0, _w, 3))]
    _col = [_i for _i in range(_w) if any(_obj(_px[_i, _j]) for _j in range(0, _h, 3))]
    _topo, _base = min(_lin), max(_lin)
    _e0, _e1 = min(_col), max(_col)
    _ml = int(0.03 * (_e1 - _e0))                   # margem de 3%
    _crop = (_e0 - _ml, _topo - _ml, _e1 + _ml, _base + _ml)
    _rec = _im.crop(_crop)
    ISO_DESENHO = os.path.join(tempfile.mkdtemp(), "iso_recorte.png")
    _rec.save(ISO_DESENHO)
    ISO_W = min(118.0, ISO_H * _rec.size[0] / float(_rec.size[1]))
    LOG["iso_recorte_px"] = {"topo": _topo, "base": _base, "esq": _e0, "dir": _e1,
                             "crop": list(_crop), "recorte_mm": [round(ISO_W, 1), round(ISO_H, 1)]}
    LOG["iso_cores_px"] = {"fundo": list(_fundo), "chao": list(_chao)}
except Exception as _e:
    LOG["iso_recorte_px"] = "sem recorte: " + repr(_e)[:70]
if not os.path.exists(ISO_PNG):
    faltas.append("render isometrico ausente: rode scripts/render_3d.py antes da prancha")
V["Iso"] = f.poe({"nome": "Iso", "vis": [], "hid": [], "w": ISO_W, "h": ISO_H,
                  "loc": [0.0, 0.0], "alertas": []}, 20.0, 205.0, 1.0)

def pm(i, di_off, ni_off, z):
    """Ponto no referencial da folha i: di_off ao longo de di desde P[i], ni_off ao longo
    da normal, z absoluto."""
    return (P[i][0] + di_off * DIR[i][0] + ni_off * NI[i][0],
            P[i][1] + di_off * DIR[i][1] + ni_off * NI[i][1], z)


def pinta_ret(vista, i, d0, d1, z0, z1, cor):
    """Preenche o retangulo (di, z) do referencial da folha i na vista dada."""
    preenche([f.para_folha(vista, *pm(i, d0, 0.0, z0)),
              f.para_folha(vista, *pm(i, d1, 0.0, z0)),
              f.para_folha(vista, *pm(i, d1, 0.0, z1)),
              f.para_folha(vista, *pm(i, d0, 0.0, z1))], cor)


# (sem preenchimento de material: o usuario mandou tirar as cores -- davam trabalho para
#  acertar e nao acrescentavam para a serralheria. O que vale aqui e' linha + cota.)
Z_PLACA0 = Z0 + TUBO + FOLGA_COMP
D_PLACA0 = TUBO + FOLGA_COMP                                    # 33: offset do compensado

f.desenha()
for n, t in (("Frente", "FRENTE (1:25), folha central de face"),
             ("Lateral", "LATERAL (1:25), folhas das pontas de face"),
             ("Topo", "TOPO (1:25), vista de cima"),
             ("Compensado", "COMPENSADO DECORADO (1:20) - 1 por folha"),
             ("Iso", "ISOMETRICA (1:25, mesma escala das vistas)")):
    v = V[n]
    f.texto(v["px"], v["py"] + v["fh"] + 3.0, t, 8, negrito=True)
f.c.drawImage(ISO_DESENHO, V["Iso"]["px"] * f.MM, V["Iso"]["py"] * f.MM,
              ISO_W * f.MM, ISO_H * f.MM)
# moldura da imagem: da' acabamento e faz a auditoria de tinta enxergar o bloco (as linhas
# finas do render somem no threshold de 150 dpi)
f.retangulo(V["Iso"]["px"], V["Iso"]["py"], ISO_W, ISO_H, 0.5)

# --- placa: posicao dos 4 furos de parafuso (furo piloto dia 2,5) ---
for _d in (TUBO + ABA_FURO_ATE_FACE, FOLHA_W - TUBO - ABA_FURO_ATE_FACE):
    for _z in ABA_ALTURAS:
        _p = f.para_folha("Compensado", _d - D_PLACA0, COMP_T / 2.0, _z - Z_PLACA0)
        f.linha(_p[0] - 2.0, _p[1], _p[0] + 2.0, _p[1], 0.5, None)
        f.linha(_p[0], _p[1] - 2.0, _p[0], _p[1] + 2.0, 0.5, None)
f.texto(28.0, 88.0, "x = centro dos 4 furos de parafuso (piloto dia 2,5), a 12 mm da", 6.5)
f.texto(28.0, 83.5, "borda da placa, nas alturas Z0+200 e Z0+1340", 6.5)

# --- fixacao e ordem de montagem (a ordem e' a do usuario: estofa a placa ANTES de montar) ---
for _k, _s in enumerate((
        "FIXACAO E MONTAGEM",
        "4 cantoneiras 25x25x3 por folha, soldadas de face na face interna dos montantes,",
        "em Z0+200 e Z0+1340 (2 por montante): perna A (22,5) soldada no tubo, perna B (25)",
        "deitada sobre a face do compensado, furo dia 4,2 a 15 mm da face interna.",
        "Parafuso de madeira dia 4 x 16 (piloto dia 2,5): atravessa a perna B e entra",
        "13 mm no compensado, com 2 mm de fundo.",
        "ORDEM: 1) soldar as cantoneiras. 2) colar o acabamento na placa (espuma 3 + tecido",
        "1 por face, opcional) e estofar. 3) encaixar a placa na moldura.",
        "4) aparafusar: o parafuso pega a cantoneira, o acabamento e o compensado.",
        "COM acabamento: soldar a cantoneira encostada no painel JA montado (face interna",
        "da perna B a 11,5 mm do plano medio) e usar parafuso dia 4 x 20.")):
    f.texto(272.0, 178.0 - _k * 4.5, _s, 8 if _k == 0 else 6.5, negrito=(_k == 0))

# --- cotas ---
xmin, ymin, zmin = med["min"]
xmax, ymax, zmax = med["max"]
f.cota_h("Frente", (P[0][0], P[0][1], zmin), (P[3][0], P[3][1], zmin), 7.0,
         f"{VS['Frente']['w']:.0f} total")
f.cota_v("Frente", (P[0][0], P[0][1], zmin), (P[0][0], P[0][1], zmax), 8.0,
         f"{zmax - zmin:.0f} total")
f.cota_v("Frente", (P[0][0], P[0][1], Z0), (P[0][0], P[0][1], Z1), 18.0, "1600 quadro")
f.cota_v("Frente", (P[3][0], P[3][1], zmin), (P[3][0], P[3][1], Z0), -8.0,
         f"{Z0:.0f} rodizio+chapa")
f.cota_h("Lateral", (xmin, ymin, zmin), (xmax, ymin, zmin), 7.0, f"{xmax - xmin:.0f} total")
f.cota_v("Lateral", (xmin, ymin, zmin), (xmin, ymin, zmax), -8.0, f"{zmax - zmin:.0f} total")
# placa: largura embaixo, altura a' direita
f.cota_h("Compensado", (0.0, 0.0, 0.0), (COMP_L, 0.0, 0.0), 7.0, f"{COMP_L:.0f}")
f.cota_v("Compensado", (0.0, 0.0, 0.0), (0.0, 0.0, COMP_H), -8.0, f"{COMP_H:.0f}")
# TOPO: largura total, profundidade, e o angulo entre as folhas em destaque, escrito junto
# do vertice (foi o motivo de entrar a vista de topo: os 120 graus sao o nucleo do projeto)
f.cota_h("Topo", (xmin, ymin, 0.0), (xmax, ymin, 0.0), 7.0, f"{xmax - xmin:.0f} total")
f.cota_v("Topo", (xmin, ymin, 0.0), (xmin, ymax, 0.0), 14.0, f"{ymax - ymin:.0f} profundidade")
for _k, _pt in enumerate((P[1], P[2])):
    _p = f.para_folha("Topo", _pt[0], _pt[1], 0.0)
    f.linha(_p[0] - 1.5, _p[1], _p[0] + 1.5, _p[1], 0.4)
    f.linha(_p[0], _p[1] - 1.5, _p[0], _p[1] + 1.5, 0.4)
    f.texto(_p[0], _p[1] - 5.5, f"{LOG['angulos_internos'][_k]:.0f} graus", 9, negrito=True,
            centro=True)

# ============================================================
# 9. LISTAS, CARIMBO, AUDITORIA DA FOLHA
# ============================================================
resumo = {}
for nome, c in cortes:
    resumo.setdefault((nome, round(c)), 0)
    resumo[(nome, round(c))] += 1
linhas = [f"{n:<11s} 30x30x1,5    {c:>5d} mm    {q}" for (n, c), q in sorted(resumo.items())]
linhas.append(f"{'TOTAL tubo':<11s} {'':<11s} {comp_total:>5.0f} mm    {len(cortes)}")
linhas.append(f"{'chapa base':<11s} 100x70x4    400 mm    {n_chapas}   4 rasgos 25x9 passo 70x40")
linhas.append(f"{'cantoneira':<11s} L 25x25x3   perna A 22,5 {len(abas)}   2 por montante, Z0+200 e Z0+1340")
linhas.append(f"{'compensado':<11s} decorado 15 {COMP_L:>5.0f} mm    {LOG['n_paineis']}   "
              f"({COMP_L:.0f} x {COMP_H:.0f} mm), 1 por folha")
linhas.append(f"{'parafuso':<11s} madeira 4x16  16 mm    {len(abas)}   piloto 2,5; cabeca panela 8")
linhas.append(f"{'rodizio':<11s} dia 75 freio  102 mm    4   roda de borracha, placa 91,5x60")
linhas.append(f"{'acabamento':<11s} OPCIONAL      3+1 mm    -   espuma 3 mm e tecido <1 mm nas 2 faces")
f.lista_corte("LISTA DE MATERIAL", "peca        especificacao medida      qtd",
              linhas, 128.0, 178.0, passo=4.4)

f.carimbo([
    ("Habitat / LaRA-UERJ", 10, True),
    ("BIOMBO 120  -  PASSO 2: PLACA DE COMPENSADO DECORADO", 8, True),
    (f"Placa {COMP_L:.0f} x {COMP_H:.0f} x {COMP_T:.0f} mm fixada por 12 cantoneiras 25x25x3; "
     "rodizio dia 75 com freio", 6.5, False),
    ("Cantoneira: perna A 22,5 soldada de face no montante + perna B deitada no compensado",
     6.5, False),
    (f"Fabricado {LOG['massa_total_fabricada_kg']} kg (tubo {LOG['massa_por_kit_kg']['tubo']} + "
     f"placa {LOG['massa_por_kit_kg']['compensado']} + abas {LOG['massa_por_kit_kg']['abas']}) | "
     f"carga/rodizio {LOG['carga_por_rodizio_kg']} kg", 6.5, False),
    (f"Tombamento {LOG['margem_tombamento_mm']} mm -> {LOG['tombamento_graus']} graus "
     f"(1b: 179,9 / 11,62) | A3 1o diedro  mm | Rev. 04  2026-09-18", 6.5, False),
])

caixas = {n: (v["px"], v["py"], v["px"] + v["fw"], v["py"] + v["fh"]) for n, v in f.vistas.items()}
CARIMBO_MM = (273.0, 12.0, 408.0, 54.0)
for i, a in enumerate(caixas):
    for b in list(caixas)[i + 1:]:
        A, B = caixas[a], caixas[b]
        if not (A[2] <= B[0] or A[0] >= B[2] or A[3] <= B[1] or A[1] >= B[3]):
            faltas.append(f"{a} e {b} se sobrepoem na folha")
for n, A in caixas.items():
    if not (A[2] <= CARIMBO_MM[0] or A[0] >= CARIMBO_MM[2] or A[3] <= CARIMBO_MM[1]
            or A[1] >= CARIMBO_MM[3]):
        faltas.append(f"{n} invade o carimbo")

ocupadas = list(caixas.values()) + [CARIMBO_MM]
for x0, y0, x1, y1 in ((24.0, 76.0, 112.0, 182.0),       # placa: vista, cota e notas
                       (124.0, 112.0, 240.0, 182.0),     # lista de material
                       (268.0, 126.0, 372.0, 182.0)):    # fixacao e ordem de montagem
    ocupadas.append((x0, y0, x1, y1))


def vazio(x0, y0, x1, y1, mm=2.0):
    for a in ocupadas:
        if not (x1 + mm <= a[0] or x0 - mm >= a[2] or y1 + mm <= a[1] or y0 - mm >= a[3]):
            return False
    return True


cands = []
for xi in range(14, 400, 12):
    for xj in range(xi + 40, 408, 12):
        for yi in range(14, 280, 12):
            for yj in range(yi + 30, 288, 12):
                if vazio(xi, yi, xj, yj):
                    cands.append((float(xj - xi) * float(yj - yi), xi, yi, xj, yj))
cands.sort(reverse=True)
escolhidas = []
for a, x0, y0, x1, y1 in cands:
    if all(x1 <= b[0] or x0 >= b[2] or y1 <= b[1] or y0 >= b[3] for b in escolhidas):
        escolhidas.append((x0, y0, x1, y1))
    if len(escolhidas) >= 3:
        break
LOG["regioes_vazias_mm"] = {f"vazio{i+1}": [float(x) for x in b]
                            for i, b in enumerate(escolhidas)}
LOG["carimbo_mm"] = list(CARIMBO_MM)
LOG["caixas_na_folha"] = {n: [round(x, 1) for x in b] for n, b in caixas.items()}
LOG["area_util_ocupada_pct"] = round(
    100.0 * sum((c[2] - c[0]) * (c[3] - c[1]) for c in caixas.values())
    / ((408.0 - 12.0) * (287.0 - 12.0)), 1)
LOG["escalas"] = {"Frente": 25, "Lateral": 25, "Topo": 25, "Compensado": 20,
                  "Iso": "1:25 (render recortado no modelo, base alinhada)"}

# colisao de texto: o retangulo real de cada texto contra todos os outros. E' o que pega
# o defeito de layout que a auditoria por tinta nao ve (texto em cima de texto).
faltas += f.colisoes()
LOG["textos_conferidos"] = len(f.textos)
LOG["textos_na_folha"] = [[round(v, 2) for v in t[:4]] + [t[4]] for t in f.textos]

problemas = f.salva()
LOG["prancha_pdf_bytes"] = os.path.getsize(os.path.join(SAIDA, "passo2_prancha.pdf"))

# ============================================================
# 10. DXF, STEP, CSV, RELATORIO
# ============================================================
for v in f.vistas.values():
    if "v" not in v:                      # a pseudo-vista "Iso" e' so' uma caixa (imagem PNG)
        continue
    v["v"].Scale = v["escala"]
    v["v"].X = v["px"] + v["fw"] / 2.0
    v["v"].Y = v["py"] + v["fh"] / 2.0
doc.recompute()

# o FCStd guarda TAMBEM os grupos auxiliares: o DXF so' sai correto depois de
# salvar e reabrir o documento (pitfall do writeDXFPage, ver cad-workflow.md)
fcstd = os.path.join(SAIDA, "passo2_biombo.FCStd")
doc.saveAs(fcstd)
nome_doc = doc.Name
App.closeDocument(nome_doc)
doc2 = App.openDocument(fcstd)

try:
    pg2 = [o for o in doc2.Objects if o.TypeId == "TechDraw::DrawPage"][0]
    dxf = os.path.join(SAIDA, "passo2_prancha.dxf")
    TechDraw.writeDXFPage(pg2, dxf)
    LOG["dxf_bytes"] = os.path.getsize(dxf)
except Exception as e:
    problemas.append("DXF: " + repr(e)[:120])

# STEP: so' as pecas do conjunto (auxiliares corte_/expl_/plano_ ficam fora)
prefixos_aux = ("corte_", "expl_", "plano_", "chao")
main2 = [o for o in doc2.Objects if o.TypeId == "Part::Feature"
         and not o.Name.startswith(prefixos_aux)]
try:
    stp = os.path.join(SAIDA, "passo2_biombo.step")
    Import.export(main2, stp)
    LOG["step_bytes"] = os.path.getsize(stp)
    LOG["step_pecas"] = len(main2)
    LOG["step_auxiliares_excluidos"] = len([o for o in doc2.Objects
                                            if o.TypeId == "Part::Feature"]) - len(main2)
except Exception as e:
    problemas.append("STEP: " + repr(e)[:120])

# o FCStd fica SEM os auxiliares (eles existiram so' para as vistas): assim o
# render 3D mostra o conjunto montado, e nao as copias explodidas/planas
try:
    removidos = 0
    for o in list(doc2.Objects):
        if o.TypeId == "Part::Feature" and o.Name.startswith(prefixos_aux):
            doc2.removeObject(o.Name)
            removidos += 1
    # Vista que projetava peca auxiliar fica com Source vazio e o FCStd abre cuspindo
    # "DVP::execute - <vista> - Source shape is Null". O DXF ja' foi escrito antes, entao
    # remover a vista vazia agora nao mexe no que foi entregue -- so' limpa o FCStd.
    vistas_vazias = [o.Name for o in doc2.Objects
                     if o.TypeId == "TechDraw::DrawViewPart" and not list(o.Source)]
    for n in vistas_vazias:
        doc2.removeObject(n)
    LOG["fcstd_vistas_vazias_removidas"] = vistas_vazias
    doc2.recompute()
    doc2.saveAs(fcstd)
    LOG["fcstd_auxiliares_removidos"] = removidos
    # confere reabrindo: o FCStd do render nao pode ter auxiliar nenhum
    App.closeDocument(doc2.Name)
    doc3 = App.openDocument(fcstd)
    restantes = [o.Name for o in doc3.Objects if o.TypeId == "Part::Feature"
                 and o.Name.startswith(prefixos_aux)]
    LOG["fcstd_auxiliares_reabertos"] = len(restantes)
    LOG["fcstd_pecas_para_render"] = len([o for o in doc3.Objects
                                          if o.TypeId == "Part::Feature"])
    if restantes:
        faltas.append(f"FCStd ainda com auxiliares: {restantes}")
    LOG["fcstd_bytes"] = os.path.getsize(fcstd)
except Exception as e:
    problemas.append("FCStd final: " + repr(e)[:160])

with open(os.path.join(SAIDA, "passo2_lista_corte.csv"), "w", newline="") as fh:
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
    w.writerow(["cantoneira", "chapa aco dobrada 3 mm", ABA_H, len(abas),
                f"CANTONEIRA 25x25x3, perna A {ABA_U_A[1]-ABA_U_A[0]:.1f} x {ABA_H:.0f} "
                f"soldada DE FACE na face interna do montante, perna B {ABA_V_B[1]:.0f} deitada "
                f"sobre o compensado; furo dia {ABA_FURO_D:.1f} a "
                f"{ABA_FURO_ATE_FACE:.0f} mm da face interna; 4 por folha "
                f"(Z0+200 e Z0+1340)"])
    w.writerow(["compensado", "placa decorada 15 mm", COMP_L, LOG["n_paineis"],
                f"{COMP_L:.0f}x{COMP_H:.0f}x{COMP_T:.0f} mm; 3 mm de folga ao tubo em todo o "
                f"contorno ({COMP_L:.0f} no vao de 840); decorada, acabamento opcional"])
    w.writerow(["acabamento", f"espuma {ACAB_ESPUMA_T:.0f} mm + tecido <1 mm", COMP_L,
                LOG["n_paineis"] * 2,
                "OPCIONAL, nao modelado; uma por face; se aplicado, soldar a aba com o painel "
                f"montado e usar parafuso dia {PARAF_D:.0f} x {PARAF_COMP_COM_ACAB:.0f}"])
    w.writerow(["parafuso", "madeira dia 4 x 16, cabeca panela dia 8",
                PARAF_COMP, len(parafusos),
                f"furo piloto dia {PARAF_PILOTO_D:.1f}; 3 mm na perna B + 13 mm no compensado "
                "(2 mm de fundo); 4 por folha"])

with open(os.path.join(SAIDA, "passo2_lista_compras.csv"), "w", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["item", "especificacao", "quantidade", "unidade", "observacao"])
    w.writerow(["compensado", "decorado 15 mm, 600 kg/m3", f"{3*COMP_L*COMP_H/1e6:.2f}", "m2",
                f"{LOG['n_paineis']} x {COMP_L:.0f}x{COMP_H:.0f} mm; "
                f"{LOG['massa_por_kit_kg']['compensado']:.1f} kg"])
    w.writerow(["parafuso", "madeira dia 4 x 16 cabeca panela dia 8", len(abas), "un",
                "aco zincado; 4 por folha"])
    w.writerow(["acabamento", "OPCIONAL: espuma 3 mm + tecido <1 mm",
                f"{2*3*COMP_L*COMP_H/1e6:.2f}", "m2",
                f"espuma {ACAB_ESPUMA_T:.0f} mm por face e tecido; so' se o estofamento for feito"])
    w.writerow(["cantoneira", "CANTONEIRA 25x25x3 (perna A cortada em 22,5)",
                len(abas), "un", "aco 1020; soldada de face nos montantes"])
    w.writerow(["metalon", "30x30x1,5", LOG["tubo_total_m"], "m",
                f"6 montantes de 1600 + 6 travessas de 840; {LOG['massa_tubo_kg']} kg"])
    w.writerow(["chapa_base", "100x70x4", n_chapas, "un",
                "4 rasgos oblongos 25x9 passo 70x40 (CONFERIR com o rodizio comprado)"])
    w.writerow(["rodizio", "moveleiro dia 75 com freio, altura 102, carga 70 kg",
                len(rodizios), "un", "roda de borracha, placa 91,5x60"])

LOG["problemas"] = problemas
LOG["faltas"] = faltas
LOG["verificacao_ok"] = not (problemas + faltas)
LOG["arquivos"] = {}
for n in ("passo2_prancha.pdf", "passo2_prancha.dxf", "passo2_biombo.step",
          "passo2_biombo.FCStd", "passo2_lista_corte.csv", "passo2_lista_compras.csv"):
    p = os.path.join(SAIDA, n)
    LOG["arquivos"][n] = os.path.getsize(p) if os.path.exists(p) else None
with open(os.path.join(SAIDA, "passo2_relatorio.json"), "w") as fh:
    json.dump(LOG, fh, indent=1, default=str)
print("PASSO2 OK: %d pecas | massa %.2f kg | CG %s | margem %.1f mm (%.2f graus) | "
      "carga/rodizio %.1f kg | faltas %d | problemas %d"
      % (len(pecas), LOG["massa_total_fabricada_kg"], LOG["cg_conjunto_mm"],
         LOG["margem_tombamento_mm"], LOG["tombamento_graus"],
         LOG["carga_por_rodizio_kg"], len(faltas), len(problemas)))
for x in faltas + problemas:
    print("FALHA> " + str(x))
for k in sorted(LOG["arquivos"]):
    print("ARQ> %s %s bytes" % (k, LOG["arquivos"][k]))
print("AUDITORIA> python3 scripts/auditar_prancha.py --relatorio %s"
      % os.path.join(SAIDA, "passo2_relatorio.json"))
print("RENDER> RENDER_FCSTD=%s RENDER_NOME=passo2_render xvfb-run -a freecad "
      "$PWD/scripts/render_3d.py" % fcstd)

