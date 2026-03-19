import os
import sys
import json
import time
import base64
import subprocess
import requests
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent
CAPTIONS_FILE = PROJECT_DIR / ".tmp" / "pipeline.json"


def update_caption_fields(caption_id: str, fields: dict):
    if not CAPTIONS_FILE.exists():
        return
    captions = json.loads(CAPTIONS_FILE.read_text())
    # Backup before write
    CAPTIONS_FILE.with_suffix(".json.bak").write_text(
        json.dumps(captions, indent=2, ensure_ascii=False)
    )
    for caption in captions:
        if str(caption.get("id")) == caption_id:
            caption.update(fields)
            break
    CAPTIONS_FILE.write_text(json.dumps(captions, indent=2, ensure_ascii=False))
    print(f"Caption #{caption_id} updated: {list(fields.keys())}")


def upload_images_to_kie(image_inputs, api_key, headers):
    """Upload reference images to kie.ai storage and return their hosted URLs.
    Accepts URLs (uses file-url-upload) or local file paths (uses file-base64-upload).
    """
    url_upload = "https://kieai.redpandaai.co/api/file-url-upload"
    b64_upload = "https://kieai.redpandaai.co/api/file-base64-upload"
    hosted_urls = []

    for i, entry in enumerate(image_inputs):
        print(f"Uploading reference image {i+1}/{len(image_inputs)} to kie.ai...")
        is_local = os.path.exists(entry)
        try:
            if is_local:
                with open(entry, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                ext = Path(entry).suffix.lstrip(".") or "png"
                mime = f"image/{ext}"
                payload = {
                    "base64Data": f"data:{mime};base64,{b64_data}",
                    "uploadPath": "dubery/references",
                    "fileName": Path(entry).name
                }
                resp = requests.post(b64_upload, headers=headers, json=payload, timeout=30)
            else:
                payload = {
                    "fileUrl": entry,
                    "uploadPath": "dubery/references",
                    "fileName": f"ref_{i+1}.png"
                }
                resp = requests.post(url_upload, headers=headers, json=payload, timeout=30)

            resp.raise_for_status()
            data = resp.json()
            download_url = data.get("data", {}).get("downloadUrl")
            if not download_url:
                print(f"WARNING: No downloadUrl for image {i+1}. Using original.")
                hosted_urls.append(entry)
            else:
                print(f"Uploaded: {download_url}")
                hosted_urls.append(download_url)
        except Exception as e:
            print(f"WARNING: Upload failed for image {i+1} ({e}). Using original.")
            hosted_urls.append(entry)
    return hosted_urls


def run():
    if len(sys.argv) < 3:
        print("Usage: python generate_kie.py <prompt_json_file> <output_file> [aspect_ratio]")
        sys.exit(1)
        
    prompt_file = sys.argv[1]
    output_file = sys.argv[2]
    aspect_ratio = sys.argv[3] if len(sys.argv) > 3 else "auto"

    # Extract caption ID from output filename (e.g. dubery_4.jpg → "4")
    stem = Path(output_file).stem  # "dubery_4"
    caption_id = stem.split("_", 1)[1] if "_" in stem else None
    
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if not os.path.exists(env_path):
        print(f"ERROR: .env not found at {env_path}")
        sys.exit(1)
        
    api_key = None
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('KIE_AI_API_KEY=') or line.startswith('KIE_API_KEY='):
                api_key = line.strip().split('=', 1)[1].strip('"\'')
                break
                
    if not api_key:
        print("ERROR: KIE_API_KEY not found in .env")
        sys.exit(1)
        
    if prompt_file.endswith('.txt'):
        # Natural language mode: read prompt as plain text
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_string = f.read().strip()
        # Load sidecar config for image_input + api_parameters
        stem = Path(prompt_file).stem.replace('_prompt', '')
        sidecar = str(Path(prompt_file).parent / f"{stem}_config.json")
        if os.path.exists(sidecar):
            with open(sidecar, 'r', encoding='utf-8') as f:
                sidecar_data = json.load(f)
            image_input = sidecar_data.get("image_input", None)
            api_parameters = sidecar_data.get("api_parameters", {})
        else:
            image_input = None
            api_parameters = {}
    else:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_json = json.load(f)
        image_input = prompt_json.pop("image_input", None)
        api_parameters = prompt_json.pop("api_parameters", {})
        prompt_string = json.dumps(prompt_json)
    
    url = "https://api.kie.ai/api/v1/jobs/createTask"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "nano-banana-2",
        "input": {
            "prompt": prompt_string,
            "aspect_ratio": api_parameters.get("aspect_ratio", aspect_ratio),
            "resolution": api_parameters.get("resolution", "1K"),
            "output_format": api_parameters.get("output_format", "jpg")
        }
    }
    
    if "google_search" in api_parameters:
        payload["input"]["google_search"] = api_parameters["google_search"]
        
    if image_input:
        uploaded_urls = upload_images_to_kie(image_input, api_key, headers)
        payload["input"]["image_input"] = uploaded_urls

    print("Creating task via Kie.ai API...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"API response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            print(f"ERROR: Unexpected API response (type={type(result).__name__}). Raw: {response.text[:500]}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR creating task: {e}")
        if 'response' in locals() and response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text[:500]}")
        sys.exit(1)

    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        print("ERROR: No taskId returned")
        print(result)
        sys.exit(1)
        
    print(f"Task created successfully. Task ID: {task_id}. Polling...")
    
    poll_url = "https://api.kie.ai/api/v1/jobs/recordInfo"
    poll_params = {"taskId": task_id}
    
    attempts = 0
    while attempts < 60:
        time.sleep(4)
        attempts += 1
        
        try:
            poll_resp = requests.get(poll_url, headers=headers, params=poll_params, timeout=15)
            poll_resp.raise_for_status()
            poll_result = poll_resp.json()
        except Exception as e:
            print(f"Poll {attempts} Error: {e}")
            continue
            
        data = poll_result.get("data", {})
        if not data:
            print(f"Poll {attempts}: Received empty data object. Retrying...")
            continue
            
        state = data.get("state")
        print(f"Poll {attempts}: state = {state}")
        
        if state == "success" or state == "completed":
            result_json_str = data.get("resultJson", "{}")
            try:
                result_json = json.loads(result_json_str)
            except json.JSONDecodeError:
                result_json = {}
                
            result_urls = result_json.get("resultUrls", [])
            if result_urls and len(result_urls) > 0:
                image_url = result_urls[0]
                print(f"Downloading image from {image_url}")
                try:
                    img_resp = requests.get(image_url, timeout=30)
                    img_resp.raise_for_status()
                    with open(output_file, 'wb') as f:
                        f.write(img_resp.content)
                    print(f"Successfully saved to {output_file}")
                    # Upload to Google Drive as backup, save URL back to captions.json
                    drive_url = ""
                    try:
                        upload_result = subprocess.run(
                            [sys.executable, "tools/drive/upload_image.py",
                             "--file", output_file,
                             "--folder", "DuberyMNL/Generated Images"],
                            capture_output=True, text=True, timeout=60
                        )
                        if upload_result.returncode == 0:
                            drive_data = json.loads(upload_result.stdout)
                            drive_url = drive_data.get("drive_url", "")
                            print(f"Backed up to Drive: {drive_url}")
                        else:
                            print(f"Drive backup failed (non-critical): {upload_result.stderr.strip()}")
                    except Exception as e:
                        print(f"Drive backup failed (non-critical): {e}")
                    if caption_id:
                        fields = {"status": "DONE"}
                        if drive_url:
                            fields["image_url"] = drive_url
                        update_caption_fields(caption_id, fields)
                    sys.exit(0)
                except Exception as e:
                    print(f"ERROR downloading image: {e}")
                    if caption_id:
                        update_caption_fields(caption_id, {"status": "IMAGE_FAILED"})
                    sys.exit(1)
            else:
                print("ERROR: Could not find image URL in resultJson. Dumping data:")
                print(json.dumps(data, indent=2))
                if caption_id:
                    update_caption_fields(caption_id, {"status": "IMAGE_FAILED"})
                sys.exit(1)

        elif state == "failed" or state == "error":
            print("ERROR: Task failed on server side.")
            print(json.dumps(data, indent=2))
            if caption_id:
                update_caption_fields(caption_id, {"status": "IMAGE_FAILED"})
            sys.exit(1)

    print("ERROR: Timed out waiting for job completion")
    if caption_id:
        update_caption_fields(caption_id, {"status": "IMAGE_FAILED"})
    sys.exit(1)

if __name__ == "__main__":
    run()
