import random
import datetime
from faker import Faker
from locust import FastHttpUser, TaskSet, between, task, LoadTestShape, events
import math
fake = Faker()
random.seed(42)

# Product catalog from Online Boutique
products = [
    '0PUK6V6EV0', '1YMWWN1N4O', '2ZYFJ3GM2N', '66VCHSJNUP',
    '6E92ZMYYFZ', '9SIQT8TOJO', 'L9ECAV7KIM', 'LS4PSXUNUM', 'OLJCESPC7Z'
]

# Define user behavior tasks
def index(l): l.client.get("/")

def setCurrency(l):
    currencies = ['EUR', 'USD', 'JPY', 'CAD', 'GBP', 'TRY']
    l.client.post("/setCurrency", {'currency_code': random.choice(currencies)})

def browseProduct(l):
    l.client.get("/product/" + random.choice(products))

def viewCart(l): l.client.get("/cart")

def addToCart(l):
    product = random.choice(products)
    l.client.get("/product/" + product)
    l.client.post("/cart", {
        'product_id': product,
        'quantity': random.randint(1, 10)
    })

def empty_cart(l): l.client.post('/cart/empty')

def checkout(l):
    addToCart(l)
    current_year = datetime.datetime.now().year + 1
    l.client.post("/cart/checkout", {
        'email': fake.email(),
        'street_address': fake.street_address(),
        'zip_code': fake.zipcode(),
        'city': fake.city(),
        'state': fake.state_abbr(),
        'country': fake.country(),
        'credit_card_number': fake.credit_card_number(card_type="visa"),
        'credit_card_expiration_month': random.randint(1, 12),
        'credit_card_expiration_year': random.randint(current_year, current_year + 10),
        'credit_card_cvv': f"{random.randint(100, 999)}",
    })

def logout(l): l.client.get('/logout')

# Task set that mimics realistic user behavior
class UserBehavior(TaskSet):
    def on_start(self):
        index(self)

    tasks = {
        index: 1,
        setCurrency: 2,
        browseProduct: 10,
        addToCart: 2,
        viewCart: 3,
        checkout: 1
    }

# Locust user with realistic browsing behavior
class WebsiteUser(FastHttpUser):
    tasks = [UserBehavior]
    wait_time = between(0.5, 1)  # Simulate user think time
    host = "http://localhost/"  



# class ConstantUserLoad(LoadTestShape):

#     user_count = 500
#     spawn_rate = 100
#     duration = 14000

#     def tick(self):
#         run_time = self.get_run_time()
#         if run_time > self.duration:
#             return None
#         return (self.user_count, self.spawn_rate)



class FluctuatingUserLoad(LoadTestShape):
    """
    Simulates a sinusoidal load pattern with fluctuating users.
    """

    max_users = 500       # peak users
    min_users = 100       # baseline users
    spawn_rate = 100
    cycle_length = 300    # seconds for full sine wave cycle
    duration = 30000       # total run time

    def tick(self):
        run_time = self.get_run_time()
        if run_time > self.duration:
            return None

        # Calculate number of users using sine wave
        midpoint = (self.max_users + self.min_users) / 2
        amplitude = (self.max_users - self.min_users) / 2
        angle = 2 * math.pi * (run_time % self.cycle_length) / self.cycle_length
        user_count = int(midpoint + amplitude * math.sin(angle))

        return (user_count, self.spawn_rate)
    
    
@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if environment.web_ui is None:  # headless mode
        print("Locust headless started for RL testing...")