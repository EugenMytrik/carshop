from django.db import models


class Client(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.username


class CarType(models.Model):
    name = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    price = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Car(models.Model):
    car_type = models.ForeignKey(CarType, on_delete=models.CASCADE)
    color = models.CharField(max_length=50)
    year = models.IntegerField()
    photo = models.ImageField(
        upload_to="photo/",
        blank=True,
        default="default_img/2c8802a0c5f948deddea67614d2ecb63.jpg",
    )
    blocked_by_order = models.ForeignKey(
        "Order", on_delete=models.SET_NULL, null=True, related_name="reserved_cars"
    )
    owner = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, related_name="cars"
    )

    def block(self, order):
        self.blocked_by_order = order
        self.save()

    def unblock(self):
        self.blocked_by_order = None
        self.save()

    def sell(self):
        if not self.blocked_by_order:
            raise Exception("Car is not reserved")
        self.owner = self.blocked_by_order.client
        self.save()

    def __str__(self):
        return self.color


class Licence(models.Model):
    car = models.OneToOneField(
        Car, on_delete=models.SET_NULL, null=True, related_name="licence"
    )
    number = models.CharField(max_length=50)

    def __str__(self):
        return self.number


class Dealership(models.Model):
    name = models.CharField(max_length=50)
    available_car_types = models.ManyToManyField(CarType, related_name="dealerships")
    clients = models.ManyToManyField(Client, related_name="dealerships")

    def __str__(self):
        return self.name


class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    dealership = models.ForeignKey(
        Dealership, on_delete=models.CASCADE, related_name="orders"
    )
    is_paid = models.BooleanField(default=False)


class OrderQuantity(models.Model):
    car_type = models.ForeignKey(
        CarType, on_delete=models.CASCADE, related_name="order_quantities"
    )
    quantity = models.PositiveIntegerField(default=1)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="car_types")

    def get_available_quantity(self):
        return self.car_type.available_cars.count()
