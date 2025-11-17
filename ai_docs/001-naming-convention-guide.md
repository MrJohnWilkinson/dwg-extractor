# Python Naming Conventions Guide

This guide covers naming conventions for Python code in the dwg-extractor project.

---

## Python Backend

### Variables & Functions

❌ **Bad**
```python
def gd(u):  # What does 'gd' mean? Get data?
    d = db.query()
    x = process(d)
    return x

temp = calculate_something()
data2 = get_info()
myvar = 123
```

✅ **Good**
```python
def get_user_profile(user_id):
    user_data = database.query_user_by_id(user_id)
    processed_profile = format_user_profile(user_data)
    return processed_profile

monthly_revenue = calculate_monthly_revenue()
customer_order_history = get_customer_orders()
max_retry_attempts = 3
```

### Constants
❌ **Bad**
```python
timeout = 30
max_size = 1000
api_key = "sk-..."
```

✅ **Good**
```python
DEFAULT_TIMEOUT_SECONDS = 30
MAX_FILE_SIZE_BYTES = 1000
STRIPE_API_KEY = "sk-..."
DATABASE_CONNECTION_POOL_SIZE = 10
```

### Classes
❌ **Bad**
```python
class DataMgr:
class Handler:
class Utils:
class Manager2:
```

✅ **Good**
```python
class UserAuthenticationService:
class OrderPaymentProcessor:
class EmailNotificationSender:
class ProductInventoryManager:
```

### Function Naming Patterns
```python
# Retrieval functions
def get_user_by_id(user_id):
def fetch_remote_data(endpoint):
def retrieve_cached_result(key):

# Creation functions
def create_user_account(email, password):
def build_query_string(params):
def generate_auth_token(user):

# Boolean returns
def is_valid_email(email):
def has_permission(user, resource):
def can_process_payment(order):
def should_retry_request(response):

# Calculations
def calculate_order_total(items):
def compute_shipping_cost(weight, distance):

# Validation
def validate_credit_card(number):
def check_inventory_availability(product_id):

# Transformation
def format_phone_number(raw_number):
def parse_csv_data(file_content):
def serialize_to_json(data):
```

---

## Key Principles

### ❌ Bad Naming Characteristics
* Single letters (except loop counters: `i`, `j`, `k`)
* Unclear abbreviations
* Generic words (`data`, `temp`, `handler`, `manager` without context)
* Numbers appended (`data1`, `data2`)
* Inconsistent casing
* Vague or ambiguous terms

### ✅ Good Naming Characteristics
* **Self-documenting** - explains purpose without comments
* **Consistent conventions** - snake_case for Python variables/functions
* **Descriptive but concise** - find the sweet spot
* **Follows standards** - language/framework conventions
* **Domain language** - uses business terminology
* **Boolean prefixes** - `is_`, `has_`, `can_`, `should_`
* **Function verbs** - `get`, `set`, `calculate`, `fetch`, `handle`

### Acceptable Abbreviations
These abbreviations are universally understood and acceptable:
* `id` - identifier
* `url` - uniform resource locator  
* `api` - application programming interface
* `db` - database
* `auth` - authentication/authorization
* `config` - configuration
* `utils` - utilities (when part of larger name)
* `req` / `res` - request/response (in middleware)
* `ctx` - context
* `err` - error (in error handlers)
* `i`, `j`, `k` - loop counters

### Context-Based Naming

```python
# Short scope = shorter names acceptable
for user in users:  
    send_email(user)

# Long scope = more specific names
authenticated_user = get_current_authenticated_user()
primary_billing_address = user.get_primary_billing_address()
```

```python
# List comprehensions - short names are fine
active_users = [u for u in users if u.is_active]

# Module level - be specific
current_authenticated_user = get_current_user()
```

### Common Prefixes/Suffixes

**Prefixes:**
* `is_` / `has_` / `can_` / `should_` - booleans
* `get_` / `fetch_` - retrieval
* `set_` / `update_` - modification  
* `create_` / `build_` - construction
* `validate_` / `check_` - validation
* `handle_` - event handlers
* `calculate_` / `compute_` - calculations

**Suffixes:**
* `_id` - identifiers
* `_at` - timestamps (`created_at`, `updated_at`)
* `_count` / `_total` - numeric aggregations
* `_list` / `_array` - collections
* `_map` / `_dict` - key-value pairs
* `_config` / `_settings` - configuration objects

---

## Examples by Domain

### E-commerce
```python
# Python
order_total_amount
customer_lifetime_value
product_inventory_count
shopping_cart_items
payment_processing_fee
```

### User Authentication
```python
# Python
is_authenticated = check_auth_status()
access_token = generate_access_token(user)
password_reset_token = create_reset_token()
has_admin_privileges = 'admin' in user.roles
```

### Data Processing
```python
# Python
raw_sensor_data
processed_metrics
aggregated_daily_stats
normalized_values
outlier_threshold
```

---

## Remember
* **Code is read far more often than it's written** - optimize for readability
* **When in doubt, be more explicit** - clarity beats brevity
* **Follow team/project conventions** - consistency matters most
