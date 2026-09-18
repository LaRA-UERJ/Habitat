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
    RENDER_CLOSE   prefixo das pecas do close     (default: auto pelo sufixo)

Sai com 3 imagens: <nome>_iso.png (axonometrica), <nome>_persp.png (perspectiva) e
<nome>_close.png. Sem RENDER_CLOSE o close e' a primeira peca de base encontrada (rodizio);
com RENDER_CLOSE=<prefixo> o close e' UMA fixacao do painel daquela folha (aba + parafuso +
cabeca), enquadrada so' nela, com o painel visivel como fundo.

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
CLOSE = os.environ.get("RENDER_CLOSE", "").strip()

# tipo de peca -> (RGB, transparencia)
PALETA = [
    (("mont", "trav", "perna"), ((0.84, 0.86, 0.88), 0)),       # metalon, cinza claro (pedido do usuario)
    (("chapa",), ((0.62, 0.64, 0.67), 0)),                     # chapa de aco
    (("roda",), ((0.30, 0.30, 0.32), 0)),                      # roda de PU/borracha
    (("garfo", "placa"), ((0.74, 0.75, 0.78), 0)),             # zincado
    # passo 2 (acrescentado no FIM: nao altera as cores acima)
    (("comp",), ((0.98, 0.94, 0.62), 0)),                      # compensado, amarelo claro
    (("espuma",), ((0.97, 0.94, 0.74), 0)),                    # espuma (acabamento opcional)
    (("tecido",), ((0.28, 0.30, 0.34), 0)),                    # tecido
    (("aba",), ((0.68, 0.80, 0.95), 0)),                       # cantoneira, azul claro
    (("parafuso", "cabeca"), ((0.80, 0.81, 0.84), 0)),         # parafuso zincado
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
        # "Flat Lines" e nao "Shaded": com Shaded o FreeCAD nao desenha aresta nenhuma e um
        # modelo em cores claras (cinza claro / amarelo claro) some no fundo branco.
        vo.DisplayMode = "Flat Lines"
        vo.LineWidth = 2.0          # aresta visivel: com largura 1 px ela some no render de 1920 px
        vo.Visibility = True

    # esconde tudo que nao e' solido (origem, planos e eixos do documento): eles aparecem no
    # saveImage e sujam o render com planos azul/vermelho
    for o in doc.Objects:
        vo = getattr(o, "ViewObject", None)
        if vo is not None and o.TypeId != "Part::Feature":
            vo.Visibility = False

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

    # 3. close: SO as pecas do foco (o montante de 1,6 m estraga o enquadramento)
    #    e sem chao, para o fundo ficar limpo.
    #    RENDER_CLOSE ausente: comportamento antigo (primeira peca com "roda" no nome,
    #    e o close e' o grupo daquele rodizio).
    #    RENDER_CLOSE=<prefixo>: o close passa a ser a fixacao do painel da folha
    #    daquela peca (aba + parafuso + cabeca + compensado + espuma + tecido).
    alvo = None
    if CLOSE:
        cand = [o for o in pecas if o.Name.startswith(CLOSE)]
        if not cand:
            print("aviso: RENDER_CLOSE=%r nao casou peca nenhuma" % CLOSE)
        else:
            folha = cand[0].Name.split("_")[0]                  # ex. folha1
            cand.sort(key=lambda o: o.Shape.BoundBox.ZMin)
            alvo_aba = cand[0]                                  # a aba mais baixa que casou
            # o enquadramento e' SO em UMA fixacao: as 12 fixacoes da folha espalhadas por
            # 1,5 m de altura jogam a camera para tras e a aba de 25 mm vira um ponto.
            # As pecas do painel continuam VISIVEIS: o compensado e' o fundo do close.
            p = alvo_aba.Name.split("_")
            base = [alvo_aba.Name]
            if len(p) >= 4 and p[-2] == "aba":                  # ex. folha1_a_aba_1
                pref, k = "_".join(p[:-2]), p[-1]
                for tipo in ("paraf", "cabeca"):
                    n2 = "%s_%s_%s" % (pref, tipo, k)
                    if doc.getObject(n2) is not None:
                        base.append(n2)
                print("close: fixacao %s (aba + parafuso + cabeca de %s)" % (k, pref))
            else:
                base += [o.Name for o in cand[1:]]
                print("close: prefixo %r sem sufixo _aba_N; %d pecas" % (CLOSE, len(base)))
            print("close por RENDER_CLOSE=%s: %d pecas (%s)"
                  % (CLOSE, len(base), ", ".join(base)))
            if chao_obj is not None:
                chao_obj.ViewObject.Visibility = False
            orienta(False, 35)
            fit(base, 1.0)
            salva("close", 1600, 1200)
            if chao_obj is not None:
                chao_obj.ViewObject.Visibility = True
            Gui.Selection.clearSelection()
            base = None
    else:
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
