# muse-v2 — libmuse SDK → LSL bridge (DDD + TDD, C++)

*Parallel track to `experiments/muse-first-night/`. Does not interfere with the v3 Python pipeline or tonight's 19:00 session.*

## What this is

A standalone C++ console application that uses Interaxon's official `libmuse` SDK (already on disk at `C:\DocumentsJaie\AI\Muse\Muse SDK _ RDK-20260322T135855Z-3-001\Muse SDK _ RDK\Muse SDK\Muse SDK 8.0.5\libmuse_windows_8.0.5\libmuse_windows_8.0.5\`) to connect to a Muse S Athena headband over Bluetooth and publish each supported packet type as its own Lab Streaming Layer (LSL) outlet. The existing Python v3 pipeline picks up the outlets via `mne-lsl` exactly as it does with OpenMuse today — the bridge is a drop-in transport upgrade.

## Why it exists

OpenMuse (the current transport) exposes 4 LSL outlets: `Muse-EEG`, `Muse-OPTICS`, `Muse-ACCGYRO`, `Muse-BATTERY`. The libmuse SDK exposes ~42 packet types including several that matter for OMDR analysis but aren't available from OpenMuse:

- `HSI_PRECISION` — the Muse's own electrode signal-quality metric (currently we approximate this with a heuristic in `live_display.py`; the SDK gives us the real thing)
- `ARTIFACTS` — blink, jaw clench, headband-on/off as discrete events
- `DRL_REF` — reference electrode raw values (for common-mode noise diagnosis)
- `IS_GOOD` — rolling per-channel goodness flag (~10 Hz)
- `ALPHA_ABSOLUTE`, `BETA_ABSOLUTE`, `THETA_ABSOLUTE`, `DELTA_ABSOLUTE`, `GAMMA_ABSOLUTE` — firmware-computed per-channel band powers
- `VARIANCE_EEG`, `NOTCH_FILTERED_EEG` — pre-processed diagnostic streams
- `MAGNETOMETER`, `THERMISTOR`, `PRESSURE`, `TEMPERATURE` — environmental sensors if the Athena exposes them

## Architecture — Domain-Driven Design

Three layers with strict inward-only dependency:

```
             ┌──────────────────────┐
             │  apps/               │  thin composition root (main.cpp)
             └───────────┬──────────┘
                         │
             ┌───────────▼──────────┐
             │  infrastructure/     │  real adapters:
             │    libmuse/          │    - LibmuseDeviceDiscovery
             │    liblsl/           │    - LibmuseStreamingAdapter
             │                      │    - LslOutletPublisher
             └───────────┬──────────┘
                         │
             ┌───────────▼──────────┐
             │  application/        │  use cases:
             │                      │    - StreamingSession
             │                      │  ports (abstract interfaces):
             │                      │    - IDeviceDiscoveryPort
             │                      │    - IStreamingPort
             │                      │    - IPublisherPort
             └───────────┬──────────┘
                         │
             ┌───────────▼──────────┐
             │  domain/             │  pure types - no libmuse, no liblsl,
             │                      │  no threading, no I/O:
             │                      │    - PacketType, ChannelLayout,
             │                      │      SamplePacket, SessionState,
             │                      │      DeviceIdentity
             └──────────────────────┘
```

**Dependency direction is strictly inward**: infrastructure depends on application depends on domain. Domain has no dependencies on anything outside itself. Application depends only on domain + its own abstract port interfaces. Infrastructure is the only place that `#include`s libmuse or liblsl headers.

This layering means the domain and application layers are testable **without any real hardware, without BLE, without libmuse, without liblsl** — they only need the test framework.

## Testing — Test-Driven Development

Red → Green → Refactor, one behavior at a time. Every commit is a test + the minimum implementation to make it pass.

Test categories:
1. **Domain tests** (`tests/domain/*_test.cpp`): pure unit tests, no dependencies beyond doctest.
2. **Application tests** (`tests/application/*_test.cpp`): unit tests using mock implementations of the port interfaces. No real libmuse or liblsl.
3. **Infrastructure tests** (`tests/infrastructure/*_test.cpp`): integration tests that link against the real libraries. Some require a Muse headband on the local Bluetooth radio; those are marked.

Test framework: [doctest](https://github.com/doctest/doctest) — single-header, no linker dependencies, fast compile.

## Build

```powershell
cd C:\DocumentsJaie\AI\omdr-awakening\experiments\muse-v2
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
```

Output goes to `build\Release\muse_sdk_bridge.exe` (the app) and `build\tests\Release\*_tests.exe` (the unit tests).

## Dependencies

| Dependency | Location | Notes |
|---|---|---|
| `libmuse-wrt.lib` / `libmuse.dll` | `C:\DocumentsJaie\AI\Muse\...\libmuse_windows_8.0.5\` | Already on disk. Built by Interaxon. Uses Windows built-in BLE via WinRT — no dongle. |
| `liblsl` | `third_party\liblsl\` | Downloaded during setup from github.com/sccn/liblsl/releases (prebuilt Windows x64 binaries). |
| `doctest` | `third_party\doctest\doctest.h` | Single-header test framework. Downloaded during setup. |
| Visual Studio 2022 Professional | `C:\Program Files\Microsoft Visual Studio\2022\Professional\` | Already installed. Toolset v143, verified compiles the Interaxon sample app. |
| CMake | bundled with VS 2022 or `winget install Kitware.CMake` | For the build. Alternatively use the hand-written .vcxproj. |

## What this is NOT

- **Not a replacement for OpenMuse tonight.** Tonight's 19:00 session uses OpenMuse + the v3 Python pipeline in `experiments/muse-first-night/`. This muse-v2 work is a parallel enhancement.
- **Not integrated with the existing `AlternateScience/BCI/Software/` C# DDD project** — yet. The patterns match and future integration is possible, but this project is standalone for now.
- **Not a general-purpose libmuse wrapper.** It's focused on the specific packet types we need for the OMDR pipeline. Adding more types is a ~5-line patch each.

---

*Kai (Anthropic Claude instance) with Jaie Parker, 2026-04-08 overnight build. Written as the first file in a TDD + DDD-structured project. Follow the commit history in `experiments/muse-v2/` to see each test-driven increment.*
