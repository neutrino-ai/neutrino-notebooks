<p align="center">
  <img src="https://raw.githubusercontent.com/neutrino-ai/neutrino-notebooks/main/neutrino.png" width="200">
</p>

<h1 align="center">
  Neutrino Notebooks
</h1>

![GitHub stars](https://img.shields.io/github/stars/neutrino-ai/neutrino-notebooks)
![GitHub issues](https://img.shields.io/github/issues/neutrino-ai/neutrino-notebooks)
![PyPI](https://img.shields.io/pypi/v/neutrino-cli.svg)
[![Join the Slack](https://img.shields.io/badge/Slack-Join%20the%20Community-blue?logo=slack)](https://join.slack.com/t/neutrinocommunity/shared_invite/zt-2330v708n-koZBAvh04qQSHv3f9RUgVQ)
[![Documentation](https://img.shields.io/badge/docs-View%20Documentation-blue)](https://docs.neutrinolabs.dev/)




Neutrino Notebooks lets you write Jupyter Notebooks that can be easily compiled into a FastAPI application.

It allows you to define cells with a declarative syntax which will compile your cell into an HTTP endpoint, a 
websocket endpoint, or a scheduled task.

---

### Features

- Expose cells as HTTP or websockets endpoints with comment declaratives like `@HTTP` and `@WS`

- Periodically run cells as scheduled tasks for simple data pipelines with `@SCHEDULE`

- Automatic routing based on filename and directory structure, sort of similar to NextJs.

- Ignore sandbox files by naming them ‘_sandbox’

Compile your notebooks with `neutrino build`, which creates a /build folder with a dockerized FastAPI app for local testing or deployment.

---

### Getting Started

`pip install neutrino-cli`

---

### Examples

**Generate a Startup Idea and Send a Pitch Email Every 3 Hours**
```python
"""
@SCHEDULE
interval: 3h
"""
try:
    idea = generate_idea()
    tldr = generate_tldr_and_summary(idea)
    subject = generate_subject(tldr)
    
    email_sender.send_email(
        source="Neutrino IdeaBot<idea-bot@neutrinoapp.com>",
        recipients=["myemail@gmail.com"],
        subject=f"Neutrino IdeaBot: {subject}",
        body=f"<html><body>{tldr}<br><br><h2>Explanation:</h2><br>{idea}</body></html>"
    )
    print("Successfully sent email!")
except Exception as e:
    print("Error: ", e)
```

**Expose a Simple Linear Regression as an HTTP Endpoint**
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

---


### Docs

[docs.neutrinolabs.dev](https://docs.neutrinolabs.dev/)

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


