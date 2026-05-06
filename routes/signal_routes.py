from flask import Blueprint, request, jsonify
import pandas as pd
from signal_processing import compute_features, compute_fft_plot, compute_time_plot

signal_bp = Blueprint('signal', __name__)


@signal_bp.route('/fft', methods=['POST'])
def compute_fft():
    file = request.files['file']
    sampling_rate = float(request.form.get('sampling_rate', 1000))

    df = pd.read_excel(file)
    signal = df.iloc[:, 1].dropna().astype(float).values

    features = compute_features(signal)
    time_image = compute_time_plot(signal, sampling_rate)
    fft_image = compute_fft_plot(signal, sampling_rate)

    return jsonify({
        "time_image": time_image,
        "fft_image": fft_image,
        "features": features
    })
