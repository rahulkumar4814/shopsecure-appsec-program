# ShopSecure AppSec Program

## Objective
Run the application security program for a fictional online store (ShopSecure) the way a
Security Application Engineering Manager would, so that every capability in the target job
description is practised hands-on and backed by evidence you can show in an interview.

By the end you will have:
1. A working microservices app (gateway, orders-api, payments-svc, Postgres) taken from a deliberately weak v1 to a hardened v2.
2. A CI/CD pipeline that blocks insecure code (SAST, SCA, secrets, DAST, SBOM, signing, IaC scan).
3. Seven manager artifacts: HLD/LLD + ADRs, threat model, gate policy, API baseline, WAF tuning notes, SLA standard + exception register, KPI scorecard.
4. A control mapping to NIST 800-53 / CIS v8 and a one-page executive summary.
5. A 60-second interview answer for each concept.

## Success measures (mirror the JD KRIs/KPIs)
- Threat model exists for the checkout flow; ASVS L2 checklist completed.
- SAST, SCA, secrets and DAST run on every pull request and fail the build on critical/high.
- SBOM generated and image signed on every release.
- Every API passes the baseline hardening checklist (authN, authZ, input validation, TLS/mTLS).
- WAF blocked vs allowed baseline recorded, false positives tuned.
- Findings tracked with severity SLAs; at least one exception with compensating control and expiry.
- Scorecard published: coverage %, gate pass rate, time-to-remediate, WAF false-positive rate.

## Folder layout
- app/        the three services (generated in Phase 0)
- docs/       one folder per phase: the manager artifacts you write
- infra/      Terraform (scanned, never applied) and Kubernetes manifests
- evidence/   screenshots, scan reports, logs that prove each control works
- JOURNAL.md  what you did, why, outcome, next step (one entry per session)

## Phases
0 Setup (1.5h) | 1 Secure system design (4h) | 2 Threat modeling + secure SDLC (3h) |
3 Pipeline gates + supply chain (5h) | 4 API + service hardening (5h) |
5 WAF + K8s guardrails (4h) | 6 Vulnerability management + scorecard (3h)

Living playbook (concept pages + progress tracker): https://claude.ai/artifact/E98esLnvd9UaJRTrNDDQEw

## Quick start
Follow `docs/00-setup/RUNBOOK.md` step by step (14 steps, every command included).
Short version, from this folder in PowerShell: `docker compose up -d --build`, then `python scripts\smoke_test.py`.
Do not open `docs/00-setup/ANSWER-KEY-do-not-open-yet.md` until Phase 1 is finished.
