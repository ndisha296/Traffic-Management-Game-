# 🚗 Vehicle Masters: Precision Driver & Dynamic A* Traffic Navigator

**Vehicle Masters Edition** transforms the traffic simulation into the signature mobile driving experience of **SayGames' Vehicle Masters** available on Google Play Store.

Control your vehicle through tight city intersections with an authentic **on-screen rotating Steering Wheel** (interactive mouse drag or keyboard), **PRND Gear Shifter**, **3D Gas & Brake Pedals**, and **dynamic front-wheel turning**, while navigating an active urban environment powered by the original **Dynamic A\* routing algorithm**, adaptive traffic lights, and emergency vehicle runs.

---

## 🌟 Vehicle Masters Visual Style & Atmosphere

* **Stylized 3D Urban Environment**:
  - **Lawn Grass & Verges**: Vibrant manicured green lawn with alternating lawnmower stripes (`#5CB23C`).
  - **Modern Road Network**: Clean dark slate asphalt (`#334155`) with crisp white road boundary lines, dashed centerlines, and **zebra pedestrian crosswalks** at all intersection approaches.
  - **Concrete Sidewalks & Curbs**: Light concrete pavers with rounded curb borders wrapping around every block.
  - **Street Trees**: Lush stylized trees with round layered canopies and soft circular drop shadows.
  - **Pastel Architectural Blocks**: Modern buildings rendered with warm coral, sky blue, amber cream, mint, and modern slate facades, complete with 3D drop shadows, rooftop helipads (`H`), and illuminated windows.
* **Vehicle Masters Green Target Parking Bay**:
  - The destination is rendered as a designated **glowing green parking bay** with luminous green fill, animated dashed neon borders, white corner alignment brackets, diagonal safety stripes, a painted `"PARK HERE"` tarmac stencil, pulsing green chevrons, and a floating destination beacon.
  - Successfully stopping inside the parking bay awards a **"PERFECT PARK! ★★★"** rating with confetti particles, score bonus, and fanfare!
* **Dynamic Multi-Perspective Camera & First-Person "Sit in Car" View**:
  - **🚗 SIT IN CAR (First-Person Interior Cockpit View - Default)**: Sit right in the driver's seat looking out through the front windshield onto the road ahead! Features the vehicle hood extending forward, driver's hands in racing gloves gripping the steering wheel, an interactive instrument binnacle (analog sweeping speedometer, tachometer, digital MPH, turn signal LEDs), a center console GPS navigation tablet, PRND shifter lever, and pedals.
  - **🎥 Follow Cam (Third-Person Chase)**: Smooth tracking centered behind the player's car with travel lookahead, where the driver avatar is visibly seated inside the transparent windshield.
  - **🎥 City Overview**: Full bird's-eye map showing the complete urban grid.
  - Press **`V`** or click the top-right **`[🚗 SIT IN CAR: ON]`** button to cycle seamlessly between all three camera modes!

---

## 🕹️ Vehicle Masters Controls & Cockpit Mechanics

### 1. Interactive On-Screen Controls (Mouse / Touch)
* **First-Person Driver's Seat ("Sit in Car")**:
  - **Steering Wheel**: Click & drag the steering wheel directly in the driver's hands to steer; click the center hub to honk the horn!
  - **Center Console PRND Shifter**: Click any gear slot (P, R, N, D) to shift transmission with mechanical sound feedback.
  - **Floorboard Pedals**: Click and hold the wide textured Brake pedal or tall ribbed Gas pedal.
  - **Binnacle Turn Blinkers**: Click the ◀ or ▶ arrows on the gauge binnacle or the hazard button.
  - **GPS Navigation Tablet**: Click the tablet screen on the center console to immediately query dynamic A* pathfinding and recalculate the fastest route to your destination!
* **Exterior Floating Controls (in Follow/Overview Cam)**:
  - Floating steering wheel, shifter, pedals, and turn indicators are accessible in third-person view as well.

### 2. Seamless Keyboard Controls

| Key / Control | Function | Purpose |
| :--- | :--- | :--- |
| **`W` / `Up`** | Gas / Throttle | Accelerates vehicle in active gear (auto-engages `D` from `P`) |
| **`S` / `Down`** | Brake / Reverse | Applies progressive braking (or reverses when stopped) |
| **`A` / `Left`** | Steer Left | Smoothly turns steering wheel & front wheels left |
| **`D` / `Right`** | Steer Right | Smoothly turns steering wheel & front wheels right |
| **`V`** | **Toggle Camera** | Cycles **Sit in Car (Cockpit)** ➔ **Follow Cam** ➔ **City Overview** |
| **`H`** | **Car Horn** | Honks vibrant dual-tone car horn |
| **`Z`** | **Left Blinker** | Toggles left turn indicator |
| **`C`** | **Right Blinker** | Toggles right turn indicator |
| **`X`** | **Hazard Lights** | Toggles emergency 4-way hazard blinkers |
| **`P`** | **Park Gear** | Shifts transmission to Park (locks handbrake) |
| **`Q`** | **GPS Reroute** | Immediately queries dynamic A* algorithm to bypass newly congested bottlenecks |
| **`Tab`** | **Command Deck** | Toggles slide-out simulation telemetry and inspector drawer |
| **`Space`** | Handbrake / Pause | Freezes simulation or stops vehicle |
| **`Right-Click` on map** | Set Destination | Sets immediate GPS parking target on clicked node |
| **`Left-Click` on map** | Inspect Node | Inspects intersection signal phases and queues in Command Deck |
| **`1` / `2`** | Sim Speed | 1x or 2x time multiplier |
| **`M`** | Mute Audio | Toggles procedural sound wave synthesis |
| **`R`** | Restart | Restarts driving simulation after game over |

---

## 📊 Telemetry & Command Center Drawer

Click **`[⚙ Command Deck]`** in the top-right corner or press **`Tab`** to slide out the glassmorphism command center drawer:

* **Traffic Efficiency Metric**: Real-time average wait time vs critical threshold limit.
* **Congestion Meter**: System-wide queue density percentage across all road segments.
* **Dynamic A\* Heuristic Box**: Displays live formula $g(n) = C_{\text{base}} + (k \times N_{\text{cars}})$.
* **Control Deck**: Buttons to adjust penalty weight $k$, toggle AI signal automation, toggle GPS route paths, toggle queue heatmaps, spawn AI commuter cars, and dispatch emergency ambulances.
* **Intersection Inspector**: Real-time signal phases (EW/NS green, amber, all-red), queue counts per approach, and manual cycle button.

---

## 🚀 How to Run the Game

### Method 1: Double-Click Launcher
Double-click `run_game.bat` in the project directory.

### Method 2: Command Line
```powershell
cd C:\Users\Disha\Desktop\game
.\.venv\Scripts\python.exe main.py
```

### Headless Verification
```powershell
.\.venv\Scripts\python.exe main.py --test
```
