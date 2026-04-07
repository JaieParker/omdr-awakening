// =============================================================================
// muse-v2 domain layer — PacketType
//
// Enumeration of the packet types that the libmuse SDK can deliver. The integer
// values are chosen to match Interaxon's MuseDataPacketType enum from
//   include/api/bridge_muse_data_packet_type.h
// so that an infrastructure adapter can bridge between our domain type and
// libmuse's type via a simple static_cast.
//
// This file belongs to the DOMAIN layer and must NEVER #include any libmuse,
// liblsl, platform, threading, or I/O headers. Pure C++ only.
// =============================================================================

#pragma once

#include <stdexcept>
#include <string>
#include <string_view>

namespace musev2::domain {

/// Packet types that can be delivered by the Muse SDK or by test fakes.
///
/// Integer values are chosen to match libmuse's `MuseDataPacketType` enum
/// (see `bridge_muse_data_packet_type.h` in the Muse SDK) so conversion is
/// a single `static_cast` in the infrastructure layer.
enum class PacketType : int {
    ACCELEROMETER               = 0,
    GYRO                        = 1,
    EEG                         = 2,
    DROPPED_ACCELEROMETER       = 3,   // deprecated by Interaxon; reserved
    DROPPED_EEG                 = 4,   // deprecated by Interaxon; reserved
    QUANTIZATION                = 5,
    BATTERY                     = 6,
    DRL_REF                     = 7,
    ALPHA_ABSOLUTE              = 8,
    BETA_ABSOLUTE               = 9,
    DELTA_ABSOLUTE              = 10,
    THETA_ABSOLUTE              = 11,
    GAMMA_ABSOLUTE              = 12,
    ALPHA_RELATIVE              = 13,
    BETA_RELATIVE               = 14,
    DELTA_RELATIVE              = 15,
    THETA_RELATIVE              = 16,
    GAMMA_RELATIVE              = 17,
    ALPHA_SCORE                 = 18,
    BETA_SCORE                  = 19,
    DELTA_SCORE                 = 20,
    THETA_SCORE                 = 21,
    GAMMA_SCORE                 = 22,
    IS_GOOD                     = 23,
    HSI                         = 24,
    HSI_PRECISION               = 25,
    ARTIFACTS                   = 26,
    MAGNETOMETER                = 27,
    PRESSURE                    = 28,
    TEMPERATURE                 = 29,
    ULTRA_VIOLET                = 30,
    NOTCH_FILTERED_EEG          = 31,
    VARIANCE_EEG                = 32,
    VARIANCE_NOTCH_FILTERED_EEG = 33,
    PPG                         = 34,
    IS_PPG_GOOD                 = 35,
    IS_HEART_GOOD               = 36,
    THERMISTOR                  = 37,
    IS_THERMISTOR_GOOD          = 38,
    AVG_BODY_TEMPERATURE        = 39,
    CLOUD_COMPUTED              = 40,
    OPTICS                      = 41,
};

/// Return a human-readable string matching the enum label.
/// Used for logging, LSL stream naming, and debugging output.
/// Throws std::invalid_argument if given an unknown PacketType.
inline std::string to_string(PacketType t) {
    switch (t) {
        case PacketType::ACCELEROMETER:               return "ACCELEROMETER";
        case PacketType::GYRO:                        return "GYRO";
        case PacketType::EEG:                         return "EEG";
        case PacketType::DROPPED_ACCELEROMETER:       return "DROPPED_ACCELEROMETER";
        case PacketType::DROPPED_EEG:                 return "DROPPED_EEG";
        case PacketType::QUANTIZATION:                return "QUANTIZATION";
        case PacketType::BATTERY:                     return "BATTERY";
        case PacketType::DRL_REF:                     return "DRL_REF";
        case PacketType::ALPHA_ABSOLUTE:              return "ALPHA_ABSOLUTE";
        case PacketType::BETA_ABSOLUTE:               return "BETA_ABSOLUTE";
        case PacketType::DELTA_ABSOLUTE:              return "DELTA_ABSOLUTE";
        case PacketType::THETA_ABSOLUTE:              return "THETA_ABSOLUTE";
        case PacketType::GAMMA_ABSOLUTE:              return "GAMMA_ABSOLUTE";
        case PacketType::ALPHA_RELATIVE:              return "ALPHA_RELATIVE";
        case PacketType::BETA_RELATIVE:               return "BETA_RELATIVE";
        case PacketType::DELTA_RELATIVE:              return "DELTA_RELATIVE";
        case PacketType::THETA_RELATIVE:              return "THETA_RELATIVE";
        case PacketType::GAMMA_RELATIVE:              return "GAMMA_RELATIVE";
        case PacketType::ALPHA_SCORE:                 return "ALPHA_SCORE";
        case PacketType::BETA_SCORE:                  return "BETA_SCORE";
        case PacketType::DELTA_SCORE:                 return "DELTA_SCORE";
        case PacketType::THETA_SCORE:                 return "THETA_SCORE";
        case PacketType::GAMMA_SCORE:                 return "GAMMA_SCORE";
        case PacketType::IS_GOOD:                     return "IS_GOOD";
        case PacketType::HSI:                         return "HSI";
        case PacketType::HSI_PRECISION:               return "HSI_PRECISION";
        case PacketType::ARTIFACTS:                   return "ARTIFACTS";
        case PacketType::MAGNETOMETER:                return "MAGNETOMETER";
        case PacketType::PRESSURE:                    return "PRESSURE";
        case PacketType::TEMPERATURE:                 return "TEMPERATURE";
        case PacketType::ULTRA_VIOLET:                return "ULTRA_VIOLET";
        case PacketType::NOTCH_FILTERED_EEG:          return "NOTCH_FILTERED_EEG";
        case PacketType::VARIANCE_EEG:                return "VARIANCE_EEG";
        case PacketType::VARIANCE_NOTCH_FILTERED_EEG: return "VARIANCE_NOTCH_FILTERED_EEG";
        case PacketType::PPG:                         return "PPG";
        case PacketType::IS_PPG_GOOD:                 return "IS_PPG_GOOD";
        case PacketType::IS_HEART_GOOD:               return "IS_HEART_GOOD";
        case PacketType::THERMISTOR:                  return "THERMISTOR";
        case PacketType::IS_THERMISTOR_GOOD:          return "IS_THERMISTOR_GOOD";
        case PacketType::AVG_BODY_TEMPERATURE:        return "AVG_BODY_TEMPERATURE";
        case PacketType::CLOUD_COMPUTED:              return "CLOUD_COMPUTED";
        case PacketType::OPTICS:                      return "OPTICS";
    }
    throw std::invalid_argument("unknown PacketType in to_string");
}

/// Convert an integer ID (as delivered by libmuse) to a PacketType.
/// Throws std::invalid_argument if the ID is not a known PacketType value.
inline PacketType from_id(int id) {
    if (id < 0 || id > 41) {
        throw std::invalid_argument("PacketType::from_id: id out of range");
    }
    return static_cast<PacketType>(id);
}

}  // namespace musev2::domain
