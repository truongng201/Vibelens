"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { Upload, Music, Play, Pause, ImageIcon, Sparkles, Heart, Clock, MessageSquare } from "lucide-react"
import { toast } from "../hooks/use-toast";

function LoadingOverlay({ show }) {
  if (!show) return null;
  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      width: "100vw",
      height: "100vh",
      background: "rgba(0,0,0,0.3)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 10000
    }}>
      <div className="spinner" style={{
        border: "4px solid #10b981",
        borderTop: "4px solid #fff",
        borderRadius: "50%",
        width: 48,
        height: 48,
        animation: "spin 1s linear infinite"
      }} />
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default function VibelensApp() {
  const [uploadedImage, setUploadedImage] = useState(null)
  const [imageDescription, setImageDescription] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [recommendations, setRecommendations] = useState([])
  const [playingId, setPlayingId] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [likedSongs, setLikedSongs] = useState(new Set())
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioLoadingId, setAudioLoadingId] = useState(null);
  const [audioElement, setAudioElement] = useState(null);
  const [audioProgress, setAudioProgress] = useState(0);
  const audioRef = useRef(null);

  useEffect(() => {
    if (audioElement && audioRef.current !== audioElement) {
      audioRef.current = audioElement;
    }
  }, [audioElement]);

  useEffect(() => {
    if (audioElement && playingId) {
      audioElement.play();
      const updateProgress = () => setAudioProgress(audioElement.currentTime);
      audioElement.addEventListener('timeupdate', updateProgress);
      return () => {
        audioElement.removeEventListener('timeupdate', updateProgress);
      };
    }
  }, [audioElement, playingId, audioUrl]);

  const getRecommendations = async (imageUrl, prompt) => {
    try {
      // Use your backend endpoint directly (adjust if needed)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/recommend-music`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: imageUrl, prompt }),
      });
      const data = await response.json();
      if (!response.ok) {
        console.error("Recommendation error:", data);
        throw new Error(data.error || "Recommendation failed");
      }
      console.log("Recommendation success:", data);
      return data;
    } catch (err) {
      console.error("Recommendation exception:", err);
      throw err;
    }
  };

  const playMusicFromBackend = async (musicTitle) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/play-music`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ music_title: musicTitle }),
      });
      const data = await response.json();
      if (!response.ok) {
        console.error("Play music error:", data);
        throw new Error(data.error || "Play music failed");
      }
      return data.url;
    } catch (err) {
      console.error("Play music exception:", err);
      throw err;
    }
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }, [])

  const uploadImageToBackend = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    try {
      // Use your backend endpoint directly (adjust if needed)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/upload-image`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      console.log(data)
      if (!response.ok) {
        console.error("Image upload error:", data);
        throw new Error(data.error || "Image upload failed");
      }
      console.log("Image upload success:", data);
      // Return the shared_url from backend
      return data?.shared_url;
    } catch (err) {
      console.error("Image upload exception:", err);
      throw err;
    }
  };

  const handleFile = async (file) => {
    if (file.type.startsWith("image/")) {
      // Always preview the image immediately
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedImage(e.target.result);
      };
      reader.readAsDataURL(file);

      setIsAnalyzing(true);
      try {
        const imageUrl = await uploadImageToBackend(file);
        // Store backend-served image URL for later recommendation
        setUploadedImage(imageUrl);
        // Do NOT call getRecommendations here
      } catch (err) {
        toast({ title: "Error", description: err.message, variant: "destructive" });
      } finally {
        setIsAnalyzing(false);
      }
    }
  }

  const togglePlay = (id) => {
    setPlayingId(playingId === id ? null : id)
  }

  const toggleLike = (id) => {
    const newLikedSongs = new Set(likedSongs)
    if (likedSongs.has(id)) {
      newLikedSongs.delete(id)
    } else {
      newLikedSongs.add(id)
    }
    setLikedSongs(newLikedSongs)
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const handleAnalyzeClick = async () => {
    if (uploadedImage) {
      setIsAnalyzing(true);
      try {
        const recRes = await getRecommendations(uploadedImage, imageDescription);
        setRecommendations(recRes.recommendations || []);
      } catch (err) {
        toast({ title: "Error", description: err.message, variant: "destructive" });
      } finally {
        setIsAnalyzing(false);
      }
    }
  }

  const handlePlay = async (song) => {
    // If clicking the same song, toggle pause/play
    if (playingId === song.id && audioElement) {
      if (!audioElement.paused) {
        audioElement.pause();
      } else {
        audioElement.play();
      }
      return;
    }
    setAudioLoadingId(song.id);
    setIsAnalyzing(true);
    try {
      const url = await playMusicFromBackend(song.title);
      setAudioUrl(url);
      setPlayingId(song.id);
    } catch (err) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setAudioLoadingId(null);
      setIsAnalyzing(false);
    }
  }

  return (
    <>
      <LoadingOverlay show={isAnalyzing} />
      <div style={{ minHeight: "100vh", backgroundColor: "#000000", color: "#ffffff" }}>
        {/* Header */}
        <div
          style={{
            background: "linear-gradient(to bottom, #1f2937, #000000)",
            padding: "2rem",
          }}
        >
          <div style={{ maxWidth: "72rem", margin: "0 auto" }}>
            {/* Logo and Title - Centered */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "1rem",
                marginBottom: "1.5rem",
              }}
            >
              <div
                style={{
                  width: "4rem",
                  height: "4rem",
                  background: "linear-gradient(to bottom right, #0a5bb8, #083f86)",
                  borderRadius: "0.5rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                }}
              >
                <Sparkles style={{ width: "2rem", height: "2rem", color: "#ffffff" }} />
              </div>
              <div style={{ textAlign: "center" }}>
                <h1
                  style={{
                    fontSize: "2.25rem",
                    fontWeight: "bold",
                    color: "#ffffff",
                    marginBottom: "0.5rem",
                    margin: 0,
                  }}
                >
                  Vibelens
                </h1>
                <p
                  style={{
                    color: "#d1d5db",
                    margin: 0,
                    fontSize: "1rem",
                  }}
                >
                Image-Based Music Recommendations System
                </p>
              </div>
            </div>

            {/* Upload Area */}
            <div
              style={{
                backgroundColor: "#1f2937",
                border: `2px solid ${dragActive ? "#10b981" : "#374151"}`,
                borderRadius: "0.5rem",
                padding: "2rem",
                transition: "all 0.2s",
              }}
            >
              <div onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}>
                {!uploadedImage ? (
                  <div style={{ textAlign: "center" }}>
                    <div
                      style={{
                        margin: "0 auto 1.5rem",
                        width: "5rem",
                        height: "5rem",
                        backgroundColor: "#1f2937",
                        borderRadius: "50%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        border: "2px solid #374151",
                      }}
                    >
                      <Upload style={{ width: "2.5rem", height: "2.5rem", color: "#9ca3af" }} />
                    </div>
                    <div style={{ marginBottom: "1.5rem" }}>
                      <p
                        style={{
                          fontSize: "1.25rem",
                          fontWeight: "500",
                          color: "#ffffff",
                          marginBottom: "0.5rem",
                          margin: "0 0 0.5rem 0",
                        }}
                      >
                        Upload your image
                      </p>
                      <p style={{ color: "#9ca3af", margin: 0 }}>Drag and drop or click to browse</p>
                    </div>
                    <button
                      style={{
                        backgroundColor: "#083f86",
                        color: "#ffffff",
                        fontWeight: "600",
                        padding: "0.75rem 2rem",
                        borderRadius: "9999px",
                        border: "none",
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        fontSize: "1rem",
                        transition: "background-color 0.2s",
                      }}
                      onMouseOver={(e) => (e.target.style.backgroundColor = "#0a5bb8")}
                      onMouseOut={(e) => (e.target.style.backgroundColor = "#083f86")}
                      onClick={() => document.getElementById("file-input")?.click()}
                    >
                      <ImageIcon style={{ width: "1.25rem", height: "1.25rem" }} />
                      Choose Image
                    </button>
                    <input
                      id="file-input"
                      type="file"
                      accept="image/*"
                      style={{ display: "none" }}
                      onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                    />
                  </div>
                ) : (
                  <div>
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "1.5rem", marginBottom: "1.5rem" }}>
                      <div style={{ position: "relative" }}>
                        <img
                          src={uploadedImage || "/placeholder.svg"}
                          alt="Uploaded image"
                          style={{
                            borderRadius: "0.5rem",
                            objectFit: "cover",
                            width: "12rem",
                            height: "12rem",
                            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                          }}
                        />
                        <button
                          style={{
                            position: "absolute",
                            top: "0.5rem",
                            right: "0.5rem",
                            backgroundColor: "rgba(0, 0, 0, 0.7)",
                            color: "#ffffff",
                            border: "1px solid #374151",
                            borderRadius: "0.25rem",
                            padding: "0.25rem 0.5rem",
                            fontSize: "0.875rem",
                            cursor: "pointer",
                          }}
                          onClick={() => {
                            setUploadedImage(null)
                            setImageDescription("")
                            setRecommendations([])
                            setIsAnalyzing(false)
                          }}
                        >
                          Change
                        </button>
                      </div>

                      <div style={{ flex: 1 }}>
                        <h3
                          style={{
                            fontSize: "1.5rem",
                            fontWeight: "bold",
                            color: "#ffffff",
                            marginBottom: "0.5rem",
                            margin: "0 0 0.5rem 0",
                          }}
                        >
                          Your Visual Vibe
                        </h3>
                        <p
                          style={{
                            color: "#9ca3af",
                            marginBottom: "1rem",
                            margin: "0 0 1rem 0",
                          }}
                        >
                          AI will analyze your image to find matching music segments
                        </p>

                        {isAnalyzing && (
                          <div>
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "0.75rem",
                                marginBottom: "0.75rem",
                              }}
                            >
                              <Sparkles
                                style={{
                                  width: "1.25rem",
                                  height: "1.25rem",
                                  color: "#10b981",
                                  animation: "pulse 2s infinite",
                                }}
                              />
                              <span style={{ color: "#34d399", fontWeight: "500" }}>Analyzing visual elements...</span>
                            </div>
                            <div
                              style={{
                                width: "100%",
                                height: "0.5rem",
                                backgroundColor: "#1f2937",
                                borderRadius: "0.25rem",
                                overflow: "hidden",
                              }}
                            >
                              <div
                                style={{
                                  width: "66%",
                                  height: "100%",
                                  backgroundColor: "#10b981",
                                  transition: "width 0.3s ease",
                                }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Image Description Input */}
                    <div style={{ marginBottom: "1.5rem" }}>
                      <label
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.5rem",
                          fontSize: "0.875rem",
                          fontWeight: "500",
                          color: "#d1d5db",
                          marginBottom: "0.5rem",
                        }}
                      >
                        <MessageSquare style={{ width: "1rem", height: "1rem" }} />
                        Describe your image (optional)
                      </label>
                      <textarea
                        value={imageDescription}
                        onChange={(e) => setImageDescription(e.target.value)}
                        placeholder="Tell us about the mood, setting, or feeling of your image to get better recommendations..."
                        style={{
                          width: "100%",
                          minHeight: "4rem",
                          padding: "0.75rem",
                          backgroundColor: "#374151",
                          border: "1px solid #4b5563",
                          borderRadius: "0.375rem",
                          color: "#ffffff",
                          fontSize: "0.875rem",
                          resize: "vertical",
                          fontFamily: "inherit",
                          outline: "none",
                          transition: "border-color 0.2s",
                        }}
                        onFocus={(e) => (e.target.style.borderColor = "#10b981")}
                        onBlur={(e) => (e.target.style.borderColor = "#4b5563")}
                      />
                      <p
                        style={{
                          fontSize: "0.75rem",
                          color: "#9ca3af",
                          marginTop: "0.25rem",
                          margin: "0.25rem 0 0 0",
                        }}
                      >
                        Example: "A peaceful sunset over the ocean with warm golden colors" or "Energetic city nightlife
                        with neon lights"
                      </p>
                    </div>

                    {/* Analyze Button */}
                    {!isAnalyzing && recommendations.length === 0 && (
                      <div style={{ textAlign: "center" }}>
                        <button
                          style={{
                            backgroundColor: "#10b981",
                            color: "#000000",
                            fontWeight: "600",
                            padding: "0.75rem 2rem",
                            borderRadius: "9999px",
                            border: "none",
                            cursor: "pointer",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.5rem",
                            fontSize: "1rem",
                            transition: "background-color 0.2s",
                          }}
                          onMouseOver={(e) => (e.target.style.backgroundColor = "#059669")}
                          onMouseOut={(e) => (e.target.style.backgroundColor = "#10b981")}
                          onClick={handleAnalyzeClick}
                        >
                          <Sparkles style={{ width: "1.25rem", height: "1.25rem" }} />
                          Find My Music
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div style={{ maxWidth: "72rem", margin: "0 auto" }}>
            <div style={{ marginBottom: "2rem" }}>
              <h2
                style={{
                  fontSize: "1.875rem",
                  fontWeight: "bold",
                  color: "#ffffff",
                  marginBottom: "0.5rem",
                  margin: "0 0 0.5rem 0",
                }}
              >
                Recommended for you
              </h2>
              <p style={{ color: "#9ca3af", margin: 0 }}>
                Based on your image{imageDescription && " and description"} • {recommendations.length} songs
              </p>
            </div>

            {/* Show user's description if provided */}
            {imageDescription && (
              <div
                style={{
                  backgroundColor: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: "0.5rem",
                  padding: "1rem",
                  marginBottom: "1.5rem",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    marginBottom: "0.5rem",
                  }}
                >
                  <MessageSquare style={{ width: "1rem", height: "1rem", color: "#10b981" }} />
                  <span style={{ fontSize: "0.875rem", fontWeight: "500", color: "#d1d5db" }}>Your description:</span>
                </div>
                <p
                  style={{
                    color: "#9ca3af",
                    fontSize: "0.875rem",
                    fontStyle: "italic",
                    margin: 0,
                  }}
                >
                  "{imageDescription}"
                </p>
              </div>
            )}

            {/* Playlist Header */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 7fr 1fr 1fr",
                gap: "1rem",
                padding: "0 1rem 0.5rem",
                fontSize: "0.875rem",
                color: "#9ca3af",
                borderBottom: "1px solid #1f2937",
                marginBottom: "0.5rem",
              }}
            >
              <div>#</div>
              <div>TITLE</div>
              <div>MATCH</div>
              <div style={{ display: "flex", justifyContent: "center" }}>
                <Clock style={{ width: "1rem", height: "1rem" }} />
              </div>
            </div>

            {/* Song List */}
            <div>
              {recommendations.map((song, index) => (
                <div
                  key={song.id}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 7fr 1fr 1fr",
                    gap: "1rem",
                    padding: "0.75rem 1rem",
                    borderRadius: "0.375rem",
                    transition: "background-color 0.2s",
                    cursor: "pointer",
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "#1f2937")}
                  onMouseOut={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                >
                  <div style={{ display: "flex", alignItems: "center" }}>
                    <div style={{ width: "1rem", textAlign: "center" }}>
                      {playingId === song.id ? (
                        <div
                          style={{
                            width: "1rem",
                            height: "1rem",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                        >
                          <div style={{ display: "flex", gap: "0.125rem" }}>
                            <div
                              style={{
                                width: "0.125rem",
                                height: "0.75rem",
                                backgroundColor: "#10b981",
                                animation: "pulse 1.5s infinite",
                              }}
                            />
                            <div
                              style={{
                                width: "0.125rem",
                                height: "0.5rem",
                                backgroundColor: "#10b981",
                                animation: "pulse 1.5s infinite",
                                animationDelay: "0.1s",
                              }}
                            />
                            <div
                              style={{
                                width: "0.125rem",
                                height: "1rem",
                                backgroundColor: "#10b981",
                                animation: "pulse 1.5s infinite",
                                animationDelay: "0.2s",
                              }}
                            />
                          </div>
                        </div>
                      ) : (
                        <span style={{ color: "#9ca3af" }}>{index + 1}</span>
                      )}
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <div
                      style={{
                        width: "2.5rem",
                        height: "2.5rem",
                        backgroundColor: "#374151",
                        borderRadius: "0.25rem",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        overflow: "hidden",
                      }}
                    >
                      {song.image_url ? (
                        <img
                          src={song.image_url}
                          alt={song.title}
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      ) : (
                        <Music style={{ width: "1.25rem", height: "1.25rem", color: "#9ca3af" }} />
                      )}
                    </div>
                    <div>
                      <p
                        style={{
                          fontWeight: "500",
                          color: playingId === song.id ? "#10b981" : "#ffffff",
                          margin: "0 0 0.25rem 0",
                        }}
                      >
                        {song.title}
                      </p>
                      <p style={{ fontSize: "0.875rem", color: "#9ca3af", margin: "0 0 0.25rem 0" }}>{song.artist}</p>
                      <p style={{ fontSize: "0.75rem", color: "#6b7280", margin: 0 }}>
                        {song.segment.description} • {formatTime(song.segment.start)} - {formatTime(song.segment.end)}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center" }}>
                    <span
                      style={{
                        backgroundColor: "rgba(16, 185, 129, 0.2)",
                        color: "#34d399",
                        border: "1px solid rgba(16, 185, 129, 0.3)",
                        borderRadius: "9999px",
                        padding: "0.125rem 0.5rem",
                        fontSize: "0.75rem",
                        fontWeight: "600",
                      }}
                    >
                      {song.segment.relevanceScore !== undefined
                        ? `${Number(song.segment.relevanceScore).toFixed(2)}%`
                        : "-"}
                    </span>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <button
                      style={{
                        width: "2rem",
                        height: "2rem",
                        padding: 0,
                        backgroundColor: "transparent",
                        border: "none",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                      onClick={() => toggleLike(song.id)}
                    >
                      <Heart
                        style={{
                          width: "1rem",
                          height: "1rem",
                          color: likedSongs.has(song.id) ? "#10b981" : "#9ca3af",
                          fill: likedSongs.has(song.id) ? "#10b981" : "none",
                        }}
                      />
                    </button>
                    <span style={{ color: "#9ca3af", fontSize: "0.875rem" }}>{formatTime(song.duration)}</span>
                    {/* Song row play button logic */}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {playingId !== song.id && (
                        <button
                          style={{
                            width: "2rem",
                            height: "2rem",
                            padding: 0,
                            backgroundColor: "transparent",
                            border: "none",
                            cursor: audioLoadingId === song.id ? "wait" : "pointer",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                          onClick={() => handlePlay(song)}
                          disabled={audioLoadingId === song.id || isAnalyzing}
                        >
                          <Play style={{ width: "1rem", height: "1rem", color: "#ffffff" }} />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Audio Player for the current song */}
                  {playingId === song.id && audioUrl && (
                    <div style={{
                      gridColumn: '1 / -1',
                      margin: '0.5rem 0 1rem 0',
                      display: 'flex',
                      alignItems: 'center',
                      background: 'linear-gradient(90deg, #23272b 60%, #18181b 100%)',
                      borderRadius: 12,
                      padding: '1rem 1.5rem',
                      boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
                      gap: '1.5rem',
                      position: 'relative',
                    }}>
                      <img
                        src={song.image_url || '/placeholder.svg'}
                        alt={song.title}
                        style={{ width: 56, height: 56, borderRadius: 8, objectFit: 'cover', boxShadow: '0 2px 8px #0002' }}
                      />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, color: '#fff', fontSize: 18, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{song.title}</div>
                        <div style={{ color: '#b3b3b3', fontSize: 14, marginBottom: 4 }}>{song.artist}</div>
                        <input
                          type="range"
                          min={0}
                          max={audioElement?.duration || 0}
                          value={audioProgress}
                          onChange={e => {
                            if (audioElement) audioElement.currentTime = Number(e.target.value);
                            setAudioProgress(Number(e.target.value));
                          }}
                          style={{ width: '100%', accentColor: '#1db954' }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#b3b3b3', fontSize: 12 }}>
                          <span>{formatTime(Math.floor(audioProgress))}</span>
                          <span>{formatTime(Math.floor(audioElement?.duration || 0))}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          if (audioElement) {
                            if (audioElement.paused) audioElement.play();
                            else audioElement.pause();
                          }
                        }}
                        style={{
                          background: '#1db954',
                          border: 'none',
                          borderRadius: '50%',
                          width: 44,
                          height: 44,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          boxShadow: '0 2px 8px #0003',
                          cursor: 'pointer',
                          marginLeft: 16,
                        }}
                      >
                        {audioElement && !audioElement.paused ? (
                          <Pause style={{ width: 24, height: 24, color: '#fff' }} />
                        ) : (
                          <Play style={{ width: 24, height: 24, color: '#fff' }} />
                        )}
                      </button>
                      <audio
                        src={audioUrl}
                        controls={false}
                        autoPlay
                        ref={el => setAudioElement(el)}
                        style={{ display: 'none' }}
                        onEnded={() => setPlayingId(null)}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Segment Info */}
            <div
              style={{
                marginTop: "2rem",
                padding: "1.5rem",
                backgroundColor: "#1f2937",
                borderRadius: "0.5rem",
                border: "1px solid #1f2937",
              }}
            >
              <h3
                style={{
                  fontSize: "1.125rem",
                  fontWeight: "600",
                  color: "#ffffff",
                  marginBottom: "0.75rem",
                  margin: "0 0 0.75rem 0",
                }}
              >
                About these recommendations
              </h3>
              <p
                style={{
                  color: "#9ca3af",
                  fontSize: "0.875rem",
                  lineHeight: "1.6",
                  margin: 0,
                }}
              >
                Each song shows the most relevant segment based on your image analysis
                {imageDescription && " and description"}. The match percentage indicates how well the musical elements
                align with the visual mood, colors, and atmosphere detected in your image.
              </p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!uploadedImage && recommendations.length === 0 && (
          <div style={{ maxWidth: "72rem", margin: "0 auto" }}>
            <div
              style={{
                background: "linear-gradient(to right, #1f2937, #1f2937)",
                border: "1px solid #374151",
                borderRadius: "0.5rem",
                padding: "3rem",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.75rem",
                  fontSize: "1.5rem",
                  color: "#ffffff",
                  marginBottom: "1rem",
                }}
              >
                <Music style={{ width: "1.5rem", height: "1.5rem", color: "#0a5bb8" }} />
                Discover music through your images
              </div>
              <p
                style={{
                  color: "#9ca3af",
                  fontSize: "1.125rem",
                  margin: 0,
                }}
              >
                Upload any image and let AI find the perfect soundtrack that matches your visual vibe
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
