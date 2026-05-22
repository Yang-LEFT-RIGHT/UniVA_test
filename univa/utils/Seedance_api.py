import time
import logging
import os
import base64
from datetime import datetime

import requests
from volcenginesdkarkruntime import Ark

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger()

client=Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)


#唯一需要传入的参数为prompt，其余相关设置如分辨率等需要在此处修改
def text_to_image_generate(api_key: str,
                            prompt: str,
                            model: str = "doubao-seedream-5-0-260128",
                            size: str = "2K",
                            output_format: str = "jpg",
                            watermark: bool = False,
                            **kwargs) -> dict:

    try:
        begin = time.time()
        response = client.images.generate(
            api_key=api_key,
            model=model,
            prompt=prompt,
            size=size,
            output_format=output_format,
            response_format="url",
            watermark=watermark
        )
        end = time.time()
        logger.info(f"Task completed in {end - begin:.2f} seconds.")
        
        if response.data and len(response.data) > 0:
            image_url = response.data[0].url
            logger.info(f"Generated image URL: {image_url}")
            return image_url
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error in text_to_image_generate: {e}")
        return None

#
def image_to_image_generate(api_key: str,
                            prompt: str,    
                            image,
                            model: str = "doubao-seedream-5-0-260128",
                            size: str = "2K",
                            output_format: str = "jpg",
                            watermark: bool = False,
                            sequential_image_generation: str = "disabled",
                            **kwargs) -> dict:

    processed_images = []

    try:
        if isinstance(image, list):
            for img in image:
                if isinstance(img, str) and (img.startswith("http://") or img.startswith("https://")):
                    processed_images.append(img)
                elif os.path.exists(img):
                    with open(img, "rb") as f:
                        img_bytes = f.read()
                    b64 = base64.b64encode(img_bytes).decode("utf-8")
                    ext = os.path.splitext(img)[1].lower().lstrip(".")
                    if ext in ("jpg", "jpeg"):
                        ext = "jpeg"
                    elif ext not in ("png", "webp", "bmp", "tiff", "gif", "heic", "heif"):
                        ext = "png"
                    processed_images.append(f"data:image/{ext};base64,{b64}")
                else:
                    logger.warning(f"Invalid image path or URL, skipping: {img}")
        else:
            if isinstance(img, str) and (img.startswith("http://") or img.startswith("https://")):
                processed_images.append(img)
            elif os.path.exists(img):
                with open(img, "rb") as f:
                    img_bytes = f.read()
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                ext = os.path.splitext(img)[1].lower().lstrip(".")
                if ext in ("jpg", "jpeg"):
                    ext = "jpeg"
                elif ext not in ("png", "webp", "bmp", "tiff", "gif", "heic", "heif"):
                    ext = "png"
                processed_images.append(f"data:image/{ext};base64,{b64}")
            else:
                logger.warning(f"Invalid image path or URL, skipping: {img}")

        params = {
            "api_key": api_key,
            "model": model,
            "prompt": prompt,
            "image": image_input,
            "size": size,
            "output_format": output_format,
            "response_format": "url",
            "watermark": watermark,
            "sequential_image_generation": sequential_image_generation,
        }
    
        begin = time.time()
        response = client.images.generate(**params)
        end = time.time()
        logger.info(f"Task completed in {end - begin:.2f} seconds.")

        if response.data and len(response.data) > 0:
            output_url = response.data[0].url
            logger.info(f"Generated image URL: {output_url}")
            return output_url
        else:
            return None

    except Exception as e:
        logger.error(f"Error in image_to_image_generate: {e}")
        return None

def text_to_video_generate(api_key: str,
                           prompt: str,
                           save_path: str,
                           model: str = "doubao-seedance-2-0-260128",
                           ratio: str = "16:9",
                           duration: int = 5,
                           generate_audio: bool = True,
                           watermark: bool = False,
                           resolution: str = "1080p",
                           ) -> dict:

    try:
        content = [{"type": "text", "text": prompt}]

        begin = time.time()
        create_result = client.content_generation.tasks.create(
            api_key=api_key,
            model=model,
            content=content,
            ratio=ratio,
            duration=duration,
            generate_audio=generate_audio,
            watermark=watermark,
            resolution=resolution
        )
        task_id = create_result.id
        logger.info(f"Task submitted successfully. Request ID: {task_id}")

        while True:
            get_result = client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            if status == "succeeded":
                end = time.time()
                logger.info(f"Task completed in {end - begin:.2f} seconds.")

                video_url = get_result.content.video_url

                #last_frame_url=get_result.content.last_frame_url

                resp = requests.get(video_url, stream=True)
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                return {
                    'success': True,
                    'output_path': save_path,
                    'message': "Video generated successfully."
                }

            elif status == "failed":
                error_msg = get_result.error.message
                logger.error(f"Task failed: {error_msg}")
                return {
                    'success': False, 
                    'error': error_msg
                }
            else:
                logger.info(f"Task still processing. Status: {status}")
                time.sleep(30)

    except Exception as e:
        logger.error(f"Error in text_to_video_generate: {e}")
        return {'success': False, 'error': str(e)}


# 这个函数调用seedance2，是支持音频生成的，但是wavespeed配套的api调用并没有这个选项，并且有独立的音频生成，所以暂时注释掉，确定后再选择
# 同时还有视频长度、尾帧等，视频长度可以考虑要不要长一点？尾帧也可以考虑保存，对后续进一步生成长镜头可能有用
def image_to_video_generate(api_key: str,
                            prompt: str,
                            image: str,
                            model: str = "doubao-seedance-2-0-260128",
                            ratio: str = "16:9",
                            duration: int = 5,
                            #generate_audio: bool = True,
                            watermark: bool = False,
                            resolution: str = "1080p",
                            save_path: str = None) -> dict:

    try:

        image_url = image
        if os.path.exists(image):
            with open(image, "rb") as f:
                img_bytes = f.read()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            ext = os.path.splitext(image)[1].lower()
            mime = "jpeg" if ext in [".jpg", ".jpeg"] else ext.strip(".")
            image_url = f"data:image/{mime};base64,{b64}"

        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": image_url},
                "role": "reference_image"
            }
        ]

        begin = time.time()
        create_result = client.content_generation.tasks.create(
            api_key=api_key,
            model=model,
            content=content,
            ratio=ratio,
            duration=duration,
            #generate_audio=generate_audio,
            watermark=watermark,
            resolution=resolution
        )
        task_id = create_result.id
        logger.info(f"Task submitted successfully. Request ID: {task_id}")

        while True:
            get_result = client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            if status == "succeeded":
                end = time.time()
                logger.info(f"Task completed in {end - begin:.2f} seconds.")

                video_url=get_result.content.video_url
                #last_frame_url=get_result.content.last_frame_url

                if not save_path:
                    time_ft = datetime.now().strftime("%m%d%H%M%S")
                    url_name = video_url.split("/")[-1]
                    save_path = f"{time_ft}_{url_name}"

                resp = requests.get(video_url, stream=True)
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                return {
                    'success': True,
                    'output_path': save_path,
                    'message': "Video generated successfully."
                }

            elif status == "failed":
                error_msg=get_result.error.message
                logger.error(f"Task failed: {error_msg}")
                return {'success': False, 'error': error_msg}
            else:
                logger.info(f"Task still processing. Status: {status}")
                time.sleep(30)

    except Exception as e:
        logger.error(f"Error in image_to_video_generate: {e}")
        return {'success': False, 'error': str(e)}

def frame_to_frame_video_seedance(api_key: str,
                                    prompt: str,
                                    images: list,
                                    save_path: str = None,
                                    model: str = "doubao-seedance-2-0-260128",
                                    duration: int = 5,
                                    ratio: str = "16:9",
                                    generate_audio: bool = False,
                                    watermark: bool = False,
):


    def prepare_image(image_src):
        if isinstance(image_src, str) and image_src.startswith(("http://", "https://")):
            return image_src
        with open(image_src, "rb") as f:
            img_bytes = f.read()
        
        ext = os.path.splitext(image_src)[1].lower().lstrip(".")
        if ext not in ("jpg", "jpeg", "png", "webp", "bmp", "tiff", "gif", "heic", "heif"):
            ext = "jpeg"
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/{ext};base64,{b64}"

    first_frame_src = prepare_image(images[0])
    last_frame_src = prepare_image(images[-1])


    content = [
        {"type": "text", "text": prompt},
        {
            "type": "image_url",
            "image_url": {"url": first_frame_src},
            "role": "first_frame",
        },
        {
            "type": "image_url",
            "image_url": {"url": last_frame_src},
            "role": "last_frame",
        },
    ]

    logger.info("Submitting Seedance 2.0 frame-to-frame task...")
    try:
        create_result = client.content_generation.tasks.create(
            api_key=api_key,
            model=model,
            content=content,
            generate_audio=generate_audio,
            ratio=ratio,
            duration=duration,
            watermark=watermark,
        )
        task_id = create_result.id
        logger.info(f"Task submitted. ID: {task_id}")
    except Exception as e:
        logger.error(f"Task creation failed: {e}")
        return {"success": False, "error": str(e)}


    begin = time.time()
    while True:
        try:
            get_result = client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            if status == "succeeded":
                end = time.time()
                logger.info(f"Task succeeded in {end - begin:.2f} seconds.")

                video_url = get_result.content.video_url
                if not video_url:
                    return {"success": False, "error": "No video URL found in result."}

                time_ft = datetime.now().strftime("%m%d%H%M%S")
                url_name = video_url.split("/")[-1].split("?")[0]
                output_filename = save_path if save_path else f"{time_ft}_{url_name}"
                resp = requests.get(video_url, stream=True)
                resp.raise_for_status()
                with open(output_filename, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                logger.info(f"Video saved to {output_filename}")
                return {
                    "success": True,
                    "output_path": output_filename,
                    "message": f"{prompt} success generate video",
                }
            elif status == "failed":
                error_msg = get_result.error if hasattr(get_result, "error") else "Unknown failure"
                logger.error(f"Task failed: {error_msg}")
                return {"success": False, "error": f"Task failed: {error_msg}"}
            else:
                logger.info(f"Status: {status}, retrying in 30s...")
                time.sleep(30)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            return {"success": False, "error": str(e)}

#def audio_gen():
#火山引擎内没有根据视频的音频生成，要做替换

def seedance_video_editing(
    api_key: str,
    prompt: str,
    video_url: str,
    aspect_ratio: str = "16:9",
    save_path: str = None,
    model: str = "doubao-seedance-2-0-260128",
    duration: int = 5,
    generate_audio: bool = False,
    watermark: bool = False,
    reference_images: list = None,
    **kwargs
):


    if not (video_url.startswith(("http://", "https://")) or video_url.startswith("asset://")):
        return {
            "success": False,
            "error": "video_url must be a public HTTP(S) URL or asset:// ID. Local files are not supported."
        }

    content = [
        {"type": "text", "text": prompt},
        {
            "type": "video_url",
            "video_url": {"url": video_url},
            "role": "reference_video",
        },
    ]


    if reference_images:
        for img_url in reference_images:

            if not (img_url.startswith(("http://", "https://")) or img_url.startswith("asset://")):
                logger.warning(f"Ignoring invalid image URL: {img_url}")
                continue
            content.append({
                "type": "image_url",
                "image_url": {"url": img_url},
                "role": "reference_image",
            })


    logger.info("Submitting Seedance 2.0 video editing task...")
    try:
        create_result = client.content_generation.tasks.create(
            api_key=api_key,
            model=model,
            content=content,
            generate_audio=generate_audio,
            ratio=aspect_ratio,
            duration=duration,
            watermark=watermark,
        )
        task_id = create_result.id
        logger.info(f"Task submitted. ID: {task_id}")
    except Exception as e:
        logger.error(f"Task creation failed: {e}")
        return {"success": False, "error": str(e)}

    begin = time.time()
    while True:
        try:
            get_result = client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            if status == "succeeded":
                end = time.time()
                logger.info(f"Task succeeded in {end - begin:.2f} seconds.")

                video_url_out = get_result.content.video_url
                if not video_url_out:
                    return {"success": False, "error": "No video URL found in result."}

                time_ft = datetime.now().strftime("%m%d%H%M%S")

                url_name = video_url_out.split("/")[-1].split("?")[0]
                output_filename = save_path if save_path else f"results/{time_ft}_{url_name}"


                out_dir = os.path.dirname(output_filename)
                if out_dir:
                    os.makedirs(out_dir, exist_ok=True)
                else:
                    os.makedirs("results", exist_ok=True)
                    output_filename = os.path.join("results", output_filename)


                resp = requests.get(video_url_out, stream=True)
                resp.raise_for_status()
                with open(output_filename, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                logger.info(f"Video saved to {output_filename}")
                return {
                    "success": True,
                    "output_path": output_filename,
                    "message": f"{prompt} success generate video",
                }
            elif status == "failed":
                error_msg = get_result.error if hasattr(get_result, "error") else "Unknown failure"
                logger.error(f"Task failed: {error_msg}")
                return {"success": False, "error": f"Task failed: {error_msg}"}
            else:
                logger.info(f"Status: {status}, retrying in 10s...")
                time.sleep(10)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            return {"success": False, "error": str(e)}

#def speech_gen():
#火山引擎的语音合成api格式差太多，人物对话这些最好均使用seedance 2.0直接生成

import os
import base64
import logging
from typing import List, Optional, Union, Dict, Any
from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions

logger = logging.getLogger(__name__)


def seedream5_sequential_edit(
    api_key: str,
    prompt: str,
    images: List[str],
    max_images: int,
    size: str = "2K",
    output_format: str = "jpg",
    watermark: bool = False,
    response_format: str = "url",
    model="doubao-seedream-5-0-260128",
    equential_image_generation="auto",
) -> Dict[str, Any]:
    
   
    processed_images = []
    for img in images:
        if not img:
            continue
        if isinstance(img, str) and (img.startswith("http://") or img.startswith("https://")):
            processed_images.append(img)
        elif os.path.exists(img):
            with open(img, "rb") as f:
                img_bytes = f.read()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            ext = os.path.splitext(img)[1].lower().lstrip(".")
            if ext in ("jpg", "jpeg"):
                ext = "jpeg"
            elif ext not in ("png", "webp", "bmp", "tiff", "gif", "heic", "heif"):
                ext = "png"
            processed_images.append(f"data:image/{ext};base64,{b64}")
        else:
            logger.warning(f"Invalid image path or URL, skipping: {img}")

    if not processed_images:
        return {"success": False, "error": "No valid reference images provided."}


    try:
        resp = client.images.generate(
            api_key=api_key,
            model=model,
            prompt=prompt,
            image=processed_images,
            size=size,
            sequential_image_generation=equential_image_generation,
            sequential_image_generation_options=SequentialImageGenerationOptions(
                max_images=max_images
            ),
            output_format=output_format,
            response_format=response_format,
            watermark=watermark,
        )
    except Exception as e:
        logger.error(f"Seedream 5.0 generation failed: {e}")
        return {"success": False, "error": str(e)}

    urls = [img.url for img in resp.data if img.url]
    if not urls:
        return {"success": False, "error": "No image URLs returned."}

    logger.info(f"Generated {len(urls)} images.")
    return {
        "success": True,
        "output_urls": urls,
        "message": f"Generated {len(urls)} images successfully.",
    }

# 这个函数暂时未用到
def seedream5_edit(
    api_key: str,
    prompt: str,
    images: Union[str, List[str]],
    size: str = "1024*1024",
    enable_base64_output: bool = False, 
    enable_sync_mode: bool = False,
    save_path: str = None
) -> Dict[str, Any]:


    if isinstance(images, str):
        images = [images]

    processed = []
    for img in images:
        if not img:
            continue
        if img.startswith(("http://", "https://")):
            processed.append(img)
        elif os.path.exists(img):
            with open(img, "rb") as f:
                img_bytes = f.read()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            ext = os.path.splitext(img)[1].lower().lstrip(".")
            if ext in ("jpg", "jpeg"):
                ext = "jpeg"
            elif ext not in ("png", "webp", "bmp", "tiff", "gif", "heic", "heif"):
                ext = "png"  # 默认
            processed.append(f"data:image/{ext};base64,{b64}")
        else:
            logger.warning(f"Ignoring invalid image: {img}")

    if not processed:
        return {"success": False, "error": "No valid images provided."}

    
    try:
        resp = client.images.generate(
            api_key=api_key,
            model="doubao-seedream-5-0-260128",
            prompt=prompt,
            image=processed if len(processed) > 1 else processed[0],
            size=size,
            sequential_image_generation="disabled",
            output_format="png",
            response_format="url",
            watermark=False,
        )
    except Exception as e:
        logger.error(f"Seedream 5.0 edit failed: {e}")
        return {"success": False, "error": str(e)}

    if not resp or not resp.data:
        return {"success": False, "error": "No data returned from API."}

    output_url = resp.data[0].url
    return {
        "success": True,
        "output_path": output_url,
        "message": "Image editing completed successfully."
    }
