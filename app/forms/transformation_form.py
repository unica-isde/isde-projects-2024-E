from fastapi import Request


class TransformationForm:
    def __init__(self, request: Request) -> None:
        self.request: Request = request
        self.errors: list = []
        self.image_id: str = ""
        self.color: float = 1.0
        self.brightness: float = 1.0
        self.contrast: float = 1.0
        self.sharpness: float = 1.0

    async def load_data(self):
        form = await self.request.form()
        self.image_id = form.get("image_id")

        if form.get("color") != "":
            self.color = float(form.get("color"))

        if form.get("brightness") != "":
            self.brightness = float(form.get("brightness"))

        if form.get("contrast") != "":
            self.contrast = float(form.get("contrast"))

        if form.get("sharpness") != "":
            self.sharpness = float(form.get("sharpness"))
        

    def is_valid(self):
        if not self.image_id or not isinstance(self.image_id, str):
            self.errors.append("A valid image id is required")
        if not self.color or not isinstance(self.color, float) or self.color < 0.0 or self.color > 1.0:
            self.errors.append("A valid color value is required")
        if not self.brightness or not isinstance(self.brightness, float) or self.brightness<0.0:
            self.errors.append("A valid brightness value is required")
        if not self.contrast or not isinstance(self.contrast, float) or self.contrast<0.0:
            self.errors.append("A valid contrast value is required")
        if not self.sharpness or not isinstance(self.sharpness, float) or self.sharpness<0.0:
            self.errors.append("A valid sharpness value is required")
        if not self.errors:
            return True
        return False
