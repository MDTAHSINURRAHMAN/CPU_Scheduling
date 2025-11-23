#!/usr/bin/env python3
import socket
import sys

# Configuration Constants
DEFAULT_PORT = 50000
DEFAULT_HOST = "127.0.0.1"
BUFFER_SIZE = 4096

# Scheduling Algorithm Constants
WAIT_TIME_MULTIPLIER = 0.3  # Factor for estimating wait time based on queued jobs
BOOT_TIME_ESTIMATE = 20     # Estimated remaining boot time in seconds
INACTIVE_STARTUP_TIME = 60  # Time to boot inactive server in seconds
MAX_WAIT_TIME = 99999       # Penalty for unavailable servers
DEFAULT_EST_RUNTIME = 100   # Default estimated runtime if not specified

class DSClient:
    """
    Distributed System Client for job scheduling.
    Communicates with ds-server to schedule jobs on available servers.
    """

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, algorithm="bestfit"):
        """
        Initialize the DS client.

        Args:
            host: Server hostname or IP address
            port: Server port number
            algorithm: Scheduling algorithm to use
        """
        self.host = host
        self.port = port
        self.sock = None
        self.buffer = b""  # Buffer for received data
        self.algorithm = algorithm
        
    def connect(self):
        """Establish connection to ds-server"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        
    def send(self, msg):
        """Send message to server"""
        self.sock.sendall((msg + "\n").encode())
        
    def receive(self):
        """Receive message from server with proper buffering"""
        while b"\n" not in self.buffer:
            chunk = self.sock.recv(BUFFER_SIZE)
            if not chunk:
                break
            self.buffer += chunk
        
        if b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            return line.decode().strip()
        else:
            # No complete line found
            result = self.buffer.decode().strip()
            self.buffer = b""
            return result
    
    def handshake(self):
        """Perform initial handshake with the server"""
        self.send("HELO")
        response = self.receive()
        if response != "OK":
            sys.exit(1)

        self.send("AUTH student")
        response = self.receive()
        if response != "OK":
            sys.exit(1)

    def get_servers(self, job):
        """
        Query servers capable of running the specified job.

        Args:
            job: Dictionary containing job resource requirements (cores, memory, disk)

        Returns:
            List of server dictionaries with capabilities and current state
        """
        self.send(f"GETS Capable {job['cores']} {job['memory']} {job['disk']}")

        response = self.receive()
        if not response.startswith("DATA"):
            return []

        # Parse the DATA response to get record count
        parts = response.split()
        record_count = int(parts[1]) if len(parts) > 1 else 0

        self.send("OK")

        servers = []
        # Receive exactly record_count lines
        for _ in range(record_count):
            data = self.receive()
            parts = data.split()
            if len(parts) >= 9:
                server = {
                    'type': parts[0],
                    'id': int(parts[1]),
                    'state': parts[2],
                    'curStartTime': int(parts[3]),
                    'cores': int(parts[4]),
                    'memory': int(parts[5]),
                    'disk': int(parts[6]),
                    'wJobs': int(parts[7]),  # Waiting jobs
                    'rJobs': int(parts[8])   # Running jobs
                }
                servers.append(server)

        # Send OK after receiving all records (server will then send ".")
        self.send("OK")

        # Receive the terminator "."
        terminator = self.receive()
        if terminator != ".":
            print(f"Warning: Expected '.', got '{terminator}'", file=sys.stderr)

        return servers
    
    def select_optimal_server(self, job):
        """
        Select the optimal server for a job based on estimated turnaround time.
        Uses an aggressive scheduling algorithm that minimizes wait time.

        Args:
            job: Dictionary containing job requirements

        Returns:
            Best server dictionary or None if no servers available
        """
        servers = self.get_servers(job)

        if not servers:
            return None

        est_runtime = job.get('estRunTime', DEFAULT_EST_RUNTIME)

        best_server = None
        best_wait_time = float('inf')

        for server in servers:
            # Calculate estimated wait time based on server state
            if server['state'] == 'idle':
                wait_time = 0

            elif server['state'] == 'active':
                cores = max(server['cores'], 1)  # Prevent division by zero
                # Estimate based on queued jobs and processing capacity
                wait_time = server['wJobs'] * (est_runtime / cores) * WAIT_TIME_MULTIPLIER

            elif server['state'] == 'booting':
                cores = max(server['cores'], 1)
                # Include boot time plus queue processing time
                wait_time = BOOT_TIME_ESTIMATE + server['wJobs'] * (est_runtime / cores) * WAIT_TIME_MULTIPLIER

            elif server['state'] == 'inactive':
                cores = max(server['cores'], 1)
                # Include full startup time plus queue processing time
                wait_time = INACTIVE_STARTUP_TIME + server['wJobs'] * (est_runtime / cores) * WAIT_TIME_MULTIPLIER

            else:
                # Unknown state - apply penalty
                wait_time = MAX_WAIT_TIME

            # Tie-breaker: prefer servers with fewer running jobs, then best-fit resources
            tiebreaker = (server['rJobs'], server['cores'], server['memory'], server['disk'], server['id'])

            if best_server is None:
                best_server = server
                best_wait_time = wait_time
            else:
                current_tiebreaker = (best_server['rJobs'], best_server['cores'],
                                    best_server['memory'], best_server['disk'], best_server['id'])
                if (wait_time, tiebreaker) < (best_wait_time, current_tiebreaker):
                    best_server = server
                    best_wait_time = wait_time

        return best_server


    def schedule_job(self, job):
        """
        Schedule a job to a server according to selected algorithm.

        Args:
            job: Dictionary containing job details

        Returns:
            True if scheduling succeeded, False otherwise
        """
        # Select the optimal server for this job
        server = self.select_optimal_server(job)

        if server:
            self.send(f"SCHD {job['jobID']} {server['type']} {server['id']}")
            response = self.receive()
            return response == "OK"
        return False
    
    def run(self):
        """
        Main scheduling loop.
        Connects to server, performs handshake, and processes job scheduling events.
        """
        self.connect()
        self.handshake()

        while True:
            self.send("REDY")
            response = self.receive()

            if response == "NONE":
                # No more jobs to schedule
                break

            if response.startswith("JOBN") or response.startswith("JOBP"):
                # JOBN: New job, JOBP: Pre-empted job
                parts = response.split()
                if len(parts) >= 7:
                    job = {
                        'jobID': int(parts[1]),
                        'submitTime': int(parts[2]),
                        'cores': int(parts[3]),
                        'memory': int(parts[4]),
                        'disk': int(parts[5]),
                        'estRunTime': int(parts[6])
                    }
                    self.schedule_job(job)

            elif response.startswith("JCPL"):
                # Job completed - no action required
                continue

            elif response.startswith("RESF") or response.startswith("RESR"):
                # RESF: Server failure, RESR: Server recovery - no action required
                continue

            elif response.startswith("CHKQ"):
                # Check jobs in queue - no action required
                continue

        # Gracefully terminate connection
        self.send("QUIT")
        self.receive()
        self.sock.close()

if __name__ == "__main__":
    # Run the client with aggressive scheduling algorithm
    client = DSClient(algorithm="aggressive")
    client.run()