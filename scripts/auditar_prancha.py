#!/usr/bin/env python3
"""Auditoria de prancha quando o agente nao enxerga imagem.

Le o PDF e o relatorio JSON gerados por um passo de CAD e verifica, por densidade de
tinta rasterizada (pdftoppm + PIL):

  1. toda vista de `caixas_na_folha` tem tinta (vista em branco reprova);
  2. nenhuma vista esta borrada (densidade alta demais);
  3. o carimbo tem tinta;
  4. NAO existe tinta fora das duas molduras -- cobre o que o Folha.verificar() nao pega,
     porque ele so' registra o PONTO INICIAL de cada texto (um texto que comece dentro
     da folha e transborde a borda passa batido).

Uso:
  python3 scripts/auditar_prancha.py [--relatorio saida/passoN_relatorio.json]
                                     [--pdf saida/passoN_prancha.pdf] [--regioes r.json]

Sem --regioes, checa as regioes que DEVEM estar vazias que vierem no JSON (chave
"regioes_vazias_mm": {"nome": [x0, y0, x1, y1]}).

Sai com codigo 1 se qualquer checagem falhar.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image

MOLDURA_EXTERNA = 10.0      # mm: moldura desenhada por Folha.moldura()
MOLDURA_INTERNA = 12.0      # mm: linha interna
A3 = (420.0, 297.0)


def densidade(im, x0, y0, x1, y1, margem=0.0):
    f = im.size[0] / A3[0]
    a, b = int((x0 + margem) * f), int((A3[1] - y1 + margem) * f)
    c, d = int((x1 - margem) * f), int((A3[1] - y0 - margem) * f)
    a, b = max(a, 0), max(b, 0)
    c, d = min(c, im.size[0]), min(d, im.size[1])
    if c <= a or d <= b:
        return -1.0, 0
    reg = im.crop((a, b, c, d))
    escuros = sum(1 for p in reg.getdata() if int(p) < 128)
    return escuros / float(reg.size[0] * reg.size[1]), escuros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf")
    ap.add_argument("--relatorio")
    ap.add_argument("--regioes", help="JSON com regioes que devem estar vazias")
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args()

    pdf = a.pdf
    rel = a.relatorio
    if not rel:
        base = os.path.dirname(pdf) if pdf else "."
        cands = [f for f in os.listdir(base) if f.endswith("_relatorio.json")]
        if len(cands) != 1:
            sys.exit(f"informe --relatorio (candidatos: {cands})")
        rel = os.path.join(base, cands[0])
    d = json.load(open(rel))
    if not pdf:
        pdf = os.path.join(os.path.dirname(rel),
                           os.path.basename(rel).replace("_relatorio.json", "_prancha.pdf"))

    tmp = tempfile.mkdtemp()
    png = os.path.join(tmp, "pagina")
    subprocess.run(["pdftoppm", "-r", str(a.dpi), "-png", "-singlefile", pdf, png],
                   check=True)
    im = Image.open(png + ".png").convert("L")
    print("prancha: %s\nrelatorio: %s\nimagem: %dx%d px" % (pdf, rel, im.size[0], im.size[1]))

    falhas = []
    print("\n=== vistas ===")
    for nome, cx in (d.get("caixas_na_folha") or {}).items():
        f, _ = densidade(im, *cx)
        st = "ok" if 0.0005 < f < 0.45 else "FALHA"
        print("  %-10s [%7.1f %7.1f %7.1f %7.1f] tinta=%.4f  %s" % (nome, *cx, f, st))
        if f <= 0.0005:
            falhas.append(f"{nome}: vista sem tinta")
        if f >= 0.45:
            falhas.append(f"{nome}: tinta demais ({f:.2f})")

    cb = d.get("carimbo_mm") or [273.0, 12.0, 408.0, 54.0]
    f, _ = densidade(im, *cb)
    print("  %-10s tinta=%.4f  %s" % ("carimbo", f, "ok" if f > 0.0005 else "FALHA"))
    if f <= 0.0005:
        falhas.append("carimbo sem tinta")

    print("\n=== fora das molduras (o que verificar() nao pega) ===")
    f = im.size[0] / A3[0]
    lim = MOLDURA_EXTERNA - 0.5      # a propria moldura externa esta em 10 mm
    bandas = {"esquerda": (0, 0, lim, A3[1]), "direita": (A3[0] - lim, 0, A3[0], A3[1]),
              "topo": (0, A3[1] - lim, A3[0], A3[1]), "base": (0, 0, A3[0], lim)}
    for nome, (x0, y0, x1, y1) in bandas.items():
        a0, b0 = int(x0 * f), int((A3[1] - y1) * f)
        a1, b1 = int(x1 * f), int((A3[1] - y0) * f)
        reg = im.crop((max(a0, 0), max(b0, 0),
                       min(a1, im.size[0]), min(b1, im.size[1])))
        n = sum(1 for v in reg.getdata() if int(v) < 128)
        print("  banda %-9s %5d px  %s" % (nome, n, "ok" if n == 0 else "FALHA"))
        if n:
            falhas.append(f"tinta na banda {nome} (fora da folha util)")

    reg = a.regioes
    if reg:
        reg = json.load(open(reg)) if isinstance(reg, str) else reg
        reg = reg.get("regioes_vazias_mm", reg)
        print("\n=== regioes que devem estar vazias ===")
        for nome, cx in reg.items():
            fv, _ = densidade(im, *cx, margem=2.0)
            print("  %-26s tinta=%.4f  %s" % (nome, fv, "ok" if fv <= 0.02 else "FALHA"))
            if fv > 0.02:
                falhas.append(f"{nome}: deveria estar vazia ({fv:.3f})")

    print("\nRESULTADO:", "TUDO OK" if not falhas else "FALHAS:")
    for x in falhas:
        print("  -", x)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
