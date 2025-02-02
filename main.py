import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import Configuration
from app.forms.classification_form import ClassificationForm
from app.forms.upload_form import UploadForm
from app.ml.classification_utils import classify_image
from app.utils import list_images
from app.utils import add_image_to_list


app = FastAPI()
config = Configuration()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/info")
def info() -> dict[str, list[str]]:
    """Returns a dictionary with the list of models and
    the list of available image files."""
    list_of_images = list_images()
    list_of_models = Configuration.models
    data = {"models": list_of_models, "images": list_of_images}
    return data


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """The home page of the service."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/classifications")
def create_classify(request: Request):
    return templates.TemplateResponse(
        "classification_select.html",
        {"request": request, "images": list_images(), "models": Configuration.models},
    )

@app.post("/classifications")
async def request_classification(request: Request):
    form = ClassificationForm(request)
    await form.load_data()
    image_id = form.image_id
    model_id = form.model_id
    classification_scores = classify_image(model_id=model_id, img_id=image_id)
    return templates.TemplateResponse(
        "classification_output.html",
        {
            "request": request,
            "image_id": image_id,
            "classification_scores": json.dumps(classification_scores),
        },
    )

@app.get("/upload-image")
def create_upload_image(request: Request):
    return templates.TemplateResponse(
        "upload_image_select.html",
        {"request": request, "models": Configuration.models},
    )

@app.post("/upload-image")
async def request_upload_image(request: Request):
    form = UploadForm(request)
    await form.load_data()
    model_id = form.model_id
    image = form.image
    image_id = str(image.filename)

    if not form.is_valid():
        print("".join(form.errors))
        return templates.TemplateResponse(
            "upload_image_select.html",
            {"request": request, "models": Configuration.models},
        )

    retVal = await add_image_to_list(image, image_id)
    if retVal == False:
        print("Error in adding image")
        return templates.TemplateResponse(
            "upload_image_select.html",
            {"request": request, "models": Configuration.models},
        )

    # To test a valid image submission
    print("valid")
    return templates.TemplateResponse(
        "upload_image_select.html",
        {"request": request, "models": Configuration.models},
    )

