from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.availability_service import AvailabilityService
from app.schemas.availability_schema import (
    CreateAvailabilityRequest,
    CreateAvailabilityResponse,
    UpdateAvailabilityRequest,
    ProviderAvailabilityResponse,
    AvailabilitySearchRequest,
    AvailabilitySearchResponse,
    DeleteAvailabilityRequest,
    ErrorResponse,
)
from app.middlewares.auth_middleware import get_current_provider
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["Provider Availability"])


@router.post(
    "/provider/availability",
    response_model=CreateAvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Provider Availability Slots",
    description="Create availability slots for a healthcare provider",
)
async def create_availability_slots(
    request: CreateAvailabilityRequest,
    current_provider: dict = Depends(get_current_provider),
    db: Session = Depends(get_db),
):
    """
    Create availability slots for a healthcare provider.

    This endpoint allows providers to set their available time slots for appointments.
    Supports both single and recurring availability patterns.
    """
    try:
        service = AvailabilityService(db)
        result = service.create_availability_slots(
            provider_id=current_provider["id"], request=request
        )

        return CreateAvailabilityResponse(
            success=True, message="Availability slots created successfully", data=result
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create availability slots",
        )


@router.get(
    "/provider/{provider_id}/availability",
    response_model=ProviderAvailabilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Provider Availability",
    description="Retrieve availability information for a specific provider",
)
async def get_provider_availability(
    provider_id: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by slot status"),
    appointment_type: Optional[str] = Query(
        None, description="Filter by appointment type"
    ),
    timezone: Optional[str] = Query(None, description="Timezone for time conversion"),
    current_provider: dict = Depends(get_current_provider),
    db: Session = Depends(get_db),
):
    """
    Get availability information for a specific provider within a date range.

    This endpoint returns detailed availability information including:
    - Summary statistics (total, available, booked, cancelled slots)
    - Daily breakdown of availability slots
    - Slot details including times, status, and pricing
    """
    try:
        # Validate that the current provider can access this data
        if current_provider["id"] != provider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        service = AvailabilityService(db)
        result = service.get_provider_availability(
            provider_id=provider_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            appointment_type=appointment_type,
            timezone=timezone,
        )

        return ProviderAvailabilityResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider availability",
        )


@router.put(
    "/provider/availability/{slot_id}",
    status_code=status.HTTP_200_OK,
    summary="Update Availability Slot",
    description="Update a specific availability slot",
)
async def update_availability_slot(
    slot_id: str,
    request: UpdateAvailabilityRequest,
    current_provider: dict = Depends(get_current_provider),
    db: Session = Depends(get_db),
):
    """
    Update a specific availability slot.

    This endpoint allows providers to modify existing availability slots,
    including changing times, status, pricing, and other details.
    """
    try:
        service = AvailabilityService(db)
        success = service.update_availability_slot(slot_id=slot_id, request=request)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found"
            )

        return {"success": True, "message": "Availability slot updated successfully"}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update availability slot",
        )


@router.delete(
    "/provider/availability/{slot_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Availability Slot",
    description="Delete a specific availability slot",
)
async def delete_availability_slot(
    slot_id: str,
    delete_recurring: bool = Query(False, description="Delete all recurring instances"),
    reason: Optional[str] = Query(None, description="Reason for deletion"),
    current_provider: dict = Depends(get_current_provider),
    db: Session = Depends(get_db),
):
    """
    Delete a specific availability slot.

    This endpoint allows providers to remove availability slots.
    Can optionally delete all recurring instances of the slot.
    """
    try:
        service = AvailabilityService(db)
        success = service.delete_availability_slot(
            slot_id=slot_id, delete_recurring=delete_recurring, reason=reason
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found"
            )

        return {"success": True, "message": "Availability slot deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete availability slot",
        )


@router.get(
    "/availability/search",
    response_model=AvailabilitySearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Available Slots",
    description="Search for available appointment slots across providers",
)
async def search_available_slots(
    date: Optional[date] = Query(None, description="Specific date to search"),
    start_date: Optional[date] = Query(None, description="Start date for range search"),
    end_date: Optional[date] = Query(None, description="End date for range search"),
    specialization: Optional[str] = Query(None, description="Medical specialization"),
    location: Optional[str] = Query(None, description="Location (city, state, or zip)"),
    appointment_type: Optional[str] = Query(None, description="Appointment type"),
    insurance_accepted: Optional[bool] = Query(
        None, description="Whether insurance is accepted"
    ),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    timezone: Optional[str] = Query(None, description="Timezone for time conversion"),
    available_only: bool = Query(True, description="Show only available slots"),
    db: Session = Depends(get_db),
):
    """
    Search for available appointment slots across all providers.

    This endpoint allows patients to search for available appointment slots
    based on various criteria including date, specialization, location, and pricing.
    """
    try:
        # Build search request
        search_request = AvailabilitySearchRequest(
            date=date,
            start_date=start_date,
            end_date=end_date,
            specialization=specialization,
            location=location,
            appointment_type=appointment_type,
            insurance_accepted=insurance_accepted,
            max_price=max_price,
            timezone=timezone,
            available_only=available_only,
        )

        service = AvailabilityService(db)
        result = service.search_available_slots(search_request)

        return AvailabilitySearchResponse(success=True, data=result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search available slots",
        )


@router.get(
    "/provider/availability/summary",
    status_code=status.HTTP_200_OK,
    summary="Get Availability Summary",
    description="Get a summary of provider's availability statistics",
)
async def get_availability_summary(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    current_provider: dict = Depends(get_current_provider),
    db: Session = Depends(get_db),
):
    """
    Get a summary of provider's availability statistics.

    This endpoint returns aggregated statistics about the provider's availability
    including total slots, booking rates, and revenue potential.
    """
    try:
        service = AvailabilityService(db)
        availability_data = service.get_provider_availability(
            provider_id=current_provider["id"], start_date=start_date, end_date=end_date
        )

        summary = availability_data["availability_summary"]

        # Calculate additional metrics
        total_days = (end_date - start_date).days + 1
        avg_slots_per_day = summary["total_slots"] / total_days if total_days > 0 else 0
        booking_rate = (
            (summary["booked_slots"] / summary["total_slots"]) * 100
            if summary["total_slots"] > 0
            else 0
        )

        return {
            "success": True,
            "data": {
                "provider_id": current_provider["id"],
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "total_days": total_days,
                },
                "summary": summary,
                "metrics": {
                    "avg_slots_per_day": round(avg_slots_per_day, 2),
                    "booking_rate_percentage": round(booking_rate, 2),
                    "utilization_rate": round(booking_rate, 2),
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve availability summary",
        )


@router.post(
    "/provider/availability/bulk-update",
    status_code=status.HTTP_200_OK,
    summary="Bulk Update Availability",
    description="Update multiple availability slots at once",
)
async def bulk_update_availability(
    slot_ids: List[str],
    request: UpdateAvailabilityRequest,
    current_provider: dict = Depends(get_current_provider),
    db: Session = Depends(get_db),
):
    """
    Bulk update multiple availability slots.

    This endpoint allows providers to update multiple slots simultaneously,
    useful for making widespread changes to availability.
    """
    try:
        service = AvailabilityService(db)
        updated_count = 0
        failed_slots = []

        for slot_id in slot_ids:
            try:
                success = service.update_availability_slot(slot_id, request)
                if success:
                    updated_count += 1
                else:
                    failed_slots.append(slot_id)
            except Exception as e:
                failed_slots.append(slot_id)

        return {
            "success": True,
            "message": f"Updated {updated_count} out of {len(slot_ids)} slots",
            "data": {
                "total_slots": len(slot_ids),
                "updated_slots": updated_count,
                "failed_slots": failed_slots,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk update",
        )


@router.get(
    "/provider/availability/conflicts",
    status_code=status.HTTP_200_OK,
    summary="Check for Conflicts",
    description="Check for scheduling conflicts in provider's availability",
)
async def check_availability_conflicts(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    current_provider: dict = Depends(get_current_provider),
    db: Session = Depends(get_db),
):
    """
    Check for scheduling conflicts in provider's availability.

    This endpoint identifies overlapping or conflicting availability slots
    that might cause scheduling issues.
    """
    try:
        service = AvailabilityService(db)
        availability_data = service.get_provider_availability(
            provider_id=current_provider["id"], start_date=start_date, end_date=end_date
        )

        # Analyze for conflicts (simplified implementation)
        conflicts = []
        all_slots = []

        for daily_availability in availability_data["availability"]:
            for slot in daily_availability["slots"]:
                all_slots.append(
                    {
                        "date": daily_availability["date"],
                        "start_time": slot["start_time"],
                        "end_time": slot["end_time"],
                        "slot_id": slot["slot_id"],
                    }
                )

        # Check for overlapping slots on the same day
        for i, slot1 in enumerate(all_slots):
            for j, slot2 in enumerate(all_slots[i + 1 :], i + 1):
                if (
                    slot1["date"] == slot2["date"]
                    and slot1["start_time"] < slot2["end_time"]
                    and slot1["end_time"] > slot2["start_time"]
                ):
                    conflicts.append(
                        {"slot1": slot1, "slot2": slot2, "type": "overlap"}
                    )

        return {
            "success": True,
            "data": {
                "provider_id": current_provider["id"],
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "total_slots_analyzed": len(all_slots),
                "conflicts_found": len(conflicts),
                "conflicts": conflicts,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check for conflicts",
        )
