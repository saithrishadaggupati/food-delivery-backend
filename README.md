# Food Delivery Backend

Honestly, I built this because I was tired of only following tutorials. I wanted 
to build something on my own and actually understand how a backend works — not 
just copy code and hope it runs.

I use Swiggy a lot. I started wondering what actually happens when I place an 
order. How does the app know who I am? How does it make sure my order goes to 
the right restaurant? I couldn't answer any of that, so I decided to build my 
own version and find out.

---

## What surprised me

I thought the hard part would be the logic — building the order system, getting 
JWT auth right, setting up the database relationships. But the hours I lost were 
to things I didn't expect. Docker couldn't connect to the database. The login 
endpoint was rejecting valid credentials because it expected username but I was 
sending email. A serializers file got deleted by accident and broke everything.

That's where I actually learned. Not from the parts that worked — from the parts 
that didn't.

---

## What this does

A backend API for a food delivery platform. Three user roles — customer, 
restaurant owner, delivery agent. Owners create restaurants and menus. Customers 
place orders. Orders move through a full lifecycle: pending → confirmed → 
preparing → out for delivery → delivered.

The part I found most interesting was role-based access control. A customer token 
cannot create a restaurant. An owner can only update orders from their own 
restaurant. That distinction between authentication and authorization — I'd heard 
both words before but didn't really understand the difference until I had to 
implement it myself.

---

## Try it live

- **API:** https://food-delivery-backend-4rl9.onrender.com
- **Swagger docs:** https://food-delivery-backend-4rl9.onrender.com/api/docs/

---

## Stack

Python · Django · Django REST Framework · PostgreSQL · JWT · Docker · Swagger · Render

---

## Run locally

```bash
git clone https://github.com/saithrishadaggupati/food-delivery-backend.git
cd food-delivery-backend
docker-compose up --build
docker-compose exec web python manage.py migrate