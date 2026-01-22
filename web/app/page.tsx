"use client";
import React, { useState, useRef } from 'react';
import Link from 'next/link';
import { FileText, Layers, Scissors, Image, Shield, Zap, ArrowRight, CheckCircle, AlertCircle, Sparkles, Heart } from 'lucide-react';
import { FileUploader } from './components/FileUploader';
import { ToolConfig } from './components/ToolConfig';

export default function Home() {
  const [activeTool, setActiveTool] = useState('');
  const [stage, setStage] = useState<'select' | 'upload' | 'config' | 'result'>('select');
  const [files, setFiles] = useState<File[]>([]);
  const [processingResult, setProcessingResult] = useState<{ message: string, downloadUrl: string, status: 'success' | 'error' | 'idle' }>({ message: '', downloadUrl: '', status: 'idle' });
  const [isProcessing, setIsProcessing] = useState(false);

  const handleToolClick = (toolName: string) => {
    setActiveTool(toolName);
    setStage('upload');
    setFiles([]); // Reset files
    setProcessingResult({ message: '', downloadUrl: '', status: 'idle' });
  };

  const handleFileSelect = (file: File | null) => {
    if (file) {
      setFiles([file]);
      setStage('config');
    }
  };

  const handleBack = () => {
    if (stage === 'config') setStage('upload');
    if (stage === 'upload') {
      setStage('select');
      setActiveTool('');
    }
    if (stage === 'result') setStage('select');
  };

  const processTool = async (config: any) => {
    setIsProcessing(true);
    setProcessingResult({ message: 'Processing...', downloadUrl: '', status: 'idle' });

    try {
      const file = files[0];
      const formData = new FormData();
      formData.append('file', file);

      if (config.password) formData.append('password', config.password);
      if (config.selectedPages && config.selectedPages.length > 0) {
        formData.append('pages', config.selectedPages.join(','));
      }

      let endpoint = '';
      if (activeTool === 'PDF to Word') endpoint = '/upload/';
      else if (activeTool === 'Split PDF') endpoint = '/split/';
      else if (activeTool === 'PDF to JPG') endpoint = '/convert/pdf-to-jpg/';
      else if (activeTool === 'Protect PDF') endpoint = '/protect/';
      else if (activeTool === 'Compress') endpoint = '/compress/';

      if (activeTool === 'PDF to Word') {
        const uploadRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/upload/`, { method: 'POST', body: formData });
        if (!uploadRes.ok) throw new Error('Upload failed');
        const upData = await uploadRes.json();

        const convertRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/convert/pdf-to-word/?file_id=${upData.file_id}`, { method: 'POST' });
        if (!convertRes.ok) throw new Error('Conversion failed');
        const data = await convertRes.json();
        setProcessingResult({ message: 'Conversion Successful!', downloadUrl: `${process.env.NEXT_PUBLIC_API_URL}${data.download_url}`, status: 'success' });
        setStage('result');
        return;
      }

      if (activeTool === 'Merge PDF') {
        alert("Merge feature coming soon with multi-file support!");
        setIsProcessing(false);
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Processing failed');
      const data = await response.json();

      setProcessingResult({
        message: 'Success!',
        downloadUrl: `${process.env.NEXT_PUBLIC_API_URL}${data.download_url}`,
        status: 'success'
      });
      setStage('result');

    } catch (error: any) {
      console.error(error);
      setProcessingResult({ message: error.message || 'Error occurred', downloadUrl: '', status: 'error' });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col relative overflow-hidden bg-slate-50 font-sans selection:bg-purple-100 selection:text-purple-900">

      {/* Premium Background */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 bg-[#f8fafc]">
        <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] rounded-full bg-gradient-to-tr from-purple-200/40 to-blue-200/40 blur-[120px] animate-pulse-slow"></div>
        <div className="absolute bottom-[-20%] left-[-10%] w-[800px] h-[800px] rounded-full bg-gradient-to-tr from-blue-200/40 to-pink-200/40 blur-[120px] animate-pulse-slow delay-1000"></div>
      </div>

      <header className="w-full flex justify-center py-6 backdrop-blur-sm sticky top-0 z-50 bg-white/5 border-b border-white/10">
        <div onClick={() => { setStage('select'); setActiveTool(''); }} className="cursor-pointer flex items-center gap-3 hover:scale-105 transition-transform duration-300 group">
          <div className="w-10 h-10 bg-gradient-to-br from-slate-900 to-slate-700 rounded-xl flex items-center justify-center text-white shadow-xl shadow-blue-900/10 group-hover:shadow-blue-900/20">
            <Zap className="w-6 h-6 fill-yellow-400 text-yellow-400" />
          </div>
          <span className="text-2xl font-black tracking-tighter text-slate-800 group-hover:bg-clip-text group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-slate-900 group-hover:to-blue-600 transition-all">
            EASYPDF
          </span>
        </div>
      </header>

      <div className="flex-grow flex flex-col items-center justify-center p-4 w-full max-w-7xl mx-auto">

        {/* STAGE 1: SELECT TOOL */}
        {stage === 'select' && (
          <div className="w-full animate-in fade-in slide-in-from-bottom-8 duration-500">
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 border border-white/50 backdrop-blur-md shadow-sm mb-6 text-sm font-semibold text-slate-600">
                <Sparkles className="w-4 h-4 text-purple-500" />
                <span>Simple. Fast. Secure.</span>
              </div>
              <h1 className="text-5xl md:text-7xl font-black text-slate-900 mb-6 tracking-tight leading-tight">
                Everything you need <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 animate-gradient-x">
                  for your PDFs
                </span>
              </h1>
              <p className="text-xl text-slate-500 max-w-2xl mx-auto">
                Merge, split, compress, convert, and protect. All in one place.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 px-4">
              <ToolCard icon={<FileText className="text-blue-500" />} title="PDF to Word" desc="Convert PDF to editable Word" onClick={() => handleToolClick('PDF to Word')} color="blue" />
              <ToolCard icon={<Layers className="text-purple-500" />} title="Merge PDF" desc="Combine multiple PDFs" onClick={() => handleToolClick('Merge PDF')} color="purple" />
              <ToolCard icon={<Scissors className="text-pink-500" />} title="Split PDF" desc="Extract specific pages" onClick={() => handleToolClick('Split PDF')} color="pink" />
              <ToolCard icon={<Image className="text-green-500" />} title="PDF to JPG" desc="Convert pages to images" onClick={() => handleToolClick('PDF to JPG')} color="green" />
              <ToolCard icon={<Shield className="text-indigo-500" />} title="Protect PDF" desc="Add password security" onClick={() => handleToolClick('Protect PDF')} color="indigo" />
              <ToolCard icon={<Zap className="text-yellow-500" />} title="Compress" desc="Reduce file size" onClick={() => handleToolClick('Compress')} color="yellow" />
            </div>
          </div>
        )}

        {/* STAGE 2: UPLOAD */}
        {stage === 'upload' && (
          <div className="w-full max-w-3xl text-center animate-in fade-in slide-in-from-bottom-8">
            <button onClick={handleBack} className="mb-8 group flex items-center justify-center gap-2 text-slate-500 hover:text-slate-900 transition-colors mx-auto">
              <div className="p-2 rounded-full bg-white shadow-sm border border-slate-100 group-hover:border-slate-300 transition-all">
                <ArrowRight className="w-4 h-4 rotate-180" />
              </div>
              <span className="font-semibold">Back to Tools</span>
            </button>
            <h2 className="text-4xl font-extrabold text-slate-800 mb-4 tracking-tight">{activeTool}</h2>
            <p className="text-lg text-slate-500 mb-10">Upload your file to get started.</p>

            <FileUploader onFileSelect={handleFileSelect} />
          </div>
        )}

        {/* STAGE 3: CONFIGURE */}
        {stage === 'config' && (
          <div className="w-full max-w-5xl animate-in zoom-in-95 duration-300 flex justify-center">
            <ToolConfig
              toolName={activeTool}
              files={files}
              onBack={handleBack}
              onProcess={processTool}
              isProcessing={isProcessing}
            />
          </div>
        )}

        {/* STAGE 4: RESULT */}
        {stage === 'result' && (
          <div className="w-full max-w-2xl bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-blue-900/10 p-12 text-center animate-in zoom-in-50 mx-auto border border-white/50">
            {processingResult.status === 'success' ? (
              <div className="flex flex-col items-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-green-500/20 blur-xl rounded-full animate-pulse"></div>
                  <div className="relative w-24 h-24 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mb-8 shadow-xl shadow-green-500/30">
                    <CheckCircle className="w-12 h-12 text-white stroke-[3px]" />
                  </div>
                </div>
                <h2 className="text-3xl font-black text-slate-800 mb-4 tracking-tight">{processingResult.message}</h2>
                <p className="text-slate-500 mb-10 text-lg">Your file is ready for download.</p>

                <div className="flex flex-col sm:flex-row gap-4 w-full justify-center">
                  <a href={processingResult.downloadUrl} download className="group relative px-8 py-4 bg-slate-900 text-white rounded-xl font-bold shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all flex items-center justify-center gap-3 overflow-hidden">
                    <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                    <span className="relative">Download File</span>
                    <ArrowRight className="w-5 h-5 relative group-hover:translate-x-1 transition-transform" />
                  </a>
                  <button onClick={() => setStage('select')} className="px-8 py-4 bg-white border border-slate-200 text-slate-700 rounded-xl font-bold hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm hover:shadow-md">
                    Do Another Task
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mb-6">
                  <AlertCircle className="w-12 h-12 text-red-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-800 mb-2">Something went wrong</h2>
                <p className="text-red-500 mb-8 max-w-md mx-auto bg-red-50 p-4 rounded-lg font-mono text-sm">{processingResult.message}</p>
                <button onClick={() => setStage('select')} className="px-8 py-3 bg-slate-800 text-white rounded-xl font-bold hover:bg-slate-900 transition-all shadow-lg">
                  Try Again
                </button>
              </div>
            )}
          </div>
        )}

      </div>

      <footer className="w-full py-8 text-center mt-auto border-t border-slate-200/60 bg-white/30 backdrop-blur-md">
        <p className="font-bold text-slate-400 text-sm tracking-widest uppercase flex items-center justify-center gap-2">
          CREATED BY <span className="text-slate-800 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600"> KHALED ALFADHLI</span>
        </p>
      </footer>

    </main>
  );
}

function ToolCard({ icon, title, desc, onClick, color }: { icon: any, title: string, desc: string, onClick: () => void, color: string }) {
  const colorClasses: { [key: string]: string } = {
    blue: "group-hover:shadow-blue-500/30 group-hover:border-blue-200",
    purple: "group-hover:shadow-purple-500/30 group-hover:border-purple-200",
    pink: "group-hover:shadow-pink-500/30 group-hover:border-pink-200",
    green: "group-hover:shadow-green-500/30 group-hover:border-green-200",
    indigo: "group-hover:shadow-indigo-500/30 group-hover:border-indigo-200",
    yellow: "group-hover:shadow-yellow-500/30 group-hover:border-yellow-200",
  }

  return (
    <div onClick={onClick} className={`bg-white/60 p-8 rounded-3xl shadow-sm border border-white/80 transition-all duration-300 cursor-pointer hover:-translate-y-2 group ${colorClasses[color]}`}>
      <div className={`w-14 h-14 bg-white rounded-2xl flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform duration-300 border border-slate-50`}>
        {React.cloneElement(icon, { className: `w-7 h-7 ${icon.props.className}` })}
      </div>
      <h3 className="text-xl font-extrabold text-slate-800 mb-2">{title}</h3>
      <p className="text-sm font-medium text-slate-500 leading-relaxed">{desc}</p>
    </div>
  )
}
