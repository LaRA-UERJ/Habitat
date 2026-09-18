"""cad_lib - desenho tecnico por codigo, headless (FreeCAD + reportlab).

Pipeline: solidos FreeCAD -> projecao TechDraw (HLR) -> folha vetorial cotada.

Convencoes do FreeCAD 1.1.1, todas verificadas empiricamente (nao confie na doc):
  * v.Direction = vetor do OBJETO para o OBSERVADOR. v.XDirection e' o eixo
    horizontal da vista e TEM de ser perpendicular a Direction, senao a vista
    falha com "failed to create projection CS" e sai vazia.
  * direita = XDirection normalizado;  cima = Direction x XDirection.
      Frente  D=(0,-1,0) XD=(1,0,0)   direita=+X  cima=+Z
      Planta  D=(0,0,-1) XD=(1,0,0)   direita=+X  cima=-Y   (1o diedro, abaixo)
      Lateral D=(1,0,0)  XD=(0,1,0)   direita=+Y  cima=+Z   (1o diedro, a direita)
  * getVisibleEdges()/getHiddenEdges() devolvem coords 2D CENTRADAS no conteudo.
  * projectPoint() devolve coords ABSOLUTAS (p.direita, p.cima) -- os dois
    referenciais diferem; para_folha() faz a conversao.
  * TechDraw.writeDXFPage funciona e inclui DIMENSION/TEXT/SOLID; $INSUNITS=4 (mm).
  * TechDraw.writePageAsPdf NAO existe em 1.1.1 -> o PDF sai daqui, via reportlab.

Uso tipico:
    doc, med = modelo(...)            # voce monta os solidos
    prj = Projetor(doc)
    vs = {"Planta": prj.vista("Planta", objs, *DIRECOES["Planta"])}
    f = Folha("saida/prancha.pdf")
    f.moldura(); f.poe(vs["Planta"], 36, 40, 0.05); f.desenha()
    f.cota_h(vs["Planta"], "largura", 0, 1366, 0, 7, "1366")
    f.carimbo([...]); f.salva()
"""

import math
import os
import Part
import FreeCAD as App
from FreeCAD import Vector

TEMPLATES = {
    "A4": "/usr/share/freecad/Mod/TechDraw/Templates/ISO/A4_Landscape_TD.svg",
    "A3": "/usr/share/freecad/Mod/TechDraw/Templates/ISO/A3_Landscape_TD.svg",
}

# direcao / xdirection de cada vista, na convencao de 1o diedro (ABNT)
DIRECOES = {
    "Frente":  (Vector(0, -1, 0), Vector(1, 0, 0)),
    "Planta":  (Vector(0, 0, -1), Vector(1, 0, 0)),
    "Lateral": (Vector(1, 0, 0),  Vector(0, 1, 0)),
    "Posterior": (Vector(0, 1, 0), Vector(-1, 0, 0)),
    "Iso":     (Vector(1, -1, 1), Vector(1, 1, 0)),
}

# assinatura esperada (direita, cima) por eixo do modelo, para auditoria
ASSINATURA = {
    "Frente":  {"x": (1, 0), "y": (0, 0), "z": (0, 1)},
    "Planta":  {"x": (1, 0), "y": (0, -1), "z": (0, 0)},
    "Lateral": {"x": (0, 0), "y": (1, 0), "z": (0, 1)},
}


# ============================================================
# 1. SOLIDOS
# ============================================================
def novo_doc(nome="Modelo"):
    return App.newDocument(nome)


def solido(doc, nome, shp):
    o = doc.addObject("Part::Feature", nome)
    o.Shape = shp
    return o


def caixa(doc, nome, base, L, W, H):
    """Caixa alinhada aos eixos, canto em 'base'."""
    return solido(doc, nome, Part.makeBox(L, W, H, Vector(*[float(v) for v in base])))


def caixa_orientada(doc, nome, centro_xy, ang_deg, L, W, H, z_base):
    """Caixa centrada em centro_xy no plano XY, girada ang_deg em Z, de z_base para cima."""
    shp = Part.makeBox(L, W, H, Vector(-L / 2.0, -W / 2.0, 0.0))
    shp.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang_deg)
    shp.translate(Vector(centro_xy[0], centro_xy[1], z_base))
    return solido(doc, nome, shp)


def cilindro(doc, nome, centro, ang_deg, dia, comprimento):
    """Cilindro de eixo HORIZONTAL, perpendicular a direcao ang_deg, centrado em centro (3D)."""
    shp = Part.makeCylinder(dia / 2.0, comprimento,
                            Vector(0, -comprimento / 2.0, 0), Vector(0, 1, 0))
    shp.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang_deg)
    shp.translate(Vector(*[float(v) for v in centro]))
    return solido(doc, nome, shp)


def barra(doc, nome, p1, p2, sec):
    """Barra reta de secao quadrada 'sec' CENTRADA no eixo p1->p2."""
    a, b = Vector(*[float(v) for v in p1]), Vector(*[float(v) for v in p2])
    d = b - a
    comp = d.Length
    if comp < 1e-9:
        raise ValueError(f"{nome}: comprimento nulo")
    if abs(d.x) < 1e-9 and abs(d.y) < 1e-9:          # vertical
        lo = min(a.z, b.z)
        return solido(doc, nome, Part.makeBox(sec, sec, comp,
                                              Vector(a.x - sec / 2, a.y - sec / 2, lo)))
    ang = math.degrees(math.atan2(d.y, d.x))
    shp = Part.makeBox(comp, sec, sec, Vector(0, -sec / 2.0, -sec / 2.0))
    shp.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang)
    shp.translate(a)
    return solido(doc, nome, shp)


def medir(objs):
    """bbox, volume e massa (com densidade opcional) do conjunto."""
    bb = [min(o.Shape.BoundBox.XMin for o in objs),
          min(o.Shape.BoundBox.YMin for o in objs),
          min(o.Shape.BoundBox.ZMin for o in objs)]
    bx = [max(o.Shape.BoundBox.XMax for o in objs),
          max(o.Shape.BoundBox.YMax for o in objs),
          max(o.Shape.BoundBox.ZMax for o in objs)]
    return {"min": bb, "max": bx,
            "centro": [(bb[i] + bx[i]) / 2.0 for i in range(3)],
            "volume_mm3": sum(o.Shape.Volume for o in objs)}


# ============================================================
# 2. PROJECAO
# ============================================================
class Projetor:
    def __init__(self, doc, template="A3"):
        self.doc = doc
        self.page = doc.addObject("TechDraw::DrawPage", "Prancha")
        t = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        t.Template = TEMPLATES[template]
        self.page.Template = t
        doc.recompute()

    def _segs(self, v, metodo):
        out = []
        try:
            edges = getattr(v, metodo)()
        except Exception:
            return out
        for e in edges:
            try:
                a, b = e.valueAt(e.FirstParameter), e.valueAt(e.LastParameter)
            except Exception:
                vs = e.Vertexes
                if len(vs) < 2:
                    continue
                a, b = vs[0].Point, vs[-1].Point
            if (a - b).Length > 1e-6:
                out.append(((a.x, a.y), (b.x, b.y)))
        return out

    def _centro_conteudo(self, v, objs):
        """Centro do CONTEUDO projetado (2D), medido amostrando vertices e arestas curvas.

        Necessario porque `para_folha` converte projectPoint -> folha usando esse offset.
        Em vista alinhada aos eixos o centro do conteudo coincide com a projecao do centro
        do bbox 3D; em vista OBLIQUA (ex.: perpendicular a uma folha a 60 graus) nao
        coincide, e a cota ancora fora da vista. Ver docs/cad-workflow.md.
        """
        xs, ys = [], []
        for o in objs:
            for vtx in o.Shape.Vertexes:
                q = v.projectPoint(vtx.Point)
                xs.append(q.x)
                ys.append(q.y)
            for e in o.Shape.Edges:
                if isinstance(e.Curve, Part.Line):
                    continue
                t0, t1 = e.FirstParameter, e.LastParameter
                for k in range(17):
                    q = v.projectPoint(e.valueAt(t0 + (t1 - t0) * k / 16.0))
                    xs.append(q.x)
                    ys.append(q.y)
        if not xs:
            return None
        return Vector((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, 0.0)

    def vista(self, nome, objs, direction, xdirection, centro_modelo, ocultas=True,
              centrar_no_conteudo=False):
        v = self.doc.addObject("TechDraw::DrawViewPart", nome)
        v.Source = objs
        v.Direction = direction
        v.XDirection = xdirection
        # ocultas: no 1.1 headless NAO existe ShowHiddenLines; quem manda e' HardHidden
        # (padrao False). SmoothHidden cobre as arestas de tangencia dos cilindros.
        if ocultas:
            for prop, val in (("HardHidden", True), ("SmoothHidden", True),
                              ("SeamHidden", False)):
                try:
                    setattr(v, prop, val)
                except Exception:
                    pass
        self.page.addView(v)
        self.doc.recompute()

        vis = self._segs(v, "getVisibleEdges")
        hid = self._segs(v, "getHiddenEdges")
        pts = [p for s in vis + hid for p in s]
        if not pts:
            raise RuntimeError(f"vista {nome}: projecao vazia (XDirection invalido?)")
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)

        pp0 = v.projectPoint(Vector(*centro_modelo))
        if centrar_no_conteudo:
            c2 = self._centro_conteudo(v, objs)
            if c2 is not None:
                pp0 = c2
        alertas = []
        # cross-check entre os DOIS referenciais (edges = local, projectPoint = absoluto):
        # a projecao do bbox do modelo tem de conter o conteudo local.
        bx0 = min(o.Shape.BoundBox.XMin for o in objs)
        by0 = min(o.Shape.BoundBox.YMin for o in objs)
        bz0 = min(o.Shape.BoundBox.ZMin for o in objs)
        bx1 = max(o.Shape.BoundBox.XMax for o in objs)
        by1 = max(o.Shape.BoundBox.YMax for o in objs)
        bz1 = max(o.Shape.BoundBox.ZMax for o in objs)
        cantos = [Vector(x, y, z) for x in (bx0, bx1) for y in (by0, by1) for z in (bz0, bz1)]
        pcs = [v.projectPoint(c) for c in cantos]
        ex = (min(p.x for p in pcs) - pp0.x, max(p.x for p in pcs) - pp0.x)
        ey = (min(p.y for p in pcs) - pp0.y, max(p.y for p in pcs) - pp0.y)
        tol = 1.0
        if not (ex[0] - tol <= x0 and x1 <= ex[1] + tol and
                ey[0] - tol <= y0 and y1 <= ey[1] + tol):
            alertas.append(f"{nome}: conteudo {x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f} fora da "
                           f"projecao do bbox {ex[0]:.1f},{ey[0]:.1f},{ex[1]:.1f},{ey[1]:.1f} "
                           "-> referenciais incompativeis")
        return {"nome": nome, "v": v, "vis": vis, "hid": hid, "pp0": pp0,
                "loc": (x0, y0, x1, y1), "w": x1 - x0, "h": y1 - y0,
                "alertas": alertas}


# ============================================================
# 3. FOLHA
# ============================================================
class Folha:
    from reportlab.lib.pagesizes import A3, A4, landscape as _land

    PAGE = {"A3": (420.0, 297.0), "A4": (297.0, 210.0)}

    def __init__(self, caminho, tamanho="A3", margem=10.0):
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import Color
        from reportlab.lib.units import mm as MM
        self.caminho = caminho
        self.MM = MM
        self.PRETO = Color(0.08, 0.08, 0.08)
        self.CINZA = Color(0.45, 0.45, 0.45)
        self.TRACO = Color(0.55, 0.55, 0.55)
        self.W, self.H = self.PAGE[tamanho]
        self.margem = margem
        self.i = (margem + 2, margem + 2, self.W - margem - 2, self.H - margem - 2)
        os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
        self.c = canvas.Canvas(caminho, pagesize=(self.W * MM, self.H * MM))
        self.vistas = {}      # nome -> dict de vista + posicao
        self.tinta = []       # (x, y) mm de tudo desenhado
        self.ancoras = []     # (vista, x, y) extremidades de cota
        self.problemas = []

    # ---- primitivas ----
    def linha(self, x1, y1, x2, y2, larg=0.5, cor=None, tracejado=None):
        self.c.setLineWidth(larg)
        self.c.setStrokeColor(cor or self.PRETO)
        if tracejado:
            self.c.setDash(*tracejado)
        self.c.line(x1 * self.MM, y1 * self.MM, x2 * self.MM, y2 * self.MM)
        if tracejado:
            self.c.setDash()
        self.tinta += [(x1, y1), (x2, y2)]

    def texto(self, x, y, s, tam=7, negrito=False, cor=None, centro=False, rot=0, fim=False):
        self.c.saveState()
        self.c.setFillColor(cor or self.PRETO)
        self.c.setFont("Helvetica-Bold" if negrito else "Helvetica", tam)
        if rot:
            self.c.translate(x * self.MM, y * self.MM)
            self.c.rotate(rot)
            (self.c.drawCentredString if centro else self.c.drawString)(0, 0, s)
        elif centro:
            self.c.drawCentredString(x * self.MM, y * self.MM, s)
        elif fim:
            self.c.drawRightString(x * self.MM, y * self.MM, s)
        else:
            self.c.drawString(x * self.MM, y * self.MM, s)
        self.c.restoreState()
        self.tinta.append((x, y))

    def retangulo(self, x, y, w, h, larg=0.6):
        self.c.setLineWidth(larg)
        self.c.setStrokeColor(self.PRETO)
        self.c.rect(x * self.MM, y * self.MM, w * self.MM, h * self.MM)
        self.tinta += [(x, y), (x + w, y + h)]

    def _seta(self, x, y, ang):
        L, W = 3.0, 1.0
        p = self.c.beginPath()
        p.moveTo(x * self.MM, y * self.MM)
        p.lineTo((x + L * math.cos(ang) + W * math.sin(ang)) * self.MM,
                 (y + L * math.sin(ang) - W * math.cos(ang)) * self.MM)
        p.lineTo((x + L * math.cos(ang) - W * math.sin(ang)) * self.MM,
                 (y + L * math.sin(ang) + W * math.cos(ang)) * self.MM)
        p.close()
        self.c.setFillColor(self.PRETO)
        self.c.drawPath(p, stroke=0, fill=1)

    # ---- moldura ----
    def moldura(self):
        x0, y0, x1, y1 = self.i
        self.c.setLineWidth(0.8)
        self.c.setStrokeColor(self.PRETO)
        self.c.rect(self.margem * self.MM, self.margem * self.MM,
                    (self.W - 2 * self.margem) * self.MM,
                    (self.H - 2 * self.margem) * self.MM)
        self.c.setLineWidth(0.3)
        self.c.rect(x0 * self.MM, y0 * self.MM, (x1 - x0) * self.MM, (y1 - y0) * self.MM)
        self.tinta += [(x0, y0), (x1, y1)]

    # ---- vistas ----
    def poe(self, vista, x, y, escala):
        """Posiciona o canto inferior-esquerdo do conteudo da vista em (x, y) mm."""
        v = dict(vista)
        v["px"], v["py"], v["escala"] = x, y, escala
        v["fw"], v["fh"] = vista["w"] * escala, vista["h"] * escala
        self.vistas[vista["nome"]] = v
        return v

    def para_folha(self, nome, mx, my, mz):
        v = self.vistas[nome]
        p = v["v"].projectPoint(Vector(mx, my, mz))
        return (v["px"] + (p.x - v["pp0"].x - v["loc"][0]) * v["escala"],
                v["py"] + (p.y - v["pp0"].y - v["loc"][1]) * v["escala"])

    def desenha(self):
        for nome, v in self.vistas.items():
            conv = lambda p: (v["px"] + (p[0] - v["loc"][0]) * v["escala"],
                              v["py"] + (p[1] - v["loc"][1]) * v["escala"])
            for (a, b) in v["vis"]:
                (x1, y1), (x2, y2) = conv(a), conv(b)
                self.linha(x1, y1, x2, y2, 0.5)
            for (a, b) in v["hid"]:
                (x1, y1), (x2, y2) = conv(a), conv(b)
                self.linha(x1, y1, x2, y2, 0.3, self.TRACO, (3, 2))

    def rotulo_vista(self, nome, txt=None):
        v = self.vistas[nome]
        self.texto(v["px"], v["py"] - 4.5, txt or nome.upper(), 8, negrito=True)

    # ---- cotas ----
    def cota_h(self, nome, pa, pb, off, rotulo=None, modo="vista"):
        """Cota horizontal entre dois pontos 3D do modelo.

        modo='vista' (padrao): linha de cota 'off' mm abaixo da CAIXA da vista
        (off negativo = acima). modo='ancora': relativa ao ponto ancorado -- so' use
        quando os dois pontos estiverem na mesma altura da vista, senao cai dentro dela.
        """
        v = self.vistas[nome]
        xa, ya = self.para_folha(nome, *pa)
        xb, yb = self.para_folha(nome, *pb)
        yd = ((v["py"] if off >= 0 else v["py"] + v["fh"]) - off) if modo == "vista" \
            else min(ya, yb) - off
        self.ancoras += [(nome, xa, ya), (nome, xb, yb)]
        self.linha(xa, yd, xb, yd, 0.25)
        self.linha(xa, ya, xa, yd - 1.5, 0.25)
        self.linha(xb, yb, xb, yd - 1.5, 0.25)
        self._seta(xa, yd, 0.0)
        self._seta(xb, yd, math.pi)
        t = rotulo or f"{abs(pb[0] - pa[0]) or abs(pb[1] - pa[1]):.0f}"
        self.texto((xa + xb) / 2.0, yd + 1.3, t, 6.5, centro=True)
        return t

    def cota_v(self, nome, pa, pb, off, rotulo=None, modo="vista"):
        """Cota vertical entre dois pontos 3D do modelo.

        modo='vista': linha de cota 'off' mm a esquerda da CAIXA da vista
        (off negativo = a direita).
        """
        v = self.vistas[nome]
        xa, ya = self.para_folha(nome, *pa)
        xb, yb = self.para_folha(nome, *pb)
        xd = ((v["px"] if off >= 0 else v["px"] + v["fw"]) - off) if modo == "vista" \
            else min(xa, xb) - off
        self.ancoras += [(nome, xa, ya), (nome, xb, yb)]
        self.linha(xd, ya, xd, yb, 0.25)
        self.linha(xa, ya, xd - 1.5, ya, 0.25)
        self.linha(xb, yb, xd - 1.5, yb, 0.25)
        self._seta(xd, ya, math.pi / 2)
        self._seta(xd, yb, -math.pi / 2)
        t = rotulo or f"{abs(yb - ya) / (v['escala']):.0f}"
        self.texto(xd - 1.7, (ya + yb) / 2.0, t, 6.5, centro=True, rot=90)
        return t

    def anotacao(self, nome, mx, my, mz, txt, dist=13.0, tam=6.5):
        """Chamada apontando para um ponto do modelo, saindo para FORA da vista."""
        v = self.vistas[nome]
        x, y = self.para_folha(nome, mx, my, mz)
        cx, cy = v["px"] + v["fw"] / 2.0, v["py"] + v["fh"] / 2.0
        dx, dy = x - cx, y - cy
        n = math.hypot(dx, dy) or 1.0
        xe, ye = x + dx / n * dist, y + dy / n * dist
        self.linha(x, y, xe, ye, 0.25)
        if dx >= 0:
            self.texto(xe + 1.5, ye - 1.5, txt, tam)
        else:
            self.texto(xe - 1.5, ye - 1.5, txt, tam, fim=True)

    # ---- carimbo e listas ----
    def carimbo(self, linhas, x=273.0, y=12.0, w=135.0, h=42.0):
        self.retangulo(x, y, w, h, 0.8)
        self.c.setLineWidth(0.3)
        for dy in (11.0, 21.0, 29.0, 35.0):
            self.linha(x + 2, y + dy, x + w - 2, y + dy, 0.3)
        linhas = list(linhas) + [("", 6.5, False)] * (6 - len(linhas))
        ys = (y + 37.5, y + 31.0, y + 23.5, y + 13.5, y + 7.0, y + 1.5)
        for (s, tam, neg), yy in zip(linhas[:6], ys):
            if s:
                self.texto(x + 3, yy, s, tam, negrito=neg)

    def lista_corte(self, titulo, colunas, linhas, x, y, passo=4.5):
        self.texto(x, y, titulo, 8, negrito=True)
        self.texto(x, y - 5, colunas, 6.5, negrito=True)
        yy = y - 9.5
        for ln in linhas:
            self.texto(x, yy, ln, 6.5)
            yy -= passo
        return yy

    # ---- finalizacao ----
    def nova_pagina(self):
        self.c.showPage()
        self.vistas.clear()
        self.ancoras.clear()

    def salva(self):
        self.c.save()
        return self.verificar()

    def verificar(self):
        x0, y0, x1, y1 = self.i
        prob = list(self.problemas)
        for (x, y) in self.tinta:
            if not (x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01):
                prob.append(f"tinta fora da moldura em ({x:.1f},{y:.1f})")
                break
        for nome, v in self.vistas.items():
            if v["px"] < x0 or v["py"] < y0 or v["px"] + v["fw"] > x1 or v["py"] + v["fh"] > y1:
                prob.append(f"{nome} fora da moldura: {v['px']:.1f},{v['py']:.1f} "
                            f"{v['fw']:.1f}x{v['fh']:.1f}")
            prob += v.get("alertas", [])
        for (nome, x, y) in self.ancoras:
            v = self.vistas[nome]
            tol = 1.5
            if not (v["px"] - tol <= x <= v["px"] + v["fw"] + tol and
                    v["py"] - tol <= y <= v["py"] + v["fh"] + tol):
                prob.append(f"ancora de cota de {nome} fora da vista: ({x:.1f},{y:.1f})")
        return prob
