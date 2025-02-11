import random
import threading
from faker import Faker
from django.core.management.base import BaseCommand
from myapp.models import Product

fake = Faker()

class Command(BaseCommand):
    help = "Generate 10,000 fake products using multi-threading"

    def handle(self, *args, **kwargs):
        num_threads = 5
        products_per_thread = 2000
        threads = []

        def generate_fake_products(count):
            """ Function to generate and save fake products in batches """
            products = []
            for _ in range(count):
                product = Product(
                    name=fake.word(),
                    price=round(random.uniform(10, 1000), 2)
                )
                products.append(product)

            # Bulk insert for efficiency
            Product.objects.bulk_create(products)

        # Create multiple threads
        for _ in range(num_threads):
            thread = threading.Thread(target=generate_fake_products, args=(products_per_thread,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        self.stdout.write(self.style.SUCCESS("Successfully added 10,000 products!"))
