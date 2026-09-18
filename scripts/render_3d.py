#!/usr/bin/env python3
"""Render 3D do modelo FreeCAD em PNG, headless (xvfb + FreeCAD GUI offscreen).

Roda assim (nao abre janela: o X virtual e' descartavel):

    xvfb-run -a freecad scripts/render_3d.py

Parametros por variavel de ambiente (o freecadcmd/freecad ignora argv proprio):

    RENDER_FCSTD   caminho do .FCStd a abrir        (obrigatorio)
    RENDER_OUT     pasta de saida                   (default: pasta do .FCStd)
    RENDER_NOME    prefixo dos PNG                  (default: render)
    RENDER_W/H     resolucao                        (default: 1920 x 1200)
    RENDER_FUNDO   White | Current | Transparent    (default: White)
    RENDER_CHAO    1 para criar plano de chao       (default: 1)
    RENDER_CLOSE   nome-base das pecas do close     (default: auto pelo sufixo)

Sai com 3 imagens: <nome>_iso.png (axonometrica), <nome>_persp.png (perspectiva) e
<nome>_close.png (aproximacao na primeira peca de base encontrada).

Cores por tipo de peca pelo nome: tubo (montante/travessa/perna) grafite, chapa aco claro,
roda PU cinza, garfo/placa zincado. Ajuste PALETA se o padrao de nome do modulo for outro.
"""
import os
import sys

import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Vector

IN = os.environ.get("RENDER_FCSTD")
if not IN or not os.path.exists(IN):
    sys.exit("RENDER_FCSTD nao existe: %r" % IN)
OUT = os.environ.get("RENDER_OUT", os.path.dirname(os.path.abspath(IN)))
NOME = os.environ.get("RENDER_NOME", "render")
W = int(os.environ.get("RENDER_W", "1920"))
H = int(os.environ.get("RENDER_H", "1200"))
FUNDO = os.environ.get("RENDER_FUNDO", "White")
CHAO = os.environ.get("RENDER_CHAO", "1") == "1"

# tipo de peca -> (RGB, transparencia)
PALETA = [
    (("mont", "trav", "perna"), ((0.16, 0.17, 0.19), 0)),      # metalon pintado preto
    (("chapa",), ((0.62, 0.64, 0.67), 0)),                     # chapa de aco
    (("roda",), ((0.30, 0.30, 0.32), 0)),                      # roda de PU/borracha
    (("garfo", "placa"), ((0.74, 0.75, 0.78), 0)),             # zincado
]


def cor(nome):
    for chaves, val in PALETA:
        if any(k in nome for k in chaves):
            return val
    return ((0.55, 0.55, 0.58), 0)


def main():
    linhas = []
    doc = App.openDocument(IN)
    App.setActiveDocument(doc.Name)
    try:
        Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        pass
    pecas = [o for o in doc.Objects if o.TypeId == "Part::Feature"]

    for o in pecas:
        vo = getattr(o, "ViewObject", None)
        if vo is None:
            continue
        rgb, tr = cor(o.Name)
        vo.ShapeColor = rgb
        vo.LineColor = (0.05, 0.05, 0.05)
        vo.Transparency = tr
        vo.DisplayMode = "Shaded"
        vo.Visibility = True

    if CHAO:
        bbs = [o.Shape.BoundBox for o in pecas]
        x0 = min(b.XMin for b in bbs) - 300
        x1 = max(b.XMax for b in bbs) + 300
        y0 = min(b.YMin for b in bbs) - 300
        y1 = max(b.YMax for b in bbs) + 300
        chao = doc.addObject("Part::Plane", "chao")
        chao.Length = x1 - x0
        chao.Width = y1 - y0
        chao.Placement.Base = Vector(x0, y0, -0.5)
        doc.recompute()
        cv = chao.ViewObject
        cv.ShapeColor = (0.86, 0.86, 0.86)
        cv.DisplayMode = "Shaded"

    doc.recompute()
    view = Gui.activeDocument().activeView()
    view.setAnimationEnabled(False)

    def salva(sufixo, w=W, h=H):
        p = os.path.join(OUT, "%s_%s.png" % (NOME, sufixo))
        view.saveImage(p, w, h, FUNDO)
        linhas.append("PNG %s  %d bytes  %dx%d" % (p, os.path.getsize(p), w, h))
        print(linhas[-1])
        return p

    def fit(nomes, margem=1.0):
        """Enquadra a SELECAO (nao o chao, senao o conjunto encolhe na imagem).

        Sem zoomBy extra: ViewSelection ja' deixa margem, e fator > 1 pode CORTAR a peca.
        """
        Gui.Selection.clearSelection()
        for n in nomes:
            Gui.Selection.addSelection(doc.Name, n)
        Gui.SendMsgToActiveView("ViewSelection")

    def orienta(perspectiva, rot_z):
        """ORIENTA primeiro; enquadrar depois, senao o giro joga o objeto fora do quadro."""
        view.setCameraType("Perspective" if perspectiva else "Orthographic")
        view.viewAxonometric()
        if rot_z:
            try:
                view.setCameraOrientation(App.Rotation(Vector(0, 0, 1), rot_z).multiply(
                    view.getCameraOrientation()))
            except Exception as e:
                print("aviso: nao consegui girar a camera (%r)" % (e,))

    todas = [o.Name for o in pecas]
    chao_obj = doc.getObject("chao")

    # 1. axonometrica geral
    orienta(False, 0)
    fit(todas)
    salva("iso")

    # 2. perspectiva girada, para dar nocao de volume
    orienta(True, 40)
    fit(todas)
    salva("persp")

    # 3. close na base: SO as pecas do rodizio (o montante de 1,6 m estraga o
    #    enquadramento) e sem chao, para o fundo ficar limpo
    alvo = None
    for o in pecas:
        if "roda" in o.Name:
            alvo = o
            break
    if alvo is not None:
        pref = "_".join(alvo.Name.split("_")[:2])          # ex. folha1_a
        base = [o.Name for o in pecas
                if o.Name.startswith(pref) and "mont" not in o.Name]
        if chao_obj is not None:
            chao_obj.ViewObject.Visibility = False
        orienta(False, 35)
        fit(base, 1.0)
        salva("close", 1600, 1200)
        if chao_obj is not None:
            chao_obj.ViewObject.Visibility = True
        Gui.Selection.clearSelection()

    linhas.append("render ok: 3 PNGs em %s" % OUT)
    print(linhas[-1])
    with open(os.path.join(OUT, "%s.txt" % NOME), "w") as fh:
        fh.write("\n".join(linhas) + "\n")
    sys.stdout.flush()
    try:
        Gui.doCommand("Std_Quit")
    except Exception:
        pass
    os._exit(0)      # Std_Quit nao encerra o processo headless: sem isso o xvfb-run pendura


main()
