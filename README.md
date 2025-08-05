# Ride Dispatch System

A simplified ride-hailing backend system built with FastAPI and a basic frontend UI to visualize and simulate the system.

## Features

- **FastAPI Backend**: Manages city grid, drivers, riders, and ride requests
- **Dispatch Logic**: Assigns drivers to ride requests based on ETA, fairness, and availability
- **Grid-based City**: 2D grid (20x20) where drivers and riders exist at (x,y) coordinates
- **Time-based Simulation**: Manual time advancement through `/tick` endpoint
- **Simple Frontend**: Browser-based UI to interact with the system

## How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**:
   ```bash
   python main.py
   ```

3. **Access the Application**:
   - Open your browser and go to `http://localhost:8000`
   - The FastAPI documentation is available at `http://localhost:8000/docs`

## How the Dispatching Works

### Dispatch Logic Goals

The system balances the following objectives:

1. **Low ETA**: Assigns drivers with shortest travel time to pickup location
2. **Fairness**: Ensures no driver gets all requests; distributes evenly
3. **Efficiency**: Maximizes fulfilled rides; minimizes idle drivers
4. **Fallbacks**: Retries with other drivers if the first one rejects

### Current Implementation

- **ETA Calculation**: Uses Manhattan distance (`|x1-x2| + |y1-y2|`)
- **Driver Selection**: Sorts available drivers by distance to pickup location
- **Movement**: Drivers move 1 unit per tick towards their destination
- **Simple Fairness**: Currently implements basic closest-driver assignment

### Algorithm Details

```python
def find_best_driver(pickup_location: Location) -> Optional[str]:
    # Get all available drivers
    available_drivers = [d for d in drivers.values() if d.status == DriverStatus.AVAILABLE]
    
    if not available_drivers:
        return None
    
    # Sort by ETA (distance to pickup)
    available_drivers.sort(key=lambda d: calculate_eta(d.location, pickup_location))
    
    # Return the closest driver
    return available_drivers[0].id
```

## System Entities

### Driver
- Unique ID
- Current location (x, y)
- Status: `available`, `on_trip`, or `offline`

### Rider
- Unique ID
- Pickup location (x, y)
- Dropoff location (x, y)

### RideRequest
- Rider ID
- Pickup and dropoff locations
- Status: `waiting`, `assigned`, `rejected`, `completed`, or `failed`
- Assigned driver ID

## API Endpoints

- `GET /` - Frontend UI
- `GET /state` - Get current system state
- `POST /drivers` - Create a new driver
- `GET /drivers` - Get all drivers
- `DELETE /drivers/{driver_id}` - Delete a driver
- `POST /riders` - Create a new rider
- `GET /riders` - Get all riders
- `DELETE /riders/{rider_id}` - Delete a rider
- `POST /rides` - Request a ride
- `GET /rides` - Get all ride requests
- `POST /tick` - Advance time by one tick

## Frontend Features

- **Grid Visualization**: 20x20 grid showing drivers, riders, and active rides
- **Add/Remove Entities**: Add drivers and riders at specific coordinates
- **Request Rides**: Select a rider and request a ride
- **Time Control**: Advance simulation time with "Next Tick" button
- **Real-time Updates**: See current system state and ride status

## Assumptions and Simplifications

1. **Grid Size**: Using 20x20 grid for better visualization (instead of 100x100)
2. **Movement**: Drivers move 1 unit per tick in both x and y directions
3. **ETA Calculation**: Manhattan distance for simplicity
4. **Driver Rejection**: Not implemented in this basic version
5. **Persistence**: In-memory storage only
6. **Real-time**: No WebSocket connections; manual refresh required
7. **Authentication**: No authentication required
8. **Driver Speed**: Fixed at 1 unit per tick

## Future Enhancements

- Implement driver rejection mechanism
- Add more sophisticated fairness algorithms
- Implement ride cancellation
- Add driver earnings tracking
- Implement multiple driver types with different speeds
- Add traffic simulation
- Implement persistent storage
- Add real-time WebSocket updates

## Evaluation Criteria

- ✅ **Correctness**: Ride requests are assigned and completed correctly
- 🧠 **Dispatch Logic**: Logic is well-thought-out and documented
- 🧹 **Code Quality**: Code is clean, modular, and understandable
- 🔁 **Extensibility**: System is designed to scale and support future features 