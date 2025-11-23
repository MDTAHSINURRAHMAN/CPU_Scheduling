# ds-sim: Server-Client Interaction Guide

This document outlines the command-line options for `ds-server`, the communication protocol between `ds-server` and `ds-client`, and the detailed commands used for interaction.

## 1. ds-server Command Line Options

The following is a list of command-line options for `ds-server`. Many of these can also be specified in a configuration file.

* **`-b job ID`** : Break simulation at job `n`. The simulation can run in an interactive mode with `ds-client`.
* **`-c configuration_file_name.xml`** : Use a configuration file.
* **`-d n`** : Set simulation duration/end time in seconds.
* **`-f teragrid|nd07cpu|websits02|g5k06|pl05|ldns04`** : Set failure distribution model.
* **`-g n`** : Set time granularity for resource failures in seconds.
* **`-h all|usage|limits|states`** : Show help.
* **`-i`** : Run the simulation in interactive mode without `ds-client`.
* **`-j n`** : Set job count (max #jobs to generate).
* **`-l n`** : Set the number of servers (uniform for all "hard-coded" server types).
* **`-n`** : Use the newline character (`\n`) at the end of each message. This is useful for clients written in Java or other languages.
* **`-o`** : Omit sending server failure event messages (RESF and RESR) for fast simulation. Effective only if failures are simulated.
* **`-p n`** : Set TCP/IP port number. (min: 49152, max: 65535, default: 50000). When running multiple simulations, each pair must use a unique port and run in a different directory.
* **`-r n`** : Set a random seed.
* **`-s n`** : Set a scale factor for resource failures between 1 and 100 (in percentage). 1 for nearly no failures, 100 for original.
* **`-v all|brief|jobs|stats[+]`** : Verbose mode.
* `all`: Show all messages.
* `brief`: Show less than `all` (e.g., omits server status details in GETS response).
* `jobs`: Show job status messages only.
* `stats`: Show only statistical data.

## 2. Simulation Protocol

`ds-sim` uses a client-server model where `ds-client` (scheduler) must follow a specific communication protocol to interact with `ds-server` (system simulator).

### 2.1. Protocol Flow Diagram (Text Description)

The protocol follows a sequence similar to SMTP:

1. **Handshake** :

* Client -> Server: `HELO`
* Server -> Client: `OK`
* Client -> Server: `AUTH username`
* Server -> Client: `OK` (Server writes `ds-system.xml` and sends a welcome message)

1. **Event Loop** :

* Client -> Server: `REDY` (Client is ready for the next event)
* Server -> Client: Sends the next event (`JOBN`, `JCPL`, `RESF`, `NONE`, etc.)

1. **Action Loop (if event is not `NONE`)** :

* Client -> Server: Sends an action command (`GETS`, `SCHD`, etc.)
* Server -> Client: Responds to the action (`DATA n`, `OK`, `ERR`, etc.)
* **If `DATA n`** :
  * Client -> Server: `OK`
  * Server -> Client: Sends `n` lines of data, followed by `.`
  * Client -> Server: `OK`
  * Client returns to the Action Loop (e.g., sends `SCHD` after getting data).
* **If `OK` (from `SCHD`, etc.)** :
  * Client breaks from the Action Loop and returns to the Event Loop (sends `REDY`).
* **If `ERR`** :
  * Client returns to the Action Loop to try a different action.

1. **Termination (if event is `NONE`)** :

* Client -> Server: `QUIT`
* Server -> Client: `QUIT` (Server writes log files)
* Both client and server exit.

### 2.2. Detailed Protocol Steps

1. **C(lient)** : sends `HELO` to **S(erver)**
2. **S** : replies with `OK`
3. **C** : sends `AUTH xxx` (authentication information/username) to **S**
4. **S** : replies with `OK` after writing `ds-system.xml`
5. **C** : sends `REDY` to **S** (probably after reading `ds-system.xml`)
6. **S** : sends one of the following:

* `JOBN`: A normal job for scheduling.
* `JOBP`: A re-submitted (preempted/failed/killed) job.
* `JCPL`: Information on the latest job completion.
* `RESF`: Information on the latest server failure.
* `RESR`: Information on the latest server recovery.
* `CHKQ`: Some jobs are in the queue, but no new jobs are being submitted.
* `NONE`: No more jobs to schedule.

1. **C** : sends one of the following (or goes to Step 12 for `NONE`):

* `GETS`: Request for server state information.
* `SCHD`: The actual scheduling decision.
* `ENQJ`: Request to enqueue a job to the global queue.
* `DEQJ`: Request to dequeue a job from the global queue.
* `LSTQ`: Request to get job information in the global queue.
* `CNTJ`: Request for job count on a server, by job state.
* `EJWT`: Request for the sum of estimated waiting time on a server.
* `LSTJ`: Request for info on running/waiting jobs on a server.
* `MIGJ`: Request to migrate a job.
* `KILJ`: Signal to kill a specific job.
* `TERM`: Request to terminate a server.

1. **S** : sends one of the following corresponding messages to  **C** :

* `DATA n` (for `GETS`, `LSTQ *`, `LSTJ`): Indicates `n` records will be sent.
* `OK` (for `SCHD`, `ENQJ`, `DEQJ`, `MIGJ`, `KILJ`): Action was successful.
* `n` (for `CNTJ`, `LSTQ #`): The number of jobs.
* `time` (for `EJWT`): The sum of estimated waiting time.
* `"n jobs killed"` (for `TERM`): Number of jobs killed by server termination.
* `ERR`: Invalid request or scheduling decision.

1. **C** : takes one of the following actions:

* Sends `OK` (if `DATA` was received).
* Goes to Step 5 (if `OK` was received).
* Goes to Step 7 (if `ERR` was received).

1. **S** : sends resource/job information (if `DATA` was sent in Step 8) or `.` if no more info.
2. **C** :

* Reads the resource/jobs information, sends `OK` to  **S** , and goes to Step 10, or
* Goes to Step 7 (if `.` was received).

1. **C** : sends `QUIT` to  **S** .
2. **S** : sends `QUIT` to **C** and exits.
3. **C** : exits.

## 3. ds-sim Commands

Commands in **blue** are used by `ds-client`, **red** by `ds-server`, and **black** by both.

| **Category** | **Command**  | **Description**                               |
| ------------------ | ------------------ | --------------------------------------------------- |
| Connection         | **`HELO`** | Initial message from client                         |
| Connection         | **`AUTH`** | Authentication information                          |
| Connection         | **`QUIT`** | Simulation termination                              |
| Preparation        | **`REDY`** | Client signals server for a job                     |
| Preparation        | **`DATA`** | The indicator for the actual information to be sent |
| Simulation event   | **`JOBN`** | Job submission information                          |
| Simulation event   | **`JOBP`** | Job resubmission information                        |
| Simulation event   | **`JCPL`** | Job completion                                      |
| Simulation event   | **`RESF`** | Server failure notice                               |
| Simulation event   | **`RESR`** | Server recovery notice                              |
| Simulation event   | **`CHKQ`** | Jobs in queue, no new jobs                          |
| Simulation event   | **`NONE`** | No more jobs to schedule                            |
| Client action      | **`GETS`** | Server information request                          |
| Client action      | **`SCHD`** | Scheduling decision                                 |
| Client action      | **`ENQJ`** | Enqueue job                                         |
| Client action      | **`DEQJ`** | Dequeue job                                         |
| Client action      | **`LSTQ`** | List job information in a queue                     |
| Client action      | **`CNTJ`** | The number of jobs on a server by state             |
| Client action      | **`EJWT`** | The sum of estimated waiting time on a server       |
| Client action      | **`LSTJ`** | Job list of a server (waiting and running)          |
| Client action      | **`MIGJ`** | Migrate a job                                       |
| Client action      | **`KILJ`** | Kill a job                                          |
| Client action      | **`TERM`** | Server termination                                  |
| Error              | **`ERR`**  | Error message                                       |
| Acknowledgement    | **`OK`**   | Response to a valid command                         |

### Command Details

**`HELO`**

* **Synopsis** : `HELO`
* **Description** : Greets `ds-server` at the start of the simulation.

**`OK`**

* **Synopsis** : `OK`
* **Description** : Acknowledges the validity of a command received from either `ds-server` or `ds-client`.

**`AUTH`**

* **Synopsis** : `AUTH username`
* **Description** : Authenticates the user. The `username` can be any string as no actual authentication is performed.

**`REDY`**

* **Synopsis** : `REDY`
* **Description** : Signals `ds-server` that the client is ready for the next simulation event.

**`JOBN`**

* **Synopsis** : `JOBN jobID submitTime core memory disk estRuntime`
* **Description** : Sends a normal job submitted for the first time. All fields are integers.

**`JOBP`**

* **Synopsis** : `JOBP jobID submitTime core memory disk estRuntime`
* **Description** : Resends a job that was previously submitted but failed, was killed, or pre-empted. The job restarts from the beginning.

**`JCPL`**

* **Synopsis** : `JCPL endTime jobID serverType serverID`
* **Description** : Provides information on the most recent job completion.

**`RESF`**

* **Synopsis** : `RESF serverType serverID timeOfFailure`
* **Description** : Notifies a server failure. All jobs on the failed server are terminated and will be resubmitted via `JOBP`.

**`RESR`**

* **Synopsis** : `RESR serverType serverID timeOfRecovery`
* **Description** : Notifies the recovery of a server after failure. The server state is set to `inactive`.

**`CHKQ`**

* **Synopsis** : `CHKQ`
* **Description** : Indicates there are one or more jobs in the queue, but no new jobs are being submitted.

**`NONE`**

* **Synopsis** : `NONE`
* **Description** : Indicates there are no more jobs to be scheduled.

**`GETS`**

* **Synopsis** : `GETS All | Type serverType | Capable core memory disk | Avail core memory disk`
* **Description** : Queries server state information.
* `All`: Info on all servers, regardless of state.
* `Type serverType`: Info on all servers of a specific type.
* `Capable core memory disk`: Info on servers that can *eventually* run a job with these requirements.
* `Avail core memory disk`: Info on servers that can *immediately* run a job with these requirements.
* **Response Format** : The server replies with `DATA nRecs recLen`, followed by `OK` from the client. Then the server sends `nRecs` records as a single message (newline-delimited), followed by `.`.
* **Record Format** : `serverType serverID state curStartTime core memory disk #wJobs #rJobs [#failures totalFailtime mttf mttr madf lastStartTime]`

**`SCHD`**

* **Synopsis** : `SCHD jobID serverType serverID`
* **Description** : Schedules a job (`jobID`) to a specific server (`serverType serverID`).

**`ENQJ`**

* **Synopsis** : `ENQJ queueName`
* **Description** : Places the current job into a specified queue. The global queue is named `GQ`.

**`DEQJ`**

* **Synopsis** : `DEQJ queue_name qID`
* **Description** : Gets the job at the specified queue position (`qID`, starting from 0) from the specified queue.

**`LSTQ`**

* **Synopsis** : `LSTQ queue_name [qID | # | *]`
* **Description** : Gets job information from the specified queue.
* `LSTQ GQ 3`: Gets info for job at index 3.
* `LSTQ GQ #`: Gets the count of jobs in the queue.
* `LSTQ GQ *`: Lists all jobs in the queue (responds with `DATA`).

**`CNTJ`**

* **Synopsis** : `CNTJ serverType serverID jobState`
* **Description** : Queries the number of jobs of a specified state on a specified server. `jobState` is a code (e.g., 1 for waiting, 2 for running).

**`EJWT`**

* **Synopsis** : `EJWT serverType serverID`
* **Description** : Queries the sum of estimated waiting times on a given server (based on waiting jobs only, not 100% accurate).

**`LSTJ`**

* **Synopsis** : `LSTJ serverType serverID`
* **Description** : Queries the list of running (state 2) and waiting (state 1) jobs on a given server. Responds with `DATA`.
* **Record Format** : `jobID jobState submitTime startTime estRunTime core memory disk`

**`MIGJ`**

* **Synopsis** : `MIGJ jobID srcServerType srcServerID tgtServerType tgtServerID`
* **Description** : Migrates a job from a source server to a target server. The job will restart on the target server.

**`KILJ`**

* **Synopsis** : `KILJ serverType serverID jobID`
* **Description** : Kills a job. The killed job is pushed back to the queue and will be resubmitted with `JOBP`.

**`TERM`**

* **Synopsis** : `TERM serverType serverID`
* **Description** : Terminates a server. All waiting/running jobs are killed and resubmitted. The server is put into the `inactive` state.

**`DATA`**

* **Synopsis** : `DATA nRecs recLen`
* **Description** : Sent by `ds-server` in response to `GETS` or `LSTJ`. Indicates that `nRecs` records, each with a max length of `recLen`, are about to be sent.

**`ERR`**

* **Synopsis** : `ERR: errorMessage`
* **Description** : Sends an error message from `ds-server`, typically due to a malformed or infeasible command from `ds-client`.

**`QUIT`**

* **Synopsis** : `QUIT`
* **Description** : Terminates the simulation. Sent by the client after receiving `NONE`, and then echoed by the server.
