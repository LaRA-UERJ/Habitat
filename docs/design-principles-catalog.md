# Design Principles Catalog

A collection of design principles extracted from multiple philosophies and sources. Presented as a **reference catalog** for evaluation — no principles are adopted as requirements yet.

---

## Spatial Geometry

### 120° Instead of 90°

**Source:** Robert Propst, *The Office: A Facility Based on Change* (1968)

Right angles are building geometry, not human geometry. Three panels at 120° form a partial enclosure ("amphitheater") that:
- Provides partial enclosure without cell-like feeling
- Preserves peripheral vision
- Creates natural entry/exit flow
- Eliminates the dead corner of cubicles
- Is better for collaborative pair work

**Applied to benches:** A 120° angle between work surface and whiteboard/pegboard panel creates a natural "bay" that encloses without confining. Two students can work side by side without invading each other's space.

**Counterargument:** 120° layouts use more floor area per station than 90° grids. In a 49m² lab, every square meter matters.

---

### Organic Layout (No Grid)

**Source:** Bürolandschaft, Quickborner Team (1960s)

Arrange furniture based on actual communication and workflow patterns, not on a rectangular grid. Result is typically asymmetrical and plant-integrated.

**Counterargument:** Difficult to implement in small spaces. Requires prior study of workflows. Can look disorganized.

---

### Universal Grid

**Source:** OpenStructures, Thomas Lommée

Define a standard grid (e.g., 40×40 mm hole pattern) that all components share. Everything is interoperable by default.

**Applied to benches:** A lab-wide grid standard means a pegboard from one bench clips onto the frame of another. Tool holders, shelves, and panels are interchangeable across all workstations.

**Counterargument:** Constrains design freedom. Requires discipline and documentation to maintain.

---

## Ergonomics and Posture

### Postural Variation

**Source:** Propst (1968); modern ergonomic research

A worker should not maintain the same posture for 8 hours. Each station should offer multiple surface heights:
- Low surface for seated concentration
- High surface for standing work or brief meetings
- Intermediate surfaces for leaning/perching

**Applied to benches:** The soldering bench is standing-height by design. Could a secondary lower shelf provide a seated option? The workstation 120° could have an adjustable monitor arm + keyboard tray for sit/stand.

---

### Task-Appropriate Height

**Source:** Propst; kitchen station design; industrial ergonomics

Different tasks have different optimal heights:
- Precision soldering: elbow height or slightly above (standing)
- CAD work: standard desk height (seated) or adjustable
- Assembly/mechanical: slightly below elbow height for leverage
- Reading/discussion: counter height for standing meetings

**Counterargument:** Adjustable-height mechanisms (linear actuators) add cost and complexity.

**Practical data:** See [ergonomics.md](ergonomics.md) for anthropometric data (Brazilian population), ideal desk heights, and elbow angle tolerances. See [adjustable-height-mechanisms.md](adjustable-height-mechanisms.md) for telescoping tube combinations and DIY locking mechanisms.

---

## Vertical Surfaces

### Walls as Mental Extension

**Source:** Propst (1968)

Vertical surfaces around the workstation are for pinning, displaying, organizing — not decoration. Information is externalized into the visual field. The modern equivalent: whiteboard + Kanban board + pegboard.

**Applied to benches:**
- Soldering bench: pegboard for tools (soldering iron, hot air, probes, tweezers)
- Workstation 120°: pegboard for monitor mount + small shelf for components + whiteboard for schematics

---

### Shadow Boards

**Source:** 5S methodology (Japanese manufacturing)

Every tool has a painted/engraved outline showing where it belongs. Missing tools are instantly visible.

**Applied to benches:** Pegboard with laser-cut outlines or printed backgrounds showing where each tool lives.

---

## Privacy and Acoustics

### Gradual Privacy (Not Binary)

**Source:** Propst (1968); Activity-Based Working

Privacy is a spectrum, not a toggle. Design for:
- **High privacy** — Focus pods, enclosed booths (for deep coding/debugging)
- **Medium privacy** — Semi-enclosed bays, 120° panels (for concentrated electronics work)
- **Low privacy** — Open tables, standing benches (for collaboration, assembly)

**Applied to lab:** The 7×7m space could have a noise/focus gradient — quiet zone (CAD) on one end, noisy zone (mechanical/CNC) on the other, medium (electronics) in between.

---

### Noise Gradient

**Source:** Activity-Based Working; Propst

Organize space so incompatible noise levels don't overlap. Quiet tasks (coding, reading datasheets) should be far from noisy tasks (drilling, CNC, grinding).

**Applied to LaRA 7×7m:** CAD zone distant from CNC/mechanical zone. Electronics in the middle.

---

## Adaptability

### Everything on Casters

**Source:** Fun Palace (Cedric Price); Propst; Activity-Based Working

If it doesn't absolutely need to be fixed to the wall or floor, it should have casters with brakes. Layout changes in minutes, not days.

**Applied to benches:** Both the soldering bench and workstation 120° are designed to be mobile. Heavy equipment (CNC, 3D printers) stays fixed; workstations move.

**Counterargument:** Mobile benches need cable management solutions (retractable reels, overhead drops). Caster quality matters — cheap casters on a loaded bench are worse than fixed legs.

---

### Modular Frames (Profile Systems)

**Source:** Open Source Ecology; OpenStructures; industrial workstations

Use aluminum extrusion (V-slot, Bosch, 80/20) instead of welded steel or glued wood. Everything is bolted, nothing is permanent. A bench can grow, shrink, or reconfigure by moving a few brackets.

**Applied to benches:** Both active designs could use 4040 or 2040 profile as the structural frame. Pegboard panels, shelves, and accessories mount with standard T-slot brackets.

---

## Organization and Maintenance

### 5S for Academic Labs

**Source:** Japanese manufacturing methodology; adapted for university labs

The five pillars, adapted for a lab with 30+ rotating students:
1. **Seiri (Sort)** — Remove everything not needed for current projects. Expired components, broken tools, abandoned prototypes.
2. **Seiton (Set in order)** — Shadow boards, labeled drawers, Kanban for consumables. New student finds any tool in 30 seconds.
3. **Seiso (Shine)** — Clean bench after every session. Soldering station cleaned, tools returned, waste disposed.
4. **Seiketsu (Standardize)** — Same bench layout, same tool location, same process across all stations.
5. **Shitsuke (Sustain)** — Formal end-of-session checklist. Weekly audit by infra student. Without this, degrades in 6 months.

**The 30-second rule:** If a new student cannot find a tool in 30 seconds, the organization has failed.

---

### Project-in-Progress (PIP) Policy

**Source:** Lab management practice

The "trash" in academic labs is mostly abandoned projects from graduated students. Policy:
- Shelves numbered with labels: owner / project / date
- No update for N months → return to stock or recycle
- Formal handoff before student leaves (disassemble, document, or donate)

---

## Material and Aesthetic Choices

### Typical Palette for This Philosophy

Common across Propst-inspired, activity-based, and maker environments:
- Light wood (birch plywood, maple)
- Thin black steel/metal frame
- Glass or acrylic panels
- Diffused lighting (task + ambient)
- Plants (biophilic design)
- Perforated metal / pegboard
- Wheels and casters
- Open shelving (not closed cabinets)

### Industrial Examples

- Steelcase workstations
- Vitra office systems
- Premium coworking spaces
- Post-pandemic hybrid offices
- Adam Savage's Tested workshop
- MIT Media Lab spaces
- Stanford Product Realization Lab

---

*This is a catalog of options. Individual project briefs will reference specific principles as needed.*
