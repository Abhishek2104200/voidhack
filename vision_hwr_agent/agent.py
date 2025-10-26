import pika
import json
import base64
import io
import uuid
import os
import requests # <-- The library for our new "brain"
from PIL import Image

# --- API Setup ---
# This is read from the Docker environment
API_KEY = os.getenv('OCR_SPACE_API_KEY')
if not API_KEY:
    raise ValueError("OCR_SPACE_API_KEY environment variable not set.")

OCR_URL = 'https://api.ocr.space/parse/image'

# --- RabbitMQ Connection ---
RABBITMQ_HOST = 'rabbitmq'
TASK_QUEUE = 'task_queue'
VERDICT_QUEUE = 'verdict_queue'

def process_image(image_b64: str, content_type: str) -> dict:
    """
    This is the working "brain" from our test.
    It performs the HWR task using the ocr.space API.
    """
    
    # 1. Get image size (for the 'bounding_box' in our response)
    try:
        image_data = base64.b64decode(image_b64)
        img_pil = Image.open(io.BytesIO(image_data))
    except Exception as e:
        print(f"Error decoding image: {e}")
        return {"error": "Image decoding failed"}

    # --- 2. Vision & HWR Task (ocr.space) ---
    try:
        print("Running text recognition with ocr.space API (Engine 2)...")
        
        # Build the correct Data URI prefix
        base64_string_with_prefix = f"data:{content_type};base64,{image_b64}"
        
        payload = {
            'apikey': API_KEY,
            'language': 'eng',
            'isOverlayRequired': False,
            'base64image': base64_string_with_prefix,
            'OCREngine': 2  # Use the better engine
        }
        
        response = requests.post(OCR_URL, data=payload)
        response.raise_for_status() 
        
        result_json = response.json()
        
        if result_json.get('IsErroredOnProcessing'):
            raise Exception(result_json.get('ErrorMessage'))
            
        final_text = result_json['ParsedResults'][0]['ParsedText']
        avg_confidence = 0.95 # Placeholder

    except Exception as e:
        print(f"Error during ocr.space API: {e}")
        return {"error": f"ocr.space API failed: {e}"}

    # 4. Combine results
    full_box = [0, 0, img_pil.width, img_pil.height] 

    return {
        "extracted_text": final_text,
        "bounding_box": full_box, 
        "agent_confidence": round(avg_confidence, 4)
    }

# --- This is the RabbitMQ "body" of the agent ---

def on_message_callback(ch, method, properties, body):
    """
    This function is called by RabbitMQ for every new task.
    """
    try:
        # 1. Parse the incoming task
        task_data = json.loads(body)
        task_id = task_data.get('task_id')
        image_b64 = task_data.get('image_b64')
        
        # --- NEW: Get the file type from the task ---
        # (The Orchestrator will need to add this)
        file_ext = task_data.get('file_extension', '.png') # default to png
        
        if file_ext.lower() == ".png":
            mime_type = "image/png"
        elif file_ext.lower() in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        else:
            mime_type = "application/octet-stream"
        
        print(f"Received task: {task_id}")

        # 2. Call our working "brain"
        result = process_image(image_b64, mime_type)

        if "error" in result:
            print(f"Task {task_id} failed: {result['error']}")
        else:
            # 3. Build the final verdict JSON [cite: 28]
            verdict_json = {
                "agent_id": "HWR_Agent_v4_OCRSpace",
                "task_id": task_id,
                "agent_confidence": result['agent_confidence'],
                "verdict_data": {
                    "extracted_text": result['extracted_text'],
                    "bounding_box": result['bounding_box'],
                    "ocr_model_used": "ocr.space-API"
                }
            }
            
            # 4. Send the result back
            ch.basic_publish(
                exchange='',
                routing_key=VERDICT_QUEUE,
                body=json.dumps(verdict_json)
            )
            print(f"Published verdict for task: {task_id}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    print("Starting Vision/HWR Agent (ocr.space)...")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600, blocked_connection_timeout=300)
    )
    channel = connection.channel()
    channel.queue_declare(queue=TASK_QUEUE, durable=True)
    channel.queue_declare(queue=VERDICT_QUEUE, durable=True)
    channel.basic_consume(
        queue=TASK_QUEUE,
        on_message_callback=on_message_callback
    )

    print(f"[*] Waiting for messages on queue '{TASK_QUEUE}'. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')