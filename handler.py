import os
import requests
import runpod

# Define the two different API endpoints from fal.ai
TEXT_TO_IMAGE_URL = "https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image"
IMAGE_TO_IMAGE_URL = "https://fal.run/fal-ai/bytedance/seedream/v4/edit"

def call_fal_api(job_input):
    """
    This function now sends the job_input it receives DIRECTLY as the payload,
    which matches the official documentation.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY environment variable not set on RunPod.")

    is_img2img = 'image_urls' in job_input and job_input.get('image_urls')

    if is_img2img:
        api_url = IMAGE_TO_IMAGE_URL
    else:
        api_url = TEXT_TO_IMAGE_URL
    
    # --- THIS IS THE FINAL FIX ---
    # The payload is the job_input itself. No more nesting.
    payload = job_input
    
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    print(f"--- Sending FINAL PAYLOAD to: {api_url} ---")
    print(f"--- PAYLOAD CONTENT: {payload} ---")
    
    response = requests.post(api_url, json=payload, headers=headers, timeout=180)

    # ... (the rest of the error handling and response processing is the same and correct)
    if not response.ok:
        error_status = response.status_code
        error_reason = response.reason
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        raise Exception(f"Failed to call fal.ai API. Status: {error_status} {error_reason}. Details: {error_detail}")

    data = response.json()
    image_url = None
    if "images" in data and data["images"]:
        image_url = data["images"][0].get("url")
    elif "image" in data and isinstance(data["image"], dict):
        image_url = data["image"].get("url")

    if not image_url:
        raise RuntimeError(f"API response did not contain an image URL. Full response: {data}")
    
    return {"image_url": image_url}

def handler(job):
    """ Main handler function. """
    job_input = job.get('input', {})
    
    if 'prompt' not in job_input:
        return {"error": "Input must include a 'prompt'"}

    try:
        result = call_fal_api(job_input)
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}

# Start the worker
runpod.serverless.start({"handler": handler})