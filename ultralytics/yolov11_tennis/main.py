import os
import io
import json
import base64
import numpy as np
from PIL import Image
from ultralytics import YOLO
# dummy update
def init_context(context):
    """
    Load YOLO model once when Nuclio function starts.
    """
    context.logger.info("Init context... 0%")

    # Get model path from environment variable, fallback to default
    model_path = os.getenv("MODEL_PATH", "/opt/nuclio/best.pt")
    context.logger.info(f"Loading YOLO model from {model_path}")

    # Load YOLO model
    try:
        model = YOLO(model_path)
    except Exception as e:
        context.logger.error(f"Failed to load YOLO model: {e}")
        raise

    # Save model in context.user_data for later use
    context.user_data.model_handler = model

    context.logger.info("Init context... 100%")


def handler(context, event):
    """
    Handle inference request from CVAT.
    Expects event.body['image'] to be a base64-encoded string.
    """
    context.logger.info("Running YOLO inference")

    try:
        data = event.body
        img_b64 = data.get("image")
        if img_b64 is None:
            raise ValueError("No 'image' field in request")

        threshold = float(data.get("threshold", 0.5))

        # Decode base64 to RGB image
        buf = io.BytesIO(base64.b64decode(img_b64))
        img = Image.open(buf).convert("RGB")

        # Run prediction
        model = context.user_data.model_handler
        results = model.predict(img, conf=threshold)

        # Format output for CVAT
        output = []
        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()    # [x1, y1, x2, y2]
            scores = r.boxes.conf.cpu().numpy()
            labels = r.boxes.cls.cpu().numpy()
            for box, score, label in zip(boxes, scores, labels):
                if score >= threshold:
                    output.append({
                        "confidence": float(score),
                        "label": model.names[int(label)],
                        "points": box.tolist(),
                        "type": "rectangle",
                    })

        return context.Response(
            body=json.dumps(output),
            headers={},
            content_type="application/json",
            status_code=200
        )

    except Exception as e:
        context.logger.error(f"Inference failed: {e}")
        return context.Response(
            body=json.dumps({"error": str(e)}),
            headers={},
            content_type="application/json",
            status_code=500
        )
