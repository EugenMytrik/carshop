import random

from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import (
    Car,
    Dealership,
    Client,
    Order,
    OrderQuantity,
    Licence,
)

from .forms import CarPhotoChangeForm


@login_required
def cars(request):
    if request.method == "GET":
        all_cars = Car.objects.filter(owner__isnull=True)
        blocked_cars = Car.objects.filter(
            blocked_by_order__isnull=False, owner__isnull=True
        )
        cars_count = (
            all_cars.values("car_type", "color").annotate(Count("id")).order_by()
        )

        print(request.user.username)
        print(request.user.email)

        return render(
            request,
            "store/car_store.html",
            context={
                "all_cars": all_cars,
                "cars_count": cars_count,
                "blocked_cars": blocked_cars,
            },
        )

    # client = Client.objects.get(id=1)

    client, existence = Client.objects.get_or_create(
        username=request.user.username, email=request.user.email, phone="0952185204"
    )

    find_order = Order.objects.filter(
        client=client,
        dealership=Dealership.objects.get(id=1),
        is_paid=False,
    )

    if find_order.exists():
        order = Order.objects.get(
            client=client,
            dealership=Dealership.objects.get(id=1),
            is_paid=False,
        )
    else:
        order = Order.objects.create(
            client=client,
            dealership=Dealership.objects.get(id=1),
            is_paid=False,
        )

    cars_id_list = []

    if request.POST.get("select"):
        select = request.POST.get("select")
        quantity = 1
        order_quantity = OrderQuantity.objects.get_or_create(
            car_type=Car.objects.get(id=int(select)).car_type,
            quantity=quantity,
            order=Order.objects.get(id=order.id),
        )

        if order_quantity[1] is False:
            order_quantity[0].quantity = order_quantity[0].quantity + 1
            order_quantity[0].save()

        cars_id_list.append(int(select))

        for el in cars_id_list:
            Car.objects.get(id=el).block(order=Order.objects.get(id=order.id))

        return redirect(reverse("cars"))

    order_id = order.id
    return redirect(reverse("order", kwargs={"order_id": order_id}))


@login_required
def order(request, order_id):
    order_created = Order.objects.get(id=order_id)
    cars = OrderQuantity.objects.filter(order=order_created).all()

    if request.GET.get("cancel"):
        order_created.delete()
        return redirect(reverse("cars"))

    if request.method == "POST":
        for el in Car.objects.filter(blocked_by_order=order_created.id):
            licence_number = random.randint(1000, 9999)
            if Licence.objects.filter(number=f"BH {licence_number} IT").exists():
                licence_number = random.randint(1000, 9999)
            Licence.objects.create(car=el, number=f"BH {licence_number} IT")

            order_created.is_paid = True
            order_created.save()
            el.sell()
        return redirect(reverse("order_is_processed", kwargs={"order_id": order_id}))

    data = {
        "order_id": order_id,
        "cars": cars,
    }
    return render(request, "store/order_page.html", context=data)


@login_required
def order_is_processed(request, order_id):
    if request.GET.get("index_page"):
        return redirect(reverse("cars"))

    return render(
        request, "store/order_is_processed.html", context={"order_id": order_id}
    )


@login_required
def update_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if request.method == "GET":
        form = CarPhotoChangeForm(instance=car)
        return render(request, "store/update_car.html", {"car": car, "form": form})

    form = CarPhotoChangeForm(request.POST, request.FILES, instance=car)
    if form.is_valid():
        form.save()
    return redirect(reverse("update_car", kwargs={"car_id": car_id}))
