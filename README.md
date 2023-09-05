# Neutrino Notebooks

Neutrino Notebooks lets you write Jupyter Notebooks that can be easily compiled into a FastAPI application.

It allows you to define cells with a declarative syntax which will compile your cell into an HTTP endpoint, a 
websocket endpoint, or a scheduled task.

**Example**
```python
"""
@HTTP
POST /api/linear-regression
body: x:list[float], y:list[float]
"""
def simple_linear_regression(x: list[float], y: list[float]):
    slope, intercept, _, _, _ = linregress(x, y)
    return {'slope': slope, 'intercept': intercept}
```


### Docs

[docs.neutrinolabs.dev](https://docs.neutrinolabs.dev/)

---

### Installation

`pip install neutrino-cli`

---

### Commands

`neutrino init`

This command will create the necessary files to compile your notebooks.

`neutrino build` 

This command will compile the notebooks into a /build folder containing a dockerized FastAPI application. 

`neutrino run`

This command will run the compiled application locally.

`neutrino run --docker`

This command will run the compiled application locally using docker.


---

## HTTP Cells
HTTP cells allow you to use the declarative `@HTTP` to expose cells as HTTP endpoints.

### Syntax

HTTP cells start with an `@HTTP` declarative. It follows with an HTTP verb (GET, POST, PUT, DELETE, PATCH) and the API endpoint URL. 
Additional settings like Body, Resp, Query, and Headers can be specified using YAML-like syntax.

```
"""
@HTTP
http_method /url_endpoint
[body]
[query]
[resp]
[headers]
"""
```

### Parameters

- `http_method`: The HTTP verb (e.g., GET, POST, PUT, DELETE).
- `url_endpoint`: API endpoint URL.

#### Optional Parameters

- `body`: The request body.
- `query`: Query parameters.
- `resp`: Expected response fields.
- `headers`: Required HTTP headers.

Fields in square brackets are optional.

**Example**  
Simple route with no parameters
```python
"""
@HTTP
GET /api/hello-world
"""
def hello_world():
    return 'Hello, World!'
```

**Example**  
Route with url parameters and response definition to calculate the correlation between two datasets
```python
"""
@HTTP
GET /api/correlation/{dataset1}/{dataset2}
resp: correlation:float
"""
def calculate_correlation(dataset1: str, dataset2: str):
    data1 = fetch_dataset(dataset1)
    data2 = fetch_dataset(dataset2)
    correlation, _ = pearsonr(data1, data2)
    return {'correlation': correlation}
```
**Example**  
Route with query parameters and response definition to filter a DataFrame
```python
"""
@HTTP
GET /api/filter-dataframe
query: column:str, value:str
resp: filtered_data:list[dict[str, Any]]
"""
def filter_dataframe(column: str, value: str):
    # Sample DataFrame for demonstration
    df = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'David'],
        'Age': [25, 30, 35, 40],
        'Occupation': ['Engineer', 'Doctor', 'Artist', 'Teacher']
    })

    # Automatically convert the value to the column's dtype
    value = df[column].dtype.type(value)

    # Filter the DataFrame based on the query parameter
    filtered_df = df[df[column] == value]

    # Convert the filtered DataFrame to a list of dictionaries
    filtered_data = filtered_df.to_dict('records')

    return {'filtered_data': filtered_data}
```

**Example**  
Route with json body parameters to perform a linear regression

```python
"""
@HTTP
POST /api/linear-regression
body: x:list[float], y:list[float]
"""
def simple_linear_regression(x: list[float], y: list[float]):
    slope, intercept, _, _, _ = linregress(x, y)
    return {'slope': slope, 'intercept': intercept}
```

**Example**  
Route with json body parameters and response definition to perform a k-means clustering

```python
"""
@HTTP
POST /api/kmeans
body: data:list[list[float]], n_clusters:int
resp: centroids:list[list[float]]
"""
def kmeans_clustering(data: list[list[float]], n_clusters: int):
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(data)
    centroids = kmeans.cluster_centers_
    return {'centroids': centroids.tolist()}
```

---

## Websockets Cells
WebSocket cells in Neutrino Notebooks empower you to establish real-time, two-way communication between your
notebook and external clients or services. These cells make it easy to set up persistent connections, allowing
for real-time data streaming and interactive features.

### Syntax

WebSocket cells start with an `@WS` declarative. They usually contain an asynchronous Python function designed to
handle WebSocket events.

```
"""
@WS /ws_endpoint
[type]
[message]
"""
```

### Parameters
- `/ws_endpoint`: The WebSocket endpoint URL, which the server listens to.

#### Optional Parameters

- `type`: The type of WebSocket. Can be `event` or `stream`. Defaults to `event`.
- `message`: The input message format of the WebSocket endpoint.


Fields in square brackets are optional.


### Event-Based WebSockets
A basic WebSocket simply receives an event and returns a response. Functions must contain the `event` parameter to
handle the event message received.

#### Basic Event-Based WebSocket

**Example**

```python
"""
@WS /ws/hello-ws
"""
async def hello_world(event: str):
    return event
```


#### Simple AI Chat Bot

**Example**

```python
"""
@WS /ws/chat
"""
async def real_time_chat(event: str):
    user_message = event.get('message')

    openai.api_key = os.environ.get('OPENAI_API_KEY')
    completion = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        temperature = 0.8,
        max_tokens = 2000,
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": user_message},
        ]
    )
    response = completion.choices[0].message

    return {'event: 'response','message': response}
```

### Streaming WebSockets
Streaming WebSockets constantly yield data in a loop. Use `type: stream` to indicate a streaming WebSocket.


#### Streaming a Stock Price

**Example**

```python
"""
@WS /ws/stream
type: stream
"""
async def stream_stock_price():
    ticker = yf.Ticker("AAPL")
    ticker_info = ticker.history(period="1d")
    price = ticker_info["Close"].iloc[-1]

    yield price
    await asyncio.sleep(5)
```


### Streaming WebSockets with Message Input
Some WebSockets require input parameters for conditional logic or personalization.


#### Streaming a Custom Stock Price

**Example**

```python
"""
@WS /ws/stream-with-input
type: stream
message: event:str, ticker:str
validate: true
"""
async def stream_with_input(event: dict):
    ticker = yf.Ticker(event.get("ticker", "AAPL"))
    ticker_info = ticker.history(period="1d")
    price = ticker_info["Close"].iloc[-1]

    yield price

    await asyncio.sleep(5)
```


### Message Format Validation
Message format validation is disabled by default. You can disable it by setting `validate: True`.
Validation will check if the message received matches the message format defined in the `message` parameter, returning
an error if it does not.


```python
"""
@WS /ws-stream-with-input
type: stream
message: event:str, ticker:str
validate: True
"""
async def my_ws_route_with_input(event: dict):
    ticker = yf.Ticker(event.get("ticker", "AAPL"))
    ticker_info = ticker.history(period="1d")
    price = ticker_info["Close"].iloc[-1]
    yield price
    await asyncio.sleep(5)
```

### Managed Connections

Websockets cells support managed connections, meaning that a response can be sent either to a specific client, all
clients in a room, or broadcasted to all connected clients.


#### Broadcasting to a room

**Example**

In this example, every message sent will be broadcasted to all clients in the room.

```python
"""
@WS /ws/join-room/{room_id}
"""
async def join_room(event: str, room_id: str):
    return event, {"room_id": room_id}
```

#### Sending a Message to a Specific Client

**Example**

In this example, a client connects with a given client_id, the client can then message another client by specifying the
target client_id in the event.

```python
"""
@WS /ws/send-message/{client_id}
"""
async def send_message(event: str, client_id: str):
    event = json.loads(event)
    target = event.get("target", None)
    message = event.get("message", None)
    data = {
        "message": message,
        "from": client_id,
    }

    return data, {"client_id": target}
```

Alternatively, when sending messages to a specific client, you can simply return the response and client_id as a tuple

```python
"""
@WS /ws/send-message/{client_id}
"""
async def send_message(event: str, client_id: str):
    event = json.loads(event)
    target = event.get("target", None)
    message = event.get("message", None)
    data = {
        "message": message,
        "from": client_id,
    }

    return data, target
```

#### Broadcasting to All Clients

**Example**

By simply returning the response without additional parameters, the response will be broadcasted to all connected
clients.

```python
"""
@WS /ws/broadcast-all
"""
async def broadcast_all(event: str):
    return event
```


### Error Handling

Error messages that will be sent to the client without closing the connection can just be returned from the function
normally.

```python
"""
@WS /handle-error
"""
async def handle_error(event: str):
    try:
        # Your logic here
    except Exception as e:
        return {'error': str(e)}
```

#### Custom Errors

Errors that should close the connection can be defined by raising an appropriate exception or defining a custom
exception.

**Example:**

```python

class CustomException(Exception):
    status_code = 400
    message = "This is a custom error message!"
```

```python
"""
@WS /custom-error
"""
async def custom_error(event: str):
    raise CustomException()
```


---

## Scheduled Cells
Scheduled Cells allow you to schedule the execution of code blocks or functions using cron or interval-based timing.
These cells are identified by the ``@SCHEDULE` declaration at the top of the cell. {{ className: 'lead' }}

### Syntax

The declaration lines following `@SCHEDULE` define the schedule in either cron format or interval format. You must specify either `cron` or `interval`, not both.

```
"""
@SCHEDULE
[interval]
[cron]
"""
```

#### Parameters

- `interval`: the time period between task execution.
- `cron`: The cron schedule.


### CRON-based Scheduling

For cron-based scheduling, use the key `cron` followed by the cron timing fields, in the following order:

```
second minute hour day month day_of_week
```

**Example:**

```python
"""
@SCHEDULE
cron: * * * * * *
"""
def scheduled_function():
    print("This will run every second")
```

This will execute the code every second.


### Interval-based Scheduling

For interval-based scheduling, use the key `interval` followed by the duration. The duration can be in seconds (`s`), minutes (`m`), or hours (`h`).

Example:

```python
"""
@SCHEDULE
interval: 10s
"""
def scheduled_function():
    print("This will run every 10 seconds")
```

This will execute the code every 10 seconds.


### Example Use Cases

Here are some examples to showcase the diverse capabilities of HTTP cells in Neutrino Notebooks.

#### Periodically Retrieving Data from S3 and Running Analysis

**Example**

```python
"""
@SCHEDULE
interval: 2h
"""
def scheduled_data_analysis():
    # Fetch data from S3 and load into DataFrame
    s3 = boto3.client('s3')
    s3.download_file('my-bucket', 'data/new_data.csv', 'new_data.csv')
    df = pd.read_csv('new_data.csv')

    # Run analysis and check condition
    analyzed_df = run_analysis(df)
    if analyzed_df['some_column'].mean() > 10:
        send_email_alert()
    else:
        store_in_db(analyzed_df)
```


#### CRON Schedule to Fetch Stock Prices

**Example**

```python
"""
@SCHEDULE
cron: 0 30 9 * * 1-5
"""
def fetch_stock_prices():
    tickers = ["AAPL", "GOOGL", "AMZN"]
    data = {ticker: yf.Ticker(ticker).history(period="1d")['Close'][0] for ticker in tickers}
    print(data)
    store_prices_in_db(data) # assuming store_prices_in_db is an implemented function
```


#### CRON Scheduled Task for Weekly Model Retraining

**Example**

```python
"""
@SCHEDULE
cron: 0 0 1 * * 1
"""
def retrain_model():
    # Assuming `train_model` is a function that trains your model
    model = train_model()
    save_model(model)
```
