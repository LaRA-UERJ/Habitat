# Adjustable Height Mechanisms

Practical solutions for building height-adjustable desk/workstation legs without electric actuators. Focuses on materials and techniques accessible in Brazil.

---

## 1. Telescoping Square Steel Tubing (Metalon)

### Combinações que encaixam

Tubos quadrados de aço (metalon) com dimensões comerciais brasileiras (NBR 6591/8261, ASTM A500). A tabela abaixo mostra combinações onde o tubo interno desliza dentro do externo com folga mínima.

| Tubo externo | Parede ext. | Diâmetro interno | Tubo interno (ext.) | Folga por lado |
|---|---|---|---|---|
| **50x50** | 3,75 mm | ~42,5 mm | **40x40** | **~1,25 mm** |
| 50x50 | 3,00 mm | ~44,0 mm | 40x40 | ~2,0 mm |
| 40x40 | 2,65 mm | ~34,7 mm | 30x30 | ~2,35 mm |
| 30x30 | 2,25 mm | ~25,5 mm | 25x25 | ~0,25 mm (muito justo) |

### Par recomendado: 50x50 (esp 3,75mm) + 40x40

- ~1,25 mm de folga por lado — suficiente para deslizar sem travar
- Com bucha de nylon ou fita UHMW no interior, fica firme sem holgura
- 2 colunas telescópicas suportam uma mesa com folga
- Para maior rigidez: 3 ou 4 colunas

### Reduzindo vibração e folga

- **Bucha de nylon** usinada ou cortada e inserida nas extremidades do tubo externo
- **Fita UHMW** (Ultra High Molecular Weight polyethylene) aplicada nas faces internas de deslizamento
- **Parafuso prisioneiro** (set screw) no tubo externo para eliminar folga residual após travar
- **Graxa ou cera** nas superfícies de deslizamento para reduzir ruído e desgaste

### Fontes de tubo no Brasil

- Cia do Ferro — https://ciadoferro.com.br/tubo-quadrado/
- Grupo Aparecida Tubos — https://www.aparecidatubos.com.br/tubos-quadrado
- Century Tubos — https://materiais.centurytubos.com.br/catalogo
- K-Ferros — https://kferros.com.br/tubo-industrial-quadrado/1941
- Tabela completa de medidas: Fábrica do Projeto — https://www.fabricadoprojeto.com.br/tabelas-de-laminados-trefilados-e-itens-comerciais/tabelas-fapro-tubo-industrial-quadrado/

---

## 2. Locking Mechanisms

### 2.1 Pino + Furos (Pin Lock)

| Aspecto | Detalhe |
|---|---|
| **Complexidade** | Baixa |
| **Custo** | ~R$ 10 |
| **Ajuste** | Discreto (a cada ~25 mm) |
| **Pros** | Simples, robusto, sem vibração, fácil de fabricar |
| **Contras** | Ajuste não-contínuo; precisa furar ambos os tubos |

**Como fazer:**
1. Furar o tubo externo em múltiplas posições (ex: a cada 25 mm)
2. Furar o tubo interno nas alturas desejadas
3. Inserir pino (parafuso, pino quick-release, ou pino com mola/bola tipo bicicleta)

**Pino quick-release (pino com mola/bola):** encontrado em lojas de bicicleta ou camping, permite ajuste sem ferramentas.

---

### 2.2 Parafuso Prisioneiro (Thumb Screw / Set Screw)

| Aspecto | Detalhe |
|---|---|
| **Complexidade** | Baixa |
| **Custo** | ~R$ 15 |
| **Ajuste** | Contínuo |
| **Pros** | Ajuste contínuo, simples de implementar |
| **Contras** | Pode marcar o tubo interno com o tempo; folga pode surgir com desgaste |

**Como fazer:**
1. Rosquear (ou soldar porca) no tubo externo
2. Parafuso com knob plástico aperta contra o tubo interno
3. Para proteger o tubo interno: aplicar uma chapa de nylon ou disco de borracha na ponta do parafuso

---

### 2.3 Twist-Lock Impresso em 3D

| Aspecto | Detalhe |
|---|---|
| **Complexidade** | Média |
| **Custo** | ~R$ 30 (filamento) |
| **Ajuste** | Contínuo |
| **Pros** | Ajuste rápido, contínuo, sem ferramentas |
| **Contras** | Precisa de impressora 3D; resistência depende do plástico |

**Princípio:** Um mecanismo excêntrico interno (tipo twist-lock de bastão de cortina) que se expande ao girar, travando o tubo interno contra o externo.

**Referência:** Thingiverse "Telescopic Pole Twist-Lock Mechanism" por Polyfoil — https://www.thingiverse.com/thing:4926237

---

### 2.4 Macaco Parafuso (Acme Thread / Screw Jack)

| Aspecto | Detalhe |
|---|---|
| **Complexidade** | Média-Alta |
| **Custo** | ~R$ 50–80 |
| **Ajuste** | Contínuo, fino |
| **Pros** | Ajuste preciso e contínuo, sem folga, auto-travante sob carga |
| **Contras** | Mais trabalho de usinagem; lento para grandes mudanças |

**Princípio:** Rosca trapezoidal (Acme, 29°) usada como macaco. Girar o parafuso eleva ou desce a mesa. Auto-travante por atrito da rosca.

**Implementação simplificada:**
- Parafuso rosca métrica (M12, M16) com porca soldada na base do tubo externo
- Girar o parafuso por baixo ajusta a altura do pé
- Para mesa com 4 colunas: 4 macacos independentes ou 2 por lado ligados por eixo+coringa

---

### 2.5 Gás Lift de Cadeira (Salvado)

| Aspecto | Detalhe |
|---|---|
| **Complexidade** | Média |
| **Custo** | ~R$ 30–60 |
| **Ajuste** | Contínuo, suave |
| **Pros** | Ajuste suave, rápido, barato se recuperado de cadeira velha |
| **Contras** | Curso limitado (~10–15 cm); precisa adaptar ao tubo; carga limitada |

**Implementação:** Remover o cilindro de gás de uma cadeira de escritório velha. Adaptar com buchas para encaixar nos tubos. Cada coluna usa um cilindro.

---

## 3. Comparativo de Mecanismos

| Mecanismo | Custo | Ajuste | Complexidade | Vibração | Velocidade |
|---|---|---|---|---|---|
| Pino + furos | R$ 10 | Discreto (~25 mm) | Baixa | Zero | Média |
| Thumb screw | R$ 15 | Contínuo | Baixa | Baixa | Rápida |
| Twist-lock 3D | R$ 30 | Contínuo | Média | Baixa | Rápida |
| Macaco rosca | R$ 50–80 | Contínuo, fino | Média-Alta | Zero | Lenta |
| Gás lift | R$ 30–60 | Contínuo | Média | Zero | Rápida |

---

## 4. Sugestão Pragmática (Custo-Benefício)

Para a maioria dos cenários:

- **2 colunas telescópicas:** tubo 50x50 (esp 3,75 mm) externo + tubo 40x40 interno
- **Bucha de nylon ou fita UHMW** nas pontas do tubo externo para eliminar folga/vibração
- **Pino quick-release** (tipo bicicleta, com mola/bola): furar o tubo externo de 25 em 25 mm, e furos no interno nas mesmas alturas
- **~6–8 posições** cobrem de sentado a em pé (~95 cm a ~118 cm)

Custo estimado por mesa (2 colunas): ~R$ 80–150 (tubos + pinos + buchas).

---

## Referências

- Alcobra Metals: "Steel Telescoping Square Tubing" — https://alcobrametals.com/telescopic-tubing/steel-telescoping-square-tubing-095/
- Lock Joint Tube: "Steel Telescopic Tubing" — https://www.ljtube.com/tubing/tubing-by-shape/telescopic/
- Thingiverse: "Telescopic Pole Twist-Lock Mechanism" — https://www.thingiverse.com/thing:4926237
- Tools Radar: "Innovative Mechanisms for Adjustable Desk Legs" — https://toolsradar.com/innovative-mechanisms-for-adjustable-desk-legs/
- Fábrica do Projeto: "Tabela de Tubo Industrial Quadrado" — https://www.fabricadoprojeto.com.br/tabelas-de-laminados-trefilados-e-itens-comerciais/tabelas-fapro-tubo-industrial-quadrado/

---

*Para dados ergonômicos (altura do brasileiro, ângulos, tolerâncias), ver [ergonomics.md](ergonomics.md).*
