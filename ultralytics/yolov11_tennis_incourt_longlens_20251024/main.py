import os
import io
import json
import base64
import traceback
from PIL import Image
from ultralytics import YOLO
import torch
import ultralytics


def get_function_labels():
    labels_spec = os.getenv("FUNCTION_LABELS")
    if not labels_spec:
        raise ValueError("FUNCTION_LABELS env var is not set")

    return {int(item["id"]): item["name"] for item in json.loads(labels_spec)}


def init_context(context):
    """
    Load YOLO model once when Nuclio function starts.
    """
    context.logger.info("=== Init context... 0% ===")

    # Get model path from environment variable
    model_path = os.getenv("MODEL_PATH", "/opt/nuclio/yolo_model.pt")
    context.logger.info(f"Loading YOLO model from: {model_path}")

    # Detect device
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    context.logger.info(f"Detected device: {device}")

    # Log Ultralytics version
    context.logger.info(f"Ultralytics version: {ultralytics.__version__}")

    # Load YOLO model
    try:
        model = YOLO(model_path)
        model.to(device)
    except Exception as e:
        context.logger.error(f"❌ Failed to load YOLO model: {e}")
        raise

    # Save model to context for reuse
    context.user_data.model_handler = model

    context.logger.info("=== Init context... 100% ===")


def handler(context, event):
    """
    Handle inference request from CVAT.
    Expects event.body['image'] to be a base64-encoded string.
    """
    context.logger.info("=== Running YOLO inference ===")

    try:
        data = event.body
        if not data:
            raise ValueError("No event body received")

        img_b64 = data.get("image")
        if img_b64 is None:
            raise ValueError("No 'image' field in request")

        threshold = float(data.get("threshold", 0.5))
        context.logger.info(f"Confidence threshold: {threshold}")

        # Decode base64 → RGB image
        buf = io.BytesIO(base64.b64decode(img_b64))
        img = Image.open(buf).convert("RGB")

        # context.logger.info(
        #     f"Image shape: {img.shape}, dtype: {img.dtype}, "
        #     f"min: {img.min()}, max: {img.max()}"
        # )

        # Run YOLO prediction
        model = context.user_data.model_handler
        context.logger.info(f"Model device: {model.device}, names: {model.names}")
        labels = get_function_labels()

        results = model.predict(img, conf=threshold, imgsz=1280, verbose=False)

        # Parse results
        output = []
        total_detections = 0

        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()
            scores = r.boxes.conf.cpu().numpy()
            label_ids = r.boxes.cls.cpu().numpy()

            for box, score, label in zip(boxes, scores, label_ids):
                if score >= threshold:
                    label_idx = int(label)
                    model_label_name = model.names[label_idx]
                    if label_idx not in labels:
                        context.logger.info(
                            f"Skipping undeclared class: model={model_label_name} ({score:.3f})"
                        )
                        continue

                    total_detections += 1
                    label_name = labels[label_idx]
                    context.logger.info(
                        f"Detection: model={model_label_name}, output={label_name} ({score:.3f}) "
                        f"at box: {box.tolist()}"
                    )
                    output.append({
                        "confidence": str(float(score)),
                        "label": label_name,
                        "points": box.tolist(),
                        "type": "rectangle",
                    })

        context.logger.info(f"Total detections above threshold: {total_detections}")

        return context.Response(
            body=json.dumps(output),
            headers={},
            content_type="application/json",
            status_code=200
        )

    except Exception as e:
        context.logger.error(f"❌ Inference failed: {e}")
        context.logger.error(traceback.format_exc())
        return context.Response(
            body=json.dumps({"error": str(e)}),
            headers={},
            content_type="application/json",
            status_code=500
        )
