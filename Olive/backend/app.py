import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, send_from_directory
import openai
import pytesseract
from PIL import Image
import io
from flask_cors import CORS
from dotenv import load_dotenv
import os
import traceback


# Load environment variables
load_dotenv()


app = Flask(__name__, static_folder=r'C:\Users\anidm\Desktop\Olive\frontend')


# Enable Cross-Origin Resource Sharing
CORS(app)


# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


# Set path for Tesseract (update if needed)
import pytesseract


# Set the correct path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\anidm\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


# Serve the index.html file from the frontend directory
from flask import render_template


@app.route('/')
def home():
    return send_from_directory(os.path.join(app.static_folder), 'index.html')




@app.route('/process', methods=['POST'])
def process():
    try:
        # Get form data
        age = request.form.get('age')
        gender = request.form.get('gender')
        sleep = request.form.get('sleep')
        allergies = request.form.get('allergies')
        activity = request.form.get('activity')
        email = request.form.get('email')  # New field to handle the email (if needed)


        # Get the uploaded image file
        image = request.files.get('report')


        if not image:
            return jsonify({"error": "No image uploaded"}), 400


        # Read and extract text from the image
        img = Image.open(io.BytesIO(image.read()))
        report_text = pytesseract.image_to_string(img)


        # Build the prompt for OpenAI
        prompt = f"""
        Patient profile:
        Age: {age}
        Gender: {gender}
        Hours of sleep: {sleep}
        Allergies: {allergies}
        Physical activity level: {activity}


        Medical Report:
        {report_text}


        Based on this information, create a personalized DAILY PLAN that includes:
        - What specific food they should eat to normalize their health values
        - Physical activities they should perform
        - One suggestion for their free time to improve mental well-being
        Make sure your answer is structured and actionable.
        """


        # Use OpenAI API to generate the personalized plan
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or another model like "gpt-3.5-turbo"
            messages=[{"role": "system", "content": "You are a helpful healthcare assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=500,  # You can adjust the max tokens based on the response length you need
            temperature=0.7  # You can adjust temperature for more creative or more structured responses
        )


        plan = response['choices'][0]['message']['content'].strip()  # Adjusted the response extraction


        # Send the email with the health plan
        send_email(email, plan)


        return jsonify({"plan": plan})


    except Exception as e:
        # Log error details for debugging
        print("Error:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500


def send_email(to_email, plan):
    try:
        from_email = os.getenv("EMAIL")  # Your email (e.g., your Gmail address)
        app_password = os.getenv("EMAIL_PASSWORD")  # The generated app password from Google


        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "Your Personalized Health Plan"


        # Email body with the health plan
        body = f"Your Personalized Health Plan:\n\n{plan}"
        msg.attach(MIMEText(body, 'plain'))


        # Setup the SMTP server and send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail's SMTP server
        server.starttls()  # Start TLS encryption
        server.login(from_email, app_password)  # Log in to your email account using the app password
        text = msg.as_string()  # Convert message to string
        server.sendmail(from_email, to_email, text)  # Send the email
        server.quit()  # Terminate the connection
        print("Email sent successfully!")


    except Exception as e:
        print("Failed to send email:", e)
        return jsonify({'error': "Failed to send email"}), 500


if __name__ == '__main__':
    app.run(debug=True)