// =============================================================================
// muse-v2 application layer — IStreamingPort
//
// Abstract interface for connecting to a specific Muse device and
// streaming packets from it. The application layer depends on this
// interface; the real implementation (LibmuseStreamingAdapter) lives in
// the infrastructure layer. Tests provide mocks.
//
// Responsibility boundary:
//   - Connect to a device given a DeviceIdentity
//   - Subscribe to a set of PacketTypes
//   - Deliver SamplePackets via callback
//   - Report connection events (connected, disconnected, error)
//   - Gracefully disconnect on request
//
// NOT responsible for:
//   - Discovery (that's IDeviceDiscoveryPort)
//   - Publishing the samples anywhere (that's IPublisherPort)
//   - FSM state (that's domain::SessionStateMachine, driven by StreamingSession)
// =============================================================================

#pragma once

#include <functional>
#include <string>
#include <vector>

#include "domain/DeviceIdentity.hpp"
#include "domain/PacketType.hpp"
#include "domain/SamplePacket.hpp"

namespace musev2::application {

/// Port interface for connecting + streaming from a single Muse device.
class IStreamingPort {
public:
    /// Called for every packet delivered from the device, in the order
    /// received. May be called from a worker thread — callers must ensure
    /// their callback is thread-safe.
    using OnPacketCallback = std::function<void(const domain::SamplePacket&)>;

    /// Called when the connection state changes significantly.
    /// The string describes the event in human-readable form, e.g.
    /// "connected", "disconnected", "connection refused by device".
    using OnConnectionEventCallback = std::function<void(const std::string&)>;

    /// Called if an unrecoverable error occurs. After this fires, the
    /// streaming port is in an unusable state and must be destroyed.
    using OnErrorCallback = std::function<void(const std::string&)>;

    virtual ~IStreamingPort() = default;

    /// Connect to the specified Muse device and subscribe to the listed
    /// packet types. When a connection is established, the connection
    /// event callback fires with "connected". When packets start flowing,
    /// the on_packet callback fires for each one.
    ///
    /// Non-blocking — returns immediately. All actual work happens on a
    /// background thread owned by the infrastructure adapter.
    virtual void connect_and_stream(
        const domain::DeviceIdentity& device,
        const std::vector<domain::PacketType>& packet_types,
        OnPacketCallback on_packet,
        OnConnectionEventCallback on_connection_event,
        OnErrorCallback on_error
    ) = 0;

    /// Disconnect from the device and stop delivering packets. Blocks
    /// until the shutdown is complete — after return, no further callbacks
    /// will be invoked.
    virtual void disconnect() = 0;

    /// True iff the port is currently streaming packets from a device.
    virtual bool is_streaming() const = 0;
};

}  // namespace musev2::application
