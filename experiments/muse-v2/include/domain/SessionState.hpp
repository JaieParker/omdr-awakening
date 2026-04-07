// =============================================================================
// muse-v2 domain layer — SessionState + SessionStateMachine
//
// A finite state machine describing one streaming session's lifecycle.
// Captures the valid transitions between states and rejects nonsensical
// moves (e.g. jumping from Idle directly to Streaming without going
// through Discovering and Connecting).
//
// The FSM is pure domain code — no threading, no I/O, no libmuse. It's
// driven by the application layer's StreamingSession use case, which
// calls the transition methods in response to events from the ports.
//
// Why a class, not just an enum with free functions: the transition
// rules are the useful invariant, and bundling them with the state
// makes it impossible for callers to skip a validation step.
// =============================================================================

#pragma once

#include <stdexcept>
#include <string>
#include <string_view>

namespace musev2::domain {

enum class SessionState {
    Idle,         ///< initial, no work started
    Discovering,  ///< scanning for Muse devices
    Connecting,   ///< found a device, BLE handshake in progress
    Streaming,    ///< connected, actively delivering SamplePackets
    Stopping,     ///< stop requested, waiting for clean shutdown
    Stopped,      ///< terminal: clean shutdown complete
    Failed,       ///< terminal: unrecoverable error
};

/// True iff the given state is terminal (no further transitions allowed).
inline bool is_terminal(SessionState s) noexcept {
    return s == SessionState::Stopped || s == SessionState::Failed;
}

/// Human-readable name for logging.
inline std::string to_string(SessionState s) {
    switch (s) {
        case SessionState::Idle:        return "Idle";
        case SessionState::Discovering: return "Discovering";
        case SessionState::Connecting:  return "Connecting";
        case SessionState::Streaming:   return "Streaming";
        case SessionState::Stopping:    return "Stopping";
        case SessionState::Stopped:     return "Stopped";
        case SessionState::Failed:      return "Failed";
    }
    return "Unknown";
}

/// Session lifecycle FSM. Starts in Idle, progresses through
/// Discovering -> Connecting -> Streaming, and terminates at Stopped
/// or Failed. Any invalid transition throws std::logic_error.
class SessionStateMachine {
public:
    SessionStateMachine() noexcept : current_(SessionState::Idle) {}

    SessionState current() const noexcept { return current_; }
    const std::string& last_error() const noexcept { return last_error_; }

    /// Idle -> Discovering
    void start_discovery() {
        transition_from_({SessionState::Idle}, SessionState::Discovering, "start_discovery");
    }

    /// Discovering -> Connecting
    void device_found() {
        transition_from_({SessionState::Discovering}, SessionState::Connecting, "device_found");
    }

    /// Connecting -> Streaming
    void connected() {
        transition_from_({SessionState::Connecting}, SessionState::Streaming, "connected");
    }

    /// Discovering | Connecting | Streaming -> Stopping
    void stop_requested() {
        transition_from_(
            {SessionState::Discovering, SessionState::Connecting, SessionState::Streaming},
            SessionState::Stopping,
            "stop_requested"
        );
    }

    /// Stopping -> Stopped
    void shutdown_complete() {
        transition_from_({SessionState::Stopping}, SessionState::Stopped, "shutdown_complete");
    }

    /// Discovering | Connecting | Streaming -> Failed
    /// Also stores the error message for later retrieval.
    void error_occurred(std::string message) {
        transition_from_(
            {SessionState::Discovering, SessionState::Connecting, SessionState::Streaming},
            SessionState::Failed,
            "error_occurred"
        );
        last_error_ = std::move(message);
    }

private:
    /// Throw if current_ is not in `allowed_from`. Otherwise move to `to`.
    void transition_from_(std::initializer_list<SessionState> allowed_from,
                          SessionState to,
                          std::string_view action_name) {
        for (auto s : allowed_from) {
            if (current_ == s) {
                current_ = to;
                return;
            }
        }
        throw std::logic_error(
            "SessionStateMachine: cannot " + std::string(action_name) +
            " from state " + to_string(current_)
        );
    }

    SessionState current_;
    std::string last_error_;
};

}  // namespace musev2::domain
