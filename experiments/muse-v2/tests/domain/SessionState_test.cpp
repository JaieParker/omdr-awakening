// =============================================================================
// SessionState — finite state machine for one streaming session's lifecycle.
//
// States:
//   Idle        — initial, nothing happening
//   Discovering — scanning for nearby Muse devices
//   Connecting  — found a device, attempting connection
//   Streaming   — connected and actively delivering packets
//   Stopping    — disconnect requested, waiting for clean shutdown
//   Stopped     — terminal, no further transitions
//   Failed      — terminal, an unrecoverable error occurred
//
// Transition rules:
//   Idle         -> Discovering (start_discovery)
//   Discovering  -> Connecting  (device_found)
//   Discovering  -> Stopping    (stop requested during discovery)
//   Connecting   -> Streaming   (connection succeeded)
//   Connecting   -> Failed      (connection failed)
//   Streaming    -> Stopping    (stop requested during streaming)
//   Stopping     -> Stopped     (shutdown completed cleanly)
//   Streaming    -> Failed      (BLE dropout or other error)
//   Connecting   -> Stopping    (stop requested while connecting)
//   (any non-terminal) -> Failed (catastrophic error)
//
// Invalid transitions throw std::logic_error. This way the application
// layer can never accidentally drive the session into a nonsensical state.
// =============================================================================

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest/doctest.h"

#include "domain/SessionState.hpp"

using musev2::domain::SessionState;
using musev2::domain::SessionStateMachine;

TEST_CASE("SessionStateMachine starts in Idle state") {
    SessionStateMachine sm;
    CHECK(sm.current() == SessionState::Idle);
}

TEST_CASE("Idle -> Discovering via start_discovery") {
    SessionStateMachine sm;
    sm.start_discovery();
    CHECK(sm.current() == SessionState::Discovering);
}

TEST_CASE("Discovering -> Connecting via device_found") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.device_found();
    CHECK(sm.current() == SessionState::Connecting);
}

TEST_CASE("Connecting -> Streaming via connected") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.device_found();
    sm.connected();
    CHECK(sm.current() == SessionState::Streaming);
}

TEST_CASE("Streaming -> Stopping via stop_requested") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.device_found();
    sm.connected();
    sm.stop_requested();
    CHECK(sm.current() == SessionState::Stopping);
}

TEST_CASE("Stopping -> Stopped via shutdown_complete") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.device_found();
    sm.connected();
    sm.stop_requested();
    sm.shutdown_complete();
    CHECK(sm.current() == SessionState::Stopped);
}

TEST_CASE("Stop can be requested during Discovering") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.stop_requested();  // no device was found yet, cancel
    CHECK(sm.current() == SessionState::Stopping);
    sm.shutdown_complete();
    CHECK(sm.current() == SessionState::Stopped);
}

TEST_CASE("Stop can be requested during Connecting") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.device_found();
    sm.stop_requested();  // abort before streaming starts
    CHECK(sm.current() == SessionState::Stopping);
}

TEST_CASE("Connecting -> Failed via error while connecting") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.device_found();
    sm.error_occurred("BLE pairing rejected");
    CHECK(sm.current() == SessionState::Failed);
    CHECK(sm.last_error() == "BLE pairing rejected");
}

TEST_CASE("Streaming -> Failed via error while streaming") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.device_found();
    sm.connected();
    sm.error_occurred("BLE dropout");
    CHECK(sm.current() == SessionState::Failed);
    CHECK(sm.last_error() == "BLE dropout");
}

TEST_CASE("Stopped is terminal — no further transitions allowed") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.device_found();
    sm.connected();
    sm.stop_requested();
    sm.shutdown_complete();

    CHECK_THROWS_AS(sm.start_discovery(), std::logic_error);
    CHECK_THROWS_AS(sm.device_found(), std::logic_error);
    CHECK_THROWS_AS(sm.connected(), std::logic_error);
    CHECK_THROWS_AS(sm.stop_requested(), std::logic_error);
}

TEST_CASE("Failed is terminal — no further transitions allowed") {
    SessionStateMachine sm;
    sm.start_discovery();
    sm.error_occurred("scan failed");
    CHECK(sm.current() == SessionState::Failed);

    CHECK_THROWS_AS(sm.start_discovery(), std::logic_error);
    CHECK_THROWS_AS(sm.device_found(), std::logic_error);
    CHECK_THROWS_AS(sm.connected(), std::logic_error);
    CHECK_THROWS_AS(sm.stop_requested(), std::logic_error);
    CHECK_THROWS_AS(sm.shutdown_complete(), std::logic_error);
}

TEST_CASE("Invalid transitions from Idle throw logic_error") {
    SessionStateMachine sm;
    CHECK_THROWS_AS(sm.device_found(), std::logic_error);
    CHECK_THROWS_AS(sm.connected(), std::logic_error);
    CHECK_THROWS_AS(sm.stop_requested(), std::logic_error);
    CHECK_THROWS_AS(sm.shutdown_complete(), std::logic_error);
}

TEST_CASE("Invalid transitions from Discovering throw logic_error") {
    SessionStateMachine sm;
    sm.start_discovery();
    CHECK_THROWS_AS(sm.connected(), std::logic_error);         // skipped Connecting
    CHECK_THROWS_AS(sm.shutdown_complete(), std::logic_error); // no shutdown in progress
}

TEST_CASE("SessionState is_terminal returns true for Stopped and Failed only") {
    using musev2::domain::is_terminal;
    CHECK_FALSE(is_terminal(SessionState::Idle));
    CHECK_FALSE(is_terminal(SessionState::Discovering));
    CHECK_FALSE(is_terminal(SessionState::Connecting));
    CHECK_FALSE(is_terminal(SessionState::Streaming));
    CHECK_FALSE(is_terminal(SessionState::Stopping));
    CHECK(is_terminal(SessionState::Stopped));
    CHECK(is_terminal(SessionState::Failed));
}
