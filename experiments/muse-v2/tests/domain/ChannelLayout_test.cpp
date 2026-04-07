// =============================================================================
// ChannelLayout — per-PacketType fixed list of channel names.
//
// Source of truth for the channel names: the CONNECTIVITY-VALIDATION.md
// observations from last night, where we read StreamInlet.get_sinfo() on
// Jaie's actual MuseS-D953 and recorded:
//
//   Muse-EEG     -> ['EEG_TP9', 'EEG_AF7', 'EEG_AF8', 'EEG_TP10',
//                    'AUX_1', 'AUX_2', 'AUX_3', 'AUX_4']
//   Muse-OPTICS  -> ['OPTICS_LO_NIR', 'OPTICS_RO_NIR', 'OPTICS_LO_IR',
//                    'OPTICS_RO_IR', 'OPTICS_LI_NIR', 'OPTICS_RI_NIR',
//                    'OPTICS_LI_IR', 'OPTICS_RI_IR', 'OPTICS_LO_RED',
//                    'OPTICS_RO_RED', 'OPTICS_LO_AMB', 'OPTICS_RO_AMB',
//                    'OPTICS_LI_RED', 'OPTICS_RI_RED', 'OPTICS_LI_AMB',
//                    'OPTICS_RI_AMB']
//   Muse-ACCGYRO -> ['ACC_X', 'ACC_Y', 'ACC_Z', 'GYRO_X', 'GYRO_Y', 'GYRO_Z']
//   Muse-BATTERY -> ['BATTERY_PERCENT']
// =============================================================================

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"

#include "domain/ChannelLayout.hpp"
#include "domain/PacketType.hpp"

using musev2::domain::ChannelLayout;
using musev2::domain::PacketType;

TEST_CASE("ChannelLayout for EEG has 8 channels in the observed Athena order") {
    const auto layout = ChannelLayout::for_packet_type(PacketType::EEG);
    CHECK(layout.packet_type() == PacketType::EEG);
    CHECK(layout.channel_count() == 8);

    const std::vector<std::string> expected = {
        "EEG_TP9", "EEG_AF7", "EEG_AF8", "EEG_TP10",
        "AUX_1", "AUX_2", "AUX_3", "AUX_4"
    };
    CHECK(layout.channel_names() == expected);
}

TEST_CASE("ChannelLayout for OPTICS has 16 channels with L/R x O/I x wavelength naming") {
    const auto layout = ChannelLayout::for_packet_type(PacketType::OPTICS);
    CHECK(layout.channel_count() == 16);

    const std::vector<std::string> expected = {
        "OPTICS_LO_NIR", "OPTICS_RO_NIR", "OPTICS_LO_IR",  "OPTICS_RO_IR",
        "OPTICS_LI_NIR", "OPTICS_RI_NIR", "OPTICS_LI_IR",  "OPTICS_RI_IR",
        "OPTICS_LO_RED", "OPTICS_RO_RED", "OPTICS_LO_AMB", "OPTICS_RO_AMB",
        "OPTICS_LI_RED", "OPTICS_RI_RED", "OPTICS_LI_AMB", "OPTICS_RI_AMB"
    };
    CHECK(layout.channel_names() == expected);
}

TEST_CASE("ChannelLayout for ACCELEROMETER has 3 channels ACC_X/Y/Z") {
    const auto layout = ChannelLayout::for_packet_type(PacketType::ACCELEROMETER);
    CHECK(layout.channel_count() == 3);
    CHECK(layout.channel_names() == std::vector<std::string>{"ACC_X", "ACC_Y", "ACC_Z"});
}

TEST_CASE("ChannelLayout for GYRO has 3 channels GYRO_X/Y/Z") {
    const auto layout = ChannelLayout::for_packet_type(PacketType::GYRO);
    CHECK(layout.channel_count() == 3);
    CHECK(layout.channel_names() == std::vector<std::string>{"GYRO_X", "GYRO_Y", "GYRO_Z"});
}

TEST_CASE("ChannelLayout for BATTERY has 1 channel BATTERY_PERCENT") {
    const auto layout = ChannelLayout::for_packet_type(PacketType::BATTERY);
    CHECK(layout.channel_count() == 1);
    CHECK(layout.channel_names() == std::vector<std::string>{"BATTERY_PERCENT"});
}

TEST_CASE("ChannelLayout for the 5 band-power packet types has 4 channels each (TP9/AF7/AF8/TP10)") {
    // Absolute band powers are 4-channel streams over the primary EEG sites
    // (the AUX channels don't participate in the Muse's internal band-power
    // computation per Interaxon's documentation).
    const std::vector<PacketType> band_types = {
        PacketType::ALPHA_ABSOLUTE,
        PacketType::BETA_ABSOLUTE,
        PacketType::DELTA_ABSOLUTE,
        PacketType::THETA_ABSOLUTE,
        PacketType::GAMMA_ABSOLUTE,
    };
    for (auto t : band_types) {
        const auto layout = ChannelLayout::for_packet_type(t);
        CHECK(layout.channel_count() == 4);
        const std::vector<std::string> expected = {"TP9", "AF7", "AF8", "TP10"};
        CHECK(layout.channel_names() == expected);
    }
}

TEST_CASE("ChannelLayout for HSI_PRECISION has 4 channels one per primary EEG site") {
    const auto layout = ChannelLayout::for_packet_type(PacketType::HSI_PRECISION);
    CHECK(layout.channel_count() == 4);
    CHECK(layout.channel_names() == std::vector<std::string>{"TP9", "AF7", "AF8", "TP10"});
}

TEST_CASE("Two ChannelLayouts constructed from the same PacketType compare equal") {
    const auto a = ChannelLayout::for_packet_type(PacketType::EEG);
    const auto b = ChannelLayout::for_packet_type(PacketType::EEG);
    CHECK(a == b);
}

TEST_CASE("Two ChannelLayouts for different PacketTypes compare not-equal") {
    const auto eeg = ChannelLayout::for_packet_type(PacketType::EEG);
    const auto optics = ChannelLayout::for_packet_type(PacketType::OPTICS);
    CHECK_FALSE(eeg == optics);
}
