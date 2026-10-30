# Course Outline (source of truth, extracted from AI_Infrastructure_Engineering_Definitive_Outline_v2_Enhanced.docx)

```text
[Normal] AI INFRASTRUCTURE ENGINEERING
[Normal] From GPU Compute and High-Speed Networking to Distributed Training, LLM Inference, and Production-Scale AI Systems
[Normal] FINAL BOOK TITLE AND COMPREHENSIVE 14-WEEK COURSE OUTLINE
[Normal] A practical, systems-oriented curriculum for designing, building, operating, and optimizing AI infrastructure at scale
[Heading 1] 1. Book positioning
[Normal] This book presents AI infrastructure as one connected engineering discipline—not as isolated GPU, networking, cloud, and machine-learning topics. It follows workloads across accelerator and host architecture, high-speed fabrics, distributed communication, storage and data movement, orchestration, observability, reliability, and cost.
[Normal] The central method: observe a workload symptom → collect evidence → trace the bottleneck across compute, network, storage, and orchestration → identify root cause → make a safe change → validate the result with repeatable measurements.
[Heading 2] Intended audience
[List Bullet] Network engineers moving into AI fabrics, RoCEv2, InfiniBand, and GPU-cluster networking.
[List Bullet] Systems, Linux, HPC, and data-center engineers supporting GPU fleets.
[List Bullet] ML platform, MLOps, SRE, and production engineers operating distributed training and inference.
[List Bullet] Performance engineers specializing in GPU, network, and distributed-AI performance.
[List Bullet] Senior engineers and architects targeting hyperscalers, neocloud providers, frontier AI labs, and hardware vendors.
[Heading 2] Prerequisites
[Normal] Linux command-line familiarity, basic programming (Python preferred), IP networking fundamentals, and general systems knowledge. CUDA, RDMA, and ML expertise are introduced progressively. A Linux environment is recommended; GPU and multi-node RDMA labs are optional hardware-backed extensions.
[Heading 1] 2. Learning outcomes
[List Bullet] Explain modern AI data-center architecture, GPU clusters, scale-up/scale-out, and infrastructure economics.
[List Bullet] Diagnose Linux host, CPU, memory, NUMA, PCIe, GPU, driver, and firmware constraints.
[List Bullet] Design and troubleshoot L2/L3, BGP/ECMP, Ethernet, RoCEv2, InfiniBand, and RDMA paths.
[List Bullet] Understand switch ASICs, buffers, queues, optics, transceivers, cabling, and physical-layer commissioning.
[List Bullet] Trace GPU-to-GPU and GPU-to-NIC paths across PCIe, NVLink/NVSwitch, NUMA, and GPUDirect RDMA.
[List Bullet] Benchmark distributed training communication with PyTorch Distributed and NCCL.
[List Bullet] Provision and operate bare-metal GPU fleets; schedule workloads with Kubernetes and Slurm.
[List Bullet] Optimize LLM inference, storage, checkpointing, data movement, and end-to-end workload performance.
[List Bullet] Build observability, SLOs, incident workflows, recovery automation, and safe operational changes.
[List Bullet] Make evidence-based capacity, utilization, reliability, security, and cost trade-offs.
[Heading 1] 3. Competency map
[Heading 1] 4. Complete book table of contents
[Heading 2] PART I — FOUNDATIONS OF AI INFRASTRUCTURE
[Normal] 1. The AI Infrastructure Landscape
[Normal] Why AI infrastructure differs from conventional cloud; training vs. inference; scale-up vs. scale-out; employer and role landscape.
[Normal] 2. Anatomy of an AI Data Center
[Normal] GPU servers, racks, pods, fabrics, storage, power/cooling, capacity planning, utilization and total cost.
[Normal] 3. Linux, Host Systems, and Performance Diagnostics
[Normal] Processes, CPU scheduling, memory, NUMA, PCIe, drivers, firmware, kernel tools and system diagnosis.
[Heading 2] PART II — ACCELERATED COMPUTE AND GPU SYSTEMS
[Normal] 4. GPU Architecture and CUDA Execution
[Normal] SMs, warps, memory hierarchy, kernels, streams, synchronization, occupancy and CUDA profiling.
[Normal] 5. GPU Interconnects and Host Topology
[Normal] PCIe, NVLink, NVSwitch, NUMA affinity, GPU-to-NIC locality, topology discovery and data paths.
[Normal] 6. GPU Performance Engineering
[Normal] Compute vs. memory limits, roofline reasoning, utilization, profiling, benchmark design and repeatable measurement.
[Heading 2] PART III — NETWORKING FOR AI CLUSTERS
[Normal] 7. Ethernet and Data-Center Network Foundations
[Normal] L2/L3, VLANs, IP addressing, MTU, routing, BGP, ECMP, leaf-spine design, QoS and convergence.
[Normal] 8. RDMA, RoCEv2, and InfiniBand
[Normal] RDMA concepts, RoCEv2, InfiniBand, addressing, transport behavior and multi-rail design.
[Normal] 9. Congestion Control and Lossless-Fabric Engineering
[Normal] ECN, PFC, WRED, queueing, incast, head-of-line blocking, buffers, congestion telemetry and trade-offs.
[Normal] 10. Switches, Optics, Cabling, and Physical-Layer Operations
[Normal] Switch ASICs, port architecture, buffers, transceivers, optics, link budgets, cabling, commissioning and fault isolation.
[Heading 2] PART IV — DISTRIBUTED AI SYSTEMS
[Normal] 11. Distributed Training Architecture
[Normal] Data, tensor, pipeline and expert parallelism; scaling behavior; topology-aware placement and failure modes.
[Normal] 12. Collective Communication and NCCL
[Normal] All-reduce, all-gather, reduce-scatter, broadcast, NCCL topology, rank mapping, algorithm selection and benchmarks.
[Normal] 13. GPU-to-GPU and GPU-to-NIC Data Movement
[Normal] GPUDirect RDMA, PCIe/NVLink paths, locality, communication overlap, stragglers and cross-layer diagnosis.
[Normal] 14. Storage, Data Pipelines, and Checkpointing
[Normal] NVMe, parallel I/O, staging, caching, throughput vs. tail latency, checkpoint/restart and recovery economics.
[Normal] 15. LLM Inference and Serving Infrastructure
[Normal] Prefill/decode, batching, KV cache, quantization, memory pressure, TTFT, inter-token latency and tokens/sec.
[Heading 2] PART V — OPERATING PRODUCTION AI INFRASTRUCTURE
[Normal] 16. Bare-Metal GPU Fleet Lifecycle
[Normal] Inventory, imaging, provisioning, acceptance tests, firmware/driver matrices, upgrades, drain/repair/replace and decommission.
[Normal] 17. Kubernetes, Slurm, and Workload Scheduling
[Normal] GPU device plugins, queues, quotas, topology-aware scheduling, isolation and tenant lifecycle.
[Normal] 18. Observability, SLOs, and Incident Response
[Normal] Host/GPU/NIC/switch telemetry, traces, dashboards, alerting, incident command, postmortems and remediation.
[Normal] 19. Reliability, Security, and Multi-Tenancy
[Normal] Fault domains, redundancy, checkpoint recovery, blast-radius control, RBAC, secrets and isolation.
[Normal] 20. Infrastructure Automation and Safe Change
[Normal] Python/shell/Go, APIs, Terraform, CI/CD, GitOps, config validation, staged rollout, rollback and fleet automation.
[Normal] 21. Capacity, Power, and Infrastructure Economics
[Normal] GPU utilization, network oversubscription, power/cooling constraints, capacity onboarding, cost and efficiency.
[Normal] 22. Cross-Layer Performance Engineering
[Normal] Diagnosis across compute, network, storage and orchestration; benchmark design, scaling efficiency and evidence-based tuning.
[Heading 2] PART VI — APPLIED ENGINEERING
[Normal] 23. Capstone: Design and Operate a Production-Scale AI Cluster
[Normal] Architecture, workload model, topology, provisioning, distributed workload, telemetry, fault injection, performance report and cost analysis.
[Normal] 24. Career Paths and Engineering Practice
[Normal] Competency maps for AI networking, GPU/HPC, cluster platform, performance, SRE/operations and hardware vendors.
[Heading 1] 5. Fourteen-week course plan
[Heading 1] 6. Capstone — build and troubleshoot an AI cluster
[List Bullet] Architecture: GPU nodes, host topology, leaf-spine fabric, storage, orchestration, security boundaries and failure domains.
[List Bullet] Workload: define a training or inference workload, scale, objectives and capacity assumptions.
[List Bullet] Network: document L2/L3 routing, BGP/ECMP, RoCEv2 or InfiniBand design, congestion controls and telemetry.
[List Bullet] Compute: map GPU, CPU, NUMA, PCIe, NVLink/NVSwitch and NIC locality; identify data paths.
[List Bullet] Operations: define hardware acceptance, firmware/driver compatibility, provisioning, scheduling, upgrades and remediation.
[List Bullet] Measurement: baseline throughput, latency percentiles, scaling efficiency, utilization and cost assumptions.
[List Bullet] Failure exercise: inject or simulate a link, node, storage, scheduling or workload failure; show detection and recovery.
[List Bullet] Final evidence: architecture, benchmark scripts/results, telemetry plan, runbook, postmortem and optimization proposal.
[Heading 1] 7. Assessment and completion criteria
[Normal] Completion requires demonstrated competence—not attendance alone. Learners must explain design trade-offs, troubleshoot at least one cross-layer failure, and support performance claims with reproducible evidence.
[Heading 1] 8. Lab environment and realism boundaries
[Normal] Core labs can use a Linux workstation or cloud VM: Python, shell, Linux networking tools, containers, Kubernetes/Slurm exercises, PyTorch CPU examples, topology diagrams, synthetic telemetry and benchmark analysis. Network emulation can help teach routing and topology; simulated fleet workflows can teach lifecycle automation.
[Normal] A laptop or simulation cannot validate production RDMA behavior, real InfiniBand/RoCE congestion, GPU-to-NIC locality, NVLink/NVSwitch performance, switch ASIC queue behavior, or multi-node GPU scaling. Label simulations explicitly. Offer optional hardware-backed or remote labs for these outcomes; never present simulated results as physical measurements.
[Heading 2] Suggested tools
[Normal] Linux; Python; Bash; Git; iproute2; ethtool; lspci; perf; eBPF/bpftrace concepts; CUDA/Nsight; PyTorch Distributed; NCCL; Kubernetes; Slurm; container runtimes; Prometheus/Grafana; Terraform; network emulation; and vendor diagnostics where available.
[Heading 1] 9. Role-specific specialization pathways
[Heading 1] 10. Employer ecosystem and role alignment
[Normal] The curriculum maps to recurring capability patterns across four employer groups. These are representative organizations, not a claim that each currently has an open role with the exact title implied.
[Heading 1] 11. Editorial and technical standards for the book
[List Bullet] Use a consistent chapter pattern: objectives, architecture, concepts, worked example, lab, troubleshooting scenario, trade-offs, review questions and further reading.
[List Bullet] Distinguish conceptual explanations, software simulations, emulated behavior and physical-hardware measurements.
[List Bullet] Include data-path diagrams for GPU↔GPU, GPU↔NIC, NIC↔switch, host↔storage and end-to-end training/inference.
[List Bullet] Version lab environments and scripts; record hardware, software, firmware, driver and topology assumptions.
[List Bullet] Include failure cases and operational runbooks—not only ideal-state architecture.
[List Bullet] Separate vendor-specific implementation details from protocol fundamentals and portable engineering principles.
[List Bullet] Refresh tool references and job-market mapping periodically; job postings are time-sensitive.
[Heading 1] 12. Recommended book positioning statement
[Normal] Learn to engineer the complete AI infrastructure stack—from GPU execution and high-speed fabrics to distributed training, LLM inference, and reliable production operations.
[Normal] The differentiator is a cross-layer perspective: networking, compute, orchestration and performance are taught as interdependent systems. Readers learn not only how each layer works, but how to prove where a workload is constrained and how to improve it safely.
[Heading 1] 13. Scope note on job-posting coverage
[Normal] This outline incorporates the four employer categories and technical requirements identified in the prior discussion: BGP/L2/L3, RoCEv2, InfiniBand, RDMA, CUDA, NVLink/NVSwitch, PyTorch/NCCL, switch and physical-layer engineering, bare-metal fleet lifecycle, distributed training, inference, storage, reliability, automation, security and capacity. It is a curriculum synthesis—not an independently verified census of 35+ currently active job postings. Any claim of a 35+ posting analysis should be supported by a dated, deduplicated register with employer, exact title, job ID, location, seniority, URL, date checked, required/preferred skills and active/archived status.
[Heading 1] Appendix — Suggested companion repository
[List Bullet] 01-foundations/ — architecture diagrams, Linux diagnostics and workload models.
[List Bullet] 02-gpu-compute/ — CUDA examples, profiling notes and topology inspection.
[List Bullet] 03-networking/ — BGP/ECMP exercises, RoCE/InfiniBand concepts and telemetry.
[List Bullet] 04-distributed-ai/ — PyTorch Distributed, NCCL benchmarks and scaling analysis.
[List Bullet] 05-fleet-platform/ — provisioning workflows, Kubernetes/Slurm examples and lifecycle automation.
[List Bullet] 06-inference-storage/ — serving benchmarks, checkpoint and data-pipeline exercises.
[List Bullet] 07-observability-reliability/ — dashboards, SLOs, incident simulations and runbooks.
[List Bullet] 08-capstone/ — reference architecture, workload assumptions, benchmark report and presentation.
[Heading 1] 14. Chapter-by-chapter exercises and practical labs
[Normal] Every chapter includes applied work. Exercises progress from concept checks and calculations to configuration, measurement, troubleshooting, and design. Where physical GPU, RDMA, InfiniBand, or switch hardware is unavailable, learners must label the activity as a simulation or analysis exercise and must not claim hardware validation.
[Heading 2] 1. The AI Infrastructure Landscape
[List Bullet] Draw a reference architecture for a model-training workload and a separate online-inference workload. Identify compute, network, storage, orchestration, and observability dependencies.
[List Bullet] Compare scale-up and scale-out communication for two hypothetical workloads. Explain which resource is likely to dominate and what evidence would confirm it.
[List Bullet] Create a role-to-skill matrix for an AI Network Engineer, GPU Cluster Engineer, and AI Infrastructure SRE.
[Normal] Deliverable: annotated architecture diagrams and a one-page workload comparison.
[Heading 2] 2. Anatomy of an AI Data Center
[List Bullet] Estimate the number of GPU servers, rack units, network ports, and fabric links for a small cluster using stated assumptions.
[List Bullet] Build a simplified capacity model that includes accelerator count, usable GPU memory, storage throughput, network bisection bandwidth, power, and utilization.
[List Bullet] Identify at least five single points of failure in a sample cluster design and propose mitigations.
[Normal] Deliverable: cluster bill of materials, capacity spreadsheet, and failure-domain diagram.
[Heading 2] 3. Linux, Host Systems, and Performance Diagnostics
[List Bullet] Use lscpu, numactl, free, vmstat, iostat, ip, ethtool, lspci, and dmesg to create a host inventory and diagnostic snapshot.
[List Bullet] Analyze a supplied case where CPU utilization is low but job throughput is poor. Form hypotheses involving memory locality, I/O wait, interrupts, or PCIe constraints.
[List Bullet] Write a Python or shell script that collects selected host metrics and produces a timestamped report.
[Normal] Deliverable: reusable host diagnostic script and troubleshooting report.
[Heading 2] 4. GPU Architecture and CUDA Execution
[List Bullet] Trace a simple vector-add or matrix-multiplication operation through host launch, kernel execution, memory movement, and synchronization.
[List Bullet] Use a CUDA sample or supplied profiler trace to identify launch overhead, memory-transfer cost, occupancy constraints, or memory bottlenecks.
[List Bullet] Explain how changing batch size or data layout could affect GPU utilization and memory behavior.
[Normal] Deliverable: annotated execution trace and a short GPU performance analysis.
[Heading 2] 5. GPU Interconnects and Host Topology
[List Bullet] Interpret a GPU/PCIe/NUMA topology diagram and identify which GPU-NIC pairings have the shortest expected data path.
[List Bullet] Compare a peer-to-peer GPU transfer with a host-staged transfer. Identify the extra copies and synchronization points in the latter.
[List Bullet] Given a multi-GPU node topology, propose rank placement and explain how you would validate the placement.
[Normal] Deliverable: topology map, locality recommendations, and validation checklist.
[Heading 2] 6. GPU Performance Engineering
[List Bullet] Construct a simple roofline-style analysis using supplied peak compute, memory bandwidth, and measured workload data.
[List Bullet] Design a benchmark protocol that controls warm-up, repetitions, concurrency, input size, software versions, and measurement noise.
[List Bullet] Analyze two benchmark runs and decide whether the apparent improvement is statistically and operationally meaningful.
[Normal] Deliverable: reproducible benchmark harness, results table, and performance conclusion.
[Heading 2] 7. Ethernet and Data-Center Network Foundations
[List Bullet] Design a two-tier leaf-spine topology for a specified number of GPU racks and calculate uplink/downlink ratios under stated port assumptions.
[List Bullet] Write a conceptual BGP/ECMP routing plan and describe expected behavior when a link, spine, or leaf fails.
[List Bullet] Troubleshoot a scenario involving an MTU mismatch, asymmetric routing, or incorrect route advertisement using a structured evidence checklist.
[Normal] Deliverable: topology diagram, routing policy summary, and failure-convergence analysis.
[Heading 2] 8. RDMA, RoCEv2, and InfiniBand
[List Bullet] Draw the data path for a message sent using conventional TCP sockets and compare it with an RDMA data path.
[List Bullet] Compare RoCEv2 and InfiniBand across transport, fabric management, operational model, and troubleshooting evidence.
[List Bullet] Create a pre-deployment checklist for an RDMA-capable cluster, including NIC, firmware, driver, addressing, MTU, and peer validation.
[Normal] Deliverable: RDMA design note and deployment-readiness checklist.
[Heading 2] 9. Congestion Control and Lossless-Fabric Engineering
[List Bullet] Analyze a synthetic time series containing queue depth, ECN marks, pause frames, throughput, and latency. Identify the likely congestion pattern.
[List Bullet] Explain why enabling PFC indiscriminately can create operational risks. Describe how you would investigate pause propagation and head-of-line blocking.
[List Bullet] Design a controlled experiment to compare congestion behavior under two documented configurations. State what cannot be concluded from a simulation.
[Normal] Deliverable: congestion diagnosis, experiment plan, and mitigation proposal.
[Heading 2] 10. Switches, Optics, Cabling, and Physical-Layer Operations
[List Bullet] Create a link commissioning checklist covering port configuration, transceiver compatibility, optical power, lane health, error counters, and cable labeling.
[List Bullet] Interpret a hypothetical set of CRC, symbol, FEC, and link-flap counters to distinguish physical-layer symptoms from higher-layer problems.
[List Bullet] Estimate port and cable requirements for a small leaf-spine fabric and identify operational spares.
[Normal] Deliverable: physical-layer runbook and port/cabling schedule.
[Heading 2] 11. Distributed Training Architecture
[List Bullet] Choose data, tensor, or pipeline parallelism for three example model/workload constraints and explain the communication implications.
[List Bullet] Estimate how step time changes when compute time, communication time, and synchronization overhead vary.
[List Bullet] Design a failure-aware training workflow with checkpoint frequency, restart behavior, and expected lost-work trade-offs.
[Normal] Deliverable: parallelism design, timing model, and recovery plan.
[Heading 2] 12. Collective Communication and NCCL
[List Bullet] Explain all-reduce, all-gather, reduce-scatter, and broadcast with small worked examples.
[List Bullet] Run or analyze an NCCL test result set across message sizes. Identify latency-dominated and bandwidth-dominated regions.
[List Bullet] Compare expected collective performance under two rank mappings and explain the topology information needed to validate the hypothesis.
[Normal] Deliverable: collective benchmark report with scaling and bottleneck analysis.
[Heading 2] 13. GPU-to-GPU and GPU-to-NIC Data Movement
[List Bullet] Trace a distributed training communication path from GPU memory through PCIe/NIC/fabric to a remote GPU.
[List Bullet] Analyze a scenario where GPU utilization is low while network utilization is high; determine whether communication, synchronization, or data imbalance is responsible.
[List Bullet] Propose measurements to validate GPUDirect RDMA and GPU/NIC locality on a supported hardware platform.
[Normal] Deliverable: annotated data-path diagram and cross-layer diagnosis.
[Heading 2] 14. Storage, Data Pipelines, and Checkpointing
[List Bullet] Estimate checkpoint size, write time, and recovery point exposure for a stated model and storage bandwidth.
[List Bullet] Compare a data pipeline limited by small-file metadata operations with one limited by sequential bandwidth.
[List Bullet] Design a checkpoint strategy that balances checkpoint overhead, storage capacity, restart time, and failure frequency.
[Normal] Deliverable: I/O benchmark plan and checkpoint/recovery design.
[Heading 2] 15. LLM Inference and Serving Infrastructure
[List Bullet] Model how batch size, sequence length, KV-cache footprint, and concurrency affect memory demand and serving capacity.
[List Bullet] Analyze a serving trace using time-to-first-token, inter-token latency, throughput, queue time, and GPU utilization.
[List Bullet] Compare two serving configurations and recommend one for latency-sensitive and another for throughput-oriented service objectives.
[Normal] Deliverable: inference capacity model and tuning recommendation.
[Heading 2] 16. Bare-Metal GPU Fleet Lifecycle
[List Bullet] Design a node acceptance test covering accelerator discovery, memory checks, NIC link validation, storage, thermals, and burn-in.
[List Bullet] Create a firmware/driver compatibility matrix and a staged upgrade plan with canary, rollback, and maintenance windows.
[List Bullet] Write a state machine for node lifecycle: discovered, imaged, validated, schedulable, drained, repair, and retired.
[Normal] Deliverable: node acceptance automation specification and lifecycle runbook.
[Heading 2] 17. Kubernetes, Slurm, and Workload Scheduling
[List Bullet] Compare Kubernetes and Slurm for interactive inference, batch training, and tightly coupled multi-node jobs.
[List Bullet] Design a scheduling policy that considers GPU type, topology, quotas, queue fairness, and gang placement.
[List Bullet] Troubleshoot a job that is pending despite apparently free GPUs; list scheduler, device-plugin, topology, quota, and node-health evidence.
[Normal] Deliverable: workload placement policy and scheduling troubleshooting guide.
[Heading 2] 18. Observability, SLOs, and Incident Response
[List Bullet] Define service-level indicators for training job completion, inference latency, cluster availability, and fabric health.
[List Bullet] Design a dashboard hierarchy from fleet overview to node, GPU, NIC, switch, and workload detail.
[List Bullet] Write an incident timeline and postmortem for a hypothetical cluster-wide throughput regression.
[Normal] Deliverable: SLO specification, dashboard mock-up, and blameless postmortem.
[Heading 2] 19. Reliability, Security, and Multi-Tenancy
[List Bullet] Perform a failure-mode analysis for GPU node, rack, leaf switch, storage, scheduler, and control-plane failures.
[List Bullet] Define tenant isolation boundaries for identity, network, storage, GPU allocation, secrets, and audit logs.
[List Bullet] Design a recovery exercise that tests fault containment and validates that one tenant's failure does not disrupt another.
[Normal] Deliverable: risk register, isolation model, and recovery test plan.
[Heading 2] 20. Infrastructure Automation and Safe Change
[List Bullet] Write an idempotent script or infrastructure-as-code example to validate a node or network configuration.
[List Bullet] Design a canary rollout with prechecks, success criteria, abort conditions, rollback, and audit evidence.
[List Bullet] Review a deliberately unsafe change plan and identify missing validation, blast-radius controls, and rollback mechanisms.
[Normal] Deliverable: automation sample and safe-change runbook.
[Heading 2] 21. Capacity, Power, and Infrastructure Economics
[List Bullet] Build a capacity forecast from accelerator supply, workload demand, utilization, maintenance reserve, and expected growth.
[List Bullet] Compare two cluster designs on useful throughput per dollar and per watt using explicit assumptions.
[List Bullet] Identify bottlenecks that make nominal GPU count a misleading measure of usable capacity.
[Normal] Deliverable: capacity model and cost/performance decision memo.
[Heading 2] 22. Cross-Layer Performance Engineering
[List Bullet] Investigate an end-to-end workload regression using supplied GPU, CPU, network, storage, and scheduler metrics.
[List Bullet] Build a hypothesis tree and rank tests by information value, cost, and risk.
[List Bullet] Write a before/after report that separates measured facts, inferred causes, and remaining uncertainty.
[Normal] Deliverable: evidence-based root-cause report and validated optimization.
[Heading 2] 23. Capstone: Design and Operate a Production-Scale AI Cluster
[List Bullet] Complete one of the capstone tracks in Section 16 below.
[List Bullet] Conduct a design review with explicit assumptions, trade-offs, failure domains, and operational constraints.
[List Bullet] Present benchmark evidence, failure exercise results, and a prioritized next-step backlog.
[Normal] Deliverable: complete capstone portfolio.
[Heading 2] 24. Career Paths and Engineering Practice
[List Bullet] Select a target role and map current skills to the role's competency requirements.
[List Bullet] Prepare a system-design interview presentation for an AI cluster or AI network problem.
[List Bullet] Write a concise incident or performance case study that communicates evidence, trade-offs, and impact.
[Normal] Deliverable: role-readiness matrix, portfolio narrative, and technical presentation.
[Heading 1] 15. Progressive practical lab sequence
[Normal] The following sequence turns individual chapter exercises into a coherent hands-on learning path. It is designed to work in a laptop-first environment, with optional hardware-backed extensions.
[Heading 1] 16. Major capstone projects
[Normal] Learners should complete one primary capstone and, optionally, one specialization mini-capstone. Each project must include a written problem statement, architecture, assumptions, implementation or simulation boundary, test plan, results, failure analysis, security considerations, and a final engineering review.
[Heading 2] Capstone A — Design a 256-GPU AI training cluster
[Normal] Audience: AI infrastructure architect, cluster engineer, network engineer.
[Normal] Required artifacts: Architecture and bill of materials; network and host topology; workload/communication model; capacity and power assumptions; acceptance plan; failure analysis; cost/performance trade-off memo.
[Normal] Advanced extension: compare two fabric or topology options and quantify expected oversubscription and communication consequences. Physical claims require a real compatible lab.
[Heading 2] Capstone B — Build an AI network troubleshooting and telemetry system
[Normal] Audience: AI Network Engineer, Network Operations Engineer.
[Normal] Required artifacts: Telemetry schema; parser or collector; dashboards or report; alert rules; runbook; injected-fault scenarios; false-positive discussion; incident report.
[Normal] Advanced extension: use streaming telemetry or lab switch counters and validate a suspected congestion issue on physical hardware.
[Heading 2] Capstone C — Distributed training performance optimization
[Normal] Audience: GPU/HPC engineer, AI Performance Engineer.
[Normal] Required artifacts: Reproducible benchmark harness; environment manifest; baseline and optimized measurements; scaling-efficiency analysis; profiler evidence; root-cause narrative.
[Normal] Advanced extension: multi-node GPU tests with NCCL and supported RDMA hardware; clearly report run-to-run variation and limitations.
[Heading 2] Capstone D — Production LLM inference platform
[Normal] Audience: AI Platform Engineer, Inference Infrastructure Engineer.
[Normal] Required artifacts: Service architecture; capacity model; SLO/SLI definitions; load-test plan; TTFT/inter-token latency/throughput results or modeled estimates; rollout and rollback plan; cost analysis.
[Normal] Advanced extension: run a supported open model and serving stack; compare configurations under identical workload and hardware conditions.
[Heading 2] Capstone E — Bare-metal GPU fleet lifecycle automation
[Normal] Audience: Cluster Platform Engineer, Infrastructure SRE.
[Normal] Required artifacts: Lifecycle state machine; node acceptance test plan; compatibility matrix; automation prototype; canary/rollback design; audit trail; operational runbook.
[Normal] Advanced extension: integrate a lab provisioning system and real hardware health checks.
[Heading 2] Capstone F — AI infrastructure reliability game day
[Normal] Audience: AI Infrastructure SRE, Production Engineer.
[Normal] Required artifacts: Fault-injection plan; expected behavior; telemetry and alerts; incident timeline; recovery evidence; blameless postmortem; prioritized reliability backlog.
[Normal] Advanced extension: conduct safe fault injection in a dedicated non-production lab with explicit rollback and isolation.
[Heading 1] 17. Capstone scoring rubric
[Normal] Suggested pass threshold: 70/100 overall, with no score below 50% in technical correctness or measurement. A distinction-level project should score 90/100 or higher and include reproducible evidence.
[Heading 1] 18. Standard exercise template for every chapter
[Normal] To keep the book consistent, each chapter should end with a structured exercise set:
[Heading 1] 19. Instructor and author guidance
[List Bullet] Provide starter files, sample telemetry, expected outputs, and a grading rubric for every lab.
[List Bullet] Offer three lab tiers: Level 1 laptop/simulation; Level 2 single-GPU or cloud GPU; Level 3 multi-node GPU plus RDMA/InfiniBand hardware.
[List Bullet] Include both learner tasks and instructor solutions in a separate answer-key repository or companion resource.
[List Bullet] Use intentionally flawed traces and configurations to teach diagnosis rather than only happy-path setup.
[List Bullet] For every benchmark, require an environment manifest, repeated runs, warm-up policy, workload definition, and clear distinction between measured and modeled values.
[List Bullet] Keep safety boundaries explicit: no production changes, disruptive fault injection, or changes to shared fabrics without authorization and a controlled test environment.
[Heading 1] 20. Definitive-edition technical enhancements
[Normal] This revision incorporates the four specialist review recommendations: distributed-training fault tolerance, disaggregated inference, facility-level power and cooling, and topology-aware multi-rail NIC/GPU mapping. These are treated as core engineering competencies rather than optional footnotes.
[Heading 2] 20.1 Distributed-training fault tolerance at scale
[Normal] At large GPU-cluster scale, hardware and fabric faults must be expected and engineered for. A single uncorrectable GPU error, PCIe fatal event, degraded NIC/HCA, intermittent link, or collective-communication hang can reduce useful cluster throughput or stall a distributed job. The book should teach detection, containment, recovery, and evidence-based diagnosis.
[List Bullet] GPU and host error taxonomy: correctable/uncorrectable ECC, row-remapping or retired pages where applicable, Xid events, thermal/power events, PCIe AER, link retraining, NIC/HCA health, and firmware/driver incompatibility.
[List Bullet] Distributed failure signatures: NCCL timeout or hang, rank loss, collective mismatch, straggler amplification, fabric partition, packet loss/congestion, and host-side stalls.
[List Bullet] Fast isolation workflow: correlate job/rank identity with GPU UUID, PCIe BDF, NUMA node, NIC/HCA, switch port, link counters, kernel logs, and scheduler events.
[List Bullet] Containment: mark a device or node unhealthy, prevent new placement, drain safely, isolate the smallest defensible failure domain, preserve diagnostic evidence, and return hardware only after acceptance checks.
[List Bullet] Recovery design: coordinated restart, elastic or fault-tolerant training where supported, checkpoint selection, rank remapping, spare capacity, and explicit policies for retry loops.
[List Bullet] Checkpoint systems: PyTorch Distributed Checkpoint (DCP), asynchronous checkpointing concepts, sharded state, staging buffers, consistency boundaries, metadata durability, restore validation, and Megatron-LM asynchronous save workflows where applicable.
[List Bullet] Measure checkpoint overhead, checkpoint completion latency, recovery time objective (RTO), recovery point objective (RPO), lost accelerator-hours, and time-to-resume.
[Normal] New chapter-level exercise: Given a synthetic 512-node training incident with one flaky HCA, one GPU ECC fault, and an NCCL timeout, correlate logs and telemetry, identify the smallest failure domain, quarantine the suspect component, and produce a safe restart plan. Distinguish proven cause from correlation.
[Normal] Required evidence: failure timeline, rank-to-hardware mapping, health decision, checkpoint/restore validation, recovery metrics, and postmortem.
[Heading 2] 20.2 Disaggregated LLM serving and advanced decoding
[Normal] Chapter 15 should move beyond single-pool serving and explicitly teach the infrastructure consequences of separating prefill and decode into distinct resource pools. The data path between phases becomes a first-class performance and reliability concern.
[List Bullet] Disaggregated prefill/decode architecture: independent pools, scheduling, admission control, load balancing, heterogeneous accelerator placement, and capacity planning.
[List Bullet] KV-cache transfer: size estimation, serialization/layout, transport selection, bandwidth demand, congestion, transfer overlap, locality, and cache lifecycle.
[List Bullet] Network design for KV movement: RoCEv2/RDMA where supported, TCP alternatives, isolation, QoS, congestion control, encryption/security boundaries, and failure behavior.
[List Bullet] Advanced decoding: speculative decoding, draft/target model placement, acceptance rate, memory footprint, communication overhead, and latency/throughput trade-offs.
[List Bullet] Serving SLOs: TTFT, time per output token/inter-token latency, end-to-end latency, tokens/sec, queueing delay, KV transfer time, and GPU utilization by phase.
[Normal] New exercise: Model a prompt workload split across prefill and decode pools. Estimate KV-cache bytes per request and aggregate transfer bandwidth at target concurrency; compare a shared-pool design with disaggregated serving over RDMA and TCP assumptions.
[Normal] Required evidence: capacity model, network budget, phase-specific SLOs, bottleneck analysis, and an explicit statement of which values are measured versus modeled.
[Heading 2] 20.3 Facility engineering: power density, thermal transients, and liquid cooling
[Normal] AI infrastructure architects must understand the facility envelope. High-density accelerator racks can create power-delivery and heat-removal requirements that materially affect cluster topology, deployment schedules, utilization, and reliability. Rack power figures are platform- and configuration-dependent; any cited value (including approximately 120 kW-class designs) must be tied to a specific vendor reference design and date rather than treated as a universal rack standard.
[List Bullet] Power chain: utility and facility capacity, UPS, busway, rack PDUs, branch circuits, power shelves, redundancy modes, telemetry, and safe operating limits.
[List Bullet] Dynamic power behavior: accelerator TDP, transient demand, power capping, workload-driven peaks, throttling, power headroom, and implications for concurrent job scheduling.
[List Bullet] Cooling fundamentals: air vs. liquid cooling, direct-to-chip cold plates, coolant distribution units (CDUs), supply/return loops, manifolds, flow, pressure, temperature delta, leak detection, and serviceability.
[List Bullet] Facility interfaces: MEP coordination, rack placement, weight and floor loading, electrical commissioning, coolant quality, maintenance access, and operational ownership boundaries.
[List Bullet] Thermal-performance coupling: GPU temperature, clock behavior, throttling, inlet temperature, coolant conditions, and how facility constraints alter achievable sustained performance.
[Normal] New exercise: For a hypothetical high-density rack, construct a power and heat-removal budget using explicitly stated assumptions. Include PDU headroom, redundancy, transient margin, CDU capacity, coolant flow/temperature assumptions, and a safe operating envelope.
[Normal] Required evidence: power one-line concept, thermal/cooling block diagram, rack budget, assumptions register, and a facility/MEP handoff checklist.
[Heading 2] 20.4 NUMA geometry, multi-rail mapping, and GPUDirect RDMA labs
[Normal] Chapter 5 and Week 3 should include a concrete topology-mapping lab. Correct GPU-to-NIC affinity is not a cosmetic optimization: PCIe root-complex crossings, socket-to-socket traffic, and poorly selected HCA rails can reduce effective bandwidth and create latency variance that becomes visible in collectives.
[List Bullet] Read and interpret nvidia-smi topo -m output; identify GPU-GPU, GPU-NIC, CPU affinity, and NVLink/PCIe relationship labels for the installed platform.
[List Bullet] Use lstopo / hwloc to inspect sockets, NUMA nodes, PCIe root complexes, bridges, NIC/HCA placement, and GPU devices.
[List Bullet] Map GPU UUID and PCIe BDF to NIC/HCA PCIe BDF, NUMA node, physical slot, and fabric rail. Keep a machine-readable mapping artifact.
[List Bullet] Compare a topology-aligned mapping with a deliberately poor cross-socket or oversubscribed mapping. Measure or model bandwidth, collective duration, tail latency, and run-to-run variance.
[List Bullet] Validate GPUDirect RDMA prerequisites and path: platform support, driver/firmware compatibility, IOMMU/ACS configuration as applicable, peer-memory mechanism, and vendor guidance. Do not assume the feature is active merely because the software stack is installed.
[List Bullet] Teach multi-rail assignment as a joint placement problem involving GPU locality, NIC/HCA locality, CPU affinity, rail balance, switch paths, and job rank mapping.
[Normal] New lab: Capture nvidia-smi topo -m and lstopo output on a supported multi-GPU host. Build a table mapping each GPU to its nearest NIC/HCA, PCIe root, NUMA node, and candidate rail. Create aligned and intentionally misaligned rank/rail maps, then compare NCCL all-reduce results on hardware or a clearly labeled topology/performance model.
[Normal] Required evidence: raw topology outputs, annotated topology diagram, mapping CSV, benchmark methodology, measured results (if hardware is available), and explanation of limitations.
[Heading 1] 21. Updated chapter and course integration map
[Heading 1] 22. New integrated capstone options
[Heading 2] Capstone G — Fault-tolerant 512-node distributed training operations
[Normal] Design a training operations workflow for a 512-node cluster. Simulate or use a controlled lab dataset containing GPU ECC events, PCIe AER errors, degraded NIC/HCA links, switch-port errors, rank stalls, and collective timeouts. Implement correlation, health scoring, quarantine, checkpoint selection, restart orchestration, and post-incident validation.
[List Bullet] Required outputs: rank-to-device topology inventory; telemetry correlation logic; failure classification; quarantine policy; asynchronous checkpoint and restore plan; RTO/RPO measures; recovery runbook; and blameless postmortem.
[List Bullet] Success criteria: detect and isolate the injected fault within a defined target, avoid repeatedly scheduling the unhealthy device, restore from a validated checkpoint, and show evidence that the job resumes correctly. State clearly if the environment is simulated.
[Heading 2] Capstone H — Disaggregated LLM serving across prefill and decode pools
[Normal] Design a two-pool serving architecture with separate prefill and decode capacity. Model KV-cache movement, transport choices, network bandwidth, concurrency, heterogeneous accelerators, speculative decoding, admission control, and phase-specific SLOs.
[List Bullet] Required outputs: service architecture; KV-cache size and transfer model; RDMA/TCP comparison; network QoS/isolation design; capacity model; TTFT/inter-token latency/throughput targets; failure scenarios; and cost/performance recommendation.
[List Bullet] Success criteria: identify the bottleneck at target concurrency, explain when disaggregation helps or hurts, and support the recommendation with reproducible measurements or explicitly labeled modeling.
[Heading 1] 23. Revised quality assessment and release gates
[Normal] The earlier outline was strong in breadth and practical orientation but under-specified four increasingly important production concerns. With these additions, the curriculum is substantially more complete. The score below is an editorial assessment of the course outline as a design artifact—not a rating of a finished manuscript, tested labs, or independently audited job-market dataset.
[Heading 2] Release gates before claiming a definitive 9.5+ book
[List Bullet] Validate every lab on its stated environment tier; publish exact prerequisites, versions, expected outputs, and known limitations.
[List Bullet] Have an experienced GPU-cluster/network engineer review topology, RDMA, NCCL, checkpointing, and failure-recovery chapters.
[List Bullet] Have a data-center facilities specialist review power, liquid cooling, CDU, PDU, and MEP material.
[List Bullet] Verify all vendor-specific claims and version-sensitive APIs against current primary documentation; cite date and platform assumptions.
[List Bullet] Run all benchmark and failure-injection procedures in a safe lab; preserve raw results and reproducibility instructions.
[List Bullet] Conduct a technical copyedit for consistent terms, diagrams, units, acronyms, and separation of measured results from illustrative examples.
[List Bullet] Do not describe the manuscript itself as 9.5+/10 until the complete book, code repository, lab solutions, diagrams, and technical validation have been reviewed.
TABLES 10
--- table 0
Domain | Required knowledge and capability
AI data-center architecture | GPU clusters, scale-up/scale-out, rack/pod topology, power/cooling, capacity, cost and utilization
Linux and host systems | Processes, memory, NUMA, CPU affinity, PCIe, drivers, firmware, kernel and network diagnostics
GPU and accelerator compute | GPU architecture, CUDA execution, memory hierarchy, profiling, NVLink/NVSwitch
L2/L3 networking | Ethernet, VLANs, IPv4/IPv6, routing, BGP, ECMP, MTU, QoS, convergence and failure isolation
AI networking fabrics | RDMA, RoCEv2, InfiniBand, lossless Ethernet concepts, ECN, PFC trade-offs, congestion and multi-rail
Physical and switching layer | Switch ASICs, buffers, queues, port architecture, optics, transceivers, cabling and link budgets
Distributed AI communication | PyTorch Distributed, NCCL collectives, rank mapping, GPUDirect RDMA, stragglers and overlap
Fleet and orchestration | Bare-metal imaging, provisioning, acceptance, firmware/driver lifecycle, Kubernetes, Slurm and placement
Storage and data movement | NVMe, parallel filesystems, data pipelines, caching, checkpointing and I/O tail latency
LLM serving | Prefill/decode, batching, KV cache, quantization, TTFT, inter-token latency and throughput
Reliability and operations | Telemetry, SLOs, fault domains, incident response, checkpoint/restart and automated remediation
Automation and security | Python, shell, Go/C++, Terraform, CI/CD, GitOps, RBAC, secrets and tenant isolation
Performance engineering | Workload characterization, benchmarking, profiling, percentiles, scaling efficiency and reproducibility
--- table 1
Wk | Module | Topics and activities | Deliverable
1 | AI data-center architecture and economics | GPU cluster anatomy; training/inference; scale-up/scale-out; rack, pod, fabric, storage, power and capacity. | Architecture diagram and workload assumptions.
2 | Linux, host systems and diagnostics | CPU, memory, NUMA, PCIe, drivers, firmware, network interfaces and Linux troubleshooting. | Host diagnostic runbook and baseline.
3 | GPU compute and interconnects | CUDA execution, GPU memory, profiling, PCIe, NVLink/NVSwitch and GPU-to-NIC locality. | GPU profiling exercise and topology analysis.
4 | Ethernet, L2/L3 and BGP fabrics | VLANs, IP, MTU, BGP, ECMP, leaf-spine, QoS and convergence. | Fabric design and failure analysis.
5 | RDMA, RoCEv2 and InfiniBand | RDMA concepts, RoCEv2/InfiniBand, transport behavior and multi-rail fabrics. | RDMA/RoCE design worksheet or simulation.
6 | Congestion, switching and physical layer | Queues, buffers, ECN, PFC trade-offs, optics, transceivers, cabling and commissioning. | Congestion troubleshooting tree and physical checklist.
7 | Bare-metal provisioning and fleet lifecycle | Imaging, acceptance, compatibility matrices, upgrades, drain, repair and replacement. | Node acceptance checklist and lifecycle workflow.
8 | Kubernetes, Slurm and workload placement | GPU scheduling, quotas, topology awareness, isolation and tenant provisioning. | Deploy or simulate a scheduled GPU workload.
9 | Distributed training and NCCL | PyTorch Distributed, collectives, rank placement, NCCL tests and communication bottlenecks. | Collective benchmark and scaling analysis.
10 | LLM inference and serving | Prefill/decode, batching, KV cache, quantization, TTFT and throughput/latency trade-offs. | Inference benchmark plan and optimization report.
11 | Storage, data movement and checkpointing | I/O paths, data staging, caching, checkpoint duration and recovery. | Checkpoint/data-pipeline design.
12 | Observability, SLOs and reliability | Cross-layer telemetry, SLOs, incident investigation and fault recovery. | Dashboard specification, incident report and postmortem.
13 | Automation, security and capacity | Infrastructure as code, safe rollout, tenant isolation, capacity and cost modeling. | Automated change plan and capacity model.
14 | Integrated capstone and technical review | Present cluster design; demonstrate workload, telemetry, failure analysis and measured improvement. | Portfolio-ready architecture, runbook and benchmark report.
--- table 2
Assessment | Weight | Evidence
Knowledge checks and design reviews | 15% | Accurate concepts, architecture and trade-off explanations.
Hands-on labs and troubleshooting | 30% | Reproducible diagnostics, configurations/simulations and root-cause reasoning.
Performance and benchmark assignments | 20% | Valid methodology, baselines, repeatability, percentile analysis and conclusions.
Capstone project | 35% | Integrated architecture, operational plan, failure exercise, measured results and communication.
--- table 3
Role | Primary emphasis | Advanced electives
AI Network Engineer | BGP, Ethernet, RoCEv2, InfiniBand, RDMA, congestion, optics and switch telemetry | Advanced fabric design; RDMA tuning; network operations.
GPU Compute / HPC Engineer | CUDA, GPU architecture, PCIe, NVLink/NVSwitch, NUMA and NCCL | GPU profiling; distributed collectives; accelerator topology.
AI Cluster / Platform Engineer | Bare metal, fleet lifecycle, Kubernetes, Slurm, scheduling and tenant operations | Fleet automation; scheduler internals; cluster capacity.
AI Performance Engineer | Workload characterization, profiling, benchmarking and optimization | Roofline analysis; distributed scaling; inference performance.
AI Infrastructure SRE / Operations | Observability, SLOs, incidents, reliability, remediation and safe change | Incident simulation; fault injection; automated recovery.
Network Hardware / Vendor Engineer | Switch ASICs, buffers, queues, optics, NICs, validation and interoperability | Hardware validation; congestion characterization; interoperability.
--- table 4
Employer group | Representative organizations | Recurring engineering problems
Hyperscalers / CSPs | Meta, Microsoft Azure, AWS, Google Cloud, Oracle OCI | Large-scale network/compute architecture, GPU fleet operations, reliability, capacity and automation.
AI cloud / neocloud | CoreWeave, Lambda, Crusoe, Hut 8, Highrise AI, Together AI | Rapid GPU cluster deployment, bare-metal lifecycle, tenant provisioning, utilization and network performance.
Frontier AI labs | OpenAI, Anthropic, ByteDance/TikTok, xAI | Training-cluster scale, high-performance networking, distributed compute, inference and reliability.
Hardware / networking vendors | NVIDIA, Broadcom, Arista Networks, AMD, Cisco | GPU/NIC/switch architecture, ASIC and buffer behavior, optics, interoperability and validation.
--- table 5
Lab | Build or investigate | Core skills demonstrated
Lab 1 — Host discovery | Create a repeatable Linux host inventory and health snapshot. | Linux, scripting, CPU/memory/NUMA, PCIe, NIC inventory.
Lab 2 — Fabric design | Model a leaf-spine fabric, addressing plan, BGP/ECMP intent and failure cases. | L2/L3, BGP, ECMP, topology and convergence.
Lab 3 — Network telemetry | Parse interface counters and synthetic queue/ECN/PFC data; detect anomalies. | Network operations, congestion signals, telemetry.
Lab 4 — GPU baseline | Run an available GPU workload or analyze a supplied profiler capture; establish repeatable baselines. | CUDA concepts, profiling, benchmark discipline.
Lab 5 — Distributed communication | Run PyTorch distributed examples or analyze provided collective benchmarks. | Distributed training, NCCL concepts, scaling.
Lab 6 — Storage and checkpoint | Measure or model I/O throughput, checkpoint duration and restart costs. | Storage, data pipelines, resilience.
Lab 7 — Scheduler and fleet lifecycle | Model node admission, scheduling eligibility, drain, repair and return to service. | Bare metal, Kubernetes/Slurm concepts, automation.
Lab 8 — Observability and incident | Create a small metrics dashboard or analyze a supplied telemetry bundle; write a postmortem. | SLOs, incident response, root-cause analysis.
--- table 6
Dimension | Weight | 9–10 / excellent evidence
Problem framing and assumptions | 10% | Workload, scale, constraints and assumptions are explicit, realistic and testable.
Architecture and technical correctness | 20% | Compute, network, storage and orchestration design is coherent; data paths and dependencies are correctly explained.
Implementation / reproducibility | 15% | Scripts, configurations, models or simulations are repeatable; environment and limitations are documented.
Measurement and analysis | 20% | Baselines, percentiles, scaling, utilization and comparisons use sound methods; conclusions match evidence.
Reliability, security and operations | 15% | Failure domains, isolation, SLOs, rollback, recovery and operational ownership are addressed.
Troubleshooting and engineering judgment | 10% | Hypotheses are ranked, tests are discriminating, root cause is evidence-based and trade-offs are acknowledged.
Communication and portfolio quality | 10% | Diagrams, report, runbooks and presentation are clear enough for another engineer to review and reproduce.
--- table 7
Exercise type | Purpose | Suggested quantity
Knowledge check | Verify vocabulary, concepts and protocol/system understanding. | 5–8 questions
Worked problem | Apply calculations, architecture reasoning or performance models. | 1–2 problems
Hands-on lab | Use tools, scripts, configuration, traces or datasets. | 1 core lab
Troubleshooting case | Diagnose a realistic failure from incomplete evidence. | 1 scenario
Design challenge | Make and defend an engineering trade-off. | 1 prompt
Reflection / review | State limitations, assumptions and what evidence is still missing. | 3–5 questions
--- table 8
Existing location | Required enhancement | New learner evidence
Chapter 2 / Week 1 | Add rack power density, TDP/transients, PDU/UPS, direct-to-chip cooling, CDUs, manifolds, coolant flow/pressure, MEP interfaces. | Rack power/thermal budget and facility interface diagram.
Chapter 5 / Week 3 | Add nvidia-smi topo -m and lstopo interpretation, GPU/NIC/HCA mapping, NUMA and PCIe-root locality, multi-rail assignment. | Topology map, GPU-to-HCA mapping CSV and aligned/misaligned benchmark.
Chapter 14 / Week 11 | Add asynchronous/sharded checkpointing, DCP, Megatron-LM async-save concepts, checkpoint consistency and restore validation. | Checkpoint benchmark, RPO/RTO analysis and restore test.
Chapter 15 / Week 10 | Add disaggregated prefill/decode, KV-cache transfer over RDMA/TCP, heterogeneous pools and speculative decoding. | KV transfer model, phase SLOs and serving architecture.
Chapter 19 / Week 12 | Add rapid failure isolation for GPU ECC, PCIe AER, NIC/HCA and fabric faults; rank-to-device correlation and quarantine. | Fault-isolation runbook, failure-injection/tabletop report and recovery proof.
Chapter 21 / Week 13 | Add facility capacity, rack power limits, liquid cooling constraints, transient headroom, power capping and workload/facility coordination. | Capacity/power/cooling model and operational guardrails.
--- table 9
Dimension | Revised score | Why
Technical breadth and role alignment | 9.7/10 | Covers compute, network, distributed AI, fleet operations, inference, storage, reliability and facility constraints.
Depth in production-scale systems | 9.6/10 | Now includes failure isolation, async checkpointing, disaggregated serving, topology-aware rails and facility engineering.
Hands-on learning design | 9.7/10 | Chapter exercises, progressive labs, multiple capstones, artifacts and scoring rubric.
Measurement and engineering rigor | 9.6/10 | Requires baselines, repeatability, RPO/RTO, SLOs, measured-vs-modeled separation and evidence-based diagnosis.
Editorial structure and teachability | 9.6/10 | Clear progression from fundamentals to specialist production systems and applied projects.
Overall course-outline rating | 9.6/10 | Strong, differentiated and near-release-ready as a curriculum specification.
```
