# Ride Dispatch System

A real-time ride dispatch simulation system built with FastAPI and vanilla JavaScript. The system manages drivers, riders, and ride requests with automatic driver assignment based on proximity.

## System Overview

The application simulates a ride-sharing platform where:
- Drivers are positioned on a 100x100 grid
- Riders request rides from pickup to dropoff locations
- The system automatically assigns the closest available driver
- Drivers move one step per tick towards pickup/dropoff locations
- Real-time visualization shows the entire dispatch process

## Code Structure

### Backend (Python/FastAPI)

**`main.py`**
- Application entry point
- FastAPI app configuration
- Static file serving

**`models.py`**
- Data models and enums
- Driver, Rider, RideRequest, and Location classes
- Status enums for drivers and riders

**`helpers.py`**
- Business logic functions
- Distance calculations
- Driver assignment algorithms
- Movement logic

**`routes.py`**
- API endpoints
- CRUD operations for drivers, riders, and rides
- Time advancement (tick) system
- State management

### Frontend (HTML/JavaScript)

**`static/index.html`**
- Complete web interface
- Real-time grid visualization
- Interactive controls
- Ride request management
- Activity logging system

## Key Features

- **Real-time Grid Visualization**: 100x100 grid showing drivers, riders, pickup/dropoff locations
- **Automatic Driver Assignment**: Closest available driver is assigned to each ride request
- **Time-based Movement**: Drivers move one step per tick towards destinations
- **Interactive Controls**: Add drivers/riders, request rides, accept/reject rides
- **Activity Logging**: Scrollable log of all system events
- **State Management**: Clear system state and reset functionality

## Getting Started

### Prerequisites

- Python 3.7+
- FastAPI
- Uvicorn

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the application:
```bash
python main.py
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Frontend Interface

The web interface provides a comprehensive view of the ride dispatch system:

- **Grid Visualization**: 100x100 interactive grid showing real-time positions of drivers, riders, pickup/dropoff locations
- **Legend**: Color-coded indicators for different entities (drivers, riders, pickup, dropoff, pending)
- **Controls Panel**: Add drivers/riders, request rides, advance time, and manage system state
- **System Status**: Real-time counters for drivers, riders, and active rides
- **Ride Management**: List of all ride requests with accept/reject buttons for pending rides
- **Activity Log**: Scrollable log showing all system events with timestamps and color-coded entries

## Usage

1. **Add Drivers**: Use the "Add Driver" controls to place drivers on the grid
2. **Add Riders**: Create riders with pickup and dropoff locations
3. **Request Rides**: Select a rider and click "Request Ride"
4. **Manage Rides**: Accept or reject pending ride requests
5. **Advance Time**: Click "Next Tick" to move drivers and update ride status
6. **Monitor Activity**: View the activity log for system events

## API Endpoints

- `GET /` - Main application interface
- `POST /drivers` - Create a new driver
- `POST /riders` - Create a new rider
- `POST /rides` - Request a new ride
- `POST /rides/{ride_id}/respond` - Accept/reject a ride
- `POST /tick` - Advance time by one tick
- `GET /state` - Get current system state
- `POST /clear-state` - Reset the entire system 