# Naming Conventions Guide
## Python Backend, PostgreSQL, JavaScript/React & CSS

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

## PostgreSQL Database

### Table Names
❌ **Bad**
```sql
tbl_users
user_tbl
USERS
Users_Table
tblUser
data1, data2
```

✅ **Good**
```sql
users
customer_orders
product_categories
user_authentication_tokens
order_shipping_addresses
invoice_line_items
```

### Column Names
❌ **Bad**
```sql
id1, id2
dt
val
usrname
user_email_addr_string
flag
type
```

✅ **Good**
```sql
user_id, order_id
created_at, updated_at
total_price, unit_cost
username
email
is_active, is_verified
account_type, payment_method
```

### Index & Constraint Names
❌ **Bad**
```sql
idx1
pk_constraint
fk1
unique1
```

✅ **Good**
```sql
idx_users_email
pk_orders_id
fk_orders_user_id
uq_products_sku
chk_orders_total_positive
```

### Reserved Keywords to Avoid

PostgreSQL has reserved keywords that should not be used as unquoted column names. Always use descriptive alternatives:

❌ **Bad - Reserved Keywords**
```sql
position        -- Use: display_order, sort_order, sequence_number
user            -- Use: username, user_account, account_name
order           -- Use: customer_order, order_record
group           -- Use: user_group, team_group
```

✅ **Good - Descriptive Alternatives**
```sql
display_order   -- Clear, descriptive, no conflict
sort_order      -- Common database convention
sequence_number -- Explicit about purpose
user_account    -- Specific and clear
customer_order  -- Domain-specific naming
```

**Common Reserved Keywords:**
- `position`, `order`, `user`, `group`, `type`, `value`, `check`, `table`, `index`
- See full list: https://www.postgresql.org/docs/current/sql-keywords-appendix.html

**Best Practice:** Even if you quote column names (e.g., `"position"`), avoid reserved keywords entirely to prevent confusion and potential issues with different PostgreSQL clients and tools.

---

## JavaScript/React Frontend

### Variables & Functions

❌ **Bad**
```javascript
const d = new Date();
let tmp = getData();
const arr = [...items];
function handle() { }
const func1 = () => { }
let x, y, z;
const myData = fetch();
```

✅ **Good**
```javascript
const currentDate = new Date();
const userProfile = getUserProfile();
const filteredProducts = [...products];
function handleSubmitForm() { }
const calculateTotalPrice = () => { }
const selectedProductId = productData.id;
const apiResponse = fetchUserOrders();
```

### Constants
```javascript
// Global constants in UPPER_SNAKE_CASE
const MAX_UPLOAD_SIZE_MB = 10;
const API_BASE_URL = 'https://api.example.com';
const DEBOUNCE_DELAY_MS = 300;
const DEFAULT_PAGE_SIZE = 20;
```

### React Components
❌ **Bad**
```javascript
function Comp() { }
function Page1() { }
function MyComponent2() { }
function Thing() { }
const box = () => { }
```

✅ **Good**
```javascript
function UserProfileCard() { }
function ProductCheckoutPage() { }
function NavigationHeader() { }
function OrderSummaryList() { }
const ShoppingCartButton = () => { }
```

### Props & State
❌ **Bad**
```javascript
const [data, setData] = useState();
const [flag, setFlag] = useState(false);
const [items, setItems] = useState([]);

function Button({ txt, clk, dis }) { }
```

✅ **Good**
```javascript
const [userData, setUserData] = useState();
const [isLoading, setIsLoading] = useState(false);
const [cartItems, setCartItems] = useState([]);

function SubmitButton({ 
  buttonText, 
  onClickHandler, 
  isDisabled 
}) { }
```

### Event Handlers
```javascript
// ❌ Bad
const click = () => { }
const change = (e) => { }

// ✅ Good
const handleFormSubmit = () => { }
const handleInputChange = (event) => { }
const handleUserLogout = () => { }
```

---

## CSS

### Class Names
❌ **Bad**
```css
.box { }
.container2 { }
.red { }
.btn { }
.newStyle { }
.div1 { }
.MyClass { }
```

✅ **Good**
```css
.product-card { }
.navigation-menu { }
.error-message { }
.submit-button { }
.user-avatar { }
.search-input-field { }
.checkout-summary-container { }

/* BEM convention examples */
.product-card__title { }
.product-card__price { }
.product-card--featured { }
.product-card--out-of-stock { }
```

### ID Names
❌ **Bad**
```css
#main { }
#content1 { }
#div { }
#wrapper { }
```

✅ **Good**
```css
#shopping-cart-sidebar { }
#user-profile-header { }
#product-filter-panel { }
#order-confirmation-modal { }
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
* **Consistent conventions** - snake_case for Python/SQL, camelCase for JS
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

```javascript
// Array methods - short names are fine
const activeUsers = users.filter(u => u.isActive);

// Module level - be specific
const currentAuthenticatedUser = getCurrentUser();
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

# Database
order_line_items
product_reviews
customer_addresses
inventory_movements
```

### User Authentication
```javascript
// JavaScript
const isAuthenticated = checkAuthStatus();
const accessToken = generateAccessToken(user);
const passwordResetToken = createResetToken();
const hasAdminPrivileges = user.roles.includes('admin');
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
