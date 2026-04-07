// =============================================================================
// muse-v2 domain layer — ChannelLayout
//
// Per-PacketType fixed ordered list of channel names. Value object.
//
// Channel names are the ground truth observed during the connectivity
// validation pass on Jaie's specific Muse S Athena (MAC 00:55:DA:BB:D9:53,
// firmware 3.1.15) — see experiments/muse-first-night/CONNECTIVITY-VALIDATION.md
// for the raw StreamInlet metadata dumps.
//
// This file belongs to the DOMAIN layer and has no libmuse / liblsl / I/O
// dependencies. Pure C++ only.
// =============================================================================

#pragma once

#include <stdexcept>
#include <string>
#include <vector>

#include "domain/PacketType.hpp"

namespace musev2::domain {

/// Per-PacketType ordered list of channel names.
///
/// The channel list is a fixed property of the packet type — the Athena
/// always delivers EEG in the same channel order, always delivers OPTICS
/// in the same wavelength-per-optode layout, etc. ChannelLayout captures
/// that invariant as a value object so the rest of the application can
/// rely on the ordering without re-deriving it at every call site.
class ChannelLayout {
public:
    /// Factory — returns the fixed ChannelLayout for the given PacketType.
    /// Throws std::invalid_argument if the PacketType has no declared layout
    /// (e.g. deprecated DROPPED_* types).
    static ChannelLayout for_packet_type(PacketType t);

    PacketType packet_type() const noexcept { return packet_type_; }
    std::size_t channel_count() const noexcept { return channel_names_.size(); }
    const std::vector<std::string>& channel_names() const noexcept { return channel_names_; }

    /// Two layouts are equal iff they have the same PacketType AND the same
    /// channel_names() in the same order.
    bool operator==(const ChannelLayout& other) const noexcept {
        return packet_type_ == other.packet_type_
            && channel_names_ == other.channel_names_;
    }
    bool operator!=(const ChannelLayout& other) const noexcept {
        return !(*this == other);
    }

private:
    ChannelLayout(PacketType t, std::vector<std::string> names)
        : packet_type_(t), channel_names_(std::move(names)) {}

    PacketType packet_type_;
    std::vector<std::string> channel_names_;
};

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

inline ChannelLayout ChannelLayout::for_packet_type(PacketType t) {
    switch (t) {
        case PacketType::EEG:
            return ChannelLayout(t, {
                "EEG_TP9", "EEG_AF7", "EEG_AF8", "EEG_TP10",
                "AUX_1", "AUX_2", "AUX_3", "AUX_4",
            });

        case PacketType::OPTICS:
            return ChannelLayout(t, {
                "OPTICS_LO_NIR", "OPTICS_RO_NIR", "OPTICS_LO_IR",  "OPTICS_RO_IR",
                "OPTICS_LI_NIR", "OPTICS_RI_NIR", "OPTICS_LI_IR",  "OPTICS_RI_IR",
                "OPTICS_LO_RED", "OPTICS_RO_RED", "OPTICS_LO_AMB", "OPTICS_RO_AMB",
                "OPTICS_LI_RED", "OPTICS_RI_RED", "OPTICS_LI_AMB", "OPTICS_RI_AMB",
            });

        case PacketType::ACCELEROMETER:
            return ChannelLayout(t, {"ACC_X", "ACC_Y", "ACC_Z"});

        case PacketType::GYRO:
            return ChannelLayout(t, {"GYRO_X", "GYRO_Y", "GYRO_Z"});

        case PacketType::MAGNETOMETER:
            return ChannelLayout(t, {"MAG_X", "MAG_Y", "MAG_Z"});

        case PacketType::BATTERY:
            return ChannelLayout(t, {"BATTERY_PERCENT"});

        case PacketType::PPG:
            // Three wavelengths per Interaxon's PPG definition (Ambient, IR, Red)
            return ChannelLayout(t, {"PPG_AMBIENT", "PPG_IR", "PPG_RED"});

        case PacketType::DRL_REF:
            return ChannelLayout(t, {"DRL", "REF"});

        // All EEG-derived per-channel streams use the primary 4-site layout
        // (TP9, AF7, AF8, TP10). The AUX channels don't participate in
        // libmuse's internal band-power or HSI computation.
        case PacketType::ALPHA_ABSOLUTE:
        case PacketType::BETA_ABSOLUTE:
        case PacketType::DELTA_ABSOLUTE:
        case PacketType::THETA_ABSOLUTE:
        case PacketType::GAMMA_ABSOLUTE:
        case PacketType::ALPHA_RELATIVE:
        case PacketType::BETA_RELATIVE:
        case PacketType::DELTA_RELATIVE:
        case PacketType::THETA_RELATIVE:
        case PacketType::GAMMA_RELATIVE:
        case PacketType::ALPHA_SCORE:
        case PacketType::BETA_SCORE:
        case PacketType::DELTA_SCORE:
        case PacketType::THETA_SCORE:
        case PacketType::GAMMA_SCORE:
        case PacketType::IS_GOOD:
        case PacketType::HSI:
        case PacketType::HSI_PRECISION:
        case PacketType::NOTCH_FILTERED_EEG:
        case PacketType::VARIANCE_EEG:
        case PacketType::VARIANCE_NOTCH_FILTERED_EEG:
        case PacketType::QUANTIZATION:
            return ChannelLayout(t, {"TP9", "AF7", "AF8", "TP10"});

        // Environmental / single-value streams
        case PacketType::PRESSURE:
            return ChannelLayout(t, {"PRESSURE_RAW", "PRESSURE_AVG"});
        case PacketType::TEMPERATURE:
            return ChannelLayout(t, {"TEMPERATURE"});
        case PacketType::ULTRA_VIOLET:
            return ChannelLayout(t, {"UV_A", "UV_B", "UV_AVG"});
        case PacketType::THERMISTOR:
            return ChannelLayout(t, {"THERMISTOR"});
        case PacketType::IS_PPG_GOOD:
            return ChannelLayout(t, {"IS_PPG_GOOD"});
        case PacketType::IS_HEART_GOOD:
            return ChannelLayout(t, {"IS_HEART_GOOD"});
        case PacketType::IS_THERMISTOR_GOOD:
            return ChannelLayout(t, {"IS_THERMISTOR_GOOD"});
        case PacketType::AVG_BODY_TEMPERATURE:
            return ChannelLayout(t, {"AVG_BODY_TEMPERATURE"});

        case PacketType::ARTIFACTS:
            return ChannelLayout(t, {"headband_on", "blink", "jaw_clench"});

        // Deprecated / special types have no declared layout.
        case PacketType::DROPPED_ACCELEROMETER:
        case PacketType::DROPPED_EEG:
        case PacketType::CLOUD_COMPUTED:
            throw std::invalid_argument(
                "ChannelLayout::for_packet_type: no declared layout for this PacketType"
            );
    }
    throw std::invalid_argument("ChannelLayout::for_packet_type: unknown PacketType");
}

}  // namespace musev2::domain
