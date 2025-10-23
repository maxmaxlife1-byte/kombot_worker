import os
import requests
import runpod  # <-- From the official guide

# This is our function, but we will call it from the handler
def call_seedream(prompt: str):
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise ValueError("FAL_KEY environment variable not set on RunPod.")

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    payload = {"input": {"prompt": prompt, "width": 1024, "height": 1024}}

    r = requests.post("https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image", headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()

    url = data.get("images", [{}])[0].get("url")
    if not url:
        raise RuntimeError(f"API response missing image URL. Full response: {data}")
    
    return {"image_url": url}

# This is the handler function as defined by the official guide
def handler(job):
    """
    The handler function that will be called by RunPod.
    """
    job_input = job['input']
    prompt = job_input.get('prompt')

    if not prompt:
        return {"error": "Input must include a 'prompt'"}

    # Call our image generation function
    result = call_seedream(prompt)
    return result

# This is the command that starts the worker, from the official guide
runpod.serverless.start({"handler": handler})