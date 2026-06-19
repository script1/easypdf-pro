"use client";
import React, { useState } from 'react';
import { FileText, Layers, Scissors, Image, Shield, Zap, ArrowRight, CheckCircle, AlertCircle, Sparkles, Lock, Droplets, RotateCw, Trash2, ArrowUpDown, Unlock, FileImage, Type } from 'lucide-react';
import { FileUploader } from './components/FileUploader';
import { ToolConfig } from './components/ToolConfig';

const API_URL = 'https://easypdf-pro.onrender.com';

const TOOLS = [
  { id: 'PDF to Word',      icon: <FileText className="text-blue-500" />,    title: 'PDF to Word',      desc: 'Convert PDF to editable Word',   color: 'blue' },
  { id: 'Merge PDF',        icon: <Layers className="text-purple-500" />,    title: 'Merge PDF',        desc: 'Combine multiple PDFs',          color: 'purple' },
  { id: 'Split PDF',        icon: <Scissors className="text-pink-500" />,    title: 'Split PDF',        desc: 'Extract specific pages',         color: 'pink' },
  { id: 'PDF to JPG',       icon: <Image className="text-green-500" />,      title: 'PDF to JPG',       desc: 'Convert pages to images',        color: 'green' },
  { id: 'Protect PDF',      icon: <Shield className="text-indigo-500" />,    title: 'Protect PDF',      desc: 'Add password security',          color: 'indigo' },
  { id: 'Compress',         icon: <Zap className="text-yellow-500" />,       title: 'Compress',         desc: 'Reduce file size',               color: 'yellow' },
  { id: 'Watermark',        icon: <Droplets className="text-cyan-500" />,    title: 'Watermark',        desc: 'Add text watermark',             color: 'cyan' },
  { id: 'Rotate PDF',       icon: <RotateCw className="text-orange-500" />,  title: 'Rotate PDF',       desc: 'Rotate pages 90°/180°/270°',    color: 'orange' },
  { id: 'Delete Pages',     icon: <Trash2 className="text-red-500" />,       title: 'Delete Pages',     desc: 'Remove specific pages',          color: 'red' },
  { id: 'Reorder Pages',    icon: <ArrowUpDown className="text-violet-500" />, title: 'Reorder Pages', desc: 'Change page order',              color: 'violet' },
  { id: 'Unlock PDF',       icon: <Unlock className="text-teal-500" />,      title: 'Unlock PDF',       desc: 'Remove password protection',     color: 'teal' },
  { id: 'Images to PDF',    icon: <FileImage className="text-rose-500" />,   title: 'Images to PDF',    desc: 'Convert images to PDF',          color: 'rose' },
  { id: 'Extract Text',     icon: <Type className="text-amber-500" />,       title: 'Extract Text',     desc: 'Extract text from PDF',          color: 'amber' },
];

const colorMap: Record<string, string> = {
  blue:   'group-hover:shadow-blue-500/30   group-hover:border-blue-200',
  purple: 'group-hover:shadow-purple-500/30 group-hover:border-purple-200',
  pink:   'group-hover:shadow-pink-500/30   group-hover:border-pink-200',
  green:  'group-hover:shadow-green-500/30  group-hover:border-green-200',
  indigo: 'group-hover:shadow-indigo-500/30 group-hover:border-indigo-200',
  yellow: 'group-hover:shadow-yellow-500/30 group-hover:border-yellow-200',
  cyan:   'group-hover:shadow-cyan-500/30   group-hover:border-cyan-200',
  orange: 'group-hover:shadow-orange-500/30 group-hover:border-orange-200',
  red:    'group-hover:shadow-red-500/30    group-hover:border-red-200',
  violet: 'group-hover:shadow-violet-500/30 group-hover:border-violet-200',
  teal:   'group-hover:shadow-teal-500/30   group-hover:border-teal-200',
  rose:   'group-hover:shadow-rose-500/30   group-hover:border-rose-200',
  amber:  'group-hover:shadow-amber-500/30  group-hover:border-amber-200',
};

export default function Home() {
  const [activeTool, setActiveTool] = useState('');
  const [stage, setStage] = useState<'select' | 'upload' | 'config' | 'result'>('select');
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<{ message: string; downloadUrl: string; status: 'success' | 'error' | 'idle' }>({ message: '', downloadUrl: '', status: 'idle' });
  const [isProcessing, setIsProcessing] = useState(false);

  const handleToolClick = (id: string) => {
    setActiveTool(id);
    setFiles([]);
    setResult({ message: '', downloadUrl: '', status: 'idle' });
    if (id === 'Merge PDF') {
      setStage('upload');
    } else {
      setStage('upload');
    }
  };

  const handleFileSelect = (file: File | null) => {
    if (file) {
      setFiles([file]);
      setStage('config');
    }
  };

  const handleFilesSelect = (selectedFiles: File[]) => {
    if (selectedFiles.length > 0) {
      setFiles(selectedFiles);
      setStage('config');
    }
  };

  const handleBack = () => {
    if (stage === 'config') setStage('upload');
    else if (stage === 'upload') { setStage('select'); setActiveTool(''); }
    else if (stage === 'result') setStage('select');
  };

  const processTool = async (config: any) => {
    setIsProcessing(true);
    setResult({ message: 'Processing...', downloadUrl: '', status: 'idle' });

    try {
      // ── PDF to Word ──────────────────────────────────────────────
      if (activeTool === 'PDF to Word') {
        const fd = new FormData();
        fd.append('file', files[0]);
        const upRes = await fetch(`${API_URL}/upload/`, { method: 'POST', body: fd });
        if (!upRes.ok) throw new Error('Upload failed');
        const upData = await upRes.json();
        const convRes = await fetch(`${API_URL}/convert/pdf-to-word/?file_id=${upData.file_id}`, { method: 'POST' });
        if (!convRes.ok) throw new Error('Conversion failed');
        const data = await convRes.json();
        setResult({ message: 'Conversion Successful!', downloadUrl: `${API_URL}${data.download_url}`, status: 'success' });
        setStage('result');
        return;
      }

      // ── Merge PDF ────────────────────────────────────────────────
      if (activeTool === 'Merge PDF') {
        const fd = new FormData();
        files.forEach(f => fd.append('files', f));
        const res = await fetch(`${API_URL}/merge/`, { method: 'POST', body: fd });
        if (!res.ok) throw new Error('Merge failed');
        const data = await res.json();
        setResult({ message: 'Merge Successful!', downloadUrl: `${API_URL}${data.download_url}`, status: 'success' });
        setStage('result');
        return;
      }

      // ── Images to PDF ────────────────────────────────────────────
      if (activeTool === 'Images to PDF') {
        const fd = new FormData();
        files.forEach(f => fd.append('files', f));
        const res = await fetch(`${API_URL}/convert/images-to-pdf/`, { method: 'POST', body: fd });
        if (!res.ok) throw new Error('Conversion failed');
        const data = await res.json();
        setResult({ message: 'Conversion Successful!', downloadUrl: `${API_URL}${data.download_url}`, status: 'success' });
        setStage('result');
        return;
      }

      // ── Single-file tools ────────────────────────────────────────
      const fd = new FormData();
      fd.append('file', files[0]);

      let endpoint = '';
      if (activeTool === 'Split PDF')    { endpoint = '/split/';            if (config.selectedPages?.length) fd.append('pages', config.selectedPages.join(',')); }
      if (activeTool === 'PDF to JPG')   { endpoint = '/convert/pdf-to-jpg/'; if (config.selectedPages?.length) fd.append('pages', config.selectedPages.join(',')); }
      if (activeTool === 'Protect PDF')  { endpoint = '/protect/';          fd.append('password', config.password); }
      if (activeTool === 'Unlock PDF')   { endpoint = '/unlock/';           fd.append('password', config.password); }
      if (activeTool === 'Compress')     { endpoint = '/compress/'; }
      if (activeTool === 'Watermark')    { endpoint = '/watermark/';        fd.append('text', config.watermarkText); fd.append('opacity', '0.3'); }
      if (activeTool === 'Rotate PDF')   { endpoint = '/rotate/';           fd.append('angle', config.angle); if (config.selectedPages?.length) fd.append('pages', config.selectedPages.join(',')); }
      if (activeTool === 'Delete Pages') { endpoint = '/delete-pages/';     fd.append('pages', config.selectedPages.join(',')); }
      if (activeTool === 'Reorder Pages'){ endpoint = '/reorder-pages/';    fd.append('order', config.pageOrder); }
      if (activeTool === 'Extract Text') { endpoint = '/extract-text/'; }

      if (!endpoint) throw new Error('Unknown tool');

      const res = await fetch(`${API_URL}${endpoint}`, { method: 'POST', body: fd });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Processing failed');
      }
      const data = await res.json();

      setResult({
        message: data.message || 'Success!',
        downloadUrl: data.download_url ? `${API_URL}${data.download_url}` : '',
        status: 'success',
      });
      setStage('result');

    } catch (error: any) {
      setResult({ message: error.message || 'Error occurred', downloadUrl: '', status: 'error' });
      setStage('result');
    } finally {
      setIsProcessing(false);
    }
  };

  const needsMultipleFiles = activeTool === 'Merge PDF' || activeTool === 'Images to PDF';

  return (
    <main className="min-h-screen flex flex-col relative overflow-hidden bg-slate-50 font-sans">

      {/* Background */}
      <div className="absolute inset-0 -z-10 bg-[#f8fafc]">
        <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] rounded-full bg-gradient-to-tr from-purple-200/40 to-blue-200/40 blur-[120px]" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[800px] h-[800px] rounded-full bg-gradient-to-tr from-blue-200/40 to-pink-200/40 blur-[120px]" />
      </div>

      {/* Header */}
      <header className="w-full flex justify-center py-6 sticky top-0 z-50 bg-white/5 backdrop-blur-sm border-b border-white/10">
        <div onClick={() => { setStage('select'); setActiveTool(''); }}
          className="cursor-pointer flex items-center gap-3 hover:scale-105 transition-transform group">
          <div className="w-10 h-10 bg-gradient-to-br from-slate-900 to-slate-700 rounded-xl flex items-center justify-center text-white shadow-xl">
            <Zap className="w-6 h-6 fill-yellow-400 text-yellow-400" />
          </div>
          <span className="text-2xl font-black tracking-tighter text-slate-800">EASYPDF</span>
        </div>
      </header>

      <div className="flex-grow flex flex-col items-center justify-center p-4 w-full max-w-7xl mx-auto">

        {/* STAGE: SELECT */}
        {stage === 'select' && (
          <div className="w-full animate-in fade-in slide-in-from-bottom-8 duration-500">
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 border border-white/50 backdrop-blur-md shadow-sm mb-6 text-sm font-semibold text-slate-600">
                <Sparkles className="w-4 h-4 text-purple-500" />
                <span>Simple. Fast. Secure.</span>
              </div>
              <h1 className="text-5xl md:text-7xl font-black text-slate-900 mb-6 tracking-tight leading-tight">
                Everything you need <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600">
                  for your PDFs
                </span>
              </h1>
              <p className="text-xl text-slate-500 max-w-2xl mx-auto">
                13 powerful tools. All in one place.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 px-4">
              {TOOLS.map(t => (
                <ToolCard key={t.id} icon={t.icon} title={t.title} desc={t.desc} color={t.color} onClick={() => handleToolClick(t.id)} />
              ))}
            </div>
          </div>
        )}

        {/* STAGE: UPLOAD */}
        {stage === 'upload' && (
          <div className="w-full max-w-3xl text-center animate-in fade-in slide-in-from-bottom-8">
            <button onClick={handleBack} className="mb-8 group flex items-center justify-center gap-2 text-slate-500 hover:text-slate-900 transition-colors mx-auto">
              <div className="p-2 rounded-full bg-white shadow-sm border border-slate-100 group-hover:border-slate-300 transition-all">
                <ArrowRight className="w-4 h-4 rotate-180" />
              </div>
              <span className="font-semibold">Back to Tools</span>
            </button>
            <h2 className="text-4xl font-extrabold text-slate-800 mb-4 tracking-tight">{activeTool}</h2>
            <p className="text-lg text-slate-500 mb-10">
              {needsMultipleFiles ? 'Upload your files to get started.' : 'Upload your file to get started.'}
            </p>
            <FileUploader
              onFileSelect={needsMultipleFiles ? undefined : handleFileSelect}
              onFilesSelect={needsMultipleFiles ? handleFilesSelect : undefined}
              multiple={needsMultipleFiles}
              accept={activeTool === 'Images to PDF' ? 'image/*' : '.pdf'}
            />
          </div>
        )}

        {/* STAGE: CONFIG */}
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

        {/* STAGE: RESULT */}
        {stage === 'result' && (
          <div className="w-full max-w-2xl bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-blue-900/10 p-12 text-center animate-in zoom-in-50 mx-auto border border-white/50">
            {result.status === 'success' ? (
              <div className="flex flex-col items-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-green-500/20 blur-xl rounded-full animate-pulse" />
                  <div className="relative w-24 h-24 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mb-8 shadow-xl shadow-green-500/30">
                    <CheckCircle className="w-12 h-12 text-white stroke-[3px]" />
                  </div>
                </div>
                <h2 className="text-3xl font-black text-slate-800 mb-4 tracking-tight">{result.message}</h2>
                <p className="text-slate-500 mb-10 text-lg">Your file is ready for download.</p>
                <div className="flex flex-col sm:flex-row gap-4 w-full justify-center">
                  {result.downloadUrl && (
                    <a href={result.downloadUrl} download
                      className="group relative px-8 py-4 bg-slate-900 text-white rounded-xl font-bold shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all flex items-center justify-center gap-3 overflow-hidden">
                      <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                      <span className="relative">Download File</span>
                      <ArrowRight className="w-5 h-5 relative group-hover:translate-x-1 transition-transform" />
                    </a>
                  )}
                  <button onClick={() => setStage('select')}
                    className="px-8 py-4 bg-white border border-slate-200 text-slate-700 rounded-xl font-bold hover:bg-slate-50 transition-all shadow-sm">
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
                <p className="text-red-500 mb-8 max-w-md mx-auto bg-red-50 p-4 rounded-lg font-mono text-sm">{result.message}</p>
                <button onClick={() => setStage('select')}
                  className="px-8 py-3 bg-slate-800 text-white rounded-xl font-bold hover:bg-slate-900 transition-all shadow-lg">
                  Try Again
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <footer className="w-full py-8 text-center mt-auto border-t border-slate-200/60 bg-white/30 backdrop-blur-md">
        <p className="font-bold text-slate-400 text-sm tracking-widest uppercase flex items-center justify-center gap-2">
          CREATED BY <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 ml-1"> KHALED ALFADHLI</span>
        </p>
      </footer>

    </main>
  );
}

function ToolCard({ icon, title, desc, onClick, color }: { icon: any; title: string; desc: string; onClick: () => void; color: string }) {
  return (
    <div onClick={onClick}
      className={`bg-white/60 p-8 rounded-3xl shadow-sm border border-white/80 transition-all duration-300 cursor-pointer hover:-translate-y-2 group shadow-md ${colorMap[color] ?? ''}`}>
      <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform duration-300 border border-slate-50">
        {React.cloneElement(icon, { className: `w-7 h-7 ${icon.props.className}` })}
      </div>
      <h3 className="text-xl font-extrabold text-slate-800 mb-2">{title}</h3>
      <p className="text-sm font-medium text-slate-500 leading-relaxed">{desc}</p>
    </div>
  );
}
