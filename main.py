from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Set
import uuid
from enum import Enum
import math

app = FastAPI(title="Ride Dispatch System")

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enums
class DriverStatus(str, Enum):
    IDLE = "idle"
    GOING_TO_PICKUP = "going_to_pickup"
    DRIVING_TO_DEST = "driving_to_dest"
    BUSY = "busy"

class RiderStatus(str, Enum):
    WAITING = "waiting"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"

# Models
class Location(BaseModel):
    x: int
    y: int

class Driver(BaseModel):
    id: str
    location: Location
    status: DriverStatus
    pending_requests: List[str] = []  # List of ride request IDs
    current_ride_id: Optional[str] = None

class Rider(BaseModel):
    id: str
    pickup_location: Location
    dropoff_location: Location
    status: RiderStatus
    current_ride_id: Optional[str] = None

class RideRequest(BaseModel):
    id: str
    rider_id: str
    pickup_location: Location
    dropoff_location: Location
    status: str  # "pending", "accepted", "rejected", "completed"
    assigned_driver_id: Optional[str] = None
    rejected_by: List[str] = []  # List of driver IDs who rejected this request

class RideRequestCreate(BaseModel):
    rider_id: str

class DriverResponse(BaseModel):
    action: str  # "accept" or "reject"
    ride_id: str

# Global state (in-memory storage)
drivers: Dict[str, Driver] = {}
riders: Dict[str, Rider] = {}
ride_requests: Dict[str, RideRequest] = {}
current_tick = 0
GRID_SIZE = 100
MAX_DRIVER_REQUESTS = 5

def calculate_euclidean_distance(location1: Location, location2: Location) -> float:
    """Calculate Euclidean distance between two locations"""
    return math.sqrt((location2.x - location1.x) ** 2 + (location2.y - location1.y) ** 2)

def find_available_drivers(pickup_location: Location, exclude_drivers: Set[str] = None) -> List[tuple]:
    """Find all available drivers sorted by distance to pickup location"""
    if exclude_drivers is None:
        exclude_drivers = set()
    
    available_drivers = []
    for driver_id, driver in drivers.items():
        if (driver_id not in exclude_drivers and 
            driver.status == DriverStatus.IDLE and 
            len(driver.pending_requests) < MAX_DRIVER_REQUESTS):
            distance = calculate_euclidean_distance(driver.location, pickup_location)
            available_drivers.append((driver_id, distance))
    
    # Sort by distance (closest first)
    available_drivers.sort(key=lambda x: x[1])
    return available_drivers

def send_request_to_next_driver(ride_request: RideRequest):
    """Send ride request to the next closest available driver"""
    exclude_drivers = set(ride_request.rejected_by)
    available_drivers = find_available_drivers(ride_request.pickup_location, exclude_drivers)
    
    if available_drivers:
        next_driver_id, distance = available_drivers[0]
        driver = drivers[next_driver_id]
        
        # Add request to driver's pending queue
        driver.pending_requests.append(ride_request.id)
        ride_request.assigned_driver_id = next_driver_id
        
        print(f"[REQUEST_ROUTING] Ride {ride_request.id[:8]} sent to driver {next_driver_id[:8]} (distance: {distance:.2f})")
        print(f"[REQUEST_ROUTING] Driver {next_driver_id[:8]} now has {len(driver.pending_requests)} pending requests")
    else:
        # No available drivers
        ride_request.status = "rejected"
        ride_request.assigned_driver_id = None
        print(f"[REQUEST_ROUTING] No available drivers for ride {ride_request.id[:8]}")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/drivers", response_model=Driver)
async def create_driver(location: Location):
    try:
        print(f"[DRIVER_CREATE] Starting driver creation at location: {location}")
        
        # Validate location coordinates
        if location.x < 0 or location.y < 0 or location.x >= GRID_SIZE or location.y >= GRID_SIZE:
            error_msg = f"Invalid location coordinates: ({location.x}, {location.y}). Grid size is {GRID_SIZE}x{GRID_SIZE}"
            print(f"[DRIVER_CREATE] ERROR: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        driver_id = str(uuid.uuid4())
        print(f"[DRIVER_CREATE] Generated driver ID: {driver_id}")
        
        driver = Driver(
            id=driver_id,
            location=location,
            status=DriverStatus.IDLE,
            pending_requests=[],
            current_ride_id=None
        )
        
        drivers[driver_id] = driver
        print(f"[DRIVER_CREATE] SUCCESS: Driver {driver_id} created at ({location.x}, {location.y})")
        print(f"[DRIVER_CREATE] Total drivers in system: {len(drivers)}")
        
        return driver
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error creating driver: {str(e)}"
        print(f"[DRIVER_CREATE] CRITICAL ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.delete("/drivers/{driver_id}")
async def delete_driver(driver_id: str):
    if driver_id not in drivers:
        raise HTTPException(status_code=404, detail="Driver not found")
    del drivers[driver_id]
    return {"message": "Driver deleted"}

@app.get("/drivers", response_model=List[Driver])
async def get_drivers():
    return list(drivers.values())

@app.post("/riders", response_model=Rider)
async def create_rider(pickup_location: Location, dropoff_location: Location):
    try:
        print(f"[RIDER_CREATE] Starting rider creation")
        print(f"[RIDER_CREATE] Pickup location: {pickup_location}")
        print(f"[RIDER_CREATE] Dropoff location: {dropoff_location}")
        
        # Validate pickup location coordinates
        if pickup_location.x < 0 or pickup_location.y < 0 or pickup_location.x >= GRID_SIZE or pickup_location.y >= GRID_SIZE:
            error_msg = f"Invalid pickup location coordinates: ({pickup_location.x}, {pickup_location.y}). Grid size is {GRID_SIZE}x{GRID_SIZE}"
            print(f"[RIDER_CREATE] ERROR: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate dropoff location coordinates
        if dropoff_location.x < 0 or dropoff_location.y < 0 or dropoff_location.x >= GRID_SIZE or dropoff_location.y >= GRID_SIZE:
            error_msg = f"Invalid dropoff location coordinates: ({dropoff_location.x}, {dropoff_location.y}). Grid size is {GRID_SIZE}x{GRID_SIZE}"
            print(f"[RIDER_CREATE] ERROR: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Check if pickup and dropoff are the same
        if pickup_location.x == dropoff_location.x and pickup_location.y == dropoff_location.y:
            error_msg = f"Pickup and dropoff locations cannot be the same: ({pickup_location.x}, {pickup_location.y})"
            print(f"[RIDER_CREATE] ERROR: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        rider_id = str(uuid.uuid4())
        print(f"[RIDER_CREATE] Generated rider ID: {rider_id}")
        
        rider = Rider(
            id=rider_id,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            status=RiderStatus.WAITING,
            current_ride_id=None
        )
        
        riders[rider_id] = rider
        print(f"[RIDER_CREATE] SUCCESS: Rider {rider_id} created")
        print(f"[RIDER_CREATE] Pickup: ({pickup_location.x}, {pickup_location.y}) → Dropoff: ({dropoff_location.x}, {dropoff_location.y})")
        print(f"[RIDER_CREATE] Total riders in system: {len(riders)}")
        
        return rider
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error creating rider: {str(e)}"
        print(f"[RIDER_CREATE] CRITICAL ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.delete("/riders/{rider_id}")
async def delete_rider(rider_id: str):
    if rider_id not in riders:
        raise HTTPException(status_code=404, detail="Rider not found")
    del riders[rider_id]
    return {"message": "Rider deleted"}

@app.get("/riders", response_model=List[Rider])
async def get_riders():
    return list(riders.values())

@app.post("/rides", response_model=RideRequest)
async def request_ride(ride_request: RideRequestCreate):
    try:
        rider_id = ride_request.rider_id
        print(f"[RIDE_REQUEST] Starting ride request for rider: {rider_id}")
        
        # Validate rider exists
        if rider_id not in riders:
            error_msg = f"Rider not found: {rider_id}"
            print(f"[RIDE_REQUEST] ERROR: {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)
        
        rider = riders[rider_id]
        print(f"[RIDE_REQUEST] Found rider: {rider_id}")
        print(f"[RIDE_REQUEST] Rider pickup: ({rider.pickup_location.x}, {rider.pickup_location.y})")
        print(f"[RIDE_REQUEST] Rider dropoff: ({rider.dropoff_location.x}, {rider.dropoff_location.y})")
        
        ride_id = str(uuid.uuid4())
        print(f"[RIDE_REQUEST] Generated ride ID: {ride_id}")
        
        # Create ride request
        ride_request = RideRequest(
            id=ride_id,
            rider_id=rider_id,
            pickup_location=rider.pickup_location,
            dropoff_location=rider.dropoff_location,
            status="pending",
            assigned_driver_id=None,
            rejected_by=[]
        )
        
        # Find closest available driver
        available_drivers = find_available_drivers(rider.pickup_location)
        
        if available_drivers:
            closest_driver_id, distance = available_drivers[0]
            driver = drivers[closest_driver_id]
            
            # Add request to driver's pending queue
            driver.pending_requests.append(ride_id)
            ride_request.assigned_driver_id = closest_driver_id
            
            print(f"[RIDE_REQUEST] Ride {ride_id} sent to closest driver {closest_driver_id[:8]} (distance: {distance:.2f})")
            print(f"[RIDE_REQUEST] Driver {closest_driver_id[:8]} now has {len(driver.pending_requests)} pending requests")
        else:
            print(f"[RIDE_REQUEST] WARNING: No available drivers found")
            ride_request.status = "rejected"
        
        ride_requests[ride_id] = ride_request
        print(f"[RIDE_REQUEST] SUCCESS: Ride {ride_id} created with status: {ride_request.status}")
        print(f"[RIDE_REQUEST] Total active rides: {len(ride_requests)}")
        
        return ride_request
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error requesting ride: {str(e)}"
        print(f"[RIDE_REQUEST] CRITICAL ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/rides/{ride_id}/respond", response_model=RideRequest)
async def driver_respond_to_ride(ride_id: str, response: DriverResponse):
    try:
        print(f"[DRIVER_RESPONSE] Driver responding to ride {ride_id}")
        print(f"[DRIVER_RESPONSE] Action: {response.action}")
        
        # Validate ride exists
        if ride_id not in ride_requests:
            error_msg = f"Ride not found: {ride_id}"
            print(f"[DRIVER_RESPONSE] ERROR: {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)
        
        ride = ride_requests[ride_id]
        print(f"[DRIVER_RESPONSE] Found ride: {ride_id}")
        print(f"[DRIVER_RESPONSE] Current status: {ride.status}")
        
        # Validate ride is pending
        if ride.status != "pending":
            error_msg = f"Ride {ride_id} is not pending. Current status: {ride.status}"
            print(f"[DRIVER_RESPONSE] ERROR: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate driver exists
        if not ride.assigned_driver_id or ride.assigned_driver_id not in drivers:
            error_msg = f"Assigned driver not found for ride {ride_id}"
            print(f"[DRIVER_RESPONSE] ERROR: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        driver = drivers[ride.assigned_driver_id]
        print(f"[DRIVER_RESPONSE] Driver: {ride.assigned_driver_id}")
        print(f"[DRIVER_RESPONSE] Driver current status: {driver.status}")
        
        # Process driver response
        if response.action.lower() == "accept":
            print(f"[DRIVER_RESPONSE] Driver accepting ride")
            
            # Check if driver is still idle
            if driver.status != DriverStatus.IDLE:
                error_msg = f"Driver {ride.assigned_driver_id} is not idle. Current status: {driver.status}"
                print(f"[DRIVER_RESPONSE] ERROR: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Accept the ride
            ride.status = "accepted"
            driver.status = DriverStatus.GOING_TO_PICKUP
            driver.current_ride_id = ride_id
            
            # Remove this request from driver's pending requests
            if ride_id in driver.pending_requests:
                driver.pending_requests.remove(ride_id)
            
            # Reject all other pending requests for this driver
            for other_ride_id in driver.pending_requests[:]:  # Copy list to avoid modification during iteration
                other_ride = ride_requests[other_ride_id]
                other_ride.rejected_by.append(ride.assigned_driver_id)
                other_ride.assigned_driver_id = None
                send_request_to_next_driver(other_ride)
            
            # Clear driver's pending requests (all rejected)
            driver.pending_requests.clear()
            
            # Update rider status
            rider = riders[ride.rider_id]
            rider.status = RiderStatus.ASSIGNED
            rider.current_ride_id = ride_id
            
            print(f"[DRIVER_RESPONSE] SUCCESS: Ride {ride_id} accepted by driver {ride.assigned_driver_id}")
            print(f"[DRIVER_RESPONSE] Driver status changed to GOING_TO_PICKUP")
            print(f"[DRIVER_RESPONSE] All other pending requests for this driver have been rejected and rerouted")
            
        elif response.action.lower() == "reject":
            print(f"[DRIVER_RESPONSE] Driver rejecting ride")
            
            # Add driver to rejected list
            ride.rejected_by.append(ride.assigned_driver_id)
            
            # Remove request from driver's pending queue
            if ride_id in driver.pending_requests:
                driver.pending_requests.remove(ride_id)
            
            # Try to find next closest driver
            send_request_to_next_driver(ride)
            
            print(f"[DRIVER_RESPONSE] SUCCESS: Ride {ride_id} rejected by driver {ride.assigned_driver_id}")
            print(f"[DRIVER_RESPONSE] Request sent to next closest driver")
        else:
            error_msg = f"Invalid action: {response.action}. Must be 'accept' or 'reject'"
            print(f"[DRIVER_RESPONSE] ERROR: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        print(f"[DRIVER_RESPONSE] Final ride status: {ride.status}")
        return ride
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error processing driver response: {str(e)}"
        print(f"[DRIVER_RESPONSE] CRITICAL ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/drivers/{driver_id}/pending-rides", response_model=List[RideRequest])
async def get_driver_pending_rides(driver_id: str):
    try:
        print(f"[DRIVER_PENDING_RIDES] Fetching pending rides for driver: {driver_id}")
        
        # Validate driver exists
        if driver_id not in drivers:
            error_msg = f"Driver not found: {driver_id}"
            print(f"[DRIVER_PENDING_RIDES] ERROR: {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Find rides pending for this driver
        pending_rides = [
            ride for ride in ride_requests.values()
            if ride.assigned_driver_id == driver_id and ride.status == "pending"
        ]
        
        print(f"[DRIVER_PENDING_RIDES] Found {len(pending_rides)} pending rides for driver {driver_id}")
        return pending_rides
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error fetching driver pending rides: {str(e)}"
        print(f"[DRIVER_PENDING_RIDES] CRITICAL ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/rides", response_model=List[RideRequest])
async def get_rides():
    return list(ride_requests.values())

@app.post("/tick")
async def tick():
    """Advance time by one tick"""
    global current_tick
    try:
        print(f"[TICK] Starting time advancement from tick {current_tick} to {current_tick + 1}")
        
        current_tick += 1
        
        print(f"[TICK] Advanced to tick {current_tick}")
        print(f"[TICK] Processing {len(ride_requests)} ride requests")
        
        completed_rides = 0
        active_rides = 0
        
        # Update driver positions and ride statuses
        for ride_id, ride in ride_requests.items():
            if ride.status == "accepted" and ride.assigned_driver_id:
                active_rides += 1
                driver = drivers[ride.assigned_driver_id]
                rider = riders[ride.rider_id]
                
                print(f"[TICK] Processing ride {ride_id[:8]} with driver {ride.assigned_driver_id[:8]}")
                print(f"[TICK] Driver location: ({driver.location.x}, {driver.location.y})")
                print(f"[TICK] Pickup location: ({ride.pickup_location.x}, {ride.pickup_location.y})")
                print(f"[TICK] Dropoff location: ({ride.dropoff_location.x}, {ride.dropoff_location.y})")
                
                # Move driver towards pickup location
                if driver.status == DriverStatus.GOING_TO_PICKUP:
                    if driver.location != ride.pickup_location:
                        old_location = (driver.location.x, driver.location.y)
                        
                        # Move one step towards pickup
                        if driver.location.x < ride.pickup_location.x:
                            driver.location.x += 1
                        elif driver.location.x > ride.pickup_location.x:
                            driver.location.x -= 1
                        
                        if driver.location.y < ride.pickup_location.y:
                            driver.location.y += 1
                        elif driver.location.y > ride.pickup_location.y:
                            driver.location.y -= 1
                        
                        print(f"[TICK] Driver moved from {old_location} to ({driver.location.x}, {driver.location.y})")
                    
                    # Check if reached pickup location
                    if driver.location == ride.pickup_location:
                        driver.status = DriverStatus.DRIVING_TO_DEST
                        rider.status = RiderStatus.IN_TRANSIT
                        print(f"[TICK] Driver reached pickup location")
                        print(f"[TICK] Driver status changed to DRIVING_TO_DEST")
                        print(f"[TICK] Rider status changed to IN_TRANSIT")
                
                # Move driver towards dropoff location
                elif driver.status == DriverStatus.DRIVING_TO_DEST:
                    if driver.location != ride.dropoff_location:
                        old_location = (driver.location.x, driver.location.y)
                        
                        # Move one step towards dropoff
                        if driver.location.x < ride.dropoff_location.x:
                            driver.location.x += 1
                        elif driver.location.x > ride.dropoff_location.x:
                            driver.location.x -= 1
                        
                        if driver.location.y < ride.dropoff_location.y:
                            driver.location.y += 1
                        elif driver.location.y > ride.dropoff_location.y:
                            driver.location.y -= 1
                        
                        print(f"[TICK] Driver moved from {old_location} to ({driver.location.x}, {driver.location.y})")
                    
                    # Check if reached dropoff location
                    if driver.location == ride.dropoff_location:
                        ride.status = "completed"
                        driver.status = DriverStatus.IDLE
                        driver.current_ride_id = None
                        rider.status = RiderStatus.COMPLETED
                        rider.current_ride_id = None
                        completed_rides += 1
                        print(f"[TICK] SUCCESS: Ride {ride_id[:8]} completed!")
                        print(f"[TICK] Driver {ride.assigned_driver_id[:8]} status changed to IDLE")
                        print(f"[TICK] Rider {ride.rider_id[:8]} status changed to COMPLETED")
        
        print(f"[TICK] SUCCESS: Time advancement completed")
        print(f"[TICK] Summary: {active_rides} active rides processed, {completed_rides} rides completed")
        print(f"[TICK] Current system state: {len(drivers)} drivers, {len(riders)} riders, {len(ride_requests)} total rides")
        
        return {"tick": current_tick, "message": "Time advanced"}
        
    except Exception as e:
        error_msg = f"Unexpected error during time advancement: {str(e)}"
        print(f"[TICK] CRITICAL ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/state")
async def get_state():
    """Get current system state"""
    try:
        print(f"[STATE] Fetching current system state at tick {current_tick}")
        
        # Calculate statistics
        idle_drivers = [d for d in drivers.values() if d.status == DriverStatus.IDLE]
        busy_drivers = [d for d in drivers.values() if d.status != DriverStatus.IDLE]
        waiting_riders = [r for r in riders.values() if r.status == RiderStatus.WAITING]
        assigned_riders = [r for r in riders.values() if r.status == RiderStatus.ASSIGNED]
        in_transit_riders = [r for r in riders.values() if r.status == RiderStatus.IN_TRANSIT]
        completed_riders = [r for r in riders.values() if r.status == RiderStatus.COMPLETED]
        
        pending_rides = [r for r in ride_requests.values() if r.status == "pending"]
        accepted_rides = [r for r in ride_requests.values() if r.status == "accepted"]
        completed_rides = [r for r in ride_requests.values() if r.status == "completed"]
        rejected_rides = [r for r in ride_requests.values() if r.status == "rejected"]
        
        print(f"[STATE] System summary:")
        print(f"[STATE]   - Current tick: {current_tick}")
        print(f"[STATE]   - Total drivers: {len(drivers)} (idle: {len(idle_drivers)}, busy: {len(busy_drivers)})")
        print(f"[STATE]   - Total riders: {len(riders)} (waiting: {len(waiting_riders)}, assigned: {len(assigned_riders)}, in_transit: {len(in_transit_riders)}, completed: {len(completed_riders)})")
        print(f"[STATE]   - Total rides: {len(ride_requests)} (pending: {len(pending_rides)}, accepted: {len(accepted_rides)}, completed: {len(completed_rides)}, rejected: {len(rejected_rides)})")
        
        state = {
            "tick": current_tick,
            "drivers": list(drivers.values()),
            "riders": list(riders.values()),
            "rides": list(ride_requests.values()),
            "grid_size": GRID_SIZE,
            "statistics": {
                "idle_drivers": len(idle_drivers),
                "busy_drivers": len(busy_drivers),
                "waiting_riders": len(waiting_riders),
                "assigned_riders": len(assigned_riders),
                "in_transit_riders": len(in_transit_riders),
                "completed_riders": len(completed_riders),
                "pending_rides": len(pending_rides),
                "accepted_rides": len(accepted_rides),
                "completed_rides": len(completed_rides),
                "rejected_rides": len(rejected_rides)
            }
        }
        
        print(f"[STATE] SUCCESS: State returned successfully")
        return state
        
    except Exception as e:
        error_msg = f"Unexpected error fetching state: {str(e)}"
        print(f"[STATE] CRITICAL ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/system-state")
async def get_system_state():
    """Alias for /state endpoint for frontend compatibility"""
    return await get_state()

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        print(f"[STATS] Fetching system statistics at tick {current_tick}")
        
        # Calculate statistics
        idle_drivers = [d for d in drivers.values() if d.status == DriverStatus.IDLE]
        busy_drivers = [d for d in drivers.values() if d.status != DriverStatus.IDLE]
        waiting_riders = [r for r in riders.values() if r.status == RiderStatus.WAITING]
        assigned_riders = [r for r in riders.values() if r.status == RiderStatus.ASSIGNED]
        in_transit_riders = [r for r in riders.values() if r.status == RiderStatus.IN_TRANSIT]
        completed_riders = [r for r in riders.values() if r.status == RiderStatus.COMPLETED]
        
        pending_rides = [r for r in ride_requests.values() if r.status == "pending"]
        accepted_rides = [r for r in ride_requests.values() if r.status == "accepted"]
        completed_rides = [r for r in ride_requests.values() if r.status == "completed"]
        rejected_rides = [r for r in ride_requests.values() if r.status == "rejected"]
        
        stats = {
            "tick": current_tick,
            "total_drivers": len(drivers),
            "idle_drivers": len(idle_drivers),
            "busy_drivers": len(busy_drivers),
            "total_riders": len(riders),
            "waiting_riders": len(waiting_riders),
            "assigned_riders": len(assigned_riders),
            "in_transit_riders": len(in_transit_riders),
            "completed_riders": len(completed_riders),
            "total_rides": len(ride_requests),
            "pending_rides": len(pending_rides),
            "accepted_rides": len(accepted_rides),
            "completed_rides": len(completed_rides),
            "rejected_rides": len(rejected_rides)
        }
        
        print(f"[STATS] SUCCESS: Statistics returned successfully")
        return stats
        
    except Exception as e:
        error_msg = f"Unexpected error fetching statistics: {str(e)}"
        print(f"[STATS] CRITICAL ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 