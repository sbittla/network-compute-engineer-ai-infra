# Marking scheme: 3.7 Safe collection

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** Four properties, each with one example.

| Criterion | Points |
|---|---|
| Property 1 with a concrete refused or handled example (for example default-deny allowlist refusing ethtool -s rail0 speed 200000) | 1 |
| Property 2 with a concrete example (for example argv without a shell, so an interface name cannot inject a command) | 1 |
| Property 3 with a concrete example (for example per-command timeouts for a hung lspci) | 1 |
| Property 4 with a concrete example (for example no sudo, record denied and fall back to journalctl -k; record every outcome; LC_ALL=C) | 1 |
