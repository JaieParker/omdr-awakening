// =============================================================================
// muse-v2 application layer — IDeviceDiscoveryPort
//
// Abstract interface for discovering Muse devices on the local Bluetooth
// radio. The application layer depends on this interface; the real
// implementation (LibmuseDeviceDiscovery) lives in the infrastructure
// layer. Tests provide a mock implementation.
//
// This file is part of the APPLICATION layer and must NOT #include any
// libmuse or liblsl headers. Pure domain + std::function + std::vector.
// =============================================================================

#pragma once

#include <functional>
#include <vector>

#include "domain/DeviceIdentity.hpp"

namespace musev2::application {

/// Port interface for discovering Muse headbands advertising over BLE.
///
/// Responsibility: start a scan, report each newly discovered device via
/// a callback, stop on request. Nothing about streaming, nothing about
/// connecting — just "which devices are reachable right now".
class IDeviceDiscoveryPort {
public:
    /// Called with a DeviceIdentity when a new Muse is found on the radio.
    /// Called at most once per device per discovery session.
    using OnDeviceFoundCallback = std::function<void(const domain::DeviceIdentity&)>;

    virtual ~IDeviceDiscoveryPort() = default;

    /// Begin a discovery scan. The callback will be invoked asynchronously
    /// for each device found, until stop_discovery() is called.
    ///
    /// Precondition: no discovery scan currently running on this port.
    virtual void start_discovery(OnDeviceFoundCallback callback) = 0;

    /// Stop the current discovery scan. If no scan is running, this is a
    /// no-op. After this returns, no further callbacks will be invoked.
    virtual void stop_discovery() = 0;

    /// Return the list of devices found so far during the current (or most
    /// recent) discovery session. Useful for "give me everything discovered"
    /// queries without subscribing to the callback.
    virtual std::vector<domain::DeviceIdentity> discovered_devices() const = 0;
};

}  // namespace musev2::application
