import json
import time
import redis
from decimal import Decimal
from django.http import JsonResponse
from myapp.models import Product
from django.shortcuts import get_object_or_404


# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def decimal_to_str(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError("Type not serializable")

def measure_time(func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, round((end_time - start_time) * 1000, 2)  # Return time in milliseconds

# Query all products from the database
def get_all_products_db(request):
    products, exec_time = measure_time(lambda: list(Product.objects.values("id", "name", "price")))

    # Convert Decimal to string for JSON serialization
    for product in products:
        product["price"] = str(product["price"])

    return JsonResponse({"source": "Database", "query_time_ms": exec_time, "products": products})

# Query all products using Redis caching
def get_all_products_cache(request):
    cache_key = "all_products"

    def get_products_from_db():
        products = list(Product.objects.values("id", "name", "price"))
        
        # Convert Decimal to string for JSON serialization
        for product in products:
            product["price"] = str(product["price"])

        # Store result in Redis with a 5-minute expiration
        redis_client.setex(cache_key, 300, json.dumps(products, default=decimal_to_str))
        return products

    # Measure time for Redis or DB query
    products, exec_time = measure_time(
        lambda: json.loads(redis_client.get(cache_key)) if redis_client.get(cache_key) else get_products_from_db()
    )

    return JsonResponse({"source": "Redis Cache", "query_time_ms": exec_time, "products": products})


def create_product(request):
    try:
        data = json.loads(request.body)
        product = Product.objects.create(
            name=data["name"],
            price=data["price"]
        )
        
        # Invalidate Redis cache
        redis_client.delete("all_products")

        return JsonResponse({"message": "Product created successfully", "id": product.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def get_product(request, product_id):
    cache_key = f'product:{product_id}'
    product_data = redis_client.get(cache_key)

    if product_data:
        product = json.loads(product_data)
    else:
        product = get_object_or_404(Product, id=product_id)
        product = {'id': product.id, 'name': product.name, 'price': product.price}
        redis_client.setex(cache_key, 300, json.dumps(product, default=decimal_to_str))

    return JsonResponse(product)


def update_product(request, product_id):
    try:
        data = json.loads(request.body)
        product = Product.objects.get(id=product_id)
        product.name = data.get("name", product.name)
        product.price = data.get("price", product.price)
        product.save()

        # Invalidate Redis cache
        redis_client.delete("all_products")

        return JsonResponse({"message": "Product updated successfully"})
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()

    cache_key = f'product:{product_id}'
    redis_client.delete(cache_key)

    return JsonResponse({'message': 'Product deleted'})
