import json
import matplotlib.pyplot as plt
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
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
def donwload_result(request: Request):
    """Download the classification result as a JSON file."""
    result_file_path = "app/static/result.json"
    
    classification_scores = request.query_params.get("scores")

    with open(result_file_path, "w") as json_file:
        json_file.write(classification_scores)

    return FileResponse(result_file_path, filename="result.json", media_type="application/json")


@app.get("/download-plot")
def download_plot(request: Request):
    result_file_path = "app/static/plot.png"

    classification_scores = json.loads(request.query_params.get("scores"))

    top_5_scores = sorted(classification_scores, key=lambda x: x[1], reverse=True)[:5]
    models = [score[0] for score in top_5_scores]
    scores = [score[1] for score in top_5_scores]

    plt.bar(models, scores, color="blue")
    plt.xlabel("Model")
    plt.ylabel("Score")
    plt.title("Top 5 Classification Scores")
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.5) 
    plt.savefig(result_file_path)
    plt.close()

    return FileResponse(result_file_path, filename="plot.png", media_type="image/png")