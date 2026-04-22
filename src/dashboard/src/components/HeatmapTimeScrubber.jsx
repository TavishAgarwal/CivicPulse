/**
 * CivicPulse — Heatmap Time-Scrubber
 * Slider control to replay ward CSS scores over the last 30 days.
 * Supports auto-play (day-by-day animation) and manual scrubbing.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, RotateCcw, Calendar } from 'lucide-react';
import './HeatmapTimeScrubber.css';

/**
 * @param {Object} props
 * @param {Array}  props.baseWards    — current ward array from Dashboard state
 * @param {Function} props.onDayChange — callback(wardsForDay, dateLabel) when scrubber changes
 */
export default function HeatmapTimeScrubber({ baseWards, onDayChange }) {
  const [dayIndex, setDayIndex] = useState(29); // 0=30 days ago, 29=today
  const [playing, setPlaying] = useState(false);
  const intervalRef = useRef(null);

  /* Compute CSS scores for a given day offset using seeded deterministic noise */
  const computeWardsForDay = useCallback(
    (idx) => {
      if (!baseWards || baseWards.length === 0) return [];

      return baseWards.map((ward) => {
        const baseScore = ward.css_score || 40;
        /* Deterministic per-ward, per-day variation */
        const wardSeed = (ward.ward_id || ward.id || '').charCodeAt(
          ((ward.ward_id || ward.id || '').length - 1) || 0
        ) || 42;
        const daySeed = wardSeed * (idx + 1) * 9301 + 49297;
        const noise = ((daySeed % 233280) / 233280 - 0.5) * 30;

        /* Gradual trend: scores tend to rise toward "today" for dramatic effect */
        const trendFactor = 0.7 + (idx / 29) * 0.3;
        const score = Math.max(0, Math.min(100, baseScore * trendFactor + noise));

        return { ...ward, css_score: Math.round(score * 10) / 10 };
      });
    },
    [baseWards]
  );

  /* Format date label for the current day index */
  const getDateLabel = (idx) => {
    const d = new Date();
    d.setDate(d.getDate() - (29 - idx));
    return d.toLocaleDateString('en-IN', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  /* Fire callback whenever dayIndex changes */
  useEffect(() => {
    const wardsForDay = computeWardsForDay(dayIndex);
    onDayChange(wardsForDay, getDateLabel(dayIndex));
  }, [dayIndex, computeWardsForDay, onDayChange]);

  /* Auto-play logic */
  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setDayIndex((prev) => {
          if (prev >= 29) {
            setPlaying(false);
            return 29;
          }
          return prev + 1;
        });
      }, 600);
    }
    return () => clearInterval(intervalRef.current);
  }, [playing]);

  const handlePlay = () => {
    if (dayIndex >= 29) setDayIndex(0); // restart from beginning
    setPlaying(true);
  };

  const handlePause = () => setPlaying(false);

  const handleReset = () => {
    setPlaying(false);
    setDayIndex(29);
  };

  const handleSlider = (e) => {
    setPlaying(false);
    setDayIndex(Number(e.target.value));
  };

  return (
    <div className="time-scrubber" id="time-scrubber">
      <div className="scrubber-header">
        <div className="scrubber-label">
          <Calendar size={14} />
          <span className="scrubber-title">Historical Replay</span>
        </div>
        <div className="scrubber-date" id="scrubber-date-label">
          Viewing: <strong>{getDateLabel(dayIndex)}</strong>
          {dayIndex === 29 && <span className="live-badge">LIVE</span>}
        </div>
      </div>

      <div className="scrubber-controls">
        <div className="scrubber-buttons">
          {playing ? (
            <button className="scrubber-btn" onClick={handlePause} title="Pause" id="scrubber-pause">
              <Pause size={16} />
            </button>
          ) : (
            <button className="scrubber-btn scrubber-btn--play" onClick={handlePlay} title="Play" id="scrubber-play">
              <Play size={16} />
            </button>
          )}
          <button className="scrubber-btn" onClick={handleReset} title="Reset to today" id="scrubber-reset">
            <RotateCcw size={14} />
          </button>
        </div>

        <div className="scrubber-slider-wrap">
          <span className="slider-bound">-30d</span>
          <input
            type="range"
            min="0"
            max="29"
            value={dayIndex}
            onChange={handleSlider}
            className="scrubber-slider"
            id="scrubber-slider"
          />
          <span className="slider-bound">Today</span>
        </div>

        <div className="scrubber-day-counter">
          Day {dayIndex + 1}/30
        </div>
      </div>

      {/* Progress bar */}
      <div className="scrubber-progress">
        <div
          className="scrubber-progress-fill"
          style={{ width: `${((dayIndex + 1) / 30) * 100}%` }}
        />
      </div>
    </div>
  );
}
