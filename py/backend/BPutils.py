import subprocess
import sys
import json
import base64
import aiofiles
import folder_paths
from PIL import Image
import io
import os
import aiohttp
import math


def calculate_dimensions(total_pixels):
    # Calculate possible width and height combinations
    for width in range(int(math.sqrt(total_pixels // 3)), 0, -1):
        if (total_pixels // 3) % width == 0:
            height = (total_pixels // 3) // width
            return width, height
    return None, None


class directories:
    def __init__(self):
        base_folder = folder_paths.get_folder_paths("custom_nodes")[0]
        self.node = os.path.join(base_folder, "comfyui-photoshop")
        self.workflow = os.path.join(self.node, "data", "workflows")
        self.psinput = os.path.join(self.node, "data", "ps_inputs")
        self.psimg = os.path.join(self.psinput, "imgs")


dirs = directories()


def force_pull():
    try:
        import git
        repo = git.Repo(dirs.node)
        fetch_result = repo.git.fetch()
        print(fetch_result)
        reset_result = repo.git.reset("--hard", "origin/main")
        print(reset_result)
    except git.exc.GitCommandError as e:
        print(f"# PS: Error: {e}")


def install_plugin():
    installer_path = os.path.join(dirs.node, "Install_Plugin", "installer.py")
    subprocess.run([sys.executable, installer_path])


async def save_file(data: str, filename: str):
    data = base64.b64decode(data)
    async with aiofiles.open(os.path.join(dirs.psimg, filename), "wb") as file:
        await file.write(data)


async def process_and_save_mask(mask_data: list, filename: str):
    if mask_data[0] == "nomask":
        target_width, target_height = int(mask_data[1]["width"]), int(mask_data[1]["height"])
        white_image = Image.new("L", (target_width, target_height), color=255)
        white_image.save(os.path.join(dirs.psimg, filename), format="PNG")
        return

    decoded_data = base64.b64decode(mask_data[0])
    mask_image = Image.open(io.BytesIO(decoded_data)).convert("L")

    target_width, target_height = int(mask_data[1]["width"]), int(mask_data[1]["height"])
    source_bounds = {
        "left": int(mask_data[2]["left"]),
        "top": int(mask_data[2]["top"]),
        "right": int(mask_data[2]["right"]),
        "bottom": int(mask_data[2]["bottom"]),
    }

    canvas = Image.new("L", (target_width, target_height), color=0)
    left, top = source_bounds["left"], source_bounds["top"]
    canvas.paste(mask_image, (left, top))
    canvas.save(os.path.join(dirs.psimg, filename), format="PNG")


async def LatestVer(plugin_version: str):
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://raw.githubusercontent.com/NimaNzrii/comfyui-photoshop/refs/heads/main/data/PreviewFiles/version.json"
            async with session.get(url) as response:
                if response.status == 200:
                    version_data = await response.json()
                    latest_version = version_data.get("version")

                    if plugin_version < latest_version:
                        print("🚫 Your plugin version is outdated! Please update to the latest version.")
                    else:
                        print("✅ Updated already", version_data)
                else:
                    print(f"❌ Failed to Check PhotoshopPlugin Update. Status code: {response.status}")
    except aiohttp.ClientError as e:
        print(f"❌ Network error occurred: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decoding error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    else:
        return latest_version
