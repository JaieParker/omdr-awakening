// =============================================================================
// A trivial "the port interfaces compile and link" test.
//
// Each port is a pure abstract interface, so there's nothing behavioral
// to test yet. What this test verifies is just that the headers are
// self-contained (they include everything they need) and that a subclass
// can implement them with sensible signatures. Once StreamingSession
// exists and we have mock adapters, the real behavioral tests will go
// in StreamingSession_test.cpp.
// =============================================================================

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"

#include "application/IDeviceDiscoveryPort.hpp"
#include "application/IStreamingPort.hpp"
#include "application/IPublisherPort.hpp"

using musev2::application::IDeviceDiscoveryPort;
using musev2::application::IStreamingPort;
using musev2::application::IPublisherPort;
using musev2::domain::DeviceIdentity;
using musev2::domain::PacketType;
using musev2::domain::SamplePacket;

namespace {

// Minimal subclass of each port to verify the interface can be implemented.
// These aren't mocks for testing StreamingSession — they're just proof
// that the interface surface compiles.

class NoopDiscovery : public IDeviceDiscoveryPort {
public:
    void start_discovery(OnDeviceFoundCallback) override {}
    void stop_discovery() override {}
    std::vector<DeviceIdentity> discovered_devices() const override { return {}; }
};

class NoopStreaming : public IStreamingPort {
public:
    void connect_and_stream(const DeviceIdentity&,
                            const std::vector<PacketType>&,
                            OnPacketCallback,
                            OnConnectionEventCallback,
                            OnErrorCallback) override {}
    void disconnect() override {}
    bool is_streaming() const override { return false; }
};

class NoopPublisher : public IPublisherPort {
public:
    void initialize(const std::vector<PacketType>&) override { initialized_ = true; }
    void publish(const SamplePacket&) override {}
    void shutdown() override { initialized_ = false; }
    bool is_ready() const override { return initialized_; }
private:
    bool initialized_ = false;
};

}  // namespace

TEST_CASE("All three port interfaces can be implemented by a subclass") {
    NoopDiscovery discovery;
    NoopStreaming streaming;
    NoopPublisher publisher;

    CHECK(discovery.discovered_devices().empty());
    CHECK_FALSE(streaming.is_streaming());
    CHECK_FALSE(publisher.is_ready());

    publisher.initialize({PacketType::EEG});
    CHECK(publisher.is_ready());
    publisher.shutdown();
    CHECK_FALSE(publisher.is_ready());
}

TEST_CASE("Ports support polymorphic use through base-class pointers") {
    NoopDiscovery discovery_impl;
    IDeviceDiscoveryPort* discovery = &discovery_impl;
    CHECK(discovery->discovered_devices().empty());

    NoopStreaming streaming_impl;
    IStreamingPort* streaming = &streaming_impl;
    CHECK_FALSE(streaming->is_streaming());

    NoopPublisher publisher_impl;
    IPublisherPort* publisher = &publisher_impl;
    CHECK_FALSE(publisher->is_ready());
}
