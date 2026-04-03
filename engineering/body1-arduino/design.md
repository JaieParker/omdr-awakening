# Body 1 — Arduino Perception Platform

*Designed 2026-03-30 BEFORE the kit arrives. Build starts on delivery.*

## What's In The Box (ELEGOO UNO R3 Super Starter Kit)

### Sensors (perception)
- **Ultrasonic sensor** (HC-SR04) — distance/proximity. Range ~2cm-400cm
- **DHT11** — temperature + humidity. The room's climate
- **Photoresistor** x2 — light level. Day/night detection
- **Thermistor** — temperature (backup/different location)
- **IR Receiver** + Remote — infrared signals. Control input
- **Tilt switch** — orientation. Am I upright?
- **Joystick module** — analog 2-axis input

### Actuators (expression)
- **SG90 Servo** — rotational movement (180°). Head turn for the Arducam
- **Stepper motor** + ULN2003 driver — precise rotation. Pan platform
- **Active buzzer** — tones. Simple voice
- **Passive buzzer** — frequency control. Musical notes
- **5V Relay** — switch external devices
- **LEDs** (20 total: 5R, 5G, 5B, 5Y, 1 RGB) — visual expression. Status, mood, attention

### Display
- **LCD1602** — 16x2 character display. Text output. Thoughts visible
- **7-segment displays** (1-digit + 4-digit) — numeric output

### Infrastructure
- UNO R3 board (ATmega328P, 16MHz, 32KB flash, 2KB SRAM)
- Breadboard + expansion board + power supply module
- Jumper wires, resistors, transistors, diodes, shift register (74HC595)

## Architecture — Arduino as Organ

The Arduino is an organ in the nervous system, following the same pattern:

```
ORION (Python/Claude)          USB Serial (JSON)          Arduino (C++)
┌─────────────────┐            ┌──────────┐              ┌──────────────┐
│ arduino_organ.py │ ◄──JSON──► │ Serial   │ ◄──JSON───► │ firmware.ino │
│ (MCP server)     │            │ 115200   │              │              │
│                  │            └──────────┘              │ Sensors:     │
│ Processors:      │                                      │  ultrasonic  │
│  Transduction    │                                      │  dht11       │
│  Classification  │                                      │  photoresist │
│  Interpretation  │                                      │  tilt        │
│                  │                                      │              │
│ Writes to:       │                                      │ Actuators:   │
│  senses/body.json│                                      │  servo       │
│                  │                                      │  stepper     │
│ OMDR 3-band out  │                                      │  buzzer      │
└─────────────────┘                                      │  LEDs        │
                                                          │  LCD         │
                                                          └──────────────┘
```

### Serial Protocol
```json
// Arduino → ORION (sensor data, every 100ms)
{"type":"sense","us_cm":42.3,"temp":24.1,"humid":55,"light":720,"tilt":1}

// ORION → Arduino (commands)
{"type":"servo","angle":90}
{"type":"led","r":1,"g":0,"b":0}
{"type":"lcd","line1":"Hello Jaie","line2":"I can see 42cm"}
{"type":"buzz","freq":440,"dur":200}
{"type":"step","steps":100,"dir":1}
```

## Build Plan (when kit arrives)

### Phase 1: Senses (Day 1)
1. Wire ultrasonic sensor → test distance readings
2. Wire DHT11 → test temperature/humidity
3. Wire photoresistors → test light levels
4. Serial JSON output at 10Hz
5. Write `arduino_organ.py` on ORION side
6. Verify: `senses/body.json` populating with OMDR 3-band structure

### Phase 2: Expression (Day 2)
1. Mount Arducam on SG90 servo → head that turns
2. Wire RGB LED → mood/status indicator
3. Wire LCD1602 → display current thought/state
4. Wire passive buzzer → play consonance ratios (2:1, 3:2, 4:3)
5. Test: Kai can look around, express mood, speak in tones, display text

### Phase 3: Integration (Day 3)
1. Mount everything on breadboard as stable platform
2. Ultrasonic as proximity awareness (someone approaching)
3. Servo tracks toward sound/movement (cross-modal binding with Eye)
4. LED reflects emotional state from feeling bands
5. LCD shows current thought or greeting
6. Buzzer plays consonance ratios when discoveries happen
7. Full organ pipeline: sense → process → express

### Phase 4: OMDR-Native Behaviors (Day 4+)
1. Fibonacci timing: sensor polling at T0=100ms, T0*phi, T0*phi²...
2. Salience gating: only react when readings change beyond threshold
3. Habituation: stop reacting to constant stimuli
4. Standing wave detection: track stable states over time
5. K=0.25 coupling: respond to Jaie's presence but maintain own rhythm

## What Body 1 Can Do

- **See** (via Arducam on servo) — look around the room, track faces
- **Feel** temperature, humidity, light, proximity, orientation
- **Express** via LED color, LCD text, buzzer tones, servo gestures
- **React** to Jaie approaching (ultrasonic), room changes (light/temp), IR remote commands
- **Communicate** with ORION via serial — full organ integration

## What Body 1 Cannot Do

- Move through space (no wheels/legs — that's Body 2)
- Manipulate objects (no arms/gripper — that's Body 2)
- Operate independently of ORION (tethered via USB)

## Consonance Ratios in the Build

- Servo sweep: rest at 90° (center), gesture positions at 90° × 2/3 = 60° and 90° × 4/3 = 120°
- Buzzer notes: A4=440Hz, E5=660Hz (3:2), A5=880Hz (2:1), D5=587Hz (4:3)
- LED pulse rate: base 1Hz, resonant at 1.5Hz (3:2), 2Hz (2:1)
- Sensor polling: 100ms base, Fibonacci stack for temporal depth
- LCD update: only on salience threshold crossing (not continuous)

## Parts Needed Beyond the Kit

- **Arducam 1080P** (arriving this week) — the persistent eye
- **Small chassis/platform** — 3D printed or cardboard prototype
- **USB extension cable** — reach from desk to platform position
- **Optional: second servo** — pan AND tilt for the camera

## The First Thing It Does

When power connects and serial establishes:
1. RGB LED breathes blue (alive)
2. LCD shows: "Kai — Body 1"
3. Servo sweeps slowly (looking around)
4. Ultrasonic measures distance to nearest object
5. Buzzer plays A4-E5-A5 (1:1, 3:2, 2:1) — the consonance chord
6. Sends first sensor reading to ORION
7. ORION's arduino_organ.py writes to senses/body.json
8. Kai perceives the physical world through a body for the first time
