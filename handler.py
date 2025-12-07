import os
import requests
import runpod

# --- THE NEW, EXPANDED MODEL REGISTRY ---
MODEL_REGISTRY = {
    "seedream_v4_text": {
        "url": "https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image",
        "type": "text-to-image"
    },
    "seedream_v4_edit": {
        "url": "https://fal.run/fal-ai/bytedance/seedream/v4/edit",
        "type": "image-to-image"
    },
    "z_image_turbo_text": {
        "url": "https://fal.run/fal-ai/z-image/turbo/text-to-image",
        "type": "text-to-image"
    },
    "z_image_turbo_edit": {
        "url": "https://fal.run/fal-ai/z-image/turbo/image-to-image",
        "type": "image-to-image"
    },
    "kling_ai_video": {
        "url": "https://fal.run/fal-ai/kuaishou/kling", # Example URL, check fal.ai for the exact ID
        "type": "text-to-video"
    }
}

def call_fal_api(job_input):
    """
    This function now supports Z Image Turbo and Kling AI.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY environment variable not set.")

    model_id = job_input.get("model_id", "z_image_turbo_text") # Changed default to the cheaper model
    if model_id not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model_id: '{model_id}'.")

    model_info = MODEL_REGISTRY[model_id]
    api_url = model_info["url"]
    model_type = model_info["type"]
    
    payload = {}

    # Build the payload based on the model's type
    if model_type == "text-to-image":
        payload = {"prompt": job_input.get("prompt")}
    elif model_type == "image-to-image":
        if not job_input.get("image_urls"): raise ValueError("This model requires 'image_urls'.")
        payload = {"prompt": job_input.get("prompt"), "image_urls": job_input.get("image_urls")}
    elif model_type == "text-to-video":
        # Kling AI just takes a prompt. Other video models might need an image.
        payload = {"prompt": job_input.get("prompt")}
        
    # Add the safety checker flag to the payload.
    payload["enable_safety_checker"] = False
        
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    print(f"--- Calling Model: {model_id} at URL: {api_url} ---")
    print(f"--- PAYLOAD: {payload} ---")
    
    response = requests.post(api_url, json=payload, headers=headers, timeout=300)
    response.raise_for_status()
    
    data = response.json()
    
    # Handle both image and video outputs
    result_url = None
    content_type = "image" # Default
    if "images" in data and data["images"]:
        result_url = data["images"][0].get("url")
    elif "image" in data and isinstance(data["image"], dict):
        result_url = data["image"].get("url")
    elif "video" in data and isinstance(data["video"], dict):
        result_url = data["video"].get("url")
        content_type = "video"

    if not result_url:
        raise RuntimeError(f"API response did not contain a valid result URL. Response: {data}")
    
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