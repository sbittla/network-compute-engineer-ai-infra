# 2.1.1 — Power-limited, not space-limited

Sources: manuscript Sections 2.3 (rack layout), 2.5 (ORION rack budget), 2.7 (coolant arithmetic) and
2.10 (fit assessment). Values `[MODELED]` from `[ILLUSTRATIVE]` ORION parameters; `solve.py` checks them.

**Space.** Four 8U `HX8` nodes occupy 4 × 8U = 32U of a 48U rack. With 3U for the in-rack switch and
cable cassettes, 48 − 32 − 3 = **13U** is empty, so a fifth 8U node *fits physically*.

**Power.** Four nodes draw 4 × 10.2 + 0.2 = **41.0 kW** at maximum. A fifth would take the rack to
5 × 10.2 + 0.2 = **51.2 kW**, or 51.2 × 1.10 = **56.3 kW per side** with the transient margin. That
still fits under the 65.55 kW usable per side, but it breaks the rest of the rack design: liquid heat
becomes 0.75 × 51.2 = 38.4 kW per rack, so eight racks load the single 300 kW CDU to 307 kW (102 %).
Residual air rises to 12.8 kW against the room's 12 kW per rack. Floor load becomes
(5 × 135 + 280) / 0.72 = 1,326 kg/m² against a 1,200 kg/m² rating.

So the binding constraints are power and the heat that power becomes, not rack units. The rack is filled
by watts long before it is filled by servers.

**Common wrong answer:** quoting only one number (either the 13U or the 41 kW); full credit needs both.
