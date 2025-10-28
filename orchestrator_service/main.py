import json
import uuid
import pika
import time
import requests # <-- New import
import threading # <-- New import for background consumer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# --- Global Task/Audit Log (In-Memory for Hackathon MVP) ---
TASK_AUDIT_LOG = {}

app = FastAPI(title="Composable Orchestrator")

# Allow frontend dev server origins (change or use ["*"] for quick testing)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # "*"  # uncomment for quick local debugging (not recommended in prod)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Data Model for Frontend Input ---
class EvaluationRequest(BaseModel):
    exam_id: str
    rubric_text: str
    image_b64: str
    target_question: str

OPA_URL = "http://policy_engine:8181/v1/data/policy/eval" # Use Docker service name

# --- RabbitMQ Connection Setup (Robust) ---
def get_rabbitmq_channel():
    """Establishes a robust connection to RabbitMQ, retrying on failure."""
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('message_bus'))
            channel = connection.channel()
            # Declare all queues used by the orchestrator
            channel.queue_declare(queue='evaluation_tasks', durable=True)
            channel.queue_declare(queue='llm_results', durable=True) # <-- Declare consumer queue
            print(" [x] Orchestrator connected to RabbitMQ.")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            print(f" [!] Orchestrator waiting for RabbitMQ... Retrying in 5s. Error: {e}")
            time.sleep(5)

# --- OPA Interaction ---
def call_opa_policy(llm_verdict: dict):
    """Sends the LLM verdict to OPA and gets the final decision."""
    print(f" [>] Calling OPA policy for task {llm_verdict.get('task_id')}")
    try:
        # We send the *entire* LLM verdict message as input to the policy
        response = requests.post(OPA_URL, json={"input": llm_verdict})
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        opa_result = response.json().get("result", {})
        print(f" [<] OPA call successful.")
        return opa_result

    except requests.exceptions.RequestException as e:
        print(f" [!] OPA Error: Could not connect or query OPA: {e}")
        # Return a default error structure if OPA fails
        return {
            "status": "ERROR",
            "final_grade": 0,
            "justification": f"OPA Connection Error: {e}",
            "feedback": "Failed to get final evaluation from policy engine."
        }
    except Exception as e:
         print(f" [!] Unexpected Error during OPA call: {e}")
         return {
            "status": "ERROR",
            "final_grade": 0,
            "justification": f"Unexpected OPA Error: {e}",
            "feedback": "An unexpected error occurred during policy evaluation."
        }

# --- Background Consumer Logic ---
def consume_llm_results():
    """Runs in a separate thread, listening for final LLM verdicts."""
    print(" [*] Starting LLM Result Consumer Thread...")
    connection, channel = get_rabbitmq_channel()

    def callback(ch, method, properties, body):
        try:
            llm_verdict = json.loads(body)
            task_id = llm_verdict.get("task_id")
            print(f" [C] Received LLM verdict for task {task_id}")

            # Call OPA to get the final decision
            final_decision = call_opa_policy(llm_verdict)

            # Update the central task log
            if task_id in TASK_AUDIT_LOG:
                TASK_AUDIT_LOG[task_id]["status"] = final_decision.get("status", "ERROR")
                TASK_AUDIT_LOG[task_id]["step"] = "Consensus Complete"
                TASK_AUDIT_LOG[task_id]["result"] = final_decision # Store the whole decision
                print(f" [C] Updated task log for {task_id} with status: {final_decision.get('status')}")
            else:
                print(f" [!] Warning: Received result for unknown task_id {task_id}")

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
             print(f" [!] Consumer Error: Could not decode message body: {e}")
             ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # Discard malformed message
        except Exception as e:
            print(f" [!] Consumer Error: Unexpected error processing message: {e}")
            # Requeueing might cause infinite loops if the message is poison
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='llm_results', on_message_callback=callback)

    try:
        print(f" [C] Consumer waiting for messages on 'llm_results'.")
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()
        print(" [C] Consumer stopped.")
    except Exception as e:
         print(f" [!] Consumer Thread Error: {e}")
         # Attempt to clean up
         try:
             connection.close()
         except: pass
         sys.exit(1) # Exit thread on error

# Start the consumer thread when the FastAPI app starts
consumer_thread = threading.Thread(target=consume_llm_results, daemon=True)
# daemon=True ensures the thread exits when the main app exits

@app.on_event("startup")
async def startup_event():
    if not consumer_thread.is_alive():
         print("Starting background consumer...")
         consumer_thread.start()
    else:
         print("Consumer thread already running.")


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Orchestrator Service is running!"}

@app.post("/v1/evaluate")
def start_evaluation(request: EvaluationRequest):
    """
    Receives the request, creates task ID, logs it, and publishes to RabbitMQ.
    """
    task_id = str(uuid.uuid4())

    task_message = {
        "task_id": task_id,
        "exam_id": request.exam_id,
        "rubric_text": request.rubric_text,
        "image_b64": request.image_b64,
        "target_question": request.target_question,
    }

    try:
        connection, channel = get_rabbitmq_channel()
        channel.basic_publish(
            exchange='',
            routing_key='evaluation_tasks',
            body=json.dumps(task_message),
            properties=pika.BasicProperties(delivery_mode=2))
        connection.close()
    except Exception as e:
        print(f" [!] FATAL ERROR publishing to RabbitMQ: {e}")
        # Update log even if publish fails
        TASK_AUDIT_LOG[task_id] = {"status": "FAILED", "step": "Publish Error", "result": {"justification": str(e)}}
        raise HTTPException(status_code=503, detail="Messaging service unavailable.")

    # Log ONLY AFTER successful publish attempt
    TASK_AUDIT_LOG[task_id] = {"status": "PENDING", "step": "Task Queued", "result": None}
    print(f" [x] Task {task_id} published successfully.")
    return {"message": "Evaluation started and queued.", "task_id": task_id}


@app.get("/v1/status/{task_id}")
def get_evaluation_status(task_id: str):
    """
    Endpoint for the Frontend to poll the status from the TASK_AUDIT_LOG.
    """
    if task_id not in TASK_AUDIT_LOG:
        raise HTTPException(status_code=404, detail="Task ID not found.")

    # Return the current state from our in-memory log
    return TASK_AUDIT_LOG[task_id]