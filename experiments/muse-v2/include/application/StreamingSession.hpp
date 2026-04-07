// =============================================================================
// muse-v2 application layer — StreamingSession
//
// The main use case: orchestrates one full recording lifecycle from
// discovery through connection, streaming, and clean shutdown, using
// the three abstract port interfaces.
//
// Depends on: domain types + the three port interfaces. NOT on libmuse,
// NOT on liblsl, NOT on anything in the infrastructure layer.
//
// All behavior is driven by calls to start() / stop() and by events
// received via the port callbacks. The class owns a SessionStateMachine
// that enforces lifecycle invariants; any transition the FSM rejects
// propagates as a std::logic_error.
//
// Threading: StreamingSession itself is not thread-safe. Port
// implementations that deliver callbacks from a background thread must
// serialize those callbacks themselves, or the application layer must
// be wrapped in a single-threaded event loop. For tonight's initial
// tests, the mock ports call back synchronously from the test thread.
// =============================================================================

#pragma once

#include <functional>
#include <string>
#include <vector>

#include "application/IDeviceDiscoveryPort.hpp"
#include "application/IPublisherPort.hpp"
#include "application/IStreamingPort.hpp"
#include "domain/DeviceIdentity.hpp"
#include "domain/PacketType.hpp"
#include "domain/SamplePacket.hpp"
#include "domain/SessionState.hpp"

namespace musev2::application {

/// Configuration for a single streaming session.
struct StreamingSessionConfig {
    /// The packet types to subscribe to on the Muse device. Will also be
    /// passed to the publisher's initialize() so it can create outlets.
    std::vector<domain::PacketType> packet_types;

    /// If non-empty, only connect to a discovered device whose name
    /// starts with this prefix. Useful when multiple Muses are in range.
    /// Empty string means "connect to the first discovered device".
    std::string device_name_filter;
};

/// Orchestrates one streaming session.
///
/// Lifecycle: construct with injected ports + config, call start(),
/// the session drives itself through Discovering → Connecting → Streaming
/// via port callbacks, then terminates on stop() or on error.
class StreamingSession {
public:
    /// Construct with references to the three ports and a config.
    /// The ports MUST outlive the StreamingSession.
    StreamingSession(IDeviceDiscoveryPort& discovery,
                     IStreamingPort& streaming,
                     IPublisherPort& publisher,
                     StreamingSessionConfig config)
        : discovery_(discovery)
        , streaming_(streaming)
        , publisher_(publisher)
        , config_(std::move(config))
    {}

    // Non-copyable, non-movable — holds references and owns a state machine
    // whose invariants would be hard to maintain across moves.
    StreamingSession(const StreamingSession&) = delete;
    StreamingSession(StreamingSession&&) = delete;
    StreamingSession& operator=(const StreamingSession&) = delete;
    StreamingSession& operator=(StreamingSession&&) = delete;

    // ---- State accessors -----------------------------------------------
    domain::SessionState state() const noexcept { return fsm_.current(); }
    const std::string& last_error() const noexcept { return fsm_.last_error(); }

    // ---- Lifecycle operations ------------------------------------------

    /// Begin the session. Initializes the publisher and starts discovery.
    /// Transitions Idle → Discovering.
    void start() {
        publisher_.initialize(config_.packet_types);
        fsm_.start_discovery();

        discovery_.start_discovery(
            [this](const domain::DeviceIdentity& device) {
                on_device_found_(device);
            }
        );
    }

    /// Request graceful shutdown. Transitions through Stopping to Stopped,
    /// disconnecting the streaming port and shutting down the publisher.
    void stop() {
        if (domain::is_terminal(fsm_.current())) return;  // already stopped/failed

        fsm_.stop_requested();

        // If we got as far as connecting or streaming, the streaming port
        // needs to be disconnected. If we only started discovery, just
        // stop that.
        if (streaming_.is_streaming() ||
            // even if the FSM has moved past Streaming already, the port
            // may still be active
            fsm_.current() == domain::SessionState::Stopping)
        {
            streaming_.disconnect();
        }
        discovery_.stop_discovery();
        publisher_.shutdown();

        fsm_.shutdown_complete();
    }

private:
    // ---- Port callback handlers ----------------------------------------

    /// Called by the discovery port when a new device is found.
    void on_device_found_(const domain::DeviceIdentity& device) {
        // If the session has already moved past Discovering (e.g. stop was
        // called racing with a discovery callback), drop the event.
        if (fsm_.current() != domain::SessionState::Discovering) return;

        // Apply the name filter, if any.
        if (!config_.device_name_filter.empty() &&
            device.name().rfind(config_.device_name_filter, 0) != 0) {
            // Name doesn't start with the filter — ignore this device and
            // keep scanning.
            return;
        }

        // We have a match. Transition and begin connecting.
        fsm_.device_found();
        discovery_.stop_discovery();

        streaming_.connect_and_stream(
            device,
            config_.packet_types,
            [this](const domain::SamplePacket& packet) { on_packet_(packet); },
            [this](const std::string& event)            { on_connection_event_(event); },
            [this](const std::string& err)              { on_error_(err); }
        );
    }

    /// Called by the streaming port on connection state changes.
    void on_connection_event_(const std::string& event) {
        if (event == "connected" && fsm_.current() == domain::SessionState::Connecting) {
            fsm_.connected();
        }
        // Other events (disconnect notifications, reconnect attempts, etc.)
        // are ignored here — the streaming port is expected to call
        // on_error_ for unrecoverable failures.
    }

    /// Called by the streaming port for each delivered sample packet.
    void on_packet_(const domain::SamplePacket& packet) {
        // Drop packets that arrive before the session is fully in Streaming
        // state — this is a defensive check against misbehaving ports.
        if (fsm_.current() != domain::SessionState::Streaming) return;
        publisher_.publish(packet);
    }

    /// Called by the streaming port on unrecoverable errors.
    void on_error_(const std::string& message) {
        if (domain::is_terminal(fsm_.current())) return;
        fsm_.error_occurred(message);
        // Best-effort cleanup. Don't let further errors propagate out of
        // the error handler.
        try { streaming_.disconnect(); } catch (...) {}
        try { discovery_.stop_discovery(); } catch (...) {}
        try { publisher_.shutdown(); } catch (...) {}
    }

    IDeviceDiscoveryPort& discovery_;
    IStreamingPort& streaming_;
    IPublisherPort& publisher_;
    StreamingSessionConfig config_;
    domain::SessionStateMachine fsm_;
};

}  // namespace musev2::application
