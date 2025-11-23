Ensure that pyinstaller is installed in order to compile a binary executable:

```
<!-- Auto-generated polished README.md created from repository files -->

# DS-Sim Scheduler — Aggressive Python Client

A compact, socket-based job-scheduling client and test harness for the `ds-server` simulator — a project for evaluating scheduling algorithms and comparing a student client against several reference algorithms.

Overview

This repository contains a Python implementation of a distributed-system scheduling client (`client.py`) that speaks the `ds-server` simulation protocol over TCP, plus supporting tools to collect and compare performance results against reference algorithms. The project focuses on scheduling decisions (GETS/SCHD flows), automated test runs across multiple configuration files, and measurement of turnaround time, resource utilisation and rental cost. It is intended for research, assignments, or benchmarking scheduling policies using the provided `ds-server`/`ds-client` binaries.

Key Features

- Socket-based scheduler: `client.py` implements the `HELO`/`AUTH`/`REDY`/`GETS`/`SCHD`/`QUIT` protocol to interact with `ds-server`.
- Aggressive scheduling algorithm: estimates server wait times from server state (`idle`, `active`, `booting`, `inactive`) and chooses the server minimizing estimated turnaround time with tie-breakers on running jobs and resource fit.
- Automated benchmarking: `ds_test.py`, `ref_results.py`, and `mark_client.py` run simulations, collect metrics, and compare your client to baselines (`atl`, `ff`, `bf`, `fc`, `fafc`).
- Reference results: precomputed `results/ref_results.json` provides baseline metrics used by the marking script for fast comparison.
- Docker-ready: `Dockerfile` (Ubuntu 22.04) for reproducible environments; `ds-server` and `ds-client` are included as executables and made executable in the image.

Tech Stack & Tools

- Languages: Python 3 (shebangs indicate Python 3.x usage). Scripts use the standard library (`socket`, `subprocess`, `json`, `pathlib`, `re`).
- Frameworks & Libraries: None required beyond the Python standard library. `pyinstaller` is referenced in the original README for building binaries if desired.
- Infrastructure: Dockerfile (Ubuntu 22.04) for containerised runs; `ds-server` and `ds-client` are expected native executables in the repository root.
- Dev Tools: `make` (optional, referenced), `pyinstaller` (optional), `git`, and typical POSIX tools when used in containers or Unix shells. Tests/benchmarks are run via Python scripts (`ds_test.py`, `ref_results.py`, `mark_client.py`).

Project Structure (important files)

```

client/ # repository root
├─ client.py # DSClient implementation (socket protocol + scheduling)
├─ mark_client.py # Pretty-printing / marking harness for student client outputs
├─ ds_test.py # Main driver to run client + compare with reference results
├─ ref_results.py # Tool to generate reference results using ds-client
├─ results/
│ └─ ref_results.json # Reference baseline metrics (Turnaround, Util, Cost)
├─ TestConfigs/ # XML configuration files used by ds-server (many configs)
├─ ds-server # Simulator binary (executable expected in repo root)
├─ ds-client # Reference client binary (executable expected in repo root)
├─ Dockerfile # Container image setup (Ubuntu 22.04, python3)
└─ ds_sim_guide.md # Protocol + command reference for ds-server / ds-client

````

- `client.py`: Implements `DSClient` class with connection handling, buffering, `GETS` parsing and an aggressive scheduling decision function.
- `ds_test.py`: Orchestrates running your client against multiple configs and comparing to `results/ref_results.json` (or regenerating reference data).
- `mark_client.py`: Runs ds-server + your client across configs, parses server output for metrics, and prints colored tables for comparison.

Getting Started

Prerequisites

- Python 3 installed and accessible as `python3` (scripts use the standard library).
- Ensure the `ds-server` and `ds-client` executables are present and executable in the repository root (the test harness invokes `./ds-server` and `./ds-client`).
- (Optional) Docker + Docker Compose if running via `Dockerfile`.

Install (local)

```powershell
# (Optional) install pyinstaller if you plan to build a binary
pip install --user pyinstaller
````

Running locally

1. Put `ds-server`, `ds-client`, and your `client.py` in the project root.
2. Run the test harness to evaluate your client against the reference results:

```powershell
python3 ./ds_test.py "python3 client.py" -n -p 50000 -c TestConfigs
```

- `-n` : use newline-terminated messages (required for some client languages/implementations).
- `-p` : port number (use a unique port when running multiple simultaneous simulations).
- `-c` : config directory (defaults to `TestConfigs`).

Regenerate reference results

If you want to recompute the reference baseline using the included `ds-client` binaries and your own configs:

```powershell
python3 ./ds_test.py "python3 client.py" -n -p 50000 -c NewConfigs --process_reference_client -r results/new_ref_results.json
```

Docker

1. Build the image (from repository root):

```powershell
docker build -t ds-sim:latest .
```

2. Run an interactive container and execute the test commands inside it, ensuring `ds-server`/`ds-client` are present.

Environment variables

- This project does not require any `.env` variables to run. Configuration is provided through command-line options and XML files in `TestConfigs/`.

Testing

- The main test/benchmark driver is `ds_test.py` which:
  - Reads `results/ref_results.json` (or regenerates it via `--process_reference_client`).
  - Runs `parse_client_results` (in `mark_client.py`) to execute `ds-server` and the student client across configs and write `results/test_results.json`.
  - Prints comparative tables using `mark_client.print_results`.

Run the tests with:

```powershell
python3 ds_test.py "python3 client.py" -n -p 50000 -c TestConfigs
```

- There are no unit tests included in the repository; the test suite is an integration/benchmark harness that runs the simulator.


💡 Design Decisions & Architecture Notes

The project follows an object-oriented single-file client design (`DSClient` in `client.py`) for clarity and to isolate responsibilities: networking, protocol parsing, and scheduling logic. Networking uses a line-buffered TCP socket to align with the `ds-server` protocol (which can use newline-delimited messages, toggled by the `-n` flag). The scheduler implements an "aggressive" heuristic: it queries servers with `GETS Capable`, estimates per-server waiting time from server `state`, `wJobs` and `rJobs`, and includes boot/startup penalties for `booting` and `inactive` states. This approach explicitly trades off immediacy (preferring `idle` servers) with throughput (estimating queue drain based on cores and job estimates), and uses deterministic tie-breakers (fewer running jobs, better resource fit, lower server id) to ensure consistent scheduling.

Benchmark and marking scripts (`ref_results.py`, `mark_client.py`, `ds_test.py`) are designed as integration tools rather than unit tests — they spawn `ds-server` and clients as subprocesses, parse simulator log output for metrics (turnaround time, utilization, cost), and compare results against baseline algorithms. Using precomputed `results/ref_results.json` speeds up iterative development while preserving the option to regenerate baselines for fresh experiments.

📬 Contact & Attribution

Built with by the project author. For questions or collaboration, open an issue or contact via the repository profile.
