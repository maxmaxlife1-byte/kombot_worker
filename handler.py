# handler.py - Final version based on official RunPod documentation

import os
import requests
import runpod

def call_fal_api(job_input):
    """
    This function contains the logic to call the fal.ai API.
    """
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY environment variable not set on RunPod.")

    prompt = job_input.get('prompt')
    width = job_input.get('width', 1024)
    height = job_input.get('height', 1024)

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    # This is the simple, correct payload format that fal.ai expects
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height
    }

    response = requests.post(
        "https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image",
        json=payload,
        headers=headers,
        timeout=120
    )
    # This will raise a detailed error if the fal.ai API returns an error (like 422)
    response.raise_for_status()
    
    data = response.json()
    image_url = data.get("images", [{}])[0].get("url")

    if not image_url:
        raise RuntimeError(f"API response was successful but did not contain an image URL. Full response: {data}")
    
    return {"image_url": image_url}

def handler(job):
    """
    This is the main handler function that RunPod calls, as per the official guide.
    """
    job_input = job.get('input', {})
    
    if 'prompt' not in job_input:
        return {"error": "Input must include a 'prompt'"}

    try:
        # Call our API logic and return the result
        result = call_fal_api(job_input)
        return result
    except Exception as e:
        # Return a detailed error if anything goes wrong during the API call
        return {"error": str(e)}

# This is the command that starts the worker, from the official guide
runpod.serverless.start({"handler": handler})