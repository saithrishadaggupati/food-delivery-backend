# Food Delivery Backend

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Django](https://img.shields.io/badge/Django-REST-green) ![Docker](https://img.shields.io/badge/Docker-Compose-blue) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-orange) ![Redis](https://img.shields.io/badge/Redis-caching-red) ![Celery](https://img.shields.io/badge/Celery-async-green)

I use Swiggy every day and one day I got curious — what actually happens between tapping "Place Order" and getting a confirmation? I couldn't answer that, so I built my own version to find out.
  
**Swagger docs:** https://food-delivery-backend-4rl9.onrender.com/api/docs/

---

## What it does

A backend for a food delivery platform with three roles — customer, restaurant owner, and delivery agent. Owners create restaurants and menus. Customers browse, search nearby restaurants, and place orders. Orders move through a full lifecycle: pending → confirmed → preparing → out for delivery → delivered.

---

## Technical decisions worth explaining

**Cache versioning instead of pattern deletion**  
The restaurant list is cached in Redis. When a restaurant or menu item is created, most people would call `cache.delete_pattern('restaurant_list_*')` to invalidate it. The problem is that Redis's key-scan blocks the thread if you have millions of keys. I use a version counter instead — on every write, I increment a `restaurant_list_version` key in Redis. The cache read includes the version in the key name, so old entries become stale automatically. Zero blocking, O(1) invalidation.

**Atomic order placement with bulk_create**  
When a customer places an order, the order and all its items are written in a single `transaction.atomic()` block. If anything fails mid-write — a menu item going unavailable, a constraint violation — the whole thing rolls back. Order items are created with `bulk_create` instead of looping saves, which means one INSERT regardless of how many items are in the cart. Worth noting: `bulk_create` skips Django's `post_save` signals by design — that's intentional here since no signal listeners depend on order items.

**Role-based permissions as reusable classes**  
Permissions aren't inline `if request.user.role == 'owner'` checks scattered across views. I wrote a `IsRestaurantOwner` permission class that lives in `core/permissions.py` and gets composed onto any view that needs it. Cleaner to test, easier to extend.

**Idempotency on order placement**  
Order placement is protected with an idempotency key — a client-generated UUID cached in Redis for 24 hours. Duplicate requests with the same key return the original response without creating a second order. The tradeoff I'm aware of: if Redis evicts the key, the protection window shortens. In a real payments context, idempotency keys would live in Postgres alongside the order record.

**Celery for post-order notifications**  
After an order is placed, the HTTP response goes back immediately. Two Celery tasks run in the background via Redis: one sends an order confirmation email to the customer, another notifies the restaurant. The order placement endpoint doesn't wait for either.

**PostGIS for nearby restaurant search**  
The `/api/restaurants/nearby/` endpoint takes a lat/lng and radius and uses PostGIS's `dwithin` spatial index — not the naive approach of pulling all restaurants and computing distance in Python. Results are annotated with actual distance and sorted closest-first. The endpoint has a dedicated `ScopedRateThrottle` at 10 requests/minute because geospatial queries are expensive and this is the most DDoS-able endpoint in the API.

**Class-based views throughout**  
All views are `APIView` subclasses. `permission_classes`, `throttle_classes`, and `throttle_scope` are class attributes — no decorator stacking, easier to override in tests.

---

## Stack

Python 3.12 · Django · Django REST Framework · PostgreSQL + PostGIS · Redis · Celery · Docker Compose · JWT (SimpleJWT) · Swagger (drf-spectacular) · Render

---

## Run locally

```bash
git clone https://github.com/saithrishadaggupati/food-delivery-backend.git
cd food-delivery-backend
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Server runs at `http://localhost:8000`. Swagger at `http://localhost:8000/api/docs/`.

---

## API overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/users/register/` | None | Register |
| POST | `/api/users/login/` | None | Login, returns JWT |
| GET | `/api/restaurants/` | None | Paginated restaurant list (Redis cached) |
| GET | `/api/restaurants/<id>/` | None | Restaurant detail |
| POST | `/api/restaurants/create/` | Owner | Create restaurant, invalidates cache |
| POST | `/api/restaurants/<id>/menu/` | Owner | Add menu item |
| GET | `/api/restaurants/nearby/` | None | PostGIS radius search (throttled) |
| POST | `/api/orders/place/` | Customer | Place order (atomic, idempotent) |
| GET | `/api/orders/my-orders/` | Customer | Order history |
| PATCH | `/api/orders/<id>/status/` | Owner | Update order status |

---

## Tests

```bash
docker compose exec web python manage.py test
```

8 tests covering auth, restaurant creation, permission enforcement, and order placement.

---

## Known limitations

- **Idempotency key durability** — currently Redis-only. If the key gets evicted, the 24-hour protection window shortens. A production version would persist idempotency keys in Postgres.
- **Cache invalidation scope** — cache versioning handles restaurant list invalidation well. Individual restaurant detail pages aren't cached yet, which is the next obvious win.
- **No delivery agent assignment** — the delivery agent role exists in the data model but order assignment logic isn't implemented. That's the clearest gap between this and a real system.
