# /composable-orchestrator/llm_agent/agent.py (Groq Version - FINAL)
import pika
import json
import os
import time
from dotenv import load_dotenv
from groq import Groq # <-- IMPORT Groq
import sys

# --- Agent Setup ---
load_dotenv() # Load .env file
AGENT_ID = "LLM_Grader_Agent_v1"
RABBITMQ_HOST = 'message_bus'
CONSUME_QUEUE = 'vision_results'
PUBLISH_QUEUE = 'llm_results'

# --- Groq API Setup ---
API_KEY = os.getenv('GROQ_API_KEY') # <-- Use GROQ key
if not API_KEY:
    print(" [!] FATAL ERROR: GROQ_API_KEY not found. Set it in .env file.")
    sys.exit(1)

groq_client = Groq(api_key=API_KEY)
LLM_MODEL = 'llama-3.1-8b-instant' # Use Groq model

# --- Robust RabbitMQ Connection ---
def get_rabbitmq_channel():
    """Connects to RabbitMQ and returns a channel, retrying on failure."""
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()
            channel.queue_declare(queue=CONSUME_QUEUE, durable=True)
            channel.queue_declare(queue=PUBLISH_QUEUE, durable=True)
            print(" [x] LLM Agent connected to RabbitMQ.")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            print(f" [!] LLM Agent waiting for RabbitMQ... Retrying in 5s. Error: {e}")
            time.sleep(5)

def call_llm_evaluator(rubric: str, student_answer: str):
    """
    Calls the Groq API (Llama 3) to get a score and feedback.
    """
    print(f" [>] Calling Groq API with {LLM_MODEL}...")

    prompt = f"""
    You are an expert, unbiased exam evaluator. Your goal is to grade a student's answer
    based on a provided rubric.

    **SCORING RUBRIC (Max 10 Points):**
    "{rubric}"

    **STUDENT'S ANSWER (Extracted by OCR):**
    "{student_answer}"

    **INSTRUCTIONS:**
    1. Analyze the STUDENT'S ANSWER and compare it against the SCORING RUBRIC.
    2. Determine a fair score from 0 to 10.
    3. Provide a concise justification for your score.
    4. Provide constructive feedback for the student.
    5. Return your evaluation as a clean JSON object with no external markdown or text:
    {{"score": <number>, "justification": "<string>", "feedback_for_student": "<string>"}}
    """

    try:
        response = groq_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an exam evaluator specialized in outputting clean JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        json_text = response.choices[0].message.content
        evaluation = json.loads(json_text)
        print(" [<] Groq API call successful and JSON parsed.")
        return evaluation, 1.0

    except json.JSONDecodeError as json_err:
        print(f" [!] LLM JSON Error: Could not decode LLM response: {json_err}")
        return {"score": 0, "justification": f"LLM JSON Error: {json_err}", "feedback_for_student": "Error processing evaluation."}, 0.1
    except Exception as e:
        print(f" [!] LLM General/API Error: {e}")
        return {"score": 0, "justification": f"LLM Error: {e}", "feedback_for_student": "API connection failed."}, 0.1

def process_task(task_message: dict):
    """Core logic for the LLM agent."""
    task_id = task_message.get('task_id')
    print(f" [x] LLM Agent received task {task_id}")

    original_task = task_message.get('original_task', {})
    vision_verdict = task_message.get('verdict_data', {})

    rubric_text = original_task.get('rubric_text')
    extracted_text = vision_verdict.get('extracted_text')

    if not rubric_text or not extracted_text:
        print(f" [!] Task {task_id} is missing 'rubric_text' or 'extracted_text'. Aborting.")
        return None

    evaluation_data, confidence = call_llm_evaluator(rubric_text, extracted_text)

    verdict = {
        "original_task": original_task,
        "vision_verdict": task_message,
        "agent_id": AGENT_ID,
        "task_id": task_id,
        "agent_confidence": confidence,
        "verdict_data": evaluation_data
    }

    print(f" [x] LLM Agent processed task {task_id}. Score: {evaluation_data.get('score')}")
    return verdict

def main():
    print(f"--- {AGENT_ID} initializing ---")
    connection, channel = get_rabbitmq_channel()

    def callback(ch, method, properties, body):
        try:
            task_message = json.loads(body)
            verdict_message = process_task(task_message)

            if verdict_message:
                channel.basic_publish(
                    exchange='',
                    routing_key=PUBLISH_QUEUE,
                    body=json.dumps(verdict_message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f" [!] FATAL ERROR in LLM callback: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=CONSUME_QUEUE, on_message_callback=callback)

    print(f" [!] LLM Agent waiting for messages on queue '{CONSUME_QUEUE}'. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    except Exception as e:
        print(f" [!] LLM Agent main loop error: {e}")
        sys.exit(1)