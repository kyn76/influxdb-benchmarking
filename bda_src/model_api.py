from flask import Flask, render_template, request
from model import ForecastModel
import os

app = Flask(__name__)

PORT_MODEL_API = os.getenv("PORT_MODEL_API")

@app.route("/")
def hello():
    return render_template('index.html')


@app.route('/api/train')
def train():
    if request.args.get("train_size") is not None:
        train_size = int(request.args.get("train_size"))
        offset = int(request.args.get("offset"))
        bdd = int(request.args.get("bdd"))
    else:
        train_size = int(request.form.get("train_size"))
        offset = int(request.form.get("offset"))
        bdd = int(request.form.get("bdd"))
    
    if train_size is None or offset is None:
        return render_template("error.html")

    forecast_model = ForecastModel()
    
    try:
        forecast_model.fit(train_size, offset, bdd)
        return render_template("train.html")
    except Exception as e:
        print(e)
        return render_template("error.html")
    

@app.route('/api/predict')
def predict():
    predict_size = request.args.get("predict_size")
    if predict_size is None:
        return render_template("error.html")
    
    forecast_model = ForecastModel()
    try:
        forecast_model.predict(predict_size)
        return render_template("predict.html")
    except Exception as e:
        print(e)
        return render_template("error.html")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=PORT_MODEL_API)
