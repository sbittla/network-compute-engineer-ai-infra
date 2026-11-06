# Marking scheme: M2 Tenant isolation boundaries (isolation model)

Type outline-mandated · kind lab · tier L1 · 15 points

**Evidence required:** boundary table; policy YAML; checker run showing zero violations on your config

| Criterion | Points |
|---|---|
| Boundary table covering identity, network, storage, GPU allocation, secrets and audit for three tenants | 5 |
| Machine-readable policy and tenant config in the lab's format | 4 |
| check_isolation() run on the learner's own config shows zero violations; lab T6 check passes | 3 |
| Notes reachability vs performance isolation and the inference tenant's GPU mode (whole or MIG) | 3 |
