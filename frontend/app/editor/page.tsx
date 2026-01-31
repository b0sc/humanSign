"use client"

import React, { useState, useRef, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import {
    Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight,
    Download, FileText, Loader2, ChevronDown,
    ArrowLeft, Printer, Share2, Info, X, Check
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import jsPDF from 'jspdf';

const API_URL = "/api/v1";

interface KeystrokeEvent {
    key: string;
    timestamp: number;
    duration: number;
    pressure: number | null;
}

export default function EditorPage() {
    const [content, setContent] = useState("");
    const [documentTitle, setDocumentTitle] = useState("Untitled Document");
    const [events, setEvents] = useState<KeystrokeEvent[]>([]);
    const [keyDownMap, setKeyDownMap] = useState<Record<string, number>>({});
    const [isVerifying, setIsVerifying] = useState(false);
    const [showDownloadMenu, setShowDownloadMenu] = useState(false);

    // Paste detection state
    const [typedCharCount, setTypedCharCount] = useState(0);
    const [pastedCharCount, setPastedCharCount] = useState(0);
    const [showStats, setShowStats] = useState(false);
    const [verificationResult, setVerificationResult] = useState<any>(null);
    const [showVerificationModal, setShowVerificationModal] = useState(false);

    const editorRef = useRef<HTMLDivElement>(null);
    const pieChartRef = useRef<HTMLCanvasElement>(null);

    // --- Keystroke Logic ---
    const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
        const now = performance.now();
        if (e.repeat) return;
        setKeyDownMap(prev => ({ ...prev, [e.code]: now }));
    };

    const handleKeyUp = (e: React.KeyboardEvent<HTMLDivElement>) => {
        const now = performance.now();
        const startTime = keyDownMap[e.code];

        if (startTime) {
            const duration = now - startTime;
            const newEvent: KeystrokeEvent = {
                key: e.key,
                timestamp: startTime,
                duration: duration,
                pressure: null
            };

            setEvents(prev => [...prev, newEvent]);
            const newMap = { ...keyDownMap };
            delete newMap[e.code];
            setKeyDownMap(newMap);

            // Track typed characters (excluding special keys)
            if (e.key.length === 1) {
                setTypedCharCount(prev => prev + 1);
            }
        }
    };

    // --- Paste Detection ---
    const handlePaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
        const pastedText = e.clipboardData.getData('text');
        const pastedLength = pastedText.length;
        setPastedCharCount(prev => prev + pastedLength);

        // Show stats when paste is detected
        setShowStats(true);
    };

    // --- Formatting Logic ---
    const applyFormat = (command: string, value?: string) => {
        document.execCommand(command, false, value);
        editorRef.current?.focus();
    };

    // --- Helper to sanitize filename ---
    const sanitizeFilename = (name: string): string => {
        return name.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'document';
    };

    // --- Calculate percentages ---
    const totalChars = typedCharCount + pastedCharCount;
    const typedPercentage = totalChars > 0 ? Math.round((typedCharCount / totalChars) * 100) : 0;
    const pastedPercentage = totalChars > 0 ? Math.round((pastedCharCount / totalChars) * 100) : 0;

    // --- Draw Pie Chart ---
    useEffect(() => {
        if (!showVerificationModal || !pieChartRef.current || !verificationResult?.details?.content_analysis) return;

        const canvas = pieChartRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const analysis = verificationResult.details.content_analysis;
        const typed = analysis.typed_percentage || 0;
        const pasted = analysis.pasted_percentage || 0;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Set canvas size
        const size = 180;
        const centerX = size / 2;
        const centerY = size / 2;
        const radius = size / 2 - 10;

        // Draw pie chart
        let currentAngle = -Math.PI / 2; // Start from top

        // Typed slice (green)
        if (typed > 0) {
            const sliceAngle = (typed / 100) * 2 * Math.PI;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = '#10b981';
            ctx.fill();
            currentAngle += sliceAngle;
        }

        // Pasted slice (orange)
        if (pasted > 0) {
            const sliceAngle = (pasted / 100) * 2 * Math.PI;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = '#f59e0b';
            ctx.fill();
        }

        // Draw white circle in center for donut effect
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius * 0.6, 0, 2 * Math.PI);
        ctx.fillStyle = '#ffffff';
        ctx.fill();

        // Draw center text
        ctx.fillStyle = '#1f1f1f';
        ctx.font = 'bold 24px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${typed}%`, centerX, centerY - 8);
        ctx.font = '12px Inter, sans-serif';
        ctx.fillStyle = '#666';
        ctx.fillText('Typed', centerX, centerY + 12);

    }, [showVerificationModal, verificationResult]);


    // --- Automatic Verification on Download ---
    const handleDownload = async (format: 'pdf' | 'txt') => {
        const currentText = editorRef.current?.innerText || "";

        if (events.length > 5) {
            setIsVerifying(true);
            try {
                const response = await fetch(`${API_URL}/verify`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        keystroke_events: events,
                        typed_char_count: typedCharCount,
                        pasted_char_count: pastedCharCount
                    })
                });
                const data = await response.json();
                setVerificationResult(data);
                setShowVerificationModal(true);
            } catch (e) {
                console.error("Verification unavailable during download", e);
            } finally {
                setIsVerifying(false);
            }
        }

        if (format === 'pdf') {
            const doc = new jsPDF();
            doc.setFont("times", "roman");

            const splitText = doc.splitTextToSize(currentText, 170);
            doc.text(splitText, 20, 20);

            doc.setFontSize(10);
            doc.setTextColor(150);
            doc.text(`Generated by HumanSign • Secure Digital Identity`, 20, 280);

            const filename = sanitizeFilename(documentTitle) + '.pdf';
            doc.save(filename);
        } else {
            const element = document.createElement("a");
            const file = new Blob([currentText], { type: 'text/plain' });
            element.href = URL.createObjectURL(file);
            const filename = sanitizeFilename(documentTitle) + '.txt';
            element.download = filename;
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
        }
        setShowDownloadMenu(false);
    };

    return (
        <div className="min-h-screen bg-[#F8F9FA] flex flex-col font-sans text-[#333]">
            {/* Professional Google Docs-like Header */}
            <header className="bg-white px-4 py-3 flex items-center justify-between sticky top-0 z-50 shadow-[0_1px_2px_rgba(0,0,0,0.05)] border-b border-gray-100">
                <div className="flex items-center gap-4">
                    <Link href="/" passHref>
                        <div className="p-2.5 hover:bg-gray-100 rounded-full cursor-pointer transition-colors text-gray-500 hover:text-gray-700">
                            <ArrowLeft className="w-5 h-5" />
                        </div>
                    </Link>

                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center shadow-sm">
                            <FileText className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <input
                                type="text"
                                value={documentTitle}
                                onChange={(e) => setDocumentTitle(e.target.value)}
                                className="block w-full font-medium text-gray-800 text-lg border-none focus:ring-0 p-0 hover:bg-gray-50 rounded px-1.5 transition-colors -ml-1.5"
                            />
                            <div className="flex gap-4 text-[13px] text-gray-500 font-medium pt-0.5">
                                <span className="hover:text-gray-800 cursor-pointer transition-colors">File</span>
                                <span className="hover:text-gray-800 cursor-pointer transition-colors">Edit</span>
                                <span className="hover:text-gray-800 cursor-pointer transition-colors">View</span>
                                <span className="hover:text-gray-800 cursor-pointer transition-colors">Insert</span>
                                <span className="hover:text-gray-800 cursor-pointer transition-colors">Format</span>
                                <span className="hover:text-gray-800 cursor-pointer transition-colors">Tools</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* Content Stats Indicator */}
                    {totalChars > 0 && (
                        <div className="relative group">
                            <button
                                onClick={() => setShowStats(!showStats)}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors text-xs font-medium text-gray-700"
                            >
                                <Info className="w-3.5 h-3.5" />
                                {typedPercentage}% Typed
                            </button>

                            {showStats && (
                                <div className="absolute top-full right-0 mt-2 w-72 bg-white rounded-lg shadow-xl border border-gray-100 p-4 z-50 animate-in fade-in zoom-in-95 duration-200">
                                    <div className="text-sm font-semibold text-gray-800 mb-3">Content Analysis</div>

                                    <div className="space-y-3">
                                        <div>
                                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                                                <span>Typed Characters</span>
                                                <span className="font-semibold text-green-600">{typedCharCount} ({typedPercentage}%)</span>
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div
                                                    className="bg-green-500 h-2 rounded-full transition-all duration-300"
                                                    style={{ width: `${typedPercentage}%` }}
                                                />
                                            </div>
                                        </div>

                                        <div>
                                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                                                <span>Pasted Characters</span>
                                                <span className="font-semibold text-orange-600">{pastedCharCount} ({pastedPercentage}%)</span>
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div
                                                    className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                                                    style={{ width: `${pastedPercentage}%` }}
                                                />
                                            </div>
                                        </div>

                                        <div className="pt-2 border-t border-gray-100">
                                            <div className="flex justify-between text-xs">
                                                <span className="text-gray-500">Total Characters</span>
                                                <span className="font-semibold text-gray-800">{totalChars}</span>
                                            </div>
                                            <div className="flex justify-between text-xs mt-1">
                                                <span className="text-gray-500">Keystroke Events</span>
                                                <span className="font-semibold text-gray-800">{events.length}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="flex items-center gap-1 mr-2 text-gray-400">
                        <Button variant="ghost" size="icon" className="text-gray-500 hover:bg-gray-100"><Share2 className="w-5 h-5" /></Button>
                        <Button variant="ghost" size="icon" className="text-gray-500 hover:bg-gray-100"><Printer className="w-5 h-5" /></Button>
                    </div>

                    <div className="relative">
                        <Button
                            className="gap-2 rounded-full bg-[#1a73e8] hover:bg-[#1557b0] text-white px-6 font-medium shadow-sm transition-all h-[36px]"
                            onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                        >
                            <Download className="w-4 h-4" />
                            Download
                            <ChevronDown className="w-3 h-3 opacity-70 ml-1" />
                        </Button>

                        {showDownloadMenu && (
                            <div className="absolute top-full right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-100 py-2 z-50 animate-in fade-in zoom-in-95 duration-200">
                                <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Export As</div>
                                <button onClick={() => handleDownload('pdf')} className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 flex items-center gap-3 text-gray-700 transition-colors">
                                    <div className="w-8 h-8 rounded bg-red-50 flex items-center justify-center text-red-600 font-bold text-[10px]">PDF</div>
                                    <span className="font-medium">PDF Document</span>
                                </button>
                                <button onClick={() => handleDownload('txt')} className="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 flex items-center gap-3 text-gray-700 transition-colors">
                                    <div className="w-8 h-8 rounded bg-gray-100 flex items-center justify-center text-gray-600 font-bold text-[10px]">TXT</div>
                                    <span className="font-medium">Plain Text</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Sub-toolbar for formatting */}
            <div className="bg-[#fcfdfd] border-b border-gray-200 px-4 py-2 flex items-center justify-center gap-2 sticky top-[65px] z-40 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
                <div className="bg-white border border-gray-200 rounded-full px-4 py-1.5 flex items-center gap-3 shadow-sm text-gray-600">
                    <Button variant="ghost" size="icon" className="h-7 w-7"><ArrowLeft className="w-3 h-3" /></Button>
                    <div className="w-px h-4 bg-gray-200" />
                    <select onChange={(e) => applyFormat('formatBlock', e.target.value)} className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer hover:bg-gray-50 rounded">
                        <option value="p">Normal text</option>
                        <option value="h1">Heading 1</option>
                        <option value="h2">Heading 2</option>
                    </select>
                    <div className="w-px h-4 bg-gray-200" />
                    <select onChange={(e) => applyFormat('fontName', e.target.value)} className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer hover:bg-gray-50 rounded w-20">
                        <option value="Arial">Arial</option>
                        <option value="Times New Roman">Times</option>
                        <option value="Inter, sans-serif">Inter</option>
                        <option value="Courier New">Courier</option>
                    </select>
                    <div className="w-px h-4 bg-gray-200" />
                    <div className="flex items-center gap-1">
                        <Button onMouseDown={(e) => e.preventDefault()} onClick={() => applyFormat('bold')} variant="ghost" size="icon" className="h-7 w-7 rounded hover:bg-gray-100"><Bold className="w-3.5 h-3.5" /></Button>
                        <Button onMouseDown={(e) => e.preventDefault()} onClick={() => applyFormat('italic')} variant="ghost" size="icon" className="h-7 w-7 rounded hover:bg-gray-100"><Italic className="w-3.5 h-3.5" /></Button>
                        <Button onMouseDown={(e) => e.preventDefault()} onClick={() => applyFormat('underline')} variant="ghost" size="icon" className="h-7 w-7 rounded hover:bg-gray-100"><Underline className="w-3.5 h-3.5" /></Button>
                    </div>
                    <div className="w-px h-4 bg-gray-200" />
                    <div className="flex items-center gap-1">
                        <Button onMouseDown={(e) => e.preventDefault()} onClick={() => applyFormat('justifyLeft')} variant="ghost" size="icon" className="h-7 w-7 rounded hover:bg-gray-100"><AlignLeft className="w-3.5 h-3.5" /></Button>
                        <Button onMouseDown={(e) => e.preventDefault()} onClick={() => applyFormat('justifyCenter')} variant="ghost" size="icon" className="h-7 w-7 rounded hover:bg-gray-100"><AlignCenter className="w-3.5 h-3.5" /></Button>
                        <Button onMouseDown={(e) => e.preventDefault()} onClick={() => applyFormat('justifyRight')} variant="ghost" size="icon" className="h-7 w-7 rounded hover:bg-gray-100"><AlignRight className="w-3.5 h-3.5" /></Button>
                    </div>
                </div>
            </div>

            {/* Editor Canvas */}
            <main className="flex-1 overflow-y-auto p-8 flex justify-center cursor-text bg-[#F8F9FA]" onClick={() => editorRef.current?.focus()}>
                <div className="w-full max-w-[816px] bg-white min-h-[1056px] shadow-[0_2px_15px_rgba(0,0,0,0.08)] border border-gray-200/60 transition-shadow duration-300 relative animate-in fade-in slide-in-from-bottom-4 duration-500 group">
                    <div
                        ref={editorRef}
                        contentEditable
                        onInput={(e) => setContent(e.currentTarget.innerText)}
                        onKeyDown={handleKeyDown}
                        onKeyUp={handleKeyUp}
                        onPaste={handlePaste}
                        className="w-full h-full min-h-[1056px] outline-none text-[12pt] leading-[1.6] text-[#1f1f1f] font-serif p-[72px] sm:p-[96px] empty:before:content-[attr(data-placeholder)] empty:before:text-gray-300"
                        data-placeholder="Start typing..."
                        suppressContentEditableWarning
                    />

                    {/* Status Indicator */}
                    {isVerifying && (
                        <div className="absolute top-4 right-4 text-xs font-medium text-blue-600 flex items-center gap-2">
                            <Loader2 className="w-3 h-3 animate-spin" /> Saving...
                        </div>
                    )}
                    <div className="absolute bottom-4 left-0 w-full text-center text-[10px] text-gray-300 select-none opacity-0 group-hover:opacity-100 transition-opacity">
                        Page 1
                    </div>
                </div>
            </main>

            {/* Verification Results Modal */}
            {showVerificationModal && verificationResult && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] animate-in fade-in duration-200" onClick={() => setShowVerificationModal(false)}>
                    <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-6 animate-in zoom-in-95 duration-200" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-bold text-gray-800">Verification Results</h3>
                            <button onClick={() => setShowVerificationModal(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            {/* Verification Status */}
                            <div className={cn(
                                "p-4 rounded-lg border-2",
                                verificationResult.verification_result === "GENUINE"
                                    ? "bg-green-50 border-green-200"
                                    : "bg-red-50 border-red-200"
                            )}>
                                <div className="flex items-center gap-2 mb-2">
                                    {verificationResult.verification_result === "GENUINE" ? (
                                        <Check className="w-5 h-5 text-green-600" />
                                    ) : (
                                        <X className="w-5 h-5 text-red-600" />
                                    )}
                                    <span className={cn(
                                        "font-bold text-lg",
                                        verificationResult.verification_result === "GENUINE" ? "text-green-700" : "text-red-700"
                                    )}>
                                        {verificationResult.verification_result}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600">
                                    Confidence: {(verificationResult.confidence_score * 100).toFixed(2)}%
                                </p>
                            </div>

                            {/* Content Analysis */}
                            {verificationResult.details?.content_analysis && (
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <h4 className="font-semibold text-gray-800 mb-3">Content Analysis</h4>

                                    {/* Pie Chart */}
                                    <div className="flex justify-center mb-4">
                                        <div className="relative">
                                            <canvas
                                                ref={pieChartRef}
                                                width={180}
                                                height={180}
                                                className="drop-shadow-md"
                                            />
                                            <div className="flex justify-center gap-4 mt-3">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                                    <span className="text-xs text-gray-600">Typed</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                                                    <span className="text-xs text-gray-600">Pasted</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <div>
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-gray-600">Typed Content</span>
                                                <span className="font-semibold text-green-600">
                                                    {verificationResult.details.content_analysis.typed_percentage}%
                                                </span>
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div
                                                    className="bg-green-500 h-2 rounded-full transition-all"
                                                    style={{ width: `${verificationResult.details.content_analysis.typed_percentage}%` }}
                                                />
                                            </div>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {verificationResult.details.content_analysis.typed_chars} characters
                                            </p>
                                        </div>

                                        <div>
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-gray-600">Pasted Content</span>
                                                <span className="font-semibold text-orange-600">
                                                    {verificationResult.details.content_analysis.pasted_percentage}%
                                                </span>
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div
                                                    className="bg-orange-500 h-2 rounded-full transition-all"
                                                    style={{ width: `${verificationResult.details.content_analysis.pasted_percentage}%` }}
                                                />
                                            </div>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {verificationResult.details.content_analysis.pasted_chars} characters
                                            </p>
                                        </div>

                                        <div className="pt-3 border-t border-gray-200">
                                            <div className="flex justify-between text-sm">
                                                <span className="text-gray-600">Authenticity Score</span>
                                                <span className="font-bold text-blue-600">
                                                    {verificationResult.details.content_analysis.authenticity_score}%
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Keystroke Stats */}
                            <div className="bg-blue-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-gray-800 mb-2">Keystroke Analysis</h4>
                                <div className="grid grid-cols-2 gap-3 text-sm">
                                    <div>
                                        <p className="text-gray-600">Events Captured</p>
                                        <p className="font-bold text-gray-800">{verificationResult.details?.keystroke_count || 0}</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-600">Features Extracted</p>
                                        <p className="font-bold text-gray-800">{verificationResult.details?.features_extracted || 0}</p>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => setShowVerificationModal(false)}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
