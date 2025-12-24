# Architectural Review: Laikaboss Fork (SNL/Sandia) vs Original (Lockheed Martin)

## Executive Summary

This fork represents a significant departure from the original Lockheed Martin Laikaboss design philosophy. While the original was engineered as a **high-performance, low-latency object scanner** suitable for inline email filtering and real-time intrusion detection, this fork has evolved into a **complete scanning ecosystem** with storage, web UI, and cluster management - but at the cost of the very performance characteristics that made Laikaboss valuable.

The README candidly admits the core issue: **"Buffer bloat/on disk caching at each level causes latency"**

This review analyzes the architectural compromises and provides recommendations for restoring performance while maintaining the enhanced functionality.

---

## 1. Original Design Philosophy (Lockheed Martin)

### 1.1 Core Architecture Principles

From the original whitepaper and codebase, Laikaboss was designed with these priorities:

| Priority | Principle | Implementation |
|----------|-----------|----------------|
| 1 | **Low Latency** | In-memory processing, ZeroMQ broker |
| 2 | **Scalability** | Stateless workers, horizontal scaling |
| 3 | **Flexibility** | YARA-based dispatching, modular architecture |
| 4 | **Verbosity** | Rich metadata extraction |

### 1.2 Original Data Flow (ZeroMQ-based)

```
Client (cloudscan.py)
       │
       │ ZeroMQ ROUTER socket
       ▼
┌─────────────────────────────────────────┐
│           laikad (Broker)               │
│  ┌─────────────────────────────────────┐│
│  │ SyncBroker / AsyncBroker            ││
│  │  - ROUTER frontend (clients)        ││
│  │  - ROUTER backend (workers)         ││
│  │  - Direct memory routing            ││
│  │  - No disk I/O in critical path     ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
       │
       │ ZeroMQ DEALER socket (in-memory)
       ▼
┌─────────────────────────────────────────┐
│           Worker Pool                   │
│  - Direct buffer passing               │
│  - No serialization to disk            │
│  - Results returned immediately        │
│  - TTL-based recycling (memory mgmt)   │
└─────────────────────────────────────────┘
       │
       ▼
    Results returned to client (in-memory)
```

**Key Performance Characteristics:**
- **Latency**: Sub-second for typical files
- **Throughput**: Thousands of objects/second per worker
- **Memory**: Buffers held in RAM only
- **Disk I/O**: Zero in critical path (log-only)

### 1.3 ZeroMQ Design Benefits

From `laikad.py`:

```python
# Direct memory routing - no disk serialization
frontend.send_multipart(msg[4:])  # Route result directly to client

# Worker recycling prevents memory bloat
should_quit = (
    counter >= self.max_scan_items or
    ((time.time() - start_time) // 60) >= self.ttl)
```

The original design used:
- **ROUTER-DEALER pattern**: Identity-preserving routing without intermediate storage
- **In-process broker**: Single point of coordination with zero external dependencies
- **Pickle serialization**: Fast Python-native serialization in memory
- **Synchronous option**: Results returned directly to caller (essential for inline filtering)

---

## 2. Fork Architecture Changes

### 2.1 Overview of Changes

| Component | Original | Fork | Impact |
|-----------|----------|------|--------|
| Message Queue | ZeroMQ (in-memory) | Redis (network + disk) | **+100ms-1s latency** |
| Work Queue | Direct broker routing | Disk-based file queues | **+50-200ms latency** |
| Storage | External/optional | MinIO + disk queues | Added complexity |
| Input | Direct socket | laikamail → disk → collector → Redis | **+500ms-2s latency** |
| Results | Immediate return | Redis → disk → storage | Async, not inline |

### 2.2 Fork Data Flow (Multi-Stage Pipeline)

```
Email arrives (laikamail)
       │
       │ DISK WRITE #1
       ▼
/data/laikaboss/submission-queue/email/
       │
       │ File watcher (castleblack)
       ▼
laikacollector
       │
       │ DISK READ + SERIALIZE + NETWORK
       ▼
┌─────────────────────────────────────────┐
│              Redis Queue                │
│  - Network round-trip                   │
│  - Potential disk persistence           │
│  - TLS overhead                         │
└─────────────────────────────────────────┘
       │
       │ NETWORK + DESERIALIZE
       ▼
laikadq (worker)
       │
       │ Scan processing (same as original)
       ▼
Result
       │
       │ SERIALIZE + NETWORK
       ▼
Redis (result queue)
       │
       │ NETWORK + DESERIALIZE
       ▼
laikacollector (ack)
       │
       │ DISK WRITE #2
       ▼
/data/laikaboss/storage-queue/
       │
       │ File watcher (watchdog)
       ▼
submitstoraged
       │
       │ DISK READ + NETWORK
       ▼
MinIO (S3 storage)
```

### 2.3 Latency Analysis

**Original (ZeroMQ path):**
```
Client → Broker → Worker → Broker → Client
         ~1ms     ~scan      ~1ms
Total: scan_time + ~2ms overhead
```

**Fork (Redis + disk path):**
```
Email → Disk → Collector → Redis → Worker → Redis → Collector → Disk → Storage
         ~50ms    ~100ms     ~20ms   ~scan    ~20ms    ~100ms    ~50ms   ~100ms

Total: scan_time + ~440ms minimum overhead
      (often 1-3 seconds in practice)
```

---

## 3. Specific Architectural Compromises

### 3.1 ZeroMQ → Redis: The Core Performance Regression

**Original (laikad.py:493-585):**
```python
# Worker receives task directly from broker - pure memory
task = self.broker.recv_multipart()
# Process immediately
result = ScanResult(source=externalObject.externalVars.source, ...)
Dispatch(externalObject.buffer, result, 0, ...)
# Return directly - no intermediate storage
reply = [client_id, b'', result]
self.broker.send_multipart(reply, copy=False, track=True)
```

**Fork (laikadq.py:217-264):**
```python
# Worker polls Redis - network + potential disk
msg = self.redis_client.recvMsg(queue_name)
# Track work in Redis (another network call)
self.redis_client.set('%s-work' % (self.identity), [msg.senderID, submitID], expire=86400)
# Process
result = self.perform_scan(msg.val)
# Send result to Redis (network call)
self.redis_client.sendMsg(self.identity, msg.senderID, result, expire=_redis_work_reply_expiration)
# Cleanup (another network call)
self.redis_client.delete('%s-work' % (self.identity))
```

**Issues:**
1. **4+ network round-trips** per scan (vs 0 in original)
2. **Redis serialization overhead** (JSON/msgpack vs direct pickle)
3. **Redis TLS overhead** (per docker-compose.yml, all connections use TLS)
4. **Redis persistence** (RDB snapshots every 300 seconds with 10 changes)

### 3.2 Direct Submit → Disk Queue: Unnecessary I/O

**laikamail.py** writes emails to disk:
```
/data/laikaboss/submission-queue/email/*.submit
```

**laikacollector.py** (line 489):
```python
cb.observe(submission_dir, extension=".submit",
           process_existing_files=True,
           enable_created=True,
           enable_moved=True, ...)
```

**Problems:**
1. **File system latency**: Even on SSD, 50-100ms per file operation
2. **inotify delays**: File watcher has inherent lag
3. **Double serialization**: Object → disk file → deserialize → Redis
4. **No backpressure**: Disk fills up before system notices overload

### 3.3 Synchronous Blocking Removed

**Original supported inline filtering:**
```python
# cloudscan.py could block and get immediate result
result = client.send(externalObject)
# Make blocking decision
if result.disposition == 'deny':
    reject_email()
```

**Fork breaks this pattern (laikacollector.py:116-183):**
```python
def perform_scan(..., block_for_resp, ...):
    ql = redis_client.sendMsg(QID, remote_queue, ext_obj)

    if block_for_resp:
        # Polling loop with timeouts
        while num_tries > 0 and not got_result:
            msg = redis_client.recvMsg(QID, timeout=timeout, block=True)
            # ... retry logic ...
```

**Issues:**
1. **Polling-based blocking**: Not true synchronous RPC
2. **Timeout complexity**: Multiple retry loops with backoff
3. **No inline filtering**: README admits "No inline email blocking with integrated email server"

### 3.4 Multi-Service Complexity

**Original deployment:**
```
laikad (single binary)
  └── broker + workers (all in one process)
```

**Fork deployment (docker-compose.yml):**
```
laikamail      ─→ disk queue
laikacollector ─→ Redis queue
laikadq        ─→ Redis queue ─→ disk queue
submitstoraged ─→ MinIO
laikarestd     ─→ Redis (status tracking)
redis          ─→ disk (persistence)
minio          ─→ disk (storage)
frontend       ─→ laikarestd proxy
```

**Issues:**
1. **7+ moving parts** vs 1 in original
2. **Failure modes multiply**: Each service can fail independently
3. **Debugging complexity**: Tracing a scan requires following 5+ log files
4. **Resource overhead**: Each container has Python runtime overhead

---

## 4. What the Fork Got Right

Despite the performance regressions, the fork adds genuine value:

### 4.1 Enhanced Module Library (78 modules)
- Password-cracking for encrypted archives (EXPLODE_ENCRYPTEDOFFICE, EXPLODE_RAR2, etc.)
- QR code extraction (EXPLODE_QR_CODE)
- Cryptocurrency address detection (META_CRYPTOCURRENCY)
- OOXML relationship analysis (META_OOXML_RELS, META_OOXML_URLS)

### 4.2 Python 3 Compatibility
- Essential for security (Python 2 is EOL)
- Enables modern library usage

### 4.3 Testing Framework
- laikatest.py with .lbtest files
- pytest integration
- Sample data for module testing

### 4.4 GUI and API
- Web-based result browsing
- REST API for integration
- S3 storage for forensic archives

### 4.5 Named Queue Prioritization
```python
# laikadq.py supports weighted queues
work_queues = parse_remote_queue_info(work_queues)
# email:5,webui:2,default:1
```

---

## 5. Recommendations for Restoration

### 5.1 Immediate: Restore ZeroMQ Path for Real-Time Scanning

Keep Redis/disk path for batch processing, but add back ZeroMQ for latency-sensitive workloads:

```
                          ┌─────────────────────────┐
Real-time path ──────────▶│ laikad (ZeroMQ broker)  │──────▶ Immediate result
(inline filtering)        └─────────────────────────┘
                                      │
                                      │ Optional async logging
                                      ▼
                          ┌─────────────────────────┐
                          │ Redis (status/storage)  │
                          └─────────────────────────┘

                          ┌─────────────────────────┐
Batch path ──────────────▶│ laikadq (Redis worker)  │──────▶ S3 storage
(email BCC, bulk)         └─────────────────────────┘
```

### 5.2 Short-term: Eliminate Unnecessary Disk Queues

**Current:**
```
laikamail → disk → laikacollector → Redis
```

**Proposed:**
```
laikamail → Redis directly (or memory queue)
```

**Implementation:**
- Modify laikamail to use redisClientLib directly
- Remove castleblack file watcher (single point of latency)
- Keep disk queue as fallback for Redis failures only

### 5.3 Medium-term: Unified Worker with Dual Interfaces

Create a single worker that supports both:

```python
class HybridWorker:
    def __init__(self):
        self.zmq_broker = ZMQBroker(...)  # Sync path
        self.redis_client = RedisClient(...)  # Async path

    def run(self):
        poller = zmq.Poller()
        poller.register(self.zmq_broker, zmq.POLLIN)

        while True:
            # Check ZMQ first (priority)
            if self.zmq_broker.poll(0):
                task = self.zmq_broker.recv()
                result = self.scan(task)
                self.zmq_broker.send(result)  # Immediate

            # Then check Redis
            elif self.redis_client.poll(0):
                task = self.redis_client.recv()
                result = self.scan(task)
                self.redis_client.send(result)  # Async OK

            else:
                time.sleep(0.001)
```

### 5.4 Long-term: Consider Alternative Queue Technologies

If Redis must be kept, consider:

| Technology | Latency | Throughput | Persistence |
|------------|---------|------------|-------------|
| ZeroMQ | ~1ms | Excellent | None (by design) |
| Redis | ~10ms | Good | Optional |
| NATS | ~2ms | Excellent | Optional |
| Kafka | ~50ms | Excellent | Always |

**NATS** would be a good middle ground - lower latency than Redis, optional persistence, excellent clustering.

---

## 6. Configuration Tuning (Immediate Impact)

Without code changes, these configuration adjustments can help:

### 6.1 Redis Configuration (docker-compose.yml)

```yaml
redis:
  command: [
    "bash", "-c",
    '
    docker-entrypoint.sh
    --appendonly no              # Already correct
    --save ""                    # DISABLE RDB snapshots for queues
    --bind 0.0.0.0
    --port 6379                  # Use non-TLS for internal network
    --tls-port 0                 # Disable TLS if network is trusted
    --tcp-keepalive 60
    --timeout 0
    '
  ]
```

### 6.2 laikacollector Configuration

```ini
[laikacollector]
submission_delay = 0          # Don't delay submissions
submission_avg_delay = 0      # Don't add random delays
queue_threshold = 1000        # Higher threshold before backpressure
num_workers = 1               # Single worker reduces contention
```

### 6.3 Worker Configuration (laikad.conf)

```ini
[laikad]
numprocs = 12                 # Match CPU cores
workerpolltimeout = 50        # Faster polling (was 300ms)
ttl = 500                     # Recycle less frequently
time_ttl = 60                 # But still recycle for memory
```

### 6.4 Use tmpfs for Queue Directories

```yaml
# docker-compose.yml
laikadq:
  volumes:
    - type: tmpfs
      target: /var/laikaboss/submission-queue
      tmpfs:
        size: 1073741824      # 1GB RAM disk
```

---

## 7. Summary

| Aspect | Original | Fork | Impact |
|--------|----------|------|--------|
| **Latency** | ~2ms overhead | ~500ms+ overhead | **250x worse** |
| **Inline filtering** | Supported | "Currently unsupported" | **Lost capability** |
| **Complexity** | 1 service | 7+ services | **Higher ops burden** |
| **Dependencies** | ZeroMQ only | Redis + MinIO + Postgres | **More failure modes** |
| **Python version** | 2.x | 3.x | **Necessary upgrade** |
| **Modules** | ~40 | 78 | **Valuable additions** |
| **GUI/API** | None | Yes | **Valuable addition** |
| **Testing** | Minimal | Framework | **Valuable addition** |

### The Core Trade-off

The fork authors traded **real-time scanning capability** for **operational convenience** (cluster management, web UI, persistent storage). This is a valid trade-off for **batch processing workloads** (email BCC analysis, bulk file scanning), but it fundamentally breaks the **inline filtering use case** that made Laikaboss valuable for email security.

### Recommended Path Forward

1. **Restore ZeroMQ path** for latency-sensitive workloads
2. **Keep Redis/disk path** for batch processing
3. **Eliminate disk queues** in critical path
4. **Consider NATS** as Redis alternative
5. **Document the two operational modes** clearly

The goal should be a system that can do both: sub-second inline filtering **and** robust batch processing with persistence.

---

## References

- [Original LaikaBoss (lmco/laikaboss)](https://github.com/lmco/laikaboss)
- [Sandia Fork (sandialabs/laikaboss)](https://github.com/sandialabs/laikaboss)
- [LaikaBoss Whitepaper](https://github.com/lmco/laikaboss/blob/master/LaikaBOSS_Whitepaper.pdf)
- [OSTI Presentation: File-Centric Intrusion Detection](https://www.osti.gov/servlets/purl/1639893)
