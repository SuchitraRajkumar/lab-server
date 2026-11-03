# lab-server

The backend for the **Remote Robotics Learning Lab**, part of an EPICS in IEEE project with the IEEE Chicago Section.

It handles everything about **people and sessions**: who is signed in, which student is on which robot station, how much time is left, checking submitted code, sending it to the station to run, and passing the results back to the student's browser. It never controls a robot directly.

---

## Where this fits

```
 ┌────────────┐     HTTPS + WebSocket     ┌──────────────┐    Station API    ┌──────────────┐
 │  lab-web   │ ────────────────────────▶ │  lab-server  │ ────────────────▶ │ lab-station  │ ──▶ Robot
 │ (browser)  │ ◀──── output, status ──── │  (backend)   │ ◀──── events ──── │ (per robot)  │
 └────────────┘                           └──────┬───────┘                   └──────────────┘
                                                 │
                                           ┌─────▼──────┐
                                           │ PostgreSQL │
                                           └────────────┘
```

- Runs on the **lab server** (a mini PC in the lab), behind the Caddy web server, which handles HTTPS.
- There is **one** backend for the whole lab, and **one `lab-station` per robot**.
- `lab-web` talks to this backend. This backend talks to each `lab-station` through the **Station API** (defined in the [`lab-station`](https://github.com/ieee-chicago-epics/lab-station) README).

---

## What to build

### Milestone 1: first full loop

| # | Feature | Details |
|---|---|---|
| 1 | **App skeleton** | FastAPI app, config from environment variables, health check endpoint (`GET /health`). |
| 2 | **Database** | PostgreSQL tables: `users`, `stations`, `sessions`, `runs`. Use migrations. |
| 3 | **Google sign-in** | OAuth / OpenID Connect with Google. Create the user on first sign-in. Use secure session cookies. |
| 4 | **Station registry** | Know each station (id, robot type, address) and track its live status from heartbeats. |
| 5 | **Join a station** | Assign a free station to the student, start the session timer and return the session details. |
| 6 | **Code checks** | Before sending code: check syntax, allowed imports and size. Reject with a clear message and line number. This only catches mistakes early; the real security is in the station's container. |
| 7 | **Run / stop** | Send code to the station (`/run`), stop it (`/stop`), and record each run in the database. |
| 8 | **Live stream to browser** | Receive station `/events` and forward output, errors and status to the student's WebSocket. |
| 9 | **Session end** | When time runs out: stop any running program, call the station's full `/reset`, and only mark the station available after a successful reset. |
| 10 | **Station health** | Mark a station offline when heartbeats stop. Mark it "Needs attention" when a reset fails. Send an alert (Discord or Slack webhook). |
| 11 | **Mock station support** | Works with the mock station from `lab-station`, so everything can be tested without hardware. |

### Later

- Booking time slots across schools, with no-show handling and a grace period
- Roles: student, teacher, admin; sign-in limited to approved school domains
- Battery-aware booking (robots that are charging can't be booked)
- Teacher and admin endpoints (progress, station health, remote fixes)
- Metrics for reporting (session counts, completion rates), anonymized

---

## Tech stack

| Tech | Used for |
|---|---|
| **Python 3.12 + FastAPI** | The API |
| **Uvicorn** | Runs the app |
| **PostgreSQL** | Database |
| **SQLAlchemy + Alembic** | Database access and migrations |
| **Authlib** (or similar) | Google OAuth / OpenID Connect |
| **WebSockets** (FastAPI built-in) | Live updates to the browser |
| **httpx** | Calling the Station API |
| **pytest** | Tests |
| **Docker Compose** | Running the backend and database locally |

---

## Web API (used by `lab-web`)

Draft. Agree on any change before building it.

| Method | Path | Purpose | Returns |
|---|---|---|---|
| GET | `/auth/login` | Start Google sign-in | Redirect to Google |
| GET | `/auth/callback` | Google sends the user back here | Sets session cookie, redirects to app |
| GET | `/me` | Current user | `{id, name, email}` |
| GET | `/stations` | List stations and their status | `[{id, robot_type, status}]` |
| POST | `/sessions` | Join a free station | `{session_id, station_id, robot_type, ends_at, video_url}` |
| POST | `/sessions/{id}/runs` | Submit code `{code}` | `{run_id}` or `{errors: [{line, message}]}` |
| POST | `/runs/{id}/stop` | Stop a running program | `{ok}` |
| POST | `/sessions/{id}/reset-robot` | Send the robot home | `{ok}` |
| POST | `/sessions/{id}/end` | End the session early | `{ok}` |
| WS | `/sessions/{id}/stream` | Live events | see below |

**WebSocket events** (JSON, one per message):

```json
{"type": "run_started", "run_id": "..."}
{"type": "output", "run_id": "...", "stream": "stdout", "text": "Moving joint 1...\n"}
{"type": "run_ended", "run_id": "...", "reason": "finished | stopped | error | timeout", "exit_code": 0}
{"type": "station_status", "status": "available | running | resetting | needs_attention | offline"}
{"type": "timer", "ends_at": "2026-11-10T15:30:00Z"}
```

---

## Suggested structure

```
lab-server/
├── app/
│   ├── main.py          FastAPI app
│   ├── auth/            Google sign-in, session cookies
│   ├── sessions/        joining stations, timers, ending sessions
│   ├── runs/            code checks, run/stop, run records
│   ├── stations/        Station API client, heartbeats, health, alerts
│   ├── realtime/        WebSocket hub for browsers
│   ├── db/              models, migrations
│   └── config.py
├── tests/
├── docker-compose.yml   backend + PostgreSQL (+ mock station)
├── pyproject.toml
└── README.md
```

---

## Getting started

_To be filled in once the project is set up (Python version, install, run with Docker Compose)._

---

## Ground rules

- All changes go through a **pull request** and are reviewed before merging.
- Keep PRs small: one feature or fix each.
- **Never commit secrets.** Google client secrets, database passwords and webhook URLs go in a local `.env` file, which is git-ignored. This repo is public.
- Changes to the Web API must be agreed with the `lab-web` side and updated in this README.
- Changes to the Station API must be agreed with the `lab-station` side.
