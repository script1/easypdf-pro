from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import shutil
import uuid
from typing import List
import zipfile
from pypdf import PdfWriter, PdfReader
import fitz  # PyMuPDF
from pdf2docx import Converter
import asyncio
import time

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
FILE_EXPIRY_SECONDS = 3600  # 1 hour
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def cleanup_old_files():
    while True:
        await asyncio.sleep(1800)  # Run every 30 minutes
        now = time.time()
        try:
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                try:
                    if os.path.isfile(file_path) and (now - os.path.getmtime(file_path)) > FILE_EXPIRY_SECONDS:
                        os.remove(file_path)
                except Exception:
                    pass
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_old_files())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_valid_pdf(data: bytes) -> bool:
    return data[:4] == b"%PDF"


async def read_file_bytes(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")
    return data


@app.get("/")
def read_root():
    return {"message": "EasyPDF Pro Backend is Running", "version": "2.0"}


# ─────────────────────── UPLOAD ───────────────────────────────

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}.pdf"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as f:
        f.write(data)

    return {
        "filename": file.filename,
        "file_id": file_id,
        "content_type": file.content_type,
        "path": file_path,
        "message": "File uploaded successfully",
    }


# ─────────────────────── PDF TO WORD ──────────────────────────

@app.post("/convert/pdf-to-word/")
async def convert_pdf_to_word(
    file_id: str = None,
    file: UploadFile = File(None),
):
    if file_id:
        files = os.listdir(UPLOAD_DIR)
        target_file = next((f for f in files if f.startswith(file_id) and f.endswith(".pdf")), None)
        if not target_file:
            raise HTTPException(status_code=404, detail="File not found")
        pdf_path = os.path.join(UPLOAD_DIR, target_file)
    elif file:
        data = await read_file_bytes(file)
        if not is_valid_pdf(data):
            raise HTTPException(status_code=400, detail="Invalid PDF file.")
        file_id = str(uuid.uuid4())
        pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(data)
    else:
        raise HTTPException(status_code=400, detail="No file provided.")

    docx_filename = f"{file_id}.docx"
    docx_path = os.path.join(UPLOAD_DIR, docx_filename)

    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    return {
        "message": "Conversion successful",
        "docx_filename": docx_filename,
        "download_url": f"/download/{docx_filename}",
    }


# ─────────────────────── MERGE ────────────────────────────────

@app.post("/merge/")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least 2 PDF files.")

    merger = PdfWriter()
    temp_paths = []
    streams = []

    try:
        for file in files:
            data = await read_file_bytes(file)
            if not is_valid_pdf(data):
                raise HTTPException(status_code=400, detail=f"{file.filename} is not a valid PDF.")
            path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.pdf")
            with open(path, "wb") as f:
                f.write(data)
            temp_paths.append(path)
            s = open(path, "rb")
            streams.append(s)
            merger.append(s)

        merged_filename = f"merged_{uuid.uuid4()}.pdf"
        merged_path = os.path.join(UPLOAD_DIR, merged_filename)
        with open(merged_path, "wb") as f:
            merger.write(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")
    finally:
        for s in streams:
            try: s.close()
            except Exception: pass
        for p in temp_paths:
            try: os.remove(p)
            except Exception: pass

    return {"message": "Merge successful", "download_url": f"/download/{merged_filename}"}


# ─────────────────────── SPLIT ────────────────────────────────

@app.post("/split/")
async def split_pdf(file: UploadFile = File(...), pages: str = Form(None)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"split_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    generated = []
    try:
        with open(input_path, "rb") as f_in:
            reader = PdfReader(f_in)
            total = len(reader.pages)
            selected = [int(p.strip()) for p in pages.split(",") if p.strip().isdigit()] if pages else list(range(total))

            pdf_paths = []
            for i in selected:
                if 0 <= i < total:
                    w = PdfWriter()
                    w.add_page(reader.pages[i])
                    p = os.path.join(UPLOAD_DIR, f"{task_id}_page_{i+1}.pdf")
                    with open(p, "wb") as f_out:
                        w.write(f_out)
                    generated.append(p)
                    pdf_paths.append((p, f"page_{i+1}.pdf"))

            if len(pdf_paths) == 1:
                generated.remove(pdf_paths[0][0])
                return {"message": "Split successful", "download_url": f"/download/{os.path.basename(pdf_paths[0][0])}"}

            zip_filename = f"split_{task_id}.zip"
            zip_path = os.path.join(UPLOAD_DIR, zip_filename)
            with zipfile.ZipFile(zip_path, "w") as zf:
                for p, name in pdf_paths:
                    zf.write(p, arcname=name)
            return {"message": "Split successful", "download_url": f"/download/{zip_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")
    finally:
        for p in generated:
            try: os.remove(p)
            except Exception: pass
        try: os.remove(input_path)
        except Exception: pass


# ─────────────────────── PDF TO JPG ───────────────────────────

@app.post("/convert/pdf-to-jpg/")
async def convert_pdf_to_jpg(file: UploadFile = File(...), pages: str = Form(None)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"jpg_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    generated = []
    try:
        doc = fitz.open(input_path)
        total = len(doc)
        selected = [int(p.strip()) for p in pages.split(",") if p.strip().isdigit()] if pages else list(range(total))

        img_paths = []
        for i in selected:
            if 0 <= i < total:
                pix = doc[i].get_pixmap(dpi=150)
                img_path = os.path.join(UPLOAD_DIR, f"{task_id}_page_{i+1}.jpg")
                pix.save(img_path)
                generated.append(img_path)
                img_paths.append((img_path, f"page_{i+1}.jpg"))
        doc.close()

        if len(img_paths) == 1:
            generated.remove(img_paths[0][0])
            return {"message": "Conversion successful", "download_url": f"/download/{os.path.basename(img_paths[0][0])}"}

        zip_filename = f"images_{task_id}.zip"
        zip_path = os.path.join(UPLOAD_DIR, zip_filename)
        with zipfile.ZipFile(zip_path, "w") as zf:
            for p, name in img_paths:
                zf.write(p, arcname=name)
        return {"message": "Conversion successful", "download_url": f"/download/{zip_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        for p in generated:
            try: os.remove(p)
            except Exception: pass
        try: os.remove(input_path)
        except Exception: pass


# ─────────────────────── PROTECT ──────────────────────────────

@app.post("/protect/")
async def protect_pdf(file: UploadFile = File(...), password: str = Form(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"protect_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    output_filename = f"protected_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(output_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Protection failed: {str(e)}")
    finally:
        try: os.remove(input_path)
        except Exception: pass

    return {"message": "Protection successful", "download_url": f"/download/{output_filename}"}


# ─────────────────────── COMPRESS ─────────────────────────────

@app.post("/compress/")
async def compress_pdf(file: UploadFile = File(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"compress_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    output_filename = f"compressed_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        for page in writer.pages:
            page.compress_content_streams()
        writer.compress_identical_objects()
        with open(output_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")
    finally:
        try: os.remove(input_path)
        except Exception: pass

    return {"message": "Compression successful", "download_url": f"/download/{output_filename}"}


# ─────────────────────── WATERMARK ────────────────────────────

@app.post("/watermark/")
async def add_watermark(file: UploadFile = File(...), text: str = Form(...), opacity: float = Form(0.3)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"wm_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    output_filename = f"watermarked_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        doc = fitz.open(input_path)
        for page in doc:
            rect = page.rect
            page.insert_text(
                (rect.width / 4, rect.height / 2),
                text,
                fontsize=60,
                color=(0.7, 0.7, 0.7),
                rotate=45,
                overlay=True,
            )
        doc.save(output_path)
        doc.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Watermark failed: {str(e)}")
    finally:
        try: os.remove(input_path)
        except Exception: pass

    return {"message": "Watermark added successfully", "download_url": f"/download/{output_filename}"}


# ─────────────────────── ROTATE ───────────────────────────────

@app.post("/rotate/")
async def rotate_pdf(file: UploadFile = File(...), angle: int = Form(90), pages: str = Form(None)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    if angle not in (90, 180, 270):
        raise HTTPException(status_code=400, detail="Angle must be 90, 180, or 270.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"rotate_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    output_filename = f"rotated_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        total = len(reader.pages)
        selected = set(int(p.strip()) for p in pages.split(",") if p.strip().isdigit()) if pages else set(range(total))
        for i, page in enumerate(reader.pages):
            if i in selected:
                page.rotate(angle)
            writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rotation failed: {str(e)}")
    finally:
        try: os.remove(input_path)
        except Exception: pass

    return {"message": "Rotation successful", "download_url": f"/download/{output_filename}"}


# ─────────────────────── DELETE PAGES ─────────────────────────

@app.post("/delete-pages/")
async def delete_pages(file: UploadFile = File(...), pages: str = Form(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"del_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    output_filename = f"deleted_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        to_delete = set(int(p.strip()) for p in pages.split(",") if p.strip().isdigit())
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if i not in to_delete:
                writer.add_page(page)
        if len(writer.pages) == 0:
            raise HTTPException(status_code=400, detail="Cannot delete all pages.")
        with open(output_path, "wb") as f:
            writer.write(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete pages failed: {str(e)}")
    finally:
        try: os.remove(input_path)
        except Exception: pass

    return {"message": "Pages deleted successfully", "download_url": f"/download/{output_filename}"}


# ─────────────────────── REORDER PAGES ────────────────────────

@app.post("/reorder-pages/")
async def reorder_pages(file: UploadFile = File(...), order: str = Form(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"reorder_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    output_filename = f"reordered_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        new_order = [int(p.strip()) for p in order.split(",") if p.strip().isdigit()]
        reader = PdfReader(input_path)
        total = len(reader.pages)
        writer = PdfWriter()
        for i in new_order:
            if 0 <= i < total:
                writer.add_page(reader.pages[i])
        if len(writer.pages) == 0:
            raise HTTPException(status_code=400, detail="Invalid page order.")
        with open(output_path, "wb") as f:
            writer.write(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reorder failed: {str(e)}")
    finally:
        try: os.remove(input_path)
        except Exception: pass

    return {"message": "Pages reordered successfully", "download_url": f"/download/{output_filename}"}


# ─────────────────────── UNLOCK ───────────────────────────────

@app.post("/unlock/")
async def unlock_pdf(file: UploadFile = File(...), password: str = Form(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"unlock_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    output_filename = f"unlocked_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            if not reader.decrypt(password):
                raise HTTPException(status_code=400, detail="Wrong password.")
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unlock failed: {str(e)}")
    finally:
        try: os.remove(input_path)
        except Exception: pass

    return {"message": "PDF unlocked successfully", "download_url": f"/download/{output_filename}"}


# ─────────────────────── IMAGES TO PDF ────────────────────────

@app.post("/convert/images-to-pdf/")
async def images_to_pdf(files: List[UploadFile] = File(...)):
    from PIL import Image as PILImage
    import io

    task_id = str(uuid.uuid4())
    output_filename = f"images_to_pdf_{task_id}.pdf"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        images = []
        for file in files:
            data = await file.read()
            if len(data) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"{file.filename} is too large.")
            img = PILImage.open(io.BytesIO(data)).convert("RGB")
            images.append(img)

        if not images:
            raise HTTPException(status_code=400, detail="No valid images provided.")

        images[0].save(output_path, save_all=True, append_images=images[1:])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    return {"message": "Conversion successful", "download_url": f"/download/{output_filename}"}


# ─────────────────────── EXTRACT TEXT ─────────────────────────

@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    data = await read_file_bytes(file)
    if not is_valid_pdf(data):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"text_input_{task_id}.pdf")
    with open(input_path, "wb") as f:
        f.write(data)

    output_filename = f"extracted_text_{task_id}.txt"
    output_path = os.path.join(UPLOAD_DIR, output_filename)

    try:
        doc = fitz.open(input_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")
    finally:
        try: os.remove(input_path)
        except Exception: pass

    preview = full_text[:500] + "..." if len(full_text) > 500 else full_text

    return {
        "message": "Text extracted successfully",
        "output_filename": output_filename,
        "download_url": f"/download/{output_filename}",
        "preview": preview,
    }


# ─────────────────────── DOWNLOAD ─────────────────────────────

@app.get("/download/{filename}")
async def download_file(filename: str):
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=safe_filename)


# ─────────────────────── FRONTEND STATIC FILES ────────────────
_frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web', 'out')
if os.path.exists(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
