# handler.py - The Final, Definitive Multi-Modal Version

import os
import requests
import runpod

# --- THE FINAL, CORRECTED MODEL REGISTRY ---
MODEL_REGISTRY = {
    "z_image_turbo_text": {
        "url": "https://fal.run/fal-ai/z-image/turbo/text-to-image",
        "type": "text-to-image"
    },
    "z_image_turbo_edit": {
        "url": "https://fal.run/fal-ai/z-image/turbo/image-to-image",
        "type": "image-to-image",
        "image_key": "image_url"  # Requires a single URL string
    },
    "seedream_v4_edit": {
        "url": "https://fal.run/fal-ai/bytedance/seedream/v4/edit",
        "type": "image-to-image",
        "image_key": "image_urls" # Requires a list of URLs
    },
    "kling_ai_video": {
        "url": "https://fal.run/fal-ai/kuaishou/kling",
        "type": "text-to-video"
    },
    "stable_video_diffusion": {
        "url": "https://fal.run/fal-ai/stable-video-diffusion",
        "type": "image-to-video" # This model takes an image and makes a video
    }
}

def call_fal_api(job_input):
    """
    This function now correctly handles all model types.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key: raise ValueError("FAL_KEY not set.")

    model_id = job_input.get("model_id", "z_image_turbo_text")
    if model_id not in MODEL_REGISTRY: raise ValueError(f"Unknown model_id: '{model_id}'.")

    model_info = MODEL_REGISTRY[model_id]
    api_url = model_info["url"]
    model_type = model_info["type"]
    
    payload = {"prompt": job_input.get("prompt", "")} # Start with prompt, empty if not present

    # --- Build the payload based on the model's specific needs ---
    if model_type == "image-to-image" or model_type == "image-to-video":
        if not job_input.get("image_urls"): raise ValueError(f"Model '{model_id}' requires at least one image.")
        
        image_key = model_info.get("image_key", "image_url") # Default to singular 'image_url'
        
        if image_key == "image_urls":
            # This model (Seedream) expects a list
            payload["image_urls"] = job_input.get("image_urls")
        else:
            # This model (Z Image Turbo, SVD) expects a single URL string
            payload["image_url"] = job_input.get("image_urls")[0]
    
    # For text-to-image and text-to-video, the prompt is all that's needed.
        
    payload["enable_safety_checker"] = False
        
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    print(f"--- Calling Model: {model_id} ---")
    print(f"--- FINAL PAYLOAD SENT TO FAL: {payload} ---")
    
    response = requests.post(api_url, json=payload, headers=headers, timeout=300)
    if not response.ok:
        raise Exception(f"fal.ai API Error. Status: {response.status_code}. Details: {response.text}")

    data = response.json()
    
    result_url, content_type = None, "image"
    if model_type in ["text-to-video", "image-to-video"]:
        result_url = data.get("video", {}).get("url")
        content_type = "video"
    elif "images" in data and data["images"]:
        result_url = data["images"][0].get("url")

    if not result_url:
        raise RuntimeError(f"API response missing result URL. Response: {data}")
    
    return {"result_url": result_url, "content_type": content_type}

def handler(job):
    job_input = job.get('input', {})
    if not (job_input.get('prompt') or job_input.get('image_urls')):
        return {"error": "Input must include a 'prompt' or 'image_urls'"}
    try:
        result = call_fal_api(job_input)
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
