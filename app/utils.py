import os

from app.config import Configuration

conf = Configuration()


def list_images():
    """Returns the list of available images."""
    img_names = filter(
        lambda x: x.endswith(".JPEG"), os.listdir(conf.image_folder_path)
    )
    return list(img_names)
    
async def add_image_to_list(image, image_name):
    """Saves the image with the specified ID."""
    if not image_name.lower().endswith(".jpeg"):
        return False

    image_path = os.path.join(conf.image_folder_path, image_name)

    print(image_path)

    with open(image_path, "wb") as buffer:
        buffer.write(await image.read())

    return True