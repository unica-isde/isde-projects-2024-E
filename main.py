import json
from io import BytesIO
import base64
import os
import matplotlib.pyplot as plt
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from app.config import Configuration
from app.forms.classification_form import ClassificationForm
from app.forms.histogram_form import HistogramForm
from app.forms.transformation_form import TransformationForm
from app.forms.upload_form import UploadForm
from app.ml.classification_utils import classify_image
from app.utils import list_images,generate_histogram,get_image_path
from app.ml.transformation_utils import transform_image
from app.utils import add_image_to_list
import tempfile

import matplotlib
matplotlib.use("agg")


app = FastAPI()
config = Configuration()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# Histogram Creation

@app.get("/histogram", response_class=HTMLResponse)
def create_histogram(request: Request):
    """Displays the form for selecting an image."""
    return templates.TemplateResponse(
        "histogram_select.html",
        {"request": request, "images": list_images()}
    )


@app.post("/histogram")
async def request_histogram(request: Request):
    """Processes the form submission and returns the histogram image."""
    form = HistogramForm(request)
    await form.load_data()

    if not form.is_valid():
        return templates.TemplateResponse("histogram_select.html", {"request": request, "errors": form.errors})

    image_path = get_image_path(form.image_id)
    histogram_data = generate_histogram(image_path)

    return templates.TemplateResponse(
        "histogram_output.html",
        {"request": request, "image_id": form.image_id, "histogram_data": histogram_data}
    )



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

@app.get("/image-transformation")
def create_transform(request: Request):
    return templates.TemplateResponse(
        "image_transformation_select.html",
        {"request": request, "images": list_images()},
    )

@app.post("/image-transformation")
async def request_transformation(request: Request):
    form = TransformationForm(request)
    await form.load_data()
    image_id = form.image_id
    color = form.color
    brightness = form.brightness
    contrast = form.contrast
    sharpness = form.sharpness
    
    transformed_image = transform_image(
        image_id=image_id,
        color=color,
        brightness=brightness,
        contrast=contrast,
        sharpness=sharpness,
    )

    buffer = BytesIO()
    transformed_image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    transformed_image_data_url = f"data:image/png;base64,{img_str}"
    buffer.close()

    
    return templates.TemplateResponse(
        "image_transformation_output.html",
        {
            "request": request,
            "image_id": image_id,
            "transformed_image_url": transformed_image_data_url,
        },
    )
@app.get("/upload-image")
def create_upload_image(request: Request):
    """Display the form to upload an image."""
    return templates.TemplateResponse(
        "upload_image_select.html",
        {"request": request, "models": Configuration.models},
    )

@app.post("/upload-image")
async def request_upload_image(request: Request):
    """Upload an image, store it and classify it using the selected model."""
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

    classification_scores = classify_image(model_id=model_id, img_id=image_id)
    return templates.TemplateResponse(
        "classification_output.html",
        {"request": request, "image_id": image_id, "classification_scores": json.dumps(classification_scores)},
    )


@app.get("/download-result")
def download_result(request: Request, background_tasks: BackgroundTasks):
    
    classification_scores = request.query_params.get("scores")
    classification_scores = json.loads(classification_scores)

    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as temp_file:
        temp_file_path = temp_file.name
        json.dump(classification_scores, temp_file)

    background_tasks.add_task(os.remove, temp_file_path)

    return FileResponse(
        temp_file_path,
        filename="classification_result.json",
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="classification_result.json"'}
    )

@app.get("/download-plot")
def download_plot(request: Request, background_tasks: BackgroundTasks):

    classification_scores = json.loads(request.query_params.get("scores"))

    top_5_scores = sorted(classification_scores, key=lambda x: x[1], reverse=True)[:5]
    models = [score[0] for score in top_5_scores]
    scores = [score[1] for score in top_5_scores]

    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.png') as temp_file:
        result_file_path = temp_file.name 
        plt.bar(models, scores, color="blue")
        plt.xlabel("Model")
        plt.ylabel("Score")
        plt.title("Top 5 Classification Scores")
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.5) 
        plt.savefig(result_file_path)
        plt.close()

    background_tasks.add_task(os.remove,result_file_path)
    
    return FileResponse(
        result_file_path,
        filename="classification_result.png",
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="classification_result.png"'}
    )
