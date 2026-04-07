// =============================================================================
// muse-v2 domain layer — SamplePacket
//
// Immutable value object for one unit of delivered data. Stores:
//   - timestamp_us: host-clock microseconds (translated by infrastructure
//     at the libmuse boundary)
//   - packet_type: which stream this sample belongs to
//   - values: per-channel values in the order defined by ChannelLayout
//
// Invariant: values.size() must equal the ChannelLayout for packet_type,
// enforced at construction time. A SamplePacket that exists is guaranteed
// to have a valid shape.
//
// Pure domain layer. No libmuse, no liblsl, no I/O, no threading.
// =============================================================================

#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "domain/ChannelLayout.hpp"
#include "domain/PacketType.hpp"

namespace musev2::domain {

class SamplePacket {
public:
    /// Construct a SamplePacket.
    ///
    /// \throws std::invalid_argument if the size of `values` does not match
    ///         the declared ChannelLayout for `packet_type`.
    SamplePacket(std::int64_t timestamp_us,
                 PacketType packet_type,
                 std::vector<double> values)
        : timestamp_us_(timestamp_us)
        , packet_type_(packet_type)
        , values_(std::move(values))
    {
        const auto layout = ChannelLayout::for_packet_type(packet_type_);
        if (values_.size() != layout.channel_count()) {
            throw std::invalid_argument(
                "SamplePacket: value count (" + std::to_string(values_.size()) +
                ") does not match ChannelLayout channel count (" +
                std::to_string(layout.channel_count()) + ") for " +
                to_string(packet_type_)
            );
        }
    }

    // Copy + move are explicit defaults so we document them as intentional.
    SamplePacket(const SamplePacket&) = default;
    SamplePacket(SamplePacket&&) noexcept = default;
    SamplePacket& operator=(const SamplePacket&) = default;
    SamplePacket& operator=(SamplePacket&&) noexcept = default;

    // Accessors — all const, all noexcept, no mutation.
    std::int64_t timestamp_us() const noexcept { return timestamp_us_; }
    PacketType packet_type() const noexcept { return packet_type_; }
    const std::vector<double>& values() const noexcept { return values_; }
    std::size_t channel_count() const noexcept { return values_.size(); }

    bool operator==(const SamplePacket& other) const noexcept {
        return timestamp_us_ == other.timestamp_us_
            && packet_type_ == other.packet_type_
            && values_ == other.values_;
    }
    bool operator!=(const SamplePacket& other) const noexcept {
        return !(*this == other);
    }

private:
    std::int64_t timestamp_us_;
    PacketType packet_type_;
    std::vector<double> values_;
};

}  // namespace musev2::domain
