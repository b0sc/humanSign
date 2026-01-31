"use client"

import React, { useState, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Loader2, FileText, Check, X, ShieldCheck, FileCheck, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface FileVerifierProps {
    onVerify: (document: File, humansign: File) => Promise<void>;
    isVerifying: boolean;
    result?: {
        status: "GENUINE" | "FORGED";
        confidence: number;
        details?: any;
    } | null;
}

export function FileVerifier({ onVerify, isVerifying, result }: FileVerifierProps) {
    const [documentFile, setDocumentFile] = useState<File | null>(null);
    const [humansignFile, setHumansignFile] = useState<File | null>(null);
    const docInputRef = useRef<HTMLInputElement>(null);
    const hsInputRef = useRef<HTMLInputElement>(null);

    const reset = () => {
        setDocumentFile(null);
        setHumansignFile(null);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e: React.DragEvent, type: 'doc' | 'hs') => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            if (type === 'doc') setDocumentFile(file);
            else setHumansignFile(file);
        }
    };

    return (
        <Card className="w-full shadow-2xl shadow-primary/5 border-border/60 bg-card/60 backdrop-blur-xl transition-all duration-300">
            <CardHeader className="pb-4 border-b border-border/40 bg-muted/20">
                <div className="flex items-center space-x-3">
                    <div className="p-2.5 bg-background rounded-xl border border-border/50 shadow-sm">
                        <ShieldCheck className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <CardTitle className="text-lg font-semibold">Document Verification</CardTitle>
                        <CardDescription className="text-sm mt-1">
                            Securely verify documents against their cryptographic signature.
                        </CardDescription>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="space-y-8 pt-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Document Upload Area */}
                    <div
                        className={cn(
                            "relative overflow-hidden group border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 h-[200px]",
                            documentFile
                                ? "border-primary/50 bg-primary/5 ring-1 ring-primary/20"
                                : "border-border/60 hover:border-primary/40 hover:bg-muted/30"
                        )}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, 'doc')}
                        onClick={() => docInputRef.current?.click()}
                    >
                        <input
                            type="file"
                            ref={docInputRef}
                            className="hidden"
                            onChange={(e) => e.target.files && setDocumentFile(e.target.files[0])}
                        />

                        <div className={cn(
                            "w-14 h-14 rounded-full flex items-center justify-center mb-4 transition-all duration-300",
                            documentFile ? "bg-primary text-primary-foreground scale-110 shadow-lg shadow-primary/20" : "bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary"
                        )}>
                            <FileText className="w-7 h-7" />
                        </div>

                        {documentFile ? (
                            <div className="z-10 animate-in fade-in zoom-in duration-300">
                                <p className="font-semibold text-sm truncate max-w-[140px] mx-auto bg-background/80 px-2 py-0.5 rounded-md border border-border/50">{documentFile.name}</p>
                                <div className="flex items-center justify-center gap-1.5 mt-2 text-primary font-medium text-xs">
                                    <Check className="w-3 h-3" /> Uploaded
                                </div>
                            </div>
                        ) : (
                            <div className="z-10 space-y-1">
                                <p className="font-medium text-sm text-foreground/80">Original Document</p>
                                <p className="text-xs text-muted-foreground">Select file</p>
                            </div>
                        )}
                    </div>

                    {/* Humansign Upload Area */}
                    <div
                        className={cn(
                            "relative overflow-hidden group border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 h-[200px]",
                            humansignFile
                                ? "border-primary/50 bg-primary/5 ring-1 ring-primary/20"
                                : "border-border/60 hover:border-primary/40 hover:bg-muted/30"
                        )}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, 'hs')}
                        onClick={() => hsInputRef.current?.click()}
                    >
                        <input
                            type="file"
                            ref={hsInputRef}
                            className="hidden"
                            accept=".humansign"
                            onChange={(e) => e.target.files && setHumansignFile(e.target.files[0])}
                        />
                        <div className={cn(
                            "w-14 h-14 rounded-full flex items-center justify-center mb-4 transition-all duration-300",
                            humansignFile ? "bg-primary text-primary-foreground scale-110 shadow-lg shadow-primary/20" : "bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary"
                        )}>
                            <FileCheck className="w-7 h-7" />
                        </div>
                        {humansignFile ? (
                            <div className="z-10 animate-in fade-in zoom-in duration-300">
                                <p className="font-semibold text-sm truncate max-w-[140px] mx-auto bg-background/80 px-2 py-0.5 rounded-md border border-border/50">{humansignFile.name}</p>
                                <div className="flex items-center justify-center gap-1.5 mt-2 text-primary font-medium text-xs">
                                    <Check className="w-3 h-3" /> Uploaded
                                </div>
                            </div>
                        ) : (
                            <div className="z-10 space-y-1">
                                <p className="font-medium text-sm text-foreground/80">Signature File</p>
                                <p className="text-xs text-muted-foreground">Select .humansign</p>
                            </div>
                        )}
                    </div>
                </div>

                {result && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={cn(
                            "p-5 rounded-xl border-l-4 flex items-center gap-5 shadow-sm",
                            result.status === "GENUINE"
                                ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-l-emerald-500 border-y border-r border-emerald-200/50 dark:border-emerald-800/50"
                                : "bg-rose-50/50 dark:bg-rose-950/20 border-l-rose-500 border-y border-r border-rose-200/50 dark:border-rose-800/50"
                        )}
                    >
                        <div className={cn(
                            "w-12 h-12 rounded-full flex items-center justify-center border-4",
                            result.status === "GENUINE"
                                ? "bg-emerald-100 text-emerald-600 border-emerald-50 dark:bg-emerald-900/40 dark:text-emerald-400 dark:border-white/5"
                                : "bg-rose-100 text-rose-600 border-rose-50 dark:bg-rose-900/40 dark:text-rose-400 dark:border-white/5"
                        )}>
                            {result.status === "GENUINE" ? (
                                <Check className="w-6 h-6 stroke-[3px]" />
                            ) : (
                                <X className="w-6 h-6 stroke-[3px]" />
                            )}
                        </div>

                        <div className="flex-1">
                            <div className="flex items-center justify-between">
                                <h4 className={cn("font-bold text-lg", result.status === "GENUINE" ? "text-emerald-950 dark:text-emerald-100" : "text-rose-950 dark:text-rose-100")}>
                                    {result.status === "GENUINE" ? "Document Verified" : "Verification Failed"}
                                </h4>
                                {result.details?.document_hash_valid && (
                                    <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-100/50 dark:bg-emerald-900/30 px-2 py-0.5 rounded-full">
                                        <ShieldCheck className="w-3 h-3" /> Integrity Valid
                                    </div>
                                )}
                            </div>

                            <div className="grid grid-cols-2 gap-x-8 gap-y-1 mt-2 text-sm opacity-80">
                                <div className="flex justify-between">
                                    <span>Confidence:</span>
                                    <span className="font-medium font-mono">{(result.confidence * 100).toFixed(1)}%</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Subject:</span>
                                    <span className="font-medium">{result.details?.subject || 'Unknown'}</span>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </CardContent>
            <CardFooter className="flex justify-between items-center bg-muted/20 p-6 border-t border-border/40">
                <Button variant="ghost" onClick={reset} disabled={isVerifying} className="text-muted-foreground hover:text-foreground">
                    Discard
                </Button>
                <Button
                    size="lg"
                    onClick={() => humansignFile && documentFile && onVerify(documentFile, humansignFile)}
                    disabled={!documentFile || !humansignFile || isVerifying}
                    className="min-w-[180px] font-semibold text-base shadow-lg shadow-primary/25 transition-all hover:shadow-primary/40"
                >
                    {isVerifying ? (
                        <>
                            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                            Verifying...
                        </>
                    ) : (
                        "Verify Document"
                    )}
                </Button>
            </CardFooter>
        </Card>
    );
}
