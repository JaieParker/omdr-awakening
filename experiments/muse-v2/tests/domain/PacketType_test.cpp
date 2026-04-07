// =============================================================================
// First failing test in muse-v2.
//
// Verifies our domain PacketType enum matches libmuse's MuseDataPacketType
// integer IDs, so that infrastructure adapters can convert between them by
// a simple static_cast without a translation table.
//
// Source of truth for the IDs:
// C:\DocumentsJaie\AI\Muse\Muse SDK _ RDK-20260322T135855Z-3-001\Muse SDK _ RDK\
//   Muse SDK\Muse SDK 8.0.5\libmuse_windows_8.0.5\libmuse_windows_8.0.5\include\
//   api\bridge_muse_data_packet_type.h
//
// The first five IDs in that header:
//   ACCELEROMETER = 0
//   GYRO          = 1
//   EEG           = 2
//   DROPPED_ACCELEROMETER = 3 (deprecated but occupies the slot)
//   DROPPED_EEG           = 4 (deprecated but occupies the slot)
//
// and continuing:
//   QUANTIZATION  = 5
//   BATTERY       = 6
//   DRL_REF       = 7
//   ALPHA_ABSOLUTE = 8
//   BETA_ABSOLUTE  = 9
//   DELTA_ABSOLUTE = 10
//   THETA_ABSOLUTE = 11
//   GAMMA_ABSOLUTE = 12
//   ALPHA_RELATIVE = 13
//   BETA_RELATIVE  = 14
//   DELTA_RELATIVE = 15
//   THETA_RELATIVE = 16
//   GAMMA_RELATIVE = 17
//   ALPHA_SCORE    = 18
//   BETA_SCORE     = 19
//   DELTA_SCORE    = 20
//   THETA_SCORE    = 21
//   GAMMA_SCORE    = 22
//   IS_GOOD        = 23
//   HSI            = 24
//   HSI_PRECISION  = 25
//   ARTIFACTS      = 26
//   MAGNETOMETER   = 27
//   PRESSURE       = 28
//   TEMPERATURE    = 29
//   ULTRA_VIOLET   = 30
//   NOTCH_FILTERED_EEG = 31
//   VARIANCE_EEG       = 32
//   VARIANCE_NOTCH_FILTERED_EEG = 33
//   PPG                = 34
//   IS_PPG_GOOD        = 35
//   IS_HEART_GOOD      = 36
//   THERMISTOR         = 37
//   IS_THERMISTOR_GOOD = 38
//   AVG_BODY_TEMPERATURE = 39
//   CLOUD_COMPUTED     = 40
//   OPTICS             = 41
//
// We mirror these in our own enum so the domain layer is independent of
// libmuse headers, but an infrastructure adapter can static_cast between
// the two types safely.
// =============================================================================

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"

#include "domain/PacketType.hpp"

using musev2::domain::PacketType;

TEST_CASE("PacketType enum values match libmuse MuseDataPacketType IDs") {
    // Spot-check a few values at the start, middle, and end of the enum.
    // If any of these drift, the static_cast-based bridge between libmuse
    // and our domain types is broken and silently mis-labels data.
    CHECK(static_cast<int>(PacketType::ACCELEROMETER) == 0);
    CHECK(static_cast<int>(PacketType::EEG)           == 2);
    CHECK(static_cast<int>(PacketType::BATTERY)       == 6);
    CHECK(static_cast<int>(PacketType::ALPHA_ABSOLUTE) == 8);
    CHECK(static_cast<int>(PacketType::HSI_PRECISION) == 25);
    CHECK(static_cast<int>(PacketType::ARTIFACTS)     == 26);
    CHECK(static_cast<int>(PacketType::PPG)           == 34);
    CHECK(static_cast<int>(PacketType::OPTICS)        == 41);
}

TEST_CASE("PacketType::to_string produces a readable name matching libmuse") {
    using musev2::domain::to_string;
    CHECK(to_string(PacketType::EEG)           == "EEG");
    CHECK(to_string(PacketType::OPTICS)        == "OPTICS");
    CHECK(to_string(PacketType::ACCELEROMETER) == "ACCELEROMETER");
    CHECK(to_string(PacketType::HSI_PRECISION) == "HSI_PRECISION");
    CHECK(to_string(PacketType::ALPHA_ABSOLUTE) == "ALPHA_ABSOLUTE");
}

TEST_CASE("PacketType::from_id round-trips through static_cast") {
    using musev2::domain::from_id;
    // Valid IDs return the expected PacketType
    CHECK(from_id(2)  == PacketType::EEG);
    CHECK(from_id(41) == PacketType::OPTICS);
    CHECK(from_id(25) == PacketType::HSI_PRECISION);
}
