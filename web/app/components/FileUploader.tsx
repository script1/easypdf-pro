import React, { useRef, useState } from 'react';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';

interface FileUploaderProps {
    onFileSelect: (file: File | null) => void;
    accept?: string;
}

export function FileUploader({ onFileSelect, accept = ".pdf" }: FileUploaderProps) {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            handleFile(file);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleFile = (file: File) => {
        if (accept === ".pdf" && file.type !== "application/pdf") {
            alert("Please upload a PDF file");
            return;
        }
        setSelectedFile(file);
        onFileSelect(file);
    };

    const clearFile = () => {
        setSelectedFile(null);
        onFileSelect(null);
        if (inputRef.current) {
            inputRef.current.value = "";
        }
    };

    if (selectedFile) {
        return (
            <div className="w-full p-6 bg-blue-50 border-2 border-dashed border-blue-200 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-white rounded-lg shadow-sm">
                        <FileIcon className="w-8 h-8 text-blue-500" />
                    </div>
                    <div>
                        <p className="font-semibold text-slate-700">{selectedFile.name}</p>
                        <p className="text-sm text-slate-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                </div>
                <button onClick={clearFile} className="p-2 hover:bg-white rounded-full transition-colors text-slate-400 hover:text-red-500">
                    <X className="w-5 h-5" />
                </button>
            </div>
        )
    }

    return (
        <div
            className={`relative w-full h-64 border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-all cursor-pointer bg-white/50 backdrop-blur-sm ${dragActive ? "border-blue-500 bg-blue-50/50" : "border-slate-300 hover:border-blue-400 hover:bg-slate-50/50"
                }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
        >
            <input
                ref={inputRef}
                type="file"
                className="hidden"
                accept={accept}
                onChange={handleChange}
            />
            <div className="p-4 bg-white rounded-full shadow-sm mb-4">
                <UploadCloud className={`w-8 h-8 ${dragActive ? "text-blue-600" : "text-blue-500"}`} />
            </div>
            <p className="text-lg font-medium text-slate-700 mb-1">
                Click to upload or drag and drop
            </p>
            <p className="text-sm text-slate-400">
                PDF files only (max 10MB)
            </p>
        </div>
    );
}
