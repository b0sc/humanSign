"use client"

import React, { useState, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Loader2, Check, X, RefreshCcw, Keyboard, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface KeystrokeEvent {
    key: string;
    timestamp: number;
    duration: number;
    pressure: number | null;
}

interface KeystrokeRecorderProps {
    onVerify: (events: KeystrokeEvent[]) => Promise<void>;
    isVerifying: boolean;
    result?: {
        status: "GENUINE" | "FORGED";
        confidence: number;
    } | null;
}

export function KeystrokeRecorder({ onVerify, isVerifying, result }: KeystrokeRecorderProps) {
    const [text, setText] = useState("");
    const [events, setEvents] = useState<KeystrokeEvent[]>([]);
    const [keyDownMap, setKeyDownMap] = useState<Record<string, number>>({});
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const reset = () => {
        setText("");
        setEvents([]);
        setKeyDownMap({});
        if (textareaRef.current) {
            textareaRef.current.focus();
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        const now = performance.now();
        if (e.repeat) return;
        setKeyDownMap(prev => ({ ...prev, [e.code]: now }));
    };

    const handleKeyUp = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
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
        }
    };

    const MIN_KEYSTROKES = 5;
    const canVerify = events.length >= MIN_KEYSTROKES;

    return (
        <Card className="w-full shadow-2xl shadow-primary/5 border-border/60 bg-card/60 backdrop-blur-xl transition-all duration-300">
            <CardHeader className="pb-4 border-b border-border/40 bg-muted/20">
                <div className="flex items-center space-x-3">
                    <div className="p-2.5 bg-background rounded-xl border border-border/50 shadow-sm">
                        <Keyboard className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <CardTitle className="text-lg font-semibold">Live Typing Analysis</CardTitle>
                        <CardDescription className="text-sm mt-1">
                            Type naturally to verify your digital identity pattern.
                        </CardDescription>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="space-y-6 pt-6">
                <div className="relative group">
                    <Textarea
                        ref={textareaRef}
                        placeholder="Type a sentence here..."
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onKeyUp={handleKeyUp}
                        disabled={isVerifying}
                        className={cn(
                            "min-h-[240px] text-xl leading-relaxed p-6 resize-none transition-all duration-300 bg-background/50 border-border/60 shadow-inner rounded-xl",
                            "focus:ring-2 focus:ring-primary/20 focus:border-primary/50",
                            result?.status === "GENUINE" && "border-emerald-500/30 focus:ring-emerald-500/10 bg-emerald-50/5",
                            result?.status === "FORGED" && "border-rose-500/30 focus:ring-rose-500/10 bg-rose-50/5"
                        )}
                    />
                    <div className="absolute bottom-4 right-4 flex items-center gap-2 text-xs font-medium text-muted-foreground bg-background/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-border/40 shadow-sm">
                        <Activity className="w-3.5 h-3.5 text-primary" />
                        <span className="tabular-nums">{events.length}</span> strokes
                    </div>
                </div>

                {result && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={cn(
                            "p-5 rounded-xl border-l-4 flex items-center justify-between shadow-sm",
                            result.status === "GENUINE"
                                ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-l-emerald-500 border-y border-r border-emerald-200/50 dark:border-emerald-800/50"
                                : "bg-rose-50/50 dark:bg-rose-950/20 border-l-rose-500 border-y border-r border-rose-200/50 dark:border-rose-800/50"
                        )}
                    >
                        <div className="flex items-center gap-5">
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
                            <div>
                                <h4 className={cn("font-bold text-lg", result.status === "GENUINE" ? "text-emerald-950 dark:text-emerald-100" : "text-rose-950 dark:text-rose-100")}>
                                    {result.status === "GENUINE" ? "Identity Verified" : "Verification Failed"}
                                </h4>
                                <div className="flex items-center gap-2 mt-1">
                                    <div className="h-1.5 w-24 bg-black/5 dark:bg-white/10 rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${result.confidence * 100}%` }}
                                            transition={{ duration: 0.8, ease: "easeOut" }}
                                            className={cn("h-full rounded-full", result.status === "GENUINE" ? "bg-emerald-500" : "bg-rose-500")}
                                        />
                                    </div>
                                    <p className="text-sm font-medium opacity-70">{(result.confidence * 100).toFixed(1)}% match</p>
                                </div>
                            </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={reset} className="hover:bg-black/5 dark:hover:bg-white/5 rounded-full h-9 w-9 p-0">
                            <RefreshCcw className="w-4 h-4 text-muted-foreground" />
                        </Button>
                    </motion.div>
                )}
            </CardContent>
            <CardFooter className="flex justify-between items-center bg-muted/20 p-6 border-t border-border/40">
                <Button variant="ghost" onClick={reset} disabled={isVerifying} className="text-muted-foreground hover:text-foreground">
                    Reset
                </Button>
                <Button
                    size="lg"
                    onClick={() => onVerify(events)}
                    disabled={!canVerify || isVerifying || !!result}
                    className={cn(
                        "min-w-[180px] font-semibold text-base shadow-lg shadow-primary/25 transition-all hover:shadow-primary/40",
                        canVerify && !isVerifying && !result && "animate-pulse"
                    )}
                >
                    {isVerifying ? (
                        <>
                            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                            Verifying...
                        </>
                    ) : (
                        "Verify Identity"
                    )}
                </Button>
            </CardFooter>
        </Card>
    );
}
