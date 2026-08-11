from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_property_limit
from app.db.models import Amenity, Property, PropertyAmenity, PropertyPhoto, PropertyType, User
from app.db.session import get_db
from app.modules.properties.storage import delete_object, upload_file

router = APIRouter(prefix="/properties", tags=["properties"])


class PropertyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    property_type: PropertyType


class PropertyUpdate(BaseModel):
    title: str | None = None
    property_type: PropertyType | None = None
    building_type: str | None = None
    floor_number: int | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    area: str | None = None
    neighborhood: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    beds: int | None = None
    guests: int | None = None
    square_feet: float | None = None
    square_meters: float | None = None
    cleaning_fee: float | None = None
    extra_guest_fee: float | None = None
    minimum_nights: int | None = None
    maximum_nights: int | None = None
    current_price: float | None = None
    availability_notes: str | None = None
    features: dict | None = None
    onboarding_step: int | None = None
    amenity_codes: list[str] | None = None


class PhotoOut(BaseModel):
    id: UUID
    url: str
    sort_order: int
    room_tag: str | None

    model_config = {"from_attributes": True}


class AmenityOut(BaseModel):
    code: str
    name: str
    category: str


class PropertyOut(BaseModel):
    id: UUID
    title: str
    property_type: PropertyType
    building_type: str | None
    floor_number: int | None
    country: str | None
    state: str | None
    city: str | None
    area: str | None
    neighborhood: str | None
    postal_code: str | None
    latitude: float | None
    longitude: float | None
    bedrooms: int | None
    bathrooms: float | None
    beds: int | None
    guests: int | None
    square_feet: float | None
    square_meters: float | None
    cleaning_fee: float | None
    extra_guest_fee: float | None
    minimum_nights: int | None
    maximum_nights: int | None
    current_price: float | None
    availability_notes: str | None
    features: dict
    onboarding_step: int
    onboarding_complete: bool
    photos: list[PhotoOut] = []
    amenity_codes: list[str] = []

    model_config = {"from_attributes": True}


def _to_out(prop: Property) -> PropertyOut:
    codes = [pa.amenity.code for pa in (prop.amenities or []) if pa.amenity]
    return PropertyOut(
        id=prop.id,
        title=prop.title,
        property_type=prop.property_type,
        building_type=prop.building_type,
        floor_number=prop.floor_number,
        country=prop.country,
        state=prop.state,
        city=prop.city,
        area=prop.area,
        neighborhood=prop.neighborhood,
        postal_code=prop.postal_code,
        latitude=prop.latitude,
        longitude=prop.longitude,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        beds=prop.beds,
        guests=prop.guests,
        square_feet=prop.square_feet,
        square_meters=prop.square_meters,
        cleaning_fee=prop.cleaning_fee,
        extra_guest_fee=prop.extra_guest_fee,
        minimum_nights=prop.minimum_nights,
        maximum_nights=prop.maximum_nights,
        current_price=prop.current_price,
        availability_notes=prop.availability_notes,
        features=prop.features or {},
        onboarding_step=prop.onboarding_step,
        onboarding_complete=prop.onboarding_complete,
        photos=[PhotoOut.model_validate(p) for p in (prop.photos or [])],
        amenity_codes=codes,
    )


async def _reload(db: AsyncSession, property_id: UUID) -> Property:
    result = await db.execute(
        select(Property)
        .options(
            selectinload(Property.photos),
            selectinload(Property.amenities).selectinload(PropertyAmenity.amenity),
        )
        .where(Property.id == property_id)
    )
    return result.scalar_one()


async def _get_owned(
    db: AsyncSession, user: User, property_id: UUID, *, allow_inactive: bool = False
) -> Property:
    result = await db.execute(
        select(Property)
        .options(
            selectinload(Property.photos),
            selectinload(Property.amenities).selectinload(PropertyAmenity.amenity),
        )
        .where(Property.id == property_id, Property.user_id == user.id)
    )
    prop = result.scalar_one_or_none()
    if not prop or (not allow_inactive and not prop.is_active):
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.get("/amenities", response_model=list[AmenityOut])
async def list_amenities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Amenity).order_by(Amenity.category, Amenity.name))
    return [AmenityOut(code=a.code, name=a.name, category=a.category) for a in result.scalars().all()]


@router.post("", response_model=PropertyOut, status_code=status.HTTP_201_CREATED)
async def create_property(
    body: PropertyCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    count = await db.scalar(
        select(func.count()).select_from(Property).where(Property.user_id == user.id, Property.is_active.is_(True))
    )
    limit = get_property_limit(user)
    if limit is not None and (count or 0) >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Free plan allows {limit} properties. Upgrade to Pro for unlimited.",
        )
    prop = Property(user_id=user.id, title=body.title, property_type=body.property_type, onboarding_step=1)
    db.add(prop)
    await db.flush()
    return _to_out(await _reload(db, prop.id))


@router.get("", response_model=list[PropertyOut])
async def list_properties(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Property)
        .options(
            selectinload(Property.photos),
            selectinload(Property.amenities).selectinload(PropertyAmenity.amenity),
        )
        .where(Property.user_id == user.id, Property.is_active.is_(True))
        .order_by(Property.created_at.desc())
    )
    return [_to_out(p) for p in result.scalars().all()]


@router.get("/{property_id}", response_model=PropertyOut)
async def get_property(property_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return _to_out(await _get_owned(db, user, property_id))


@router.patch("/{property_id}", response_model=PropertyOut)
async def update_property(
    property_id: UUID,
    body: PropertyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prop = await _get_owned(db, user, property_id)
    data = body.model_dump(exclude_unset=True)
    amenity_codes = data.pop("amenity_codes", None)
    for k, v in data.items():
        setattr(prop, k, v)
    if amenity_codes is not None:
        for pa in list(prop.amenities):
            await db.delete(pa)
        await db.flush()
        if amenity_codes:
            result = await db.execute(select(Amenity).where(Amenity.code.in_(amenity_codes)))
            for amenity in result.scalars().all():
                db.add(PropertyAmenity(property_id=prop.id, amenity_id=amenity.id))
    await db.flush()
    return _to_out(await _reload(db, prop.id))


@router.post("/{property_id}/onboarding/complete", response_model=PropertyOut)
async def complete_onboarding(
    property_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    prop = await _get_owned(db, user, property_id)
    if not prop.city or not prop.property_type:
        raise HTTPException(status_code=400, detail="City and property type are required")
    prop.onboarding_complete = True
    prop.onboarding_step = 10
    await db.flush()
    return _to_out(await _reload(db, prop.id))


@router.post("/{property_id}/photos", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    property_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prop = await _get_owned(db, user, property_id)
    if len(prop.photos) >= 30:
        raise HTTPException(status_code=400, detail="Maximum 30 photos")
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 15MB)")
    content_type = file.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images allowed")
    key = f"properties/{prop.id}/{uuid4()}-{file.filename or 'photo.jpg'}"
    url = await upload_file(key, content, content_type)
    photo = PropertyPhoto(
        property_id=prop.id,
        s3_key=key,
        url=url,
        content_type=content_type,
        sort_order=len(prop.photos),
    )
    db.add(photo)
    await db.flush()
    return PhotoOut.model_validate(photo)


@router.delete("/{property_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    property_id: UUID,
    photo_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prop = await _get_owned(db, user, property_id)
    photo = next((p for p in prop.photos if p.id == photo_id), None)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    await delete_object(photo.s3_key)
    await db.delete(photo)


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    prop = await _get_owned(db, user, property_id, allow_inactive=True)
    if not prop.is_active:
        raise HTTPException(status_code=404, detail="Property not found")
    prop.is_active = False
    await db.flush()
