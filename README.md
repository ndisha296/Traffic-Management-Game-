# Traffic-Management-Game-

# Smart Route Game

An intelligent routing and navigation game powered by AI/ML algorithms, featuring **A\* Pathfinding** and **Q-Learning (Reinforcement Learning)** for dynamic traffic and smart route optimization.

---

## 📁 Project Structure

```text
SmartRouteGame/
│
├── venv/                 # Virtual environment
│
├── main.py               # Main application entry point
├── config.py             # Game settings, hyperparameters, and colors
├── map_data.py           # City grid, road maps, and obstacle layouts
├── astar.py              # A* pathfinding algorithm implementation
├── traffic.py            # Traffic density and congestion manager
├── traffic_light.py      # Traffic light signal states and timing
├── player.py             # Player agent movement and state
├── train_model.py        # Q-learning training script
├── q_learning.py         # Reinforcement learning Q-table agent
├── game.py               # Pygame main loop and visual rendering
│
├── models/
│   └── q_table.npy       # Saved trained Q-learning policy table
│
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### 1. Activate the Virtual Environment
On Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install pygame numpy
```

### 3. Run the Game
```powershell
python main.py
```

### 4. Train the Reinforcement Learning Model
```powershell
python train_model.py
```

---

## 🎮 Controls & Features
- **Arrow Keys / WASD**: Navigate the player vehicle.
- **A\* Pathfinding**: Visualizes optimal route dynamically avoiding obstacles.
- **Dynamic Traffic & Signals**: Real-time traffic light cycles and congestion weights.
- **Q-Learning Agent**: Reinforcement learning model for automated smart navigation.
