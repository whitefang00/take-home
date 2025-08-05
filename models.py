from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

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