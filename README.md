# F1 Race Replay

A Python-based desktop application that visualizes real-world Formula 1 race telemetry. It uses the `fastf1` library to download official F1 session data and renders a live, animated 2D top-down replay of the race using `tkinter` and `pandas`.

## Features
*   **Accurate Track Mapping**: Extracts the X and Y coordinates of the fastest lap telemetry to procedurally draw the track outline.
*   **Live Animated Leaderboard**: Re-orders drivers dynamically based on the exact Distance metric traveled along the track.
*   **Smooth Car Telemetry**: Interpolates position, speed, and gear telemetry data between timestamps to create fluid car movements.
*   **Team Branding**: Uses the `Pillow` library to dynamically draw rounded badges matched to the respective F1 team's hexadecimal colors.
*   **Playback Speed Controls**: Scrubber slider to seek through time and adjustable playback speed (1x, 2x, 5x, 10x, 20x).

## Setup & Installation
1. Ensure you have Python 3 installed.
2. Initialize and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\\venv\\Scripts\\Activate.ps1
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App
```bash
python main.py
```
> Note: Upon the first launch, the `fastf1` library will download massive quantities of telemetry data and cache them in the `f1_cache` directory. This initial loading process can take a minute or two. Subsequent launches will be near-instant.
