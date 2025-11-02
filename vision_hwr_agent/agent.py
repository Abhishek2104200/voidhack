import pika
import json
import base64
import time
import sys
import os       
import requests 

# --- Agent Setup ---
AGENT_ID = "HWR_Agent_v2_OCRSpace_E2" # Using Engine 2
RABBITMQ_HOST = 'message_bus'
CONSUME_QUEUE = 'evaluation_tasks'
PUBLISH_QUEUE = 'vision_results' 
OCRSPACE_API_KEY = os.getenv('OCRSPACE_API_KEY') 
OCRSPACE_API_URL = 'https://api.ocr.space/parse/image'

# --- (FIXED) Robust RabbitMQ Connection ---
def get_rabbitmq_channel():
    """Connects to RabbitMQ and returns a channel, retrying on failure."""
    if not OCRSPACE_API_KEY:
        print(" [!] FATAL: OCRSPACE_API_KEY not found in environment.")
        print(" [!] Please add it to vision_hwr_agent/.env and rebuild.")
        sys.exit(1)
        
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()
            # Declare the queues this agent interacts with
            channel.queue_declare(queue=CONSUME_QUEUE, durable=True)
            channel.queue_declare(queue=PUBLISH_QUEUE, durable=True)
            print(f" [x] Vision Agent ({AGENT_ID}) connected to RabbitMQ.")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            print(f" [!] Vision Agent waiting for RabbitMQ... Retrying in 5s. Error: {e}")
            time.sleep(5)

def perform_ocr(image_b64: str):
    """
    Performs OCR by calling the ocr.space API.
    """
    try:
        # 1. Create the payload for the API
        # --- *** THIS IS THE MODIFIED SECTION *** ---
        payload = {
            'apikey': OCRSPACE_API_KEY,
            'language': 'eng',
            'isOverlayRequired': False,
            'base64Image': f"data:image/jpeg;base64,{image_b64}",
            'OCREngine': 2           # <-- Use the more advanced Engine 2
            # 'removelines': True <-- THIS WAS THE ERROR. IT IS NOW REMOVED.
        }
        # --- *** END OF MODIFIED SECTION *** ---
        
        # 2. Make the API request
        print(f" [>] Calling ocr.space API (Engine 2)...")
        response = requests.post(OCRSPACE_API_URL, data=payload)
        response.raise_for_status() # Raise error for bad responses
        
        result = response.json()

        # 3. Check for API-level errors
        if result.get('IsErroredOnProcessing'):
            print(f" [!] OCR.space API Error: {result.get('ErrorMessage')}")
            # We now correctly get the error message from the API
            api_error_message = result.get('ErrorMessage', ["Unknown API Error"])[0]
            return f"API Error: {api_error_message}", 0.10

        # 4. Extract the text
        parsed_results = result.get('ParsedResults')
        if not parsed_results:
            print(" [!] OCR.space: No text found.")
            return "No text found in image (API).", 0.30
            
        text = parsed_results[0].get('ParsedText')
        
        if not text:
             print(" [!] OCR.space: ParsedText field is empty.")
             return "No text found in image (API).", 0.30

        print(" [<] OCR.space API call successful.")
        # We assume the API is highly confident if it returns text
        return text.strip(), 0.95 

    except requests.exceptions.RequestException as e:
        print(f" [!] OCR API Request Error: {e}")
        return f"Error connecting to OCR API: {e}", 0.10
    except Exception as e:
        print(f" [!] OCR General Error: {e}")
        return f"Error during OCR processing: {e}", 0.10

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
            "bounding_box": [], # API doesn't provide this by default
            "ocr_model_used": "ocr.space API (Engine 2)"
        }
    }
    print(f" [x] Vision Agent processed task {task_id}. Result: {extracted_text[:30]}...")
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