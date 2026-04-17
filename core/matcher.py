from core.models import Listing, Filter


def matches(listing: Listing, f: Filter) -> bool:
    """Return True if listing satisfies all non-null filter conditions."""
    if listing.city != f.city:
        return False
    if f.long_term_only and listing.is_long_term is False:
        return False
    if f.district and listing.district:
        if f.district.lower() not in listing.district.lower():
            return False
    if f.price_min and listing.price and listing.price < f.price_min:
        return False
    if f.price_max and listing.price and listing.price > f.price_max:
        return False
    if f.rooms_min and listing.rooms and listing.rooms < f.rooms_min:
        return False
    if f.rooms_max and listing.rooms and listing.rooms > f.rooms_max:
        return False
    if f.area_min and listing.area and listing.area < f.area_min:
        return False
    if f.area_max and listing.area and listing.area > f.area_max:
        return False
    if f.floor_min and listing.floor and listing.floor < f.floor_min:
        return False
    if f.floor_max and listing.floor and listing.floor > f.floor_max:
        return False
    if f.series and listing.series and f.series != listing.series:
        return False
    return True


async def find_matching_filters(listing: Listing, all_filters: list[Filter]) -> list[Filter]:
    return [f for f in all_filters if f.is_active and matches(listing, f)]
