## Zone Structure Terminology

**Effective:** 2026-06-06

---

### Mapping

| Old Term | New Term | Role |
|---|---|---|
| Preparation Zone | Formation | Parent structure — initial detection, large contextual area |
| — | Density Band | High-concentration region inside Formation — operational area |
| — | Active Core | Most precise region inside Density Band — highest operational precision |

---

### Definitions

**Formation**
Initial structure detection. Large contextual area. First stage of compression / preparation identification. Parent of all sub-structures. Replaces "Preparation Zone" as the top-level label.

**Density Band**
High-concentration region inside Formation. Operational area. More precise than Formation. Occurs after Formation detection.

**Active Core**
Most active and important region inside Density Band. Highest operational precision. Final actionable area. Innermost layer.

---

### Hierarchy

```
Formation
    └── Density Band
            └── Active Core
```

---

### Notes

- Active Core and Density Band occur AFTER Formation detection.
- Formation remains the parent structure.
- Density Band and Active Core refine location precision inside Formation.
- Future research: whether Density Band and Active Core improve preparation quality and RDM behavior.
- Existing code uses "preparation_zone" as the internal identifier — this terminology maps conceptually; code renaming is a separate step.
