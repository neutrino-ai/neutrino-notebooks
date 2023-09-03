# Neutrino Notebooks

Neutrino Notebooks allows you to seamlessly build and deploy complex workflows using simple and expressive syntax.

It allows you to package your notebooks ...

When you build a Neutrino Notebook, it will automatically compile the project into a FastAPI application with a docker 
image that can be deployed to any cloud provider.

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

### HTTP Cells
An HTTP cell starts with the declarative `@HTTP` 

It follows with an HTTP verb (GET, POST, PUT, DELETE, PATCH) and the API endpoint URL. 
Additional settings like Body, Resp, Query, and Headers can be specified using YAML-like syntax.

**Example**  
Simple route with no parameters
```
"""
@HTTP
GET /api/hello-world
"""
def hello_world():
    return 'Hello, World!'
```

**Example**  
Route with url parameters and response definition to calculate the correlation between two datasets
```
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
```
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

```
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

```
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

### Parameters

**http:** The HTTP verb for the request (GET, POST, PUT, DELETE, PATCH).  
**endpoint:** The API endpoint URL.  
**body:** The request body fields and their types.  
**resp:** The expected response fields and their types.  
**query:** The specified query parameters for the request. *i.e ?key=value&key2=value2*   
**headers:** HTTP headers required for the request. *i.e Authorization: Bearer {token}* 

---

### Websockets Cells
A Websockets cell starts with the declarative `@WS` 

It defines a WebSocket endpoint that clients can connect to for real-time, two-way communication between the client
and server. The WebSocket cell contains a function that takes an event argument, representing incoming data from 
the client. The function can process this data and send back a response, which the client will receive in real-time. 
The function body can include any logic required for the WebSocket operation.


**Example**  
Route with url parameters and response definition to calculate the correlation between two datasets
```
"""
@WS /api/chatbot
"""
async def real_time_chatbot(event: str):
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
    
    return {'response': response}
```

---

### Scheduled Cells
Scheduled cells start with the declarative `@SCHEDULE` and define a code block that will be executed based on 
either a cron schedule or a time interval. 
You can set the cron schedule or interval in the cell comments, using the cron and interval keys. The function 
inside a Scheduled cell takes no arguments and performs actions at specified time intervals or cron schedules.

**Example:** Interval scheduled task to retrieve csv from s3 bucket and run analysis
```
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

**Example:** Cron Scheduled Task to Fetch Stock Prices  
Fetch stock prices for a given list of tickers every weekday at 9:30 am.

```
"""
@SCHEDULE
cron: 0 30 9 * * 1-5
"""
def fetch_stock_prices():
    tickers = ["AAPL", "GOOGL", "AMZN"]
    # Assuming fetch_prices is a function that fetches stock prices
    prices = fetch_prices(tickers)
    store_prices_in_db(prices)
```


**Example:** Cron scheduled task to fetch for weekly model retraining
```
"""
@SCHEDULE
cron: 0 0 1 * * 1
"""
def retrain_model():
    # Assuming `train_model` is a function that trains your model
    model = train_model()
    save_model(model)
```