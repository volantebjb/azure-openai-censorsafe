import os
from dotenv import load_dotenv
from flask import Flask, render_template, request

from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeTextOptions, AnalyzeImageOptions, ImageData
from azure.ai.contentsafety.models import TextCategory, ImageCategory

# Load credentials
load_dotenv()  
endpoint_url = os.getenv("AZURE_CONTENTSAFETY_ENDPOINT")
credential_key = AzureKeyCredential(os.getenv("AZURE_CONTENTSAFETY_KEY"))

# Create Content Safety Client
client = ContentSafetyClient(
    endpoint=endpoint_url,
    credential=credential_key
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    if request.method == 'POST':
        input_text = request.form['text']
        
        analyze_request = AnalyzeTextOptions(text=input_text)
        try:
            response = client.analyze_text(analyze_request)
        except HttpResponseError as e:
            return render_template('error.html', error_message=str(e))

        # Initialize category results
        hate_result = None
        self_harm_result = None
        sexual_result = None
        violence_result = None

        # Iterate through the categories
        for category in response.categories_analysis:
            if category.category == TextCategory.HATE:
                hate_result = category
            elif category.category == TextCategory.SELF_HARM:
                self_harm_result = category
            elif category.category == TextCategory.SEXUAL:
                sexual_result = category
            elif category.category == TextCategory.VIOLENCE:
                violence_result = category

        # Return results to the web page
        return render_template('results.html', hate_result=hate_result,
                               self_harm_result=self_harm_result,
                               sexual_result=sexual_result,
                               violence_result=violence_result)

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if request.method == 'POST':
        # Handle file upload and get image_path
        uploaded_file = request.files['image']

        # Save the uploaded file to a temporary location
        temp_file_path = '.temp/temp_image.jpg'  # You may want to use a more secure way to handle temporary files
        uploaded_file.save(temp_file_path)

        with open(temp_file_path, "rb") as file:
            img_request = AnalyzeImageOptions(image=ImageData(content=file.read()))
        try:
            response = client.analyze_image(img_request)
        except HttpResponseError as e:
            return render_template('error.html', error_message=str(e))

        # Initialize category results
        hate_result = None
        self_harm_result = None
        sexual_result = None
        violence_result = None

        # Iterate through the categories
        for category in response.categories_analysis:
            if category.category == ImageCategory.HATE:
                hate_result = category
            elif category.category == ImageCategory.SELF_HARM:
                self_harm_result = category
            elif category.category == ImageCategory.SEXUAL:
                sexual_result = category
            elif category.category == ImageCategory.VIOLENCE:
                violence_result = category

        # Return results to the web page
        return render_template('results.html', hate_result=hate_result,
                               self_harm_result=self_harm_result,
                               sexual_result=sexual_result,
                               violence_result=violence_result)

if __name__ == '__main__':
    app.run(debug=True)