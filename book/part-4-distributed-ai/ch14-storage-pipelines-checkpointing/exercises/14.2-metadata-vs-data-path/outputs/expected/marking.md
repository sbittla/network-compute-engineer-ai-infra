# Marking scheme: 14.2 Metadata path versus data path

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** a labelled sketch or numbered sequence of the RPCs for open → read → close

| Criterion | Points |
|---|---|
| RPC sequence: open to MDS (lookup, permissions, layout), read directly to OSSs, close to MDS | 2 |
| Stripe count and stripe size semantics | 2 |
| Valid case where wider striping does not help (many clients each with own file, or small files) | 1 |
