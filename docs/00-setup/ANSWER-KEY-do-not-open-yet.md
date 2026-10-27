# ANSWER KEY - do not open until you have finished the Phase 1 design review

Open this only after you have written your own list of flaws. Compare, and note what you missed.

## Design flaws (found in Phase 1, fixed in Phases 3 to 5)
| # | Flaw | Where | Fixed by |
|---|------|-------|----------|
| 1 | payments-svc published on host port 18002 | docker-compose.yml | Phase 1 pattern: gateway-only ingress; Phase 5 network policy |
| 2 | Plain HTTP between gateway and services | nginx.conf, PAYMENTS_URL | Phase 4: mTLS |
| 3 | No authentication between orders-api and payments-svc | payments-svc/main.py | Phase 4: service identity + mTLS |
| 4 | orders-api uses the Postgres superuser | docker-compose.yml, DB_USER | Phase 4: least-privilege DB role |

## Code flaws (found by tools in Phase 3, fixed in Phase 4)
| Flaw | Where | Found by |
|------|-------|----------|
| SQL injection in product search | orders-api/main.py `products()` | Semgrep (SAST), ZAP (DAST) |
| MD5 password hashing | orders-api/main.py `register()` / `login()` | Semgrep, manual review |
| Hardcoded JWT secret ("secret123"): tokens can be forged | orders-api/main.py `JWT_SECRET` | Semgrep, Gitleaks |
| Broken access control: any order readable without login | `GET /orders/{id}` | Manual review, ZAP |
| user_id supplied by the client when creating an order | `POST /orders` | Manual review (threat model) |
| No input validation (negative quantity, huge values) | `OrderIn` model | Manual review, DAST |
| Full card number written to logs | payments-svc/main.py `charge()` | Manual review, threat model |
| Database error text returned to the caller | `products()` error handler | DAST |

## Supply chain and container flaws (Phase 3)
- Old pinned dependencies with known CVEs: fastapi 0.109.0, starlette (pulled in by fastapi), python-multipart 0.0.6, PyJWT 2.3.0. `pip-audit` and Trivy will list the exact IDs.
- Containers run as root, use full (not slim) base images and unpinned tags.
- No SBOM, no image signing, no branch protection, no CI at all yet.
- No rate limiting, no WAF, no security headers, no audit logging.
