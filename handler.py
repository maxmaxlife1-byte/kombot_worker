import os
import requests
from typing import Any, Dict

print("--- Clean Build v1.0: Worker script is loading ---")

FAL_SUBMIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4/text-to-image"

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """RunPod Serverless Handler"""
    
    inp = event.get("input", {})
    prompt = inp.get("prompt")
    
    if not prompt:
        return {"error": "Input object must contain a 'prompt'"}

    try:
        fal_key = os.environ.get("FAL_KEY")
        if not fal_key:
            raise ValueError("FAL_KEY environment variable not set on RunPod.")

        headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
        
        payload = {
            "input": {
                "prompt": prompt,
                "width": int(inp.get("width", 1024)),
                "height": int(inp.get("height", 1024)),
                "seed": inp.get("seed")
            }
        }

        print("Submitting job to fal.ai...")
        r = requests.post(FAL_SUBMIT_URL, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        print("Received response from fal.ai.")

        url = data.get("images", [{}])[0].get("url")
        if not url:
            raise RuntimeError(f"API response missing image URL. Full response: {data}")
            
        return {"image_url": url}

    except Exception as e:
        print(f"ERROR during generation: {e}")
        return {"error": str(e)}