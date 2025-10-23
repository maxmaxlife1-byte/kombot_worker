# handler.py - Final version with Image-to-Image support

import os
import requests
import runpod

# Define the two different API endpoints from fal.ai
TEXT_TO_IMAGE_URL = "https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image"
IMAGE_TO_IMAGE_URL = "https://fal.run/fal-ai/bytedance/seedream/v4/edit" # <-- The new endpoint for editing

def call_fal_api(job_input):
    """
    This function now intelligently decides which fal.ai endpoint to call
    based on whether an image_url is provided in the input.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY environment variable not set on RunPod.")

    # --- NEW: Check if this is an image-to-image job ---
    is_img2img = 'image_url' in job_input and job_input['image_url'] is not None

    # --- NEW: Set the API URL and payload based on the job type ---
    if is_img2img:
        api_url = IMAGE_TO_IMAGE_URL
        # The payload for img2img requires the image_url
        payload = {
            "prompt": job_input.get('prompt'),
            "image_url": job_input.get('image_url')
        }
    else:
        api_url = TEXT_TO_IMAGE_URL
        # The payload for text2img is simpler
        payload = {
            "prompt": job_input.get('prompt'),
            "width": job_input.get('width', 1024),
            "height": job_input.get('height', 1024)
        }
    
    # You can add more parameters to the payload here (see Part 4)

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    response = requests.post(api_url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    
    data = response.json()
    
    # fal.ai returns the image in a slightly different place for each endpoint
    if "images" in data and data["images"]:
        image_url = data["images"][0].get("url")
    elif "image" in data and isinstance(data["image"], dict):
        image_url = data["image"].get("url")
    else:
        image_url = None

    if not image_url:
        raise RuntimeError(f"API response did not contain an image URL. Full response: {data}")
    
    return {"image_url": image_url}

def handler(job):
    """
    This is the main handler function. It doesn't need many changes.
    """
    job_input = job.get('input', {})
    
    if 'prompt' not in job_input:
        return {"error": "Input must include a 'prompt'"}

    try:
        result = call_fal_api(job_input)
        return result
    except Exception as e:
        return {"error": str(e)}

# This starts the worker as per the official guide
runpod.serverless.start({"handler": handler})