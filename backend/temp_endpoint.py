@app.post("/convert/pdf-to-jpg/")
async def convert_pdf_to_jpg(file: UploadFile = File(...)):
    """
    Convert a PDF into JPG images (one per page) and return them as a ZIP.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    task_id = str(uuid.uuid4())
    input_filename = f"jpg_input_{task_id}.pdf"
    input_path = os.path.join(UPLOAD_DIR, input_filename)

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    zip_filename = f"images_{task_id}.zip"
    zip_path = os.path.join(UPLOAD_DIR, zip_filename)

    generated_files = []

    try:
        # Open the PDF with PyMuPDF
        doc = fitz.open(input_path)

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=150)  # Medium quality
                img_filename = f"page_{i+1}.jpg"
                img_path = os.path.join(UPLOAD_DIR, f"{task_id}_{img_filename}")

                pix.save(img_path)
                zipf.write(img_path, arcname=img_filename)
                generated_files.append(img_path)

        doc.close()

    except Exception as e:
        print(f"Error converting PDF to JPG: {e}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        # Cleanup
        for path in generated_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Warning: Could not remove temp image {path}: {e}")

        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception as e:
            print(f"Warning: Could not remove input file {input_path}: {e}")

    return {
        "message": "Conversion successful",
        "zip_filename": zip_filename,
        "download_url": f"/download/{zip_filename}",
    }
