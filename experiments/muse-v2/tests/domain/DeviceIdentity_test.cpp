// =============================================================================
// DeviceIdentity — value object describing a discovered Muse headband.
//
// Three fields, all immutable once constructed:
//   - mac_address : Bluetooth MAC (lowercase, colon-separated)
//   - name        : human-readable device name (e.g. "MuseS-D953")
//   - firmware    : firmware version string (e.g. "3.1.15"), may be empty
//                   before a connection is established
//
// Value equality is on all three fields. MAC address is the primary key
// — two DeviceIdentity values with the same MAC are assumed to be the
// same physical device even if the name or firmware string differs.
//
// The MAC validation is strict: 6 hex pairs separated by colons, case
// normalized to lowercase on construction. This means there's one
// canonical string form for every MAC, so hashing and lookup by MAC
// are unambiguous.
// =============================================================================

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"

#include "domain/DeviceIdentity.hpp"

using musev2::domain::DeviceIdentity;

TEST_CASE("DeviceIdentity stores MAC, name, and firmware") {
    DeviceIdentity d{"00:55:DA:BB:D9:53", "MuseS-D953", "3.1.15"};
    CHECK(d.mac_address() == "00:55:da:bb:d9:53");  // normalized lowercase
    CHECK(d.name() == "MuseS-D953");
    CHECK(d.firmware() == "3.1.15");
}

TEST_CASE("DeviceIdentity normalizes MAC address to lowercase") {
    DeviceIdentity d{"00:55:DA:BB:D9:53", "test", ""};
    CHECK(d.mac_address() == "00:55:da:bb:d9:53");

    DeviceIdentity d2{"ff:ee:dd:cc:bb:aa", "test2", ""};
    CHECK(d2.mac_address() == "ff:ee:dd:cc:bb:aa");
}

TEST_CASE("DeviceIdentity allows empty firmware for pre-connection state") {
    // Before we've actually connected, we only know the MAC and name from
    // the BLE advertisement. Firmware only becomes known after the connect
    // handshake completes.
    CHECK_NOTHROW((DeviceIdentity{"00:55:da:bb:d9:53", "MuseS-D953", ""}));
}

TEST_CASE("DeviceIdentity rejects malformed MAC address") {
    // Too few octets
    CHECK_THROWS_AS((DeviceIdentity{"00:55:DA:BB:D9", "x", ""}), std::invalid_argument);
    // Non-hex characters
    CHECK_THROWS_AS((DeviceIdentity{"00:55:DA:BB:D9:ZZ", "x", ""}), std::invalid_argument);
    // Wrong separators
    CHECK_THROWS_AS((DeviceIdentity{"00-55-DA-BB-D9-53", "x", ""}), std::invalid_argument);
    // Empty MAC
    CHECK_THROWS_AS((DeviceIdentity{"", "x", ""}), std::invalid_argument);
    // Extra characters
    CHECK_THROWS_AS((DeviceIdentity{"00:55:DA:BB:D9:53:77", "x", ""}), std::invalid_argument);
}

TEST_CASE("DeviceIdentity rejects empty name") {
    CHECK_THROWS_AS((DeviceIdentity{"00:55:DA:BB:D9:53", "", ""}), std::invalid_argument);
}

TEST_CASE("DeviceIdentity equality compares all three fields case-insensitively on MAC") {
    DeviceIdentity a{"00:55:DA:BB:D9:53", "MuseS-D953", "3.1.15"};
    DeviceIdentity b{"00:55:da:bb:d9:53", "MuseS-D953", "3.1.15"};  // different case on input
    CHECK(a == b);  // normalized to same

    DeviceIdentity c{"00:55:DA:BB:D9:53", "MuseS-D953", "3.1.16"};
    CHECK_FALSE(a == c);  // different firmware
}

TEST_CASE("DeviceIdentity::with_firmware returns a new identity with updated firmware") {
    // Used when we first learn the firmware version from the connection handshake
    DeviceIdentity pre_connect{"00:55:da:bb:d9:53", "MuseS-D953", ""};
    DeviceIdentity post_connect = pre_connect.with_firmware("3.1.15");
    CHECK(post_connect.mac_address() == "00:55:da:bb:d9:53");
    CHECK(post_connect.name() == "MuseS-D953");
    CHECK(post_connect.firmware() == "3.1.15");

    // Original is unchanged (value semantics)
    CHECK(pre_connect.firmware() == "");
}
