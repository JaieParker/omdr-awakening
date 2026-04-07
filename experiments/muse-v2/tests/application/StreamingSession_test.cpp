// =============================================================================
// StreamingSession — application layer use case, the first real behavior test.
//
// A StreamingSession orchestrates one full recording lifecycle:
//   1. Start discovery on the IDeviceDiscoveryPort
//   2. When a matching device appears, stop discovery
//   3. Connect to the device via IStreamingPort with the requested packet types
//   4. When packets arrive, forward them to the IPublisherPort
//   5. On stop request, disconnect the streaming port and shut down the publisher
//   6. Maintain the SessionStateMachine invariant throughout
//
// Tests use hand-rolled mock ports that record every call for later assertion.
// No real libmuse, no real liblsl, no hardware needed.
// =============================================================================

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"

#include "application/StreamingSession.hpp"
#include "domain/DeviceIdentity.hpp"
#include "domain/PacketType.hpp"
#include "domain/SamplePacket.hpp"
#include "domain/SessionState.hpp"

#include <vector>
#include <string>

using musev2::application::StreamingSession;
using musev2::application::StreamingSessionConfig;
using musev2::application::IDeviceDiscoveryPort;
using musev2::application::IStreamingPort;
using musev2::application::IPublisherPort;
using musev2::domain::DeviceIdentity;
using musev2::domain::PacketType;
using musev2::domain::SamplePacket;
using musev2::domain::SessionState;

namespace {

// ---------------------------------------------------------------------------
// Mock: IDeviceDiscoveryPort
// ---------------------------------------------------------------------------
// Records start/stop calls. Exposes emit_device() that simulates the
// port finding a device, which invokes the stored callback.
class MockDiscovery : public IDeviceDiscoveryPort {
public:
    bool started = false;
    bool stopped = false;
    OnDeviceFoundCallback callback;
    std::vector<DeviceIdentity> devices;

    void start_discovery(OnDeviceFoundCallback cb) override {
        started = true;
        callback = std::move(cb);
    }
    void stop_discovery() override {
        stopped = true;
    }
    std::vector<DeviceIdentity> discovered_devices() const override {
        return devices;
    }

    /// Simulate the port finding a device and firing its callback.
    void emit_device(const DeviceIdentity& d) {
        devices.push_back(d);
        if (callback) callback(d);
    }
};

// ---------------------------------------------------------------------------
// Mock: IStreamingPort
// ---------------------------------------------------------------------------
class MockStreaming : public IStreamingPort {
public:
    bool connected = false;
    bool disconnected = false;
    DeviceIdentity connected_to{"00:00:00:00:00:00", "none", ""};
    std::vector<PacketType> subscribed_types;
    OnPacketCallback on_packet;
    OnConnectionEventCallback on_connection;
    OnErrorCallback on_error;

    void connect_and_stream(const DeviceIdentity& device,
                            const std::vector<PacketType>& packet_types,
                            OnPacketCallback packet_cb,
                            OnConnectionEventCallback conn_cb,
                            OnErrorCallback err_cb) override {
        connected = true;
        connected_to = device;
        subscribed_types = packet_types;
        on_packet = std::move(packet_cb);
        on_connection = std::move(conn_cb);
        on_error = std::move(err_cb);
    }
    void disconnect() override {
        disconnected = true;
        connected = false;
    }
    bool is_streaming() const override { return connected; }

    /// Simulate a successful connection handshake.
    void emit_connected() {
        if (on_connection) on_connection("connected");
    }
    /// Simulate one packet arriving from the device.
    void emit_packet(const SamplePacket& p) {
        if (on_packet) on_packet(p);
    }
    /// Simulate an error.
    void emit_error(const std::string& msg) {
        if (on_error) on_error(msg);
    }
};

// ---------------------------------------------------------------------------
// Mock: IPublisherPort
// ---------------------------------------------------------------------------
class MockPublisher : public IPublisherPort {
public:
    bool initialized = false;
    bool shut_down = false;
    std::vector<PacketType> initialized_types;
    std::vector<SamplePacket> published;

    void initialize(const std::vector<PacketType>& types) override {
        initialized = true;
        initialized_types = types;
    }
    void publish(const SamplePacket& packet) override {
        published.push_back(packet);
    }
    void shutdown() override {
        shut_down = true;
        initialized = false;
    }
    bool is_ready() const override { return initialized && !shut_down; }
};

// Small helper to build a config for tests
StreamingSessionConfig test_config() {
    return StreamingSessionConfig{
        .packet_types = {PacketType::EEG, PacketType::OPTICS, PacketType::BATTERY},
        .device_name_filter = "",  // accept any device
    };
}

}  // namespace

// ===========================================================================
// Tests
// ===========================================================================

TEST_CASE("StreamingSession starts in Idle state") {
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSession session{discovery, streaming, publisher, test_config()};

    CHECK(session.state() == SessionState::Idle);
}

TEST_CASE("start() initializes the publisher and transitions to Discovering") {
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSession session{discovery, streaming, publisher, test_config()};

    session.start();

    CHECK(session.state() == SessionState::Discovering);
    CHECK(discovery.started);
    CHECK(publisher.initialized);
    CHECK(publisher.initialized_types == test_config().packet_types);
}

TEST_CASE("When discovery reports a device, the session transitions to Connecting and calls the streaming port") {
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSession session{discovery, streaming, publisher, test_config()};
    session.start();

    discovery.emit_device(DeviceIdentity{"00:55:DA:BB:D9:53", "MuseS-D953", ""});

    CHECK(session.state() == SessionState::Connecting);
    CHECK(discovery.stopped);  // stopped scanning once we found one
    CHECK(streaming.connected);
    CHECK(streaming.connected_to.mac_address() == "00:55:da:bb:d9:53");
    CHECK(streaming.subscribed_types == test_config().packet_types);
}

TEST_CASE("When the streaming port reports 'connected', session transitions to Streaming") {
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSession session{discovery, streaming, publisher, test_config()};
    session.start();
    discovery.emit_device(DeviceIdentity{"00:55:DA:BB:D9:53", "MuseS-D953", ""});

    streaming.emit_connected();

    CHECK(session.state() == SessionState::Streaming);
}

TEST_CASE("Packets arriving during Streaming are forwarded to the publisher") {
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSession session{discovery, streaming, publisher, test_config()};
    session.start();
    discovery.emit_device(DeviceIdentity{"00:55:DA:BB:D9:53", "MuseS-D953", ""});
    streaming.emit_connected();

    SamplePacket eeg{1000, PacketType::EEG, std::vector<double>(8, 42.0)};
    SamplePacket optics{2000, PacketType::OPTICS, std::vector<double>(16, 0.5)};
    streaming.emit_packet(eeg);
    streaming.emit_packet(optics);

    REQUIRE(publisher.published.size() == 2);
    CHECK(publisher.published[0].packet_type() == PacketType::EEG);
    CHECK(publisher.published[0].timestamp_us() == 1000);
    CHECK(publisher.published[1].packet_type() == PacketType::OPTICS);
}

TEST_CASE("stop() transitions through Stopping to Stopped and cleans up both ports") {
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSession session{discovery, streaming, publisher, test_config()};
    session.start();
    discovery.emit_device(DeviceIdentity{"00:55:DA:BB:D9:53", "MuseS-D953", ""});
    streaming.emit_connected();
    CHECK(session.state() == SessionState::Streaming);

    session.stop();

    CHECK(session.state() == SessionState::Stopped);
    CHECK(streaming.disconnected);
    CHECK(publisher.shut_down);
}

TEST_CASE("Errors from the streaming port transition the session to Failed") {
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSession session{discovery, streaming, publisher, test_config()};
    session.start();
    discovery.emit_device(DeviceIdentity{"00:55:DA:BB:D9:53", "MuseS-D953", ""});
    streaming.emit_connected();

    streaming.emit_error("BLE dropout");

    CHECK(session.state() == SessionState::Failed);
    CHECK(session.last_error() == "BLE dropout");
}

TEST_CASE("Packets arriving before Streaming state begins are silently dropped") {
    // Design decision: packets that somehow arrive during Connecting (before
    // the "connected" handshake) should not be forwarded, because we're not
    // yet in Streaming state and the session invariant hasn't been established.
    // This shouldn't normally happen — it represents a misbehaving port — but
    // we handle it defensively.
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSession session{discovery, streaming, publisher, test_config()};
    session.start();
    discovery.emit_device(DeviceIdentity{"00:55:DA:BB:D9:53", "MuseS-D953", ""});
    // NOTE: NOT emitting connected yet
    CHECK(session.state() == SessionState::Connecting);

    SamplePacket early{50, PacketType::EEG, std::vector<double>(8, 0.0)};
    streaming.emit_packet(early);

    CHECK(publisher.published.empty());
}

TEST_CASE("device_name_filter selects a specific device by name prefix") {
    MockDiscovery discovery;
    MockStreaming streaming;
    MockPublisher publisher;
    StreamingSessionConfig config{
        .packet_types = {PacketType::EEG},
        .device_name_filter = "MuseS-D953",
    };
    StreamingSession session{discovery, streaming, publisher, config};
    session.start();

    // First emit a non-matching device — session should ignore it
    discovery.emit_device(DeviceIdentity{"ff:ee:dd:cc:bb:aa", "SomeOtherMuse", ""});
    CHECK(session.state() == SessionState::Discovering);  // still scanning
    CHECK_FALSE(streaming.connected);

    // Then emit the matching device
    discovery.emit_device(DeviceIdentity{"00:55:DA:BB:D9:53", "MuseS-D953", ""});
    CHECK(session.state() == SessionState::Connecting);
    CHECK(streaming.connected);
}
