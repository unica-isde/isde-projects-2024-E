import os
from PIL import Image
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

from app.config import Configuration

conf = Configuration()


def list_images():
    """Returns the list of available images."""
    img_names = filter(
        lambda x: x.endswith(".JPEG"), os.listdir(conf.image_folder_path)
    )
    return list(img_names)

def get_image_path(image_id: str) -> str:
    return os.path.join(conf.image_folder_path, image_id)


def generate_histogram(image_path):
    img = Image.open(image_path)
    img_array = np.array(img)

    plt.figure(figsize=(6, 4))

    if len(img_array.shape) == 2:  # Grayscale image (2D)
        plt.hist(img_array.ravel(), bins=256, color='gray', alpha=0.7, label="Grayscale")
    else:  # RGB image (3D)
        colors = ['red', 'green', 'blue']
        labels = ['Red', 'Green', 'Blue']
        for i, color in enumerate(colors):
            plt.hist(img_array[:, :, i].ravel(), bins=256, color=color, alpha=0.5, label=labels[i])

    plt.xlabel('Pixel Value')
    plt.ylabel('Frequency')
    plt.legend()

    # save histogram to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode()


    
async def add_image_to_list(image, image_name):
    """Saves the image with the specified ID."""
    if not image_name.lower().endswith(".jpeg"):
        return False

    image_path = os.path.join(conf.image_folder_path, image_name)

    print(image_path)

    with open(image_path, "wb") as buffer:
        buffer.write(await image.read())

    return True