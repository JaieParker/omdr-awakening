// =============================================================================
// SamplePacket — immutable value object for one unit of delivered data.
//
// Every packet delivered from a Muse (EEG sample, OPTICS sample, artifact
// event, etc.) is wrapped in a SamplePacket with:
//   - int64_t timestamp_us: host-clock microseconds since epoch when the
//     packet was observed by our code. (libmuse itself uses its own clock
//     domain — the infrastructure adapter translates at the boundary.)
//   - PacketType packet_type: which stream this sample belongs to
//   - std::vector<double> values: the per-channel values, ordered to
//     match the ChannelLayout for that packet_type
//
// Once constructed a SamplePacket is immutable. This matches the
// non-destructive storage principle (we never modify sample data after it
// lands) and also keeps concurrent access trivially safe.
// =============================================================================

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"

#include "domain/SamplePacket.hpp"
#include "domain/PacketType.hpp"
#include "domain/ChannelLayout.hpp"

using musev2::domain::SamplePacket;
using musev2::domain::PacketType;
using musev2::domain::ChannelLayout;

TEST_CASE("SamplePacket stores timestamp, packet type, and values") {
    SamplePacket p{
        /*timestamp_us=*/1'234'567'890,
        PacketType::EEG,
        {10.0, 20.0, 30.0, 40.0, 0.0, 0.0, 0.0, 0.0},
    };
    CHECK(p.timestamp_us() == 1'234'567'890);
    CHECK(p.packet_type() == PacketType::EEG);
    CHECK(p.values().size() == 8);
    CHECK(p.values()[0] == doctest::Approx(10.0));
    CHECK(p.values()[3] == doctest::Approx(40.0));
}

TEST_CASE("SamplePacket::channel_count matches the stored values size") {
    SamplePacket p{100, PacketType::ACCELEROMETER, {0.1, 0.2, 0.3}};
    CHECK(p.channel_count() == 3);
}

TEST_CASE("SamplePacket throws when value count does not match the declared channel layout") {
    // EEG has 8 channels. Constructing with 7 values should fail because
    // it can't satisfy the ChannelLayout contract.
    CHECK_THROWS_AS(
        (SamplePacket{0, PacketType::EEG, {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0}}),
        std::invalid_argument
    );

    // OPTICS has 16 channels. Constructing with 10 values should fail.
    CHECK_THROWS_AS(
        (SamplePacket{0, PacketType::OPTICS, std::vector<double>(10, 0.0)}),
        std::invalid_argument
    );
}

TEST_CASE("SamplePacket accepts value count matching declared channel layout") {
    // Correct channel counts per layout
    CHECK_NOTHROW((SamplePacket{0, PacketType::EEG, std::vector<double>(8, 0.0)}));
    CHECK_NOTHROW((SamplePacket{0, PacketType::OPTICS, std::vector<double>(16, 0.0)}));
    CHECK_NOTHROW((SamplePacket{0, PacketType::ACCELEROMETER, {0.0, 0.0, 0.0}}));
    CHECK_NOTHROW((SamplePacket{0, PacketType::BATTERY, {99.5}}));
    CHECK_NOTHROW((SamplePacket{0, PacketType::ALPHA_ABSOLUTE, {0.0, 0.0, 0.0, 0.0}}));
}

TEST_CASE("SamplePacket is copyable and movable") {
    SamplePacket original{100, PacketType::EEG, std::vector<double>(8, 1.5)};
    SamplePacket copy = original;
    CHECK(copy.timestamp_us() == 100);
    CHECK(copy.packet_type() == PacketType::EEG);
    CHECK(copy.values()[0] == doctest::Approx(1.5));

    SamplePacket moved = std::move(copy);
    CHECK(moved.timestamp_us() == 100);
    CHECK(moved.values().size() == 8);
}

TEST_CASE("Two SamplePackets constructed from the same data compare equal") {
    SamplePacket a{100, PacketType::EEG, std::vector<double>(8, 1.0)};
    SamplePacket b{100, PacketType::EEG, std::vector<double>(8, 1.0)};
    CHECK(a == b);
}

TEST_CASE("SamplePackets differing in any field compare not-equal") {
    SamplePacket base{100, PacketType::EEG, std::vector<double>(8, 1.0)};

    SamplePacket diff_timestamp{101, PacketType::EEG, std::vector<double>(8, 1.0)};
    CHECK_FALSE(base == diff_timestamp);

    SamplePacket diff_values{100, PacketType::EEG, std::vector<double>(8, 2.0)};
    CHECK_FALSE(base == diff_values);

    // Note: we can't construct a SamplePacket with a different PacketType
    // AND the same number of values, because the layout check would fail,
    // so we compare an EEG packet against an ACCELEROMETER packet.
    SamplePacket diff_type{100, PacketType::ACCELEROMETER, {1.0, 2.0, 3.0}};
    CHECK_FALSE(base == diff_type);
}
