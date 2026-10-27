# Phase 0 Runbook: set up and run ShopSecure v1

Goal: get the deliberately weak v1 app running on your PC, prove it works, and put it on GitHub.
Time: about 1.5 hours. Run every command in **Windows PowerShell** unless a step says otherwise.
Project folder: `C:\Users\DELL\Desktop\Learning_Skills\DevSecOps\shopsecure-appsec-program`

Each step has: **Do** (the command), **Why**, **Expect** (what you should see), **If it fails**.

> ShopSecure v1 is insecure on purpose. Run it only on your own PC, and never deploy it.

---

## Step 1. Check your tools
**Do**
```powershell
git --version
docker --version
docker compose version
python --version
code --version
```
**Why** Every later phase assumes these five tools exist.
**Expect** A version for each. Python 3.10 or newer is fine (the app itself runs inside Docker).
**If it fails** Install the missing tool: Git for Windows, Docker Desktop (tick "Use WSL 2"), Python from python.org (tick "Add to PATH"), VS Code. Restart PowerShell afterwards.

## Step 2. Start Docker Desktop and confirm the engine runs
**Do** Open Docker Desktop and wait until the whale icon says "Engine running". Then:
```powershell
docker run --rm hello-world
```
**Why** Compose needs a running Docker engine.
**Expect** A message starting "Hello from Docker!".
**If it fails** "error during connect" means Docker Desktop is not running yet. If it asks for WSL2, run `wsl --install` in an admin PowerShell, reboot, and retry.

## Step 3. Open the project folder
**Do**
```powershell
cd C:\Users\DELL\Desktop\Learning_Skills\DevSecOps\shopsecure-appsec-program
code .
dir
```
**Why** All commands from here run from the project root.
**Expect** You see `app`, `docs`, `scripts`, `docker-compose.yml`, `README.md`, `JOURNAL.md`.

## Step 4. Read what you are about to run (10 minutes)
**Do** In VS Code open these files in order, and read them top to bottom:
1. `docker-compose.yml` - the four containers and which ports are published to your PC.
2. `app/gateway/nginx.conf` - the only intended public entry point.
3. `app/orders-api/main.py` - register, login, product search, create order, get order.
4. `app/payments-svc/main.py` - the mock payment service.

**Why** In Phase 1 you review this design as the AppSec architect. Start forming your own opinions now. Do not open `docs/00-setup/ANSWER-KEY-do-not-open-yet.md`.
**Expect** You can say in one sentence what each file does.

## Step 5. Validate the compose file
**Do**
```powershell
docker compose config -q
```
**Why** Catches YAML mistakes before building.
**Expect** No output (silence means valid).

## Step 6. Build and start the stack
**Do**
```powershell
docker compose up -d --build
```
**Why** Builds the three images, pulls Postgres, and starts everything in the background (`-d`). The first run downloads images and takes 3 to 8 minutes.
**Expect** Lines ending with `Started` or `Healthy` for db, payments-svc, orders-api and gateway.
**If it fails** See the troubleshooting table at the bottom.

## Step 7. Check that all four containers are up
**Do**
```powershell
docker compose ps
```
**Expect**
| Service | State | Ports |
|---|---|---|
| gateway | running | 0.0.0.0:18080->80 |
| orders-api | running | none published |
| payments-svc | running | 0.0.0.0:18002->8002 |
| db | running (healthy) | none published |

**Note for Phase 1** Look at the Ports column again. Which services are reachable from your PC? Is that what the design intended? Write down what you notice.

## Step 8. Try the API by hand
**Do**
```powershell
Invoke-RestMethod http://localhost:18080/api/health
Invoke-RestMethod "http://localhost:18080/api/products?search=lap"
Invoke-RestMethod -Method Post http://localhost:18080/api/register -ContentType "application/json" -Body '{"username":"alice","password":"Passw0rd!"}'
Invoke-RestMethod -Method Post http://localhost:18080/api/login -ContentType "application/json" -Body '{"username":"alice","password":"Passw0rd!"}'
```
**Why** Learn the request flow: PC -> gateway (port 18080) -> orders-api.
**Expect** `status: ok`; one product (Laptop); a new user with an id; a login response with an `access_token`.
**If it fails** `409` on register means alice already exists, which is fine.

## Step 9. Place an order and watch the payment hop
**Do** (use the `id` returned by register as `user_id`; the example uses 1)
```powershell
Invoke-RestMethod -Method Post http://localhost:18080/api/orders -ContentType "application/json" -Body '{"user_id":1,"product_id":1,"quantity":1,"card_number":"4111111111111111"}'
docker compose logs payments-svc --tail 5
```
**Expect** `status: approved` and a total of 899. In the payments logs, look for a line starting `charging order=`.
**Note for Phase 2** Read that log line carefully. What data is in it, and who can read logs?

## Step 10. Run the smoke test
**Do**
```powershell
python scripts\smoke_test.py
```
**Why** One command that proves the app works and confirms the seeded flaws are really present, so later phases have something real to find and fix.
**Expect** Section 1 all `[PASS]`. Section 2 shows four lines starting `[PASS] FLAW...` or `[PASS] CODE FLAW...`. In section 2, PASS means "the flaw is present". The last line should read `9/9 checks passed`.
**If it fails** Run `docker compose ps` and `docker compose logs orders-api --tail 30`.

## Step 11. Confirm flaws 2 and 4 (design facts)
**Do**
```powershell
# Flaw 4: which database account does orders-api use, and is it a superuser?
docker compose exec orders-api env | Select-String "DB_USER"
docker compose exec db psql -U postgres -d shop -c "\du"

# Flaw 2: is traffic between services encrypted?
docker compose exec orders-api env | Select-String "PAYMENTS_URL"
```
**Expect** `DB_USER=postgres`; the role list shows `postgres` with `Superuser`; `PAYMENTS_URL=http://payments-svc:8002` (http, not https).
**Why** These two flaws are in configuration, not code, so tools will not find them. Only an architecture review does. That is the point of Phase 1.

## Step 12. Save a baseline of evidence
**Do**
```powershell
python scripts\smoke_test.py | Out-File evidence\phase0-smoke-test.txt
docker compose ps | Out-File evidence\phase0-compose-ps.txt
```
**Why** The `evidence/` folder is your audit trail. Each phase adds proof that a control works.

## Step 13. Put it on GitHub
**Do**
1. On github.com create a new **public** repository named `shopsecure-appsec-program` (no README, no .gitignore, no license).
2. Then, from the project folder:
```powershell
git init
git config user.name "Your Name"
git config user.email "you@example.com"
git add .
git commit -m "Phase 0: ShopSecure v1 (deliberately weak baseline)"
git branch -M main
git remote add origin https://github.com/<your-username>/shopsecure-appsec-program.git
git push -u origin main
```
**Why** Phase 3 builds the CI/CD pipeline on this repo, and a public repo gets unlimited free Actions minutes.
**Expect** The code visible on GitHub.
**Check before pushing** Run `git status` and confirm no `.env` file is staged. v1 contains intentionally weak code but no real secrets.
**If it fails** `git push` asking for a password: use your GitHub username and a personal access token, or sign in through the browser window Git opens.

## Step 14. Add your journal entry
Add a row to `JOURNAL.md`: what you did, why, outcome, next step.

---

## Day-to-day commands
| Task | Command |
|---|---|
| Stop everything (keeps data) | `docker compose down` |
| Start again | `docker compose up -d` |
| Rebuild after code changes | `docker compose up -d --build` |
| Full reset (wipes the database) | `docker compose down -v` |
| Logs of one service | `docker compose logs orders-api --tail 50` |
| Shell inside a container | `docker compose exec orders-api bash` |

## Troubleshooting
| Symptom | Likely cause | Fix |
|---|---|---|
| `error during connect` / cannot reach the Docker API | Docker Desktop not running | Start Docker Desktop, wait for "Engine running" |
| `port is already allocated` on 18080 or 18002 | Another program uses that port | `netstat -ano \| findstr :18080`, close that program, or change the left-hand port number in `docker-compose.yml` |
| orders-api keeps restarting | Database not ready or crashed | `docker compose logs db --tail 30`, then `docker compose down -v` and `docker compose up -d --build` |
| `502 Bad Gateway` from port 18080 | orders-api is not up yet | Wait 10 seconds, check `docker compose ps` |
| `pip install` step fails during build | Network or proxy problem | Retry; check Docker Desktop can reach the internet |
| Build very slow | First-time image downloads | Normal; later builds use the cache |
| Smoke test says connection refused | Stack not started | `docker compose up -d`, wait 15 seconds |
| Containers stay `Created`, never start | A container from another lab already holds the port | `docker ps` and look at the PORTS column; stop the other container (`docker stop <name>`) or change the left-hand port in `docker-compose.yml`. ShopSecure uses 18080 and 18002 for this reason |

## Phase 0 is done when
- [ ] `docker compose ps` shows all four services running
- [ ] `python scripts\smoke_test.py` reports 9/9 checks passed
- [ ] Evidence files saved in `evidence/`
- [ ] Code pushed to a public GitHub repo
- [ ] Journal entry written
- [ ] You have written down every weakness you noticed (this feeds Phase 1)
