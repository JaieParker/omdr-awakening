// =============================================================================
// muse-v2 domain layer — DeviceIdentity
//
// Value object describing a specific Muse headband:
//   - MAC address (Bluetooth primary key, lowercase normalized)
//   - Name (human-readable, e.g. "MuseS-D953")
//   - Firmware version string (empty until post-connect handshake)
//
// Strict MAC validation: 6 hex pairs separated by colons. Malformed MACs
// throw std::invalid_argument on construction.
//
// Pure domain layer. No libmuse, no liblsl, no platform dependencies.
// =============================================================================

#pragma once

#include <cctype>
#include <stdexcept>
#include <string>

namespace musev2::domain {

class DeviceIdentity {
public:
    /// Construct a DeviceIdentity. MAC is normalized to lowercase.
    ///
    /// \throws std::invalid_argument if MAC is malformed or name is empty.
    DeviceIdentity(std::string mac_address, std::string name, std::string firmware)
        : mac_address_(normalize_mac_(std::move(mac_address)))
        , name_(std::move(name))
        , firmware_(std::move(firmware))
    {
        if (name_.empty()) {
            throw std::invalid_argument("DeviceIdentity: name must not be empty");
        }
    }

    const std::string& mac_address() const noexcept { return mac_address_; }
    const std::string& name() const noexcept { return name_; }
    const std::string& firmware() const noexcept { return firmware_; }

    /// Return a new DeviceIdentity with an updated firmware string.
    /// Used when the connection handshake reports the firmware version.
    DeviceIdentity with_firmware(std::string new_firmware) const {
        return DeviceIdentity(mac_address_, name_, std::move(new_firmware));
    }

    bool operator==(const DeviceIdentity& other) const noexcept {
        return mac_address_ == other.mac_address_
            && name_ == other.name_
            && firmware_ == other.firmware_;
    }
    bool operator!=(const DeviceIdentity& other) const noexcept {
        return !(*this == other);
    }

private:
    /// Validate a MAC address string and normalize it to lowercase.
    /// Expected form: "aa:bb:cc:dd:ee:ff" (case insensitive on input,
    /// always lowercase on output). Throws on any malformation.
    static std::string normalize_mac_(std::string mac) {
        if (mac.size() != 17) {
            throw std::invalid_argument("DeviceIdentity: MAC address must be 17 characters: " + mac);
        }
        for (std::size_t i = 0; i < mac.size(); ++i) {
            char c = mac[i];
            // positions 2, 5, 8, 11, 14 must be ':'
            if (i == 2 || i == 5 || i == 8 || i == 11 || i == 14) {
                if (c != ':') {
                    throw std::invalid_argument("DeviceIdentity: MAC address must use ':' separators: " + mac);
                }
            } else {
                if (!std::isxdigit(static_cast<unsigned char>(c))) {
                    throw std::invalid_argument("DeviceIdentity: MAC address contains non-hex character: " + mac);
                }
                mac[i] = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
            }
        }
        return mac;
    }

    std::string mac_address_;
    std::string name_;
    std::string firmware_;
};

}  // namespace musev2::domain
