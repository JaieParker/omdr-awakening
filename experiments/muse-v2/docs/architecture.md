# Architecture — muse-v2 DDD layering

## Ubiquitous language

Terms used consistently across all layers. When these change, the change is a rename refactor across every file.

| Term | Meaning |
|---|---|
| **PacketType** | One of the ~42 kinds of data the libmuse SDK can deliver: `EEG`, `OPTICS`, `ACCGYRO`, `BATTERY`, `HSI_PRECISION`, `ARTIFACTS`, `ALPHA_ABSOLUTE`, etc. Mirrors Interaxon's `MuseDataPacketType` enum but is our own type. |
| **Channel** | A single measurement within a packet. For `EEG` on the Athena: 8 channels (`EEG_TP9`, `EEG_AF7`, `EEG_AF8`, `EEG_TP10`, `AUX_1`, `AUX_2`, `AUX_3`, `AUX_4`). For `OPTICS`: 16 channels with `L/R × O/I × NIR/IR/RED/AMB` naming. |
| **ChannelLayout** | The fixed ordered set of channels for a given packet type. A value object. |
| **SamplePacket** | One unit of delivered data: a timestamp, a packet type, and a vector of values one per channel. Immutable after construction. |
| **DeviceIdentity** | MAC address + human name + firmware version of a specific Muse headband. |
| **SessionState** | Finite state machine of the streaming lifecycle: `Idle → Discovering → Connecting → Streaming → Stopping → Stopped`. Only certain transitions are valid. |
| **DeviceDiscoveryPort** (interface) | The abstract ability to "find Muse devices on the local Bluetooth radio and return their identities." Implemented by `LibmuseDeviceDiscovery` in the infrastructure layer. Mocked in tests. |
| **StreamingPort** (interface) | The abstract ability to "subscribe to packet types on a specific device and deliver sample packets to a callback." Implemented by `LibmuseStreamingAdapter`. Mocked in tests. |
| **PublisherPort** (interface) | The abstract ability to "publish a sample packet to somewhere (stdout, a file, an LSL outlet, a network socket)." Implemented by `LslOutletPublisher`. Mocked in tests. |
| **StreamingSession** (application service) | Orchestrates one full session: find device, connect, subscribe to packet types, forward received packets to the publisher, maintain session state. Depends only on the three port interfaces. |

## Layer definitions

### Domain layer (`include/domain/`, `src/domain/`, `tests/domain/`)

**Purpose**: pure types and pure rules. The vocabulary the rest of the program speaks.

**Allowed dependencies**: C++ standard library only. No `<chrono>` for wall-clock time (use explicit parameters), no `<thread>` (use sequential reasoning), no libmuse, no liblsl, no platform headers.

**Forbidden**: any I/O, any threading, any Bluetooth, any LSL, any logging to external sinks.

**Files** (each will be created test-first):
- `PacketType.hpp` — enum matching libmuse's packet types + free function helpers (`to_string`, `from_id`)
- `ChannelLayout.hpp` — per-PacketType fixed channel list, value object with equality
- `SamplePacket.hpp` — immutable `(timestamp_us, packet_type, values)` container
- `SessionState.hpp` — FSM with valid-transition rules
- `DeviceIdentity.hpp` — MAC, name, firmware value object

### Application layer (`include/application/`, `src/application/`, `tests/application/`)

**Purpose**: use cases. Each use case is a service class that orchestrates domain types via abstract port interfaces.

**Allowed dependencies**: domain + C++ standard library.

**Forbidden**: `#include <libmuse/...>` or `#include <lsl_cpp.h>` — the whole point is that this layer doesn't know which adapter is behind the ports.

**Files**:
- `IDeviceDiscoveryPort.hpp` — abstract interface for device discovery
- `IStreamingPort.hpp` — abstract interface for sample streaming with callback
- `IPublisherPort.hpp` — abstract interface for publishing samples
- `StreamingSession.hpp` — the use case: orchestrates discovery → connect → stream → publish → shutdown
- (later) `AlphaEnhancementAnalyzer.hpp` — a domain service for analysis features, if we want to pull any of this out of the Python side

### Infrastructure layer (`include/infrastructure/libmuse/`, `src/infrastructure/libmuse/`, etc.)

**Purpose**: concrete adapters that implement the application layer's port interfaces by wrapping real libraries.

**Allowed dependencies**: application, domain, libmuse, liblsl, platform headers, threading, I/O — anything needed to do the real work.

**Files**:
- `LibmuseDeviceDiscovery.hpp/.cpp` — wraps `interaxon::bridge::MuseManager`
- `LibmuseStreamingAdapter.hpp/.cpp` — wraps `interaxon::bridge::Muse` + `register_data_listener`
- `LslOutletPublisher.hpp/.cpp` — wraps `lsl::stream_outlet`

### Application entry point (`apps/muse_sdk_bridge/`)

**Purpose**: composition root. The only place where we instantiate concrete infrastructure classes and wire them into application services. Kept deliberately thin.

**File**:
- `main.cpp` — ~100 lines: parse args, instantiate infrastructure adapters, construct a `StreamingSession`, run until Ctrl+C, clean up.

## Why this layering is worth the upfront cost

1. **Testability without hardware**: the domain and application layers can be exhaustively tested with zero dependence on a Muse headband, Bluetooth radio, LSL network discovery, or liblsl binaries. A CI run could verify most of the logic.

2. **Swappable transports**: if we ever want to replace libmuse with a different SDK (or replace liblsl with a different transport), only the infrastructure layer changes. The domain and application stay identical.

3. **Inspectable contracts**: the port interfaces (`IDeviceDiscoveryPort`, `IStreamingPort`, `IPublisherPort`) are the documented contract between "what we need" and "how it's provided." Any new developer can read them and immediately see the shape of the system.

4. **Incremental build**: pure domain compiles in milliseconds and never triggers a re-link of the heavy libmuse/liblsl object files. Fast test cycles.

5. **Matches the existing OMDR.BCI .NET convention**: the existing `C:\DocumentsJaie\AI\AlternateScience\BCI\Software\` project uses the same Domain / Application / Infrastructure layering. If we ever bridge the C++ and C# sides, the patterns will line up.

## Dependency direction rule (strict)

```
apps → infrastructure → application → domain
```

Arrows go LEFT ONLY. If you ever catch yourself wanting to `#include` an infrastructure header from inside the application layer, that's a signal the port interface is missing or wrong — extract the interface, don't break the rule.

## How this architecture maps to the libmuse sample we're cribbing from

`GettingData32Dlg.cpp` is a monolithic MFC dialog that mixes everything: UI state, libmuse callbacks, data formatting, threading, Windows message pumping. It's fine for a demo, not fine as a reusable bridge.

We extract the libmuse-specific parts into the infrastructure layer's `LibmuseStreamingAdapter`, re-express the data delivery as domain `SamplePacket` values flowing through the application layer's `StreamingSession`, and have the infrastructure layer's `LslOutletPublisher` republish them as LSL outlets. The UI becomes `main.cpp` printing a status line to stdout instead of an MFC dialog.

Everything the sample code teaches us about the libmuse API (how to create a MuseManager, how to register a connection listener, how to register a data listener, how data packets arrive) moves into the infrastructure layer. Everything it hides about the semantics of "what is a packet, what is a session, what is a channel" gets made explicit in the domain layer.

## Next steps

1. Write the TDD workflow doc (`docs/tdd-workflow.md`) — explains the cycle I'll use
2. Download doctest to `third_party/doctest/doctest.h`
3. Write `CMakeLists.txt` for the top-level build
4. First failing test: `tests/domain/PacketType_test.cpp`
5. First implementation: `include/domain/PacketType.hpp`
6. Commit. Iterate.

---

*Written before any code. Any divergence from this layering during implementation should be reflected back here rather than left as undocumented drift.*
