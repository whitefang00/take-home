from typing import List, Set
import math
from models import Location, Driver, DriverStatus

def calculate_euclidean_distance(location1: Location, location2: Location) -> float:
    """Calculate Euclidean distance between two locations"""
    return math.sqrt((location2.x - location1.x) ** 2 + (location2.y - location1.y) ** 2)

def find_available_drivers(drivers: dict, pickup_location: Location, exclude_drivers: Set[str] = None, max_driver_requests: int = 5) -> List[tuple]:
    """Find all available drivers sorted by distance to pickup location"""
    if exclude_drivers is None:
        exclude_drivers = set()
    
    available_drivers = []
    for driver_id, driver in drivers.items():
        if (driver_id not in exclude_drivers and 
            driver.status == DriverStatus.IDLE and 
            len(driver.pending_requests) < max_driver_requests):
            distance = calculate_euclidean_distance(driver.location, pickup_location)
            available_drivers.append((driver_id, distance))
    
    # Sort by distance (closest first)
    available_drivers.sort(key=lambda x: x[1])
    return available_drivers

def send_request_to_next_driver(ride_request, drivers: dict, ride_requests: dict, max_driver_requests: int = 5):
    """Send ride request to the next closest available driver"""
    exclude_drivers = set(ride_request.rejected_by)
    available_drivers = find_available_drivers(drivers, ride_request.pickup_location, exclude_drivers, max_driver_requests)
    
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

def move_driver_towards_location(driver: Driver, target_location: Location):
    """Move driver one step towards the target location"""
    old_location = (driver.location.x, driver.location.y)
    
    # Move one step towards target
    if driver.location.x < target_location.x:
        driver.location.x += 1
    elif driver.location.x > target_location.x:
        driver.location.x -= 1
    
    if driver.location.y < target_location.y:
        driver.location.y += 1
    elif driver.location.y > target_location.y:
        driver.location.y -= 1
    
    print(f"[MOVEMENT] Driver moved from {old_location} to ({driver.location.x}, {driver.location.y})")
    return driver.location.x == target_location.x and driver.location.y == target_location.y 