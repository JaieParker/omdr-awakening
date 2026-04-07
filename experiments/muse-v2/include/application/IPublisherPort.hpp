// =============================================================================
// muse-v2 application layer — IPublisherPort
//
// Abstract interface for publishing sample packets to some external sink.
// The application layer depends on this interface; implementations include:
//   - LslOutletPublisher (infrastructure layer, real liblsl outlets)
//   - StdoutPublisher (testing/debugging, prints to stdout)
//   - MockPublisher (tests, records calls for later assertion)
//   - FileCsvPublisher (future, writes to a CSV for offline replay)
//
// The publisher contract is simple: given a SamplePacket, emit it to
// the sink. The publisher is responsible for any format translation
// needed (e.g. converting to LSL's float64 arrays and timestamps).
//
// Responsibility boundary:
//   - Given a SamplePacket, publish it
//   - Report whether the publisher is ready to accept packets
//
// NOT responsible for:
//   - Sourcing the packets (that's IStreamingPort)
//   - Deciding which packets to send (that's StreamingSession)
//   - Maintaining connection state to the sink (implementation detail)
// =============================================================================

#pragma once

#include <string>

#include "domain/PacketType.hpp"
#include "domain/SamplePacket.hpp"

namespace musev2::application {

/// Port interface for publishing SamplePackets to some external sink.
class IPublisherPort {
public:
    virtual ~IPublisherPort() = default;

    /// One-time initialization: prepare any outlets/connections/files
    /// needed to publish the given set of packet types. Called once
    /// before the first publish() call.
    ///
    /// For LSL: creates one lsl::stream_outlet per packet type.
    /// For stdout: no-op.
    /// For CSV: opens the output file.
    virtual void initialize(const std::vector<domain::PacketType>& packet_types) = 0;

    /// Publish a single sample packet. The implementation is responsible
    /// for finding the right sink for the packet's PacketType.
    ///
    /// May be called from a background thread — implementations must
    /// ensure publish() is thread-safe if that's possible, or document
    /// their threading requirements.
    virtual void publish(const domain::SamplePacket& packet) = 0;

    /// Shut down any sinks cleanly. After this returns, publish() must
    /// not be called.
    virtual void shutdown() = 0;

    /// True iff initialize() has been called and shutdown() has not.
    virtual bool is_ready() const = 0;
};

}  // namespace musev2::application
