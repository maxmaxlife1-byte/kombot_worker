# handler.py - Final Corrected Version with Payload Fix

import os
import requests
import runpod

# Define the two different API endpoints from fal.ai
TEXT_TO_IMAGE_URL = "https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image"
IMAGE_TO_IMAGE_URL = "https://fal.run/fal-ai/bytedance/seedream/v4/edit"

def call_fal_api(job_input):
    """
    This function now constructs the correct, nested payload for the fal.ai API.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY environment variable not set on RunPod.")

    is_img2img = 'image_url' in job_input and job_input.get('image_url')

    if is_img2img:
        print("Image-to-Image request detected.")
        api_url = IMAGE_TO_IMAGE_URL
        # --- BUG FIX: Payload is now correctly nested inside an "input" object ---
        payload = {
            "input": {
                "prompt": job_input.get('prompt'),
                "image_url": job_input.get('image_url')
            }
        }
    else:
        print("Text-to-Image request detected.")
        api_url = TEXT_TO_IMAGE_URL
        # --- BUG FIX: Payload is now correctly nested inside an "input" object ---
        payload = {
            "input": {
                "prompt": job_input.get('prompt'),
                "width": job_input.get('width', 1024),
                "height": job_input.get('height', 1024)
            }
        }
    
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    print(f"Sending request to: {api_url}")
    response = requests.post(api_url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    
    data = response.json()
    
    # Standardize image URL extraction
    image_url = None
    if "images" in data and data["images"]:
        image_url = data["images"][0].get("url")
    elif "image" in data and isinstance(data["image"], dict):
        image_url = data["image"].get("url")

    if not image_url:
        raise RuntimeError(f"API response did not contain an image URL. Full response: {data}")
    
    return {"image_url": image_url}

def handler(job):
    """
    Main handler function.
    """
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