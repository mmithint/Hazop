import os
import base64
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_session import Session
from config import Config
from services.claude_service import extract_hazop_items, generate_causes, generate_worksheet

app = Flask(__name__)
app.config.from_object(Config)
Session(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/")
def index():
    return render_template("upload.html")


@app.route("/api/extract", methods=["POST"])
def api_extract():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    # Read and encode PDF
    pdf_bytes = file.read()
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    # Save file temporarily
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

    try:
        result = extract_hazop_items(pdf_base64, app.config["ANTHROPIC_API_KEY"])
        # Store in session for later use
        session["extracted_items"] = result
        session["pdf_filename"] = file.filename
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/save-items", methods=["POST"])
def api_save_items():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Extract and store analysis parameters separately
    analysis_params = data.pop("analysis_params", {})
    session["analysis_params"] = analysis_params

    session["extracted_items"] = data
    return jsonify({"redirect": url_for("deviations")})


@app.route("/deviations")
def deviations():
    items = session.get("extracted_items")
    if not items:
        return redirect(url_for("index"))
    return render_template("deviations.html", items=items)


@app.route("/api/submit-deviations", methods=["POST"])
def api_submit_deviations():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    session["selected_deviations"] = data.get("deviations", [])
    session["other_deviation"] = data.get("other_text", "")

    app.logger.info("Selected deviations: %s", session["selected_deviations"])
    if session["other_deviation"]:
        app.logger.info("Other deviation: %s", session["other_deviation"])

    return jsonify({"status": "ok", "message": "Deviations saved successfully"})


@app.route("/api/generate-causes", methods=["POST"])
def api_generate_causes():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    deviations = data.get("deviations", [])
    other_text = data.get("other_text", "")
    if other_text:
        deviations.append(other_text)

    if not deviations:
        return jsonify({"error": "No deviations selected"}), 400

    items = session.get("extracted_items")
    if not items or "instruments_causes" not in items:
        return jsonify({"error": "No extracted items in session. Please re-upload the P&ID."}), 400

    instruments_causes = items["instruments_causes"]

    # Save selected deviations to session
    session["selected_deviations"] = deviations
    session["other_deviation"] = other_text

    try:
        causes = {}
        for deviation in deviations:
            causes[deviation] = generate_causes(
                instruments_causes, deviation, app.config["ANTHROPIC_API_KEY"]
            )
        session["causes"] = causes
        return jsonify({"causes": causes, "redirect": url_for("causes")})
    except Exception as e:
        app.logger.error("Causes generation failed: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/causes")
def causes():
    causes_data = session.get("causes")
    if not causes_data:
        return redirect(url_for("deviations"))
    return render_template("causes.html", causes=causes_data)


@app.route("/api/confirm-causes", methods=["POST"])
def api_confirm_causes():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    confirmed_causes = data.get("confirmed_causes", {})
    session["confirmed_causes"] = confirmed_causes

    # Gather all required data from session
    extracted_items = session.get("extracted_items")
    if not extracted_items:
        return jsonify({"error": "No extracted items in session. Please re-upload the P&ID."}), 400

    analysis_params = dict(session.get("analysis_params", {}))
    analysis_params["pdlor_dollar_per_bbl"] = app.config.get("PDLOR_DOLLAR_PER_BBL", 19)
    analysis_params["pdlor_apc_production_lost"] = app.config.get("PDLOR_APC_PRODUCTION_LOST", 84942)
    pdf_filename = session.get("pdf_filename", "Unknown")

    try:
        worksheet_data = generate_worksheet(
            extracted_items,
            confirmed_causes,
            analysis_params,
            pdf_filename,
            app.config["ANTHROPIC_API_KEY"],
        )
        session["worksheet_data"] = worksheet_data
        return jsonify({"redirect": url_for("worksheet")})
    except Exception as e:
        app.logger.error("Worksheet generation failed: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/worksheet")
def worksheet():
    worksheet_data = session.get("worksheet_data")
    if not worksheet_data:
        return redirect(url_for("causes"))
    analysis_params = session.get("analysis_params", {})
    pdf_filename = session.get("pdf_filename", "Unknown")
    return render_template(
        "worksheet.html",
        worksheet=worksheet_data,
        analysis_params=analysis_params,
        pdf_filename=pdf_filename,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
