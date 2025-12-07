# handler.py - The Final, Definitive Version with Model-Specific Payloads

import os
import requests
import runpod

# --- THE NEW, SMARTER MODEL REGISTRY ---
# We now add an 'image_key' to specify the correct parameter name for each model.
MODEL_REGISTRY = {
    "seedream_v4_text": {
        "url": "https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image",
        "type": "text-to-image"
    },
    "seedream_v4_edit": {
        "url": "https://fal.run/fal-ai/bytedance/seedream/v4/edit",
        "type": "image-to-image",
        "image_key": "image_urls"  # Seedream expects a list with the plural key
    },
    "z_image_turbo_text": {
        "url": "https://fal.run/fal-ai/z-image/turbo/text-to-image",
        "type": "text-to-image"
    },
    "z_image_turbo_edit": {
        "url": "https://fal.run/fal-ai/z-image/turbo/image-to-image",
        "type": "image-to-image",
        "image_key": "image_url"   # Z Image Turbo expects a single string with the singular key
    },
    "kling_ai_video": {
        "url": "https://fal.run/fal-ai/kuaishou/kling",
        "type": "text-to-video"
    }
}

# In handler.py...

def call_fal_api(job_input):
    """
    This is the final version with the corrected response parsing logic.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key: raise ValueError("FAL_KEY not set.")

    model_id = job_input.get("model_id", "z_image_turbo_text")
    if model_id not in MODEL_REGISTRY: raise ValueError(f"Unknown model_id: '{model_id}'.")

    model_info = MODEL_REGISTRY[model_id]
    api_url = model_info["url"]
    model_type = model_info["type"]
    
    payload = {}
    
    if model_type == "image-to-image":
        if not job_input.get("image_urls"): raise ValueError("This model requires at least one image.")
        image_key = model_info.get("image_key", "image_url")
        if image_key == "image_urls":
            payload = {"prompt": job_input.get("prompt"), "image_urls": job_input.get("image_urls")}
        else:
            payload = {"prompt": job_input.get("prompt"), "image_url": job_input.get("image_urls")[0]}
    elif model_type == "text-to-video":
        payload = {"prompt": job_input.get("prompt")}
    else: # Default to text-to-image
        payload = {"prompt": job_input.get("prompt")}

    payload["enable_safety_checker"] = False
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    print(f"--- Calling Model: {model_id} ---")
    print(f"--- FINAL PAYLOAD SENT TO FAL: {payload} ---")
    
    response = requests.post(api_url, json=payload, headers=headers, timeout=300)
    if not response.ok:
        raise Exception(f"fal.ai API Error. Status: {response.status_code}. Details: {response.text}")

    data = response.json()
    
    # --- THIS IS THE FINAL BUG FIX ---
    # The successful response contains an 'images' list with a 'url' key inside.
    # We will safely extract this and handle video as a special case.
    
    result_url = None
    content_type = "image" # Assume image by default
    
    if model_type == "text-to-video":
        result_url = data.get("video", {}).get("url")
        content_type = "video"
    elif "images" in data and data["images"]:
        result_url = data["images"][0].get("url")

    # --- END OF BUG FIX ---
    
    if not result_url:
        raise RuntimeError(f"API response was successful but could not parse the result URL. Full response: {data}")
    
    return {"result_url": result_url, "content_type": content_type}


def handler(job):
    # This function does not need to be changed.
    job_input = job.get('input', {})
    if not job_input.get('prompt'):
        return {"error": "Input must include a 'prompt'"}
    try:
        result = call_fal_api(job_input)
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})

