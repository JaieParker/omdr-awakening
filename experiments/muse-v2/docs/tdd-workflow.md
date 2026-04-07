# TDD workflow — muse-v2

## The cycle

For every behavior we want the code to have, we follow this loop:

```
1. RED    — write a failing test that describes the behavior
2. GREEN  — write the minimum code to make the test pass
3. REFACTOR — clean up both the test and the code without changing behavior
4. COMMIT — small focused commit with message "<what the test verifies>"
5. Move to the next behavior
```

No implementation code is written without a test that requires it. If a test is too hard to write for a piece of code, that's a signal the code is too coupled — refactor first, test second.

## Commit discipline

- **One behavior per commit** when possible. A commit should read as "X now works, and here's the proof."
- Commit message format: `muse-v2: <layer>: <behavior description>` — e.g. `muse-v2: domain: PacketType maps to libmuse enum IDs`
- Each commit leaves the tree buildable and the tests passing. No "WIP" commits with broken state.
- Commit the test and the implementation in the same commit — they go together as a unit of proof.

## Test categories

Three categories with different dependencies and different run-frequency:

### 1. Domain tests (`tests/domain/`)

**What**: pure unit tests of domain types and domain rules. No mocks, no fixtures, no libraries beyond doctest.

**Run frequency**: every change, every build. Sub-second.

**Example**:
```cpp
#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"
#include "domain/PacketType.hpp"

using musev2::domain::PacketType;

TEST_CASE("PacketType::EEG has id 2 matching libmuse enum") {
    CHECK(static_cast<int>(PacketType::EEG) == 2);
}

TEST_CASE("PacketType::to_string produces readable name") {
    CHECK(musev2::domain::to_string(PacketType::EEG) == "EEG");
    CHECK(musev2::domain::to_string(PacketType::OPTICS) == "OPTICS");
}
```

### 2. Application tests (`tests/application/`)

**What**: unit tests for use case services. Use **mock implementations** of the port interfaces, not real libmuse or liblsl.

**Run frequency**: every change to the application layer, every build. Sub-second.

**Pattern**: the test constructs a `StreamingSession` with mock ports, exercises the session, and asserts on the mocks' recorded interactions.

**Example** (pseudo):
```cpp
#include "doctest/doctest.h"
#include "application/StreamingSession.hpp"
#include "mocks/MockDeviceDiscoveryPort.hpp"
#include "mocks/MockStreamingPort.hpp"
#include "mocks/MockPublisherPort.hpp"

TEST_CASE("StreamingSession transitions Idle -> Discovering -> Connecting when started") {
    MockDeviceDiscoveryPort discovery;
    MockStreamingPort streaming;
    MockPublisherPort publisher;
    discovery.devices_to_return = { DeviceIdentity{"00:55:DA:BB:D9:53", "MuseS-D953", "3.1.15"} };

    StreamingSession session{discovery, streaming, publisher};
    CHECK(session.state() == SessionState::Idle);

    session.start();
    CHECK(session.state() == SessionState::Discovering);

    discovery.emit_discovered();
    CHECK(session.state() == SessionState::Connecting);
}
```

### 3. Infrastructure tests (`tests/infrastructure/`)

**What**: integration tests for the real adapters. These DO link against libmuse and liblsl.

**Run frequency**: only on explicit request (`cmake --build build --target infra_tests`). Some require a Muse headband on the local Bluetooth radio and are skipped otherwise.

**Example**:
- `LslOutletPublisher_test.cpp` — creates a real `LslOutletPublisher`, pushes a sample, uses liblsl to subscribe back to the outlet, verifies the sample round-trips. No Muse hardware needed.
- `LibmuseDeviceDiscovery_test.cpp` — creates a real `LibmuseDeviceDiscovery`, calls `start_listening`, asserts that the callback fires with a device identity. **Requires a Muse headband powered on and advertising**. Guarded behind a `REQUIRES_HARDWARE` flag.

## When to write a mock vs. a real fake

- **Mock** — has recorded-interactions behavior used for assertions. Use when testing the application layer and you want to verify that the session called the port in a specific sequence.
- **Fake** — has realistic behavior but uses an in-memory implementation. Use when the test reads like "given some devices exist, do X" and we don't want the test to assert on *how* we found the devices, just *that* we found them.

For this project we'll mostly use mocks for the application layer port interfaces, because those layers are about coordination.

## What we DON'T test

- The bindings themselves (libmuse internals, liblsl internals) — that's Interaxon's and SCCN's job
- Wall-clock timing — use explicit timestamp parameters in domain code, not `std::chrono::system_clock::now()`
- Threading semantics — the infrastructure layer owns any threading, and its tests can cover it explicitly if needed
- The main.cpp composition root — composition roots are de facto covered by running the program, not by unit tests

## How to run the tests

```powershell
# Build (produces build/tests/Release/*_tests.exe)
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release --target all

# Run domain tests
.\build\tests\Release\domain_tests.exe

# Run application tests
.\build\tests\Release\application_tests.exe

# Run infrastructure tests (must be explicitly enabled — may require hardware)
.\build\tests\Release\infrastructure_tests.exe --require-hardware
```

doctest auto-discovers `TEST_CASE` blocks and reports pass/fail counts. Exit code 0 on success, non-zero on any failure.

## A test's job is to FAIL first

If you write a test and it passes without any new implementation, the test isn't actually testing the behavior you meant — it's probably testing something already true. Delete it and write a different one that starts red.

## A commit's job is to STAY green

Before committing: run ALL the tests, not just the one you were working on. TDD cycles don't create regressions in isolation — they create them when refactoring touches code that already had tests. Run the full suite and confirm 100% pass before committing.

## The first 5 failing tests

To set the cadence, here's what the first 5 test-driven increments will be:

1. `PacketType_test.cpp`: `CHECK(static_cast<int>(PacketType::ACCELEROMETER) == 0)` — verifies our enum matches the libmuse numeric IDs. **This is the simplest possible test that requires the PacketType header to exist.**

2. `PacketType_test.cpp`: `CHECK(to_string(PacketType::EEG) == "EEG")` — requires a `to_string` free function.

3. `ChannelLayout_test.cpp`: `CHECK(ChannelLayout::for_packet_type(PacketType::EEG).channels.size() == 8)` — requires a `ChannelLayout` value object with the per-packet-type channel lists.

4. `ChannelLayout_test.cpp`: `CHECK(ChannelLayout::for_packet_type(PacketType::EEG).channels[0].name == "EEG_TP9")` — requires channel name values matching the observed Athena layout.

5. `SamplePacket_test.cpp`: `CHECK(SamplePacket{1000, PacketType::EEG, {1.0, 2.0}}.timestamp_us() == 1000)` — requires the basic SamplePacket immutable value object.

After those 5 are green, the session-state machine tests and the application-layer port tests follow.

---

*Follow the commit log in `experiments/muse-v2/` to see each increment actually land.*
