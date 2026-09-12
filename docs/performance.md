# Headless performance and GPU acceleration

[English](performance.md) | [简体中文](performance.zh-CN.md) · [Home](../README.md)

The current simulator runs on the **CPU**. Headless mode removes display and
rendering work; it does not provide CUDA simulation. GPU simulation, a native
environment pool and a shared-memory observation API are proposed directions,
not available features.

## Measure the complete path

Keep these rates separate when investigating throughput:

| Metric | What to count |
| --- | --- |
| Environment transitions/s | Sum of successful environment steps across all environments |
| Vector calls/s | Calls advancing a batch of environments; report the actual active batch size |
| Simulation ticks/s | Sum of `actual_ticks`, including early termination |
| Learning updates/s | Completed optimizer updates, with replay batch size and update schedule |

A vector call advancing 32 environments produces 32 transitions. Conversely,
a learner performing one update per new transition can report almost identical
transition and update rates after replay warmup. That rate includes learning
time and is not the simulator's standalone throughput.

Separate time spent on native simulation, transport and parsing, observation
encoding, action inference, replay sampling, learning, resets and logging.
Some stages can overlap, so worker times cannot simply be added to explain wall
time. Report hardware, native revision, client implementation, worker model,
ticks per action, seeds, episode limits, initialization and warmup policy.
Compare repeated measurements of the same workload; fixed-action sampling and
policy training are different workloads.

## Where parallelism can stop helping

Each [GameClient](../chromium_rl/client.py) owns one native process. A request
advances the game and exports a complete JSON snapshot through the
[native bridge](../game/src/rl/SnapshotBridge.cpp). The Python client validates
and constructs [typed state objects](../chromium_rl/state.py) before returning.
Consumer observation encoding and learning add work after that boundary.

Consider a consumer that sends 32 environment steps concurrently, then collects
each result and performs one learning update before sending the next round.
The learner still performs 32 sequential updates. Completed environments wait
for the round to finish; adding game processes does not parallelize the learner.
An update with a replay batch of 32 is still one optimizer update. Replacing
32 successive updates with one larger update changes training behavior.

Also distinguish native game processes from Python workers. One Python process
using a thread pool can overlap pipe waits, but Python-heavy parsing and encoding
remain constrained by the GIL in ordinary CPython builds. Separate Python worker
processes have different costs and scaling behavior. See the
[Python threading documentation](https://docs.python.org/3/library/threading.html#gil-and-performance-considerations).

Reducing the policy observation dimension does not by itself reduce snapshot
serialization or parsing. A consumer that encodes a full observation and then
slices it still pays for the full encoding. Consumers with their own protocol
client do not automatically benefit from changes to this repository's Python
client.

## CPU optimization path

Profile the actual consumer before choosing a change. Check whether inference
is already batched, numerical-library thread counts are already constrained,
and logging is already buffered. Avoid attributing a bottleneck to an operation
that the consumer has already optimized.

Potential runtime improvements include a versioned binary array interface and
batched transfers, with explicit object capacities, masks and overflow behavior.
Keep full diagnostic snapshots available and preserve terminal observations,
event semantics and reset boundaries. A native threaded environment pool would
first require isolating the process-wide state in [Global](../game/src/Global.h)
and related RNG/object state into independent instances. These changes require
new native validation and consumer integration.

## Two different GPU projects

**GPU learning** moves the policy, learning batches and update computation to
the GPU. A small network with frequent small updates may spend more time on
kernel dispatch, transfers and synchronization than on arithmetic. Moving only
the model is insufficient; inputs and replay batches must use compatible devices.
Per-update `.item()` calls and CPU branches on GPU results introduce waits.
CUDA Graphs can reduce dispatch overhead for suitable fixed computation, but
synchronizing operations and unsupported dynamic control flow cannot simply be
captured. Preserve finite-value checks and failure reporting when redesigning
that boundary. See the [PyTorch performance guide](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html#avoid-unnecessary-cpu-gpu-synchronization)
and [CUDA Graph constraints](https://docs.pytorch.org/docs/stable/notes/cuda.html#constraints).

**GPU simulation** requires a separate batched implementation of movement,
spawning, collisions, damage, pickups, termination, resets and state export.
Environment state would live in arrays on the device, with observations and
policy tensors sharing that device. The existing linked objects, global state
and ordered updates cannot be moved to the GPU by changing a compiler flag.

Our engineering assessment is that custom [NVIDIA Warp](https://nvidia.github.io/warp/stable/)
or CUDA kernels are a more direct fit for this game's rules than integrating
the entire [Isaac Lab / Isaac Sim stack](https://isaac-sim.github.io/IsaacLab/main/source/setup/ecosystem.html).
That is a design direction, not an implemented backend or measured speedup.
Keep the CPU game as a behavioral reference and validate collision ordering,
event accounting, random streams and episode boundaries. Different floating-point
and RNG implementations cannot inherit the current same-seed repeatability
claim without new evidence.

Changing action repeat, replay sampling, update frequency or asynchronous policy
timing also changes the experiment. Report learning quality separately from
throughput, and retain the [API semantics](api.md) when optimizing the runtime.
