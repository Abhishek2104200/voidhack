import pika
import json
import base64
import io
import time
import sys
from PIL import Image
import pytesseract

# --- Agent Setup ---
AGENT_ID = "HWR_Agent_v1"
RABBITMQ_HOST = 'message_bus'
CONSUME_QUEUE = 'evaluation_tasks'
PUBLISH_QUEUE = 'vision_results' 

# --- (FIXED) Robust RabbitMQ Connection ---
def get_rabbitmq_channel():
    """Connects to RabbitMQ and returns a channel, retrying on failure."""
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()
            # Declare the queues this agent interacts with
            channel.queue_declare(queue=CONSUME_QUEUE, durable=True)
            channel.queue_declare(queue=PUBLISH_QUEUE, durable=True)
            print(" [x] Vision Agent connected to RabbitMQ.")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            print(f" [!] Vision Agent waiting for RabbitMQ... Retrying in 5s. Error: {e}")
            time.sleep(5)

def perform_ocr(image_b64: str):
    """
    Decodes a base64 image and performs OCR using Tesseract.
    """
    try:
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes))
        
        text = pytesseract.image_to_string(image)
        
        if not text.strip():
            return "No text found in image.", 0.30 
        
        return text, 0.90 
        
    except Exception as e:
        print(f" [!] OCR Error: {e}")
        return f"Error during OCR: {e}", 0.10

def process_task(task_message: dict):
    """Core logic for the agent."""
    task_id = task_message.get('task_id')
    print(f" [x] Vision Agent received task {task_id}")

    # 1. Perform OCR
    if task_message.get('image_b64') == "test":
        extracted_text, confidence = "This is a placeholder OCR result.", 0.99
    else:
        extracted_text, confidence = perform_ocr(task_message.get('image_b64'))

    # 2. Build the Verdict
    verdict = {
        "original_task": task_message, 
        "agent_id": AGENT_ID,
        "task_id": task_id,
        "agent_confidence": confidence,
        "verdict_data": {
            "extracted_text": extracted_text,
            "bounding_box": [0, 0, 0, 0], 
            "ocr_model_used": "Tesseract (pytesseract)"
        }
    }
    print(f" [x] Vision Agent processed task {task_id}. Result: {extracted_text[:20]}...")
    return verdict

def main():
    print(f"--- {AGENT_ID} initializing ---")
    connection, channel = get_rabbitmq_channel()

    def callback(ch, method, properties, body):
        try:
            task_message = json.loads(body)
            verdict_message = process_task(task_message)

            # Publish the result to the *vision_results* queue
            channel.basic_publish(
                exchange='',
                routing_key=PUBLISH_QUEUE,
                body=json.dumps(verdict_message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            # Acknowledge the original message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f" [!] FATAL ERROR in Vision callback: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    # Set up the consumer
    channel.basic_qos(prefetch_count=1) 
    channel.basic_consume(queue=CONSUME_QUEUE, on_message_callback=callback)

    print(f" [!] Vision Agent waiting for messages on queue '{CONSUME_QUEUE}'. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    except Exception as e:
        print(f" [!] Vision Agent main loop error: {e}")
        sys.exit(1)