"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  BookOpen,
  Layers,
  Video,
  Volume2,
  Play,
  Pause,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronRight,
  Plus,
  Trash2,
  UploadCloud,
  Wand2,
  Palette,
  RotateCcw,
  Sliders,
  Check,
  Film
} from "lucide-react";

interface Voice {
  voice_id: string;
  name: string;
  accent: string;
  gender: string;
  description: string;
  category: string;
  preview_url?: string;
}

interface NCERTLesson {
  id: string;
  grade: string;
  subject: string;
  chapter_num: number;
  title: string;
  age_group: string;
  sample_outline: string[];
  default_context: string;
}

interface SlideItem {
  slide_number: number;
  title: string;
  subtitle?: string;
  bullet_points: string[];
  key_takeaway?: string;
  narration_script: string;
}

interface SlideInfo {
  slide_idx: number;
  title: string;
  image_url: string;
  audio_url?: string;
  video_url?: string;
  duration?: number;
  narration_script: string;
}

interface RenderJob {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  current_step: string;
  slides_info: SlideInfo[];
  final_video_url?: string;
  error?: string;
  renderer?: string;
}

type Renderer = "slides" | "manim";

export default function VelixStudio() {
  // Step navigation: 1: Source, 2: Voice & Style, 3: Outline, 4: Slides, 5: Render & Video
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Curriculum & Input State
  const [sourceMode, setSourceMode] = useState<"preset" | "custom" | "pdf">("preset");
  const [lessons, setLessons] = useState<NCERTLesson[]>([]);
  const [selectedLessonId, setSelectedLessonId] = useState<string>("");
  const [topic, setTopic] = useState<string>("Matter in Our Surroundings");
  const [grade, setGrade] = useState<string>("Class 9");
  const [ageGroup, setAgeGroup] = useState<string>("14-15 years");
  const [contextText, setContextText] = useState<string>("");
  const [pdfFileName, setPdfFileName] = useState<string>("");

  // Voice & Styling State
  const [voices, setVoices] = useState<Voice[]>([]);
  const [selectedVoiceId, setSelectedVoiceId] = useState<string>("Xb7hH8MSUJpSbSDYk0k2"); // Alice by default
  const [theme, setTheme] = useState<string>("modern-dark");
  const [tone, setTone] = useState<string>("engaging and clear");
  const [stability, setStability] = useState<number>(0.5);
  const [specialInstructions, setSpecialInstructions] = useState<string>("");

  // Rendering engine: "slides" (PIL static HD) or "manim" (3b1b animated)
  const [renderer, setRenderer] = useState<Renderer>("slides");

  // Audio Preview State
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const audioPreviewRef = useRef<HTMLAudioElement | null>(null);

  // Outline State
  const [subheadings, setSubheadings] = useState<string[]>([]);
  const [isGeneratingOutline, setIsGeneratingOutline] = useState<boolean>(false);

  // Slides State
  const [slides, setSlides] = useState<SlideItem[]>([]);
  const [isGeneratingSlides, setIsGeneratingSlides] = useState<boolean>(false);
  const [activeSlideTab, setActiveSlideTab] = useState<number>(0);

  // Rendering & Job State
  const [isSubmittingRender, setIsSubmittingRender] = useState<boolean>(false);
  const [currentJob, setCurrentJob] = useState<RenderJob | null>(null);

  // System status
  const [systemHealthy, setSystemHealthy] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [apiWarning, setApiWarning] = useState<string | null>(null);

  // Fetch initial data (NCERT lessons & ElevenLabs voices)
  useEffect(() => {
    // Check health
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "healthy") setSystemHealthy(true);
      })
      .catch(() => setSystemHealthy(false));

    // Load NCERT lessons
    fetch("/api/ncert/lessons")
      .then((res) => res.json())
      .then((data) => {
        if (data.lessons && data.lessons.length > 0) {
          setLessons(data.lessons);
          // select first lesson by default
          const first = data.lessons[1] || data.lessons[0];
          setSelectedLessonId(first.id);
          setTopic(first.title);
          setGrade(first.grade);
          setAgeGroup(first.age_group);
          setContextText(first.default_context);
          setSubheadings(first.sample_outline);
        }
      })
      .catch((err) => console.error("Failed to load lessons:", err));

    // Load ElevenLabs voices
    fetch("/api/voices")
      .then((res) => res.json())
      .then((data) => {
        if (data.voices && data.voices.length > 0) {
          setVoices(data.voices);
        }
      })
      .catch((err) => console.error("Failed to load voices:", err));
  }, []);

  // Handle lesson preset selection
  const handleSelectPreset = (lesson: NCERTLesson) => {
    setSelectedLessonId(lesson.id);
    setTopic(lesson.title);
    setGrade(lesson.grade);
    setAgeGroup(lesson.age_group);
    setContextText(lesson.default_context);
    setSubheadings(lesson.sample_outline);
  };

  // Handle voice preview audio
  const handlePlayVoicePreview = (voice: Voice) => {
    if (!voice.preview_url) return;

    if (playingVoiceId === voice.voice_id) {
      if (audioPreviewRef.current) {
        audioPreviewRef.current.pause();
      }
      setPlayingVoiceId(null);
    } else {
      if (audioPreviewRef.current) {
        audioPreviewRef.current.pause();
      }
      const audio = new Audio(voice.preview_url);
      audioPreviewRef.current = audio;
      audio.play();
      setPlayingVoiceId(voice.voice_id);
      audio.onended = () => setPlayingVoiceId(null);
    }
  };

  // Handle PDF upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setPdfFileName(file.name);
    setTopic(file.name.replace(".pdf", ""));

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/ncert/upload-pdf", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.text) {
        setContextText(data.text);
      }
    } catch (err) {
      setApiError("Failed to upload PDF: " + err);
    }
  };

  // Step 3: Generate Outline with DeepSeek
  const handleGenerateOutline = async () => {
    setIsGeneratingOutline(true);
    setApiError(null);
    try {
      const res = await fetch("/api/generate/outline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          grade,
          age_group: ageGroup,
          context_text: contextText,
          special_instructions: specialInstructions,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to generate outline");
      }
      const data = await res.json();
      if (data.warning) {
        setApiWarning(data.warning);
      }
      if (data.subheadings && data.subheadings.length > 0) {
        setSubheadings(data.subheadings);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setApiError(msg || "Failed to generate outline with DeepSeek");
    } finally {
      setIsGeneratingOutline(false);
    }
  };

  // Step 4: Generate Slides with DeepSeek
  const handleGenerateSlides = async () => {
    if (subheadings.length === 0) {
      setApiError("Please add at least one subheading before generating slides.");
      return;
    }
    setIsGeneratingSlides(true);
    setApiError(null);
    try {
      const res = await fetch("/api/generate/slides", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          grade,
          age_group: ageGroup,
          subheadings,
          context_text: contextText,
          tone,
          special_instructions: specialInstructions,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to generate slides");
      }
      const data = await res.json();
      if (data.warning) {
        setApiWarning(data.warning);
      }
      if (data.slides && data.slides.length > 0) {
        setSlides(data.slides);
        setActiveSlideTab(0);
        setCurrentStep(4);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setApiError(msg || "Failed to generate slides with DeepSeek");
    } finally {
      setIsGeneratingSlides(false);
    }
  };

  // Step 5: Render Video Pipeline
  const handleStartRender = async () => {
    if (slides.length === 0) {
      setApiError("Please generate slides before rendering.");
      return;
    }

    setIsSubmittingRender(true);
    setApiError(null);
    try {
      const res = await fetch("/api/generate/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          grade,
          slides,
          voice_id: selectedVoiceId,
          theme,
          stability,
          similarity_boost: 0.75,
          renderer,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to start render");
      }

      const data = await res.json();
      const jobId = data.job_id;
      setCurrentStep(5);

      // Poll job status until completed
      pollJobStatus(jobId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setApiError(msg || "Failed to start video render job");
    } finally {
      setIsSubmittingRender(false);
    }
  };

  // Polling function for render job
  const pollJobStatus = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/generate/job/${jobId}`);
        if (!res.ok) return;
        const jobData: RenderJob = await res.json();
        setCurrentJob(jobData);

        if (jobData.status === "completed" || jobData.status === "failed") {
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1500);
  };

  // Outline manipulation helpers
  const handleAddSubheading = () => {
    setSubheadings([...subheadings, `New Topic ${subheadings.length + 1}`]);
  };

  const handleUpdateSubheading = (index: number, val: string) => {
    const updated = [...subheadings];
    updated[index] = val;
    setSubheadings(updated);
  };

  const handleRemoveSubheading = (index: number) => {
    setSubheadings(subheadings.filter((_, i) => i !== index));
  };

  // Slide deck manipulation helpers
  const handleUpdateSlideField = (
    index: number,
    field: keyof SlideItem,
    val: string | number | string[]
  ) => {
    const updated = [...slides];
    updated[index] = { ...updated[index], [field]: val };
    setSlides(updated);
  };

  const handleUpdateBullet = (slideIdx: number, bulletIdx: number, val: string) => {
    const updated = [...slides];
    const bullets = [...updated[slideIdx].bullet_points];
    bullets[bulletIdx] = val;
    updated[slideIdx].bullet_points = bullets;
    setSlides(updated);
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-[#0b101e]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Film className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
                VELIX STUDIO
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/50">
                2.0 NEXT-GEN
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              AI Video & Narration Studio powered by DeepSeek & ElevenLabs
            </p>
          </div>
        </div>

        {/* System Badges & Actions */}
        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-2.5 text-xs bg-slate-900/80 border border-slate-800 rounded-lg px-3 py-1.5">
            <span className="flex h-2 w-2 relative">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  systemHealthy ? "bg-emerald-400" : "bg-amber-400"
                }`}
              ></span>
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  systemHealthy ? "bg-emerald-500" : "bg-amber-500"
                }`}
              ></span>
            </span>
            <span className="text-slate-300 font-medium">DeepSeek V3</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-300 font-medium">ElevenLabs TTS</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-300 font-medium">FFmpeg 1080p</span>
          </div>

          <button
            onClick={() => {
              setCurrentStep(1);
              setSlides([]);
              setCurrentJob(null);
            }}
            className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 rounded-lg px-3 py-1.5 transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>New Video</span>
          </button>
        </div>
      </header>

      {/* Workflow Step Tracker */}
      <div className="bg-[#0b101e]/50 border-b border-slate-800/60 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs sm:text-sm font-medium">
          {[
            { num: 1, label: "Lesson & Source", icon: BookOpen },
            { num: 2, label: "Voice & Tone", icon: Volume2 },
            { num: 3, label: "Outline Editor", icon: Layers },
            { num: 4, label: "Slide Deck", icon: Palette },
            { num: 5, label: "Render & Video", icon: Video },
          ].map((s) => {
            const Icon = s.icon;
            const isActive = currentStep === s.num;
            const isDone = currentStep > s.num;
            return (
              <button
                key={s.num}
                onClick={() => {
                  if (isDone || isActive) setCurrentStep(s.num);
                }}
                disabled={!isDone && !isActive}
                className={`flex items-center space-x-2 py-1 px-3 rounded-lg transition-all ${
                  isActive
                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-semibold"
                    : isDone
                    ? "text-slate-300 hover:text-white cursor-pointer"
                    : "text-slate-600 cursor-not-allowed"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                    isActive
                      ? "bg-cyan-500 text-slate-950 font-bold"
                      : isDone
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : "bg-slate-800 text-slate-500"
                  }`}
                >
                  {isDone ? <Check className="w-3.5 h-3.5" /> : s.num}
                </div>
                <div className="hidden sm:flex items-center space-x-1.5">
                  <Icon className="w-3.5 h-3.5 opacity-80" />
                  <span>{s.label}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Workspace Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {/* Error Alert Box */}
        {apiError && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start space-x-3 text-sm animate-in fade-in">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-rose-200">Execution Notice</p>
              <p>{apiError}</p>
            </div>
            <button
              onClick={() => setApiError(null)}
              className="text-xs bg-rose-950/40 hover:bg-rose-900/60 px-2.5 py-1 rounded-md text-rose-300 border border-rose-800/40"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Warning / Informational Alert Box */}
        {apiWarning && (
          <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-start space-x-3 text-sm animate-in fade-in">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-amber-200">System Notice</p>
              <p>{apiWarning}</p>
            </div>
            <button
              onClick={() => setApiWarning(null)}
              className="text-xs bg-amber-950/40 hover:bg-amber-900/60 px-2.5 py-1 rounded-md text-amber-300 border border-amber-800/40"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* ========================================================
            STEP 1: LESSON & SOURCE
        ======================================================== */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                  <BookOpen className="w-6 h-6 text-cyan-400" />
                  Select Lesson & Curriculum Source
                </h1>
                <p className="text-sm text-slate-400 mt-1">
                  Choose from pre-loaded NCERT textbooks, upload your own PDF, or specify a custom topic.
                </p>
              </div>

              {/* Source Mode Tabs */}
              <div className="flex p-1 bg-slate-900 border border-slate-800 rounded-xl">
                <button
                  onClick={() => setSourceMode("preset")}
                  className={`px-4 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    sourceMode === "preset"
                      ? "bg-cyan-500 text-slate-950 font-semibold shadow"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  NCERT Library
                </button>
                <button
                  onClick={() => setSourceMode("pdf")}
                  className={`px-4 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    sourceMode === "pdf"
                      ? "bg-cyan-500 text-slate-950 font-semibold shadow"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Upload PDF
                </button>
                <button
                  onClick={() => setSourceMode("custom")}
                  className={`px-4 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    sourceMode === "custom"
                      ? "bg-cyan-500 text-slate-950 font-semibold shadow"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Custom Topic
                </button>
              </div>
            </div>

            {/* PRESET MODE: NCERT Curriculum Cards */}
            {sourceMode === "preset" && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {lessons.map((lesson) => {
                  const isSelected = selectedLessonId === lesson.id;
                  return (
                    <div
                      key={lesson.id}
                      onClick={() => handleSelectPreset(lesson)}
                      className={`p-5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden group ${
                        isSelected
                          ? "bg-slate-900/90 border-cyan-500 shadow-xl shadow-cyan-500/10 ring-1 ring-cyan-500"
                          : "bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/70"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <span className="text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-full bg-cyan-950/70 text-cyan-400 border border-cyan-800/40">
                          {lesson.grade} • {lesson.subject}
                        </span>
                        {isSelected && (
                          <div className="w-5 h-5 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center">
                            <Check className="w-3.5 h-3.5 stroke-[3]" />
                          </div>
                        )}
                      </div>
                      <h3 className="text-base font-bold text-white mt-3 group-hover:text-cyan-300 transition-colors">
                        {lesson.title}
                      </h3>
                      <p className="text-xs text-slate-400 mt-2 line-clamp-3">
                        {lesson.default_context}
                      </p>
                      <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                        <span>Ages: {lesson.age_group}</span>
                        <span>{lesson.sample_outline.length} Subtopics</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* PDF UPLOAD MODE */}
            {sourceMode === "pdf" && (
              <div className="p-8 rounded-2xl border-2 border-dashed border-slate-800 hover:border-cyan-500/60 bg-slate-900/30 text-center transition-all">
                <UploadCloud className="w-12 h-12 text-cyan-400 mx-auto mb-3" />
                <h3 className="text-lg font-bold text-white">Upload Textbook Chapter PDF</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-4">
                  Upload any NCERT or academic PDF chapter. Text and topics will be automatically extracted.
                </p>
                <label className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs cursor-pointer shadow-lg shadow-cyan-500/20 transition-all">
                  <span>Browse PDF File</span>
                  <input
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </label>
                {pdfFileName && (
                  <p className="text-xs text-emerald-400 mt-3 flex items-center justify-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Loaded: {pdfFileName}
                  </p>
                )}
              </div>
            )}

            {/* CUSTOM TOPIC MODE & CONFIG DETAILS */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Topic / Lesson Name</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                  placeholder="e.g. Thermodynamics, Newton's Laws"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Grade Level</label>
                <select
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                >
                  {Array.from({ length: 12 }, (_, i) => `Class ${i + 1}`).map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Target Age Group</label>
                <input
                  type="text"
                  value={ageGroup}
                  onChange={(e) => setAgeGroup(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                  placeholder="e.g. 14-15 years"
                />
              </div>
            </div>

            {/* Context Textarea */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300">
                  Curriculum Context / Chapter Notes (Optional)
                </label>
                <span className="text-[11px] text-slate-500">
                  {contextText.length} characters
                </span>
              </div>
              <textarea
                value={contextText}
                onChange={(e) => setContextText(e.target.value)}
                rows={4}
                className="w-full bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                placeholder="Paste key lesson notes, formulas, or textbook text to ground the AI generation..."
              />
            </div>

            {/* Next Step Action */}
            <div className="flex justify-end pt-4 border-t border-slate-800/80">
              <button
                onClick={() => setCurrentStep(2)}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all"
              >
                <span>Continue to Voice & Style</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ========================================================
            STEP 2: VOICE & TONE STUDIO
        ======================================================== */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                <Volume2 className="w-6 h-6 text-cyan-400" />
                Narration Voice & Visual Styling
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Configure ElevenLabs natural voice models, pedagogical tone, and slide visual themes.
              </p>
            </div>

            {/* ElevenLabs Voice Selector Grid */}
            <div className="space-y-3">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Select ElevenLabs Voice Narration
              </label>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {voices.map((v) => {
                  const isSelected = selectedVoiceId === v.voice_id;
                  const isPlaying = playingVoiceId === v.voice_id;

                  return (
                    <div
                      key={v.voice_id}
                      onClick={() => setSelectedVoiceId(v.voice_id)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer relative ${
                        isSelected
                          ? "bg-slate-900 border-cyan-500 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500"
                          : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-bold text-white text-sm flex items-center gap-1.5">
                            {v.name}
                          </div>
                          <span className="text-[10px] text-slate-400 uppercase font-medium">
                            {v.gender} • {v.accent} • {v.category}
                          </span>
                        </div>

                        {v.preview_url && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePlayVoicePreview(v);
                            }}
                            className={`p-2 rounded-lg transition-all ${
                              isPlaying
                                ? "bg-cyan-500 text-slate-950"
                                : "bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700"
                            }`}
                            title="Preview voice sample"
                          >
                            {isPlaying ? (
                              <Pause className="w-3.5 h-3.5" />
                            ) : (
                              <Play className="w-3.5 h-3.5 fill-current" />
                            )}
                          </button>
                        )}
                      </div>

                      <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                        {v.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Voice Settings & Theme Controls */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
              {/* Visual Theme */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Palette className="w-3.5 h-3.5 text-cyan-400" />
                  Visual Theme
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: "modern-dark", name: "Slate", color: "bg-cyan-500" },
                    { id: "emerald", name: "Emerald", color: "bg-emerald-500" },
                    { id: "amber", name: "Amber", color: "bg-amber-500" },
                  ].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setTheme(t.id)}
                      className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                        theme === t.id
                          ? "border-cyan-400 bg-slate-800 text-white"
                          : "border-slate-800 bg-slate-900/60 text-slate-400 hover:text-white"
                      }`}
                    >
                      <span className={`w-2.5 h-2.5 rounded-full ${t.color}`} />
                      {t.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Teaching Tone */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                  Teaching Tone
                </label>
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="engaging and clear">Engaging & Enthusiastic</option>
                  <option value="academic and rigorous">Formal & Academic</option>
                  <option value="storytelling and vivid">Storytelling & Narrative</option>
                  <option value="patient and foundational">Patient & Step-by-Step</option>
                </select>
              </div>

              {/* ElevenLabs Stability */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold text-slate-300">
                    Voice Stability
                  </label>
                  <span className="text-xs font-mono text-cyan-400">{stability}</span>
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="0.9"
                  step="0.05"
                  value={stability}
                  onChange={(e) => setStability(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500"
                />
                <span className="text-[10px] text-slate-500 block">
                  Lower = more expressive inflection; Higher = consistent pace
                </span>
              </div>
            </div>

            {/* Special Instructions */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Special Teaching Instructions (Optional)
              </label>
              <textarea
                value={specialInstructions}
                onChange={(e) => setSpecialInstructions(e.target.value)}
                rows={2}
                className="w-full bg-slate-900/70 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                placeholder="e.g. Include real-life analogies with everyday objects. Emphasize why this concept matters in exams."
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
              <button
                onClick={() => setCurrentStep(1)}
                className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
              >
                Back to Source
              </button>
              <button
                onClick={() => setCurrentStep(3)}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all"
              >
                <span>Continue to Outline</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ========================================================
            STEP 3: OUTLINE & SUBHEADINGS EDITOR
        ======================================================== */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                  <Layers className="w-6 h-6 text-cyan-400" />
                  Curriculum Outline & Subtopics
                </h1>
                <p className="text-sm text-slate-400 mt-1">
                  Each subtopic becomes an individual animated slide and spoken narrative section.
                </p>
              </div>

              <button
                onClick={handleGenerateOutline}
                disabled={isGeneratingOutline}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
              >
                {isGeneratingOutline ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>DeepSeek Generating...</span>
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4" />
                    <span>Regenerate with DeepSeek</span>
                  </>
                )}
              </button>
            </div>

            {/* Subheadings List */}
            <div className="space-y-3">
              {subheadings.map((sub, idx) => (
                <div
                  key={idx}
                  className="flex items-center space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all group"
                >
                  <span className="w-7 h-7 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800/40 flex items-center justify-center text-xs font-bold shrink-0">
                    {idx + 1}
                  </span>
                  <input
                    type="text"
                    value={sub}
                    onChange={(e) => handleUpdateSubheading(idx, e.target.value)}
                    className="flex-1 bg-transparent text-sm text-white focus:outline-none focus:ring-1 focus:ring-cyan-500 px-2 py-1 rounded"
                  />
                  <button
                    onClick={() => handleRemoveSubheading(idx)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 opacity-60 group-hover:opacity-100 transition-all"
                    title="Remove subtopic"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}

              <button
                onClick={handleAddSubheading}
                className="w-full py-3 rounded-xl border border-dashed border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900/40 text-slate-400 hover:text-cyan-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>Add Subheading</span>
              </button>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
              <button
                onClick={() => setCurrentStep(2)}
                className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
              >
                Back to Voice
              </button>
              <button
                onClick={handleGenerateSlides}
                disabled={isGeneratingSlides}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
              >
                {isGeneratingSlides ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>DeepSeek Writing Scripts...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Generate Slide Deck & Scripts</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ========================================================
            STEP 4: SLIDE DECK & SCRIPT STUDIO
        ======================================================== */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                  <Palette className="w-6 h-6 text-cyan-400" />
                  Slide Visuals & Spoken Voiceover Scripts
                </h1>
                <p className="text-sm text-slate-400 mt-1">
                  Inspect the structured visual layout and natural spoken script for each slide before rendering.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={handleGenerateSlides}
                  disabled={isGeneratingSlides}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-slate-700/60 transition-all"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Regenerate Deck</span>
                </button>
              </div>
            </div>

            {/* Slide Navigation Tabs */}
            <div className="flex items-center space-x-2 overflow-x-auto pb-2">
              {slides.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveSlideTab(idx)}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center space-x-2 ${
                    activeSlideTab === idx
                      ? "bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20 font-bold"
                      : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  <span>Slide {idx + 1}</span>
                  <span className="text-[10px] opacity-75 truncate max-w-[120px]">
                    {s.title}
                  </span>
                </button>
              ))}
            </div>

            {/* Active Slide Editor Card */}
            {slides[activeSlideTab] && (
              <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">
                      Slide Title
                    </label>
                    <input
                      type="text"
                      value={slides[activeSlideTab].title}
                      onChange={(e) =>
                        handleUpdateSlideField(activeSlideTab, "title", e.target.value)
                      }
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-white font-bold focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">
                      Subtitle / Concept
                    </label>
                    <input
                      type="text"
                      value={slides[activeSlideTab].subtitle || ""}
                      onChange={(e) =>
                        handleUpdateSlideField(activeSlideTab, "subtitle", e.target.value)
                      }
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-300 focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                {/* Bullet Points */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">
                    Slide Content Bullets (Visual Cards)
                  </label>
                  {slides[activeSlideTab].bullet_points.map((bp, bIdx) => (
                    <div key={bIdx} className="flex items-center space-x-2">
                      <span className="w-5 h-5 rounded bg-cyan-950 text-cyan-400 text-[11px] font-bold flex items-center justify-center shrink-0">
                        {bIdx + 1}
                      </span>
                      <input
                        type="text"
                        value={bp}
                        onChange={(e) =>
                          handleUpdateBullet(activeSlideTab, bIdx, e.target.value)
                        }
                        className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  ))}
                </div>

                {/* Key Takeaway */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5">
                    <span>💡 Key Takeaway Box</span>
                  </label>
                  <input
                    type="text"
                    value={slides[activeSlideTab].key_takeaway || ""}
                    onChange={(e) =>
                      handleUpdateSlideField(activeSlideTab, "key_takeaway", e.target.value)
                    }
                    className="w-full bg-slate-950 border border-cyan-900/50 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                {/* Narration Voiceover Script */}
                <div className="space-y-1.5 pt-2 border-t border-slate-800">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                      <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
                      ElevenLabs Spoken Narration Script
                    </label>
                    <span className="text-[11px] text-slate-500">
                      {slides[activeSlideTab].narration_script.split(/\s+/).filter(Boolean).length}{" "}
                      words (~
                      {Math.round(
                        (slides[activeSlideTab].narration_script.split(/\s+/).filter(Boolean).length /
                          150) *
                          60
                      )}
                      s audio)
                    </span>
                  </div>
                  <textarea
                    value={slides[activeSlideTab].narration_script}
                    onChange={(e) =>
                      handleUpdateSlideField(
                        activeSlideTab,
                        "narration_script",
                        e.target.value
                      )
                    }
                    rows={4}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 leading-relaxed font-sans"
                    placeholder="The teacher voiceover spoken during this slide..."
                  />
                </div>
              </div>
            )}

            {/* Rendering Engine Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Rendering Engine
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {([
                  {
                    id: "slides" as Renderer,
                    name: "PIL HD Slides",
                    desc: "Static 1920×1080 slide cards · Fastest render",
                    icon: Layers,
                  },
                  {
                    id: "manim" as Renderer,
                    name: "Manim 3b1b Animation",
                    desc: "Animated kinetic typography & formulas · Slower render",
                    icon: Film,
                  },
                ]).map((r) => (
                  <button
                    key={r.id}
                    onClick={() => setRenderer(r.id)}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      renderer === r.id
                        ? "border-cyan-400 bg-slate-800 text-white ring-1 ring-cyan-500"
                        : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2 font-bold text-sm">
                      <r.icon className="w-4 h-4 text-cyan-400" />
                      {r.name}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">{r.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
              <button
                onClick={() => setCurrentStep(3)}
                className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
              >
                Back to Outline
              </button>
              <button
                onClick={handleStartRender}
                disabled={isSubmittingRender}
                className="flex items-center space-x-2 px-7 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold text-sm shadow-xl shadow-cyan-500/25 transition-all disabled:opacity-50"
              >
                {isSubmittingRender ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                    <span>Starting Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Video className="w-4 h-4 text-slate-950" />
                    <span>Render Video Presentation</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ========================================================
            STEP 5: RENDER STUDIO & VIDEO PLAYER
        ======================================================== */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                <Video className="w-6 h-6 text-cyan-400" />
                Studio Production & Final Video
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Real-time video rendering using ElevenLabs audio synthesis and high-DPI slide composition.
              </p>
            </div>

            {/* Real-time Progress Card */}
            {currentJob && currentJob.status !== "completed" && (
              <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                    <div>
                      <p className="text-sm font-bold text-white">
                        {currentJob.current_step}
                      </p>
                      <p className="text-xs text-slate-400">
                        {currentJob.renderer === "manim"
                          ? "Animating kinetic scenes with the Manim 3b1b engine, then muxing ElevenLabs audio..."
                          : "Synthesizing audio and encoding MP4 video tracks..."}
                      </p>
                    </div>
                  </div>
                  <span className="text-lg font-mono font-bold text-cyan-400">
                    {currentJob.progress}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full transition-all duration-500 ease-out"
                    style={{ width: `${currentJob.progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Video Player & Finished Studio Stage */}
            {currentJob && currentJob.status === "completed" && (
              <div className="space-y-6">
                {/* Master Presentation Player */}
                <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-2xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-800/40">
                        RENDER COMPLETE
                      </span>
                      <h2 className="text-lg font-bold text-white mt-1.5">
                        {topic} — {grade}
                      </h2>
                    </div>

                    {/* Download Actions */}
                    <div className="flex items-center space-x-2">
                      <a
                        href={currentJob.final_video_url}
                        download={`velix_${topic.toLowerCase().replace(/\s+/g, "_")}.mp4`}
                        className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download MP4</span>
                      </a>
                    </div>
                  </div>

                  {/* HTML5 Video Player */}
                  <div className="aspect-video w-full rounded-xl overflow-hidden bg-black border border-slate-800 shadow-inner">
                    <video
                      controls
                      autoPlay
                      className="w-full h-full object-contain"
                      src={currentJob.final_video_url}
                    />
                  </div>
                </div>

                {/* Slide-by-slide Clip Inspector */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                    Slide Clips & Audio Assets
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                    {currentJob.slides_info.map((si, sIdx) => (
                      <div
                        key={sIdx}
                        className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden group hover:border-slate-700 transition-all"
                      >
                        <div className="aspect-video relative bg-slate-950 overflow-hidden">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={si.image_url}
                            alt={si.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                          <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono text-white">
                            Slide {sIdx + 1} • {si.duration ? `${si.duration.toFixed(1)}s` : "6s"}
                          </span>
                        </div>
                        <div className="p-3">
                          <p className="text-xs font-bold text-white truncate">
                            {si.title}
                          </p>
                          <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800 text-[11px]">
                            {si.audio_url && (
                              <a
                                href={si.audio_url}
                                download={`audio_slide_${sIdx + 1}.mp3`}
                                className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                              >
                                <Volume2 className="w-3 h-3" /> Audio MP3
                              </a>
                            )}
                            <a
                              href={si.image_url}
                              download={`slide_${sIdx + 1}.png`}
                              className="text-slate-400 hover:text-white flex items-center gap-1"
                            >
                              <Download className="w-3 h-3" /> Image
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Failed State */}
            {currentJob && currentJob.status === "failed" && (
              <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-3">
                <div className="flex items-center space-x-2 text-rose-400 font-bold">
                  <AlertCircle className="w-5 h-5" />
                  <span>Render Pipeline Encountered an Error</span>
                </div>
                <p className="text-xs">{currentJob.error}</p>
                <button
                  onClick={() => setCurrentStep(4)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-white"
                >
                  Return to Slide Deck
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
