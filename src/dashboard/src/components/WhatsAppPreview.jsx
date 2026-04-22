/**
 * CivicPulse — WhatsApp Dispatch Preview
 * Simulates the volunteer notification experience via WhatsApp.
 * Renders as a slide-in drawer from the Dispatch Console.
 */
import { useState, useEffect } from 'react';
import { X, Check, CheckCheck } from 'lucide-react';
import './WhatsAppPreview.css';

/**
 * @param {Object}   props
 * @param {boolean}  props.open       — whether the drawer is visible
 * @param {Function} props.onClose    — close callback
 * @param {string}   props.wardName   — ward display name
 * @param {number}   props.cssScore   — CSS score for the ward
 * @param {string}   props.volunteerName — selected volunteer handle
 */
export default function WhatsAppPreview({ open, onClose, wardName, cssScore, volunteerName }) {
  const [visibleMessages, setVisibleMessages] = useState(0);

  const urgency = cssScore >= 76 ? 'CRITICAL' : cssScore >= 56 ? 'HIGH' : 'ELEVATED';
  const urgencyEmoji = cssScore >= 76 ? '🔴' : cssScore >= 56 ? '🟠' : '🟡';
  const timeNow = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });

  /* Simulated eta */
  const etaTime = new Date(Date.now() + 45 * 60 * 1000).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const messages = [
    {
      from: 'bot',
      text: `🚨 *CivicPulse Dispatch Alert*\n\n📍 Ward: *${wardName || 'WARD-DEL-007'}*\n📊 CSS Score: *${(cssScore || 72).toFixed(0)}/100*\n${urgencyEmoji} Urgency: *${urgency}*\n\nYou've been matched based on your skills and proximity.\n\nReply *YES* to accept or *NO* to pass.`,
      time: timeNow,
    },
    {
      from: 'user',
      text: 'YES',
      time: timeNow,
    },
    {
      from: 'bot',
      text: `✅ *Assignment Confirmed!*\n\n📍 Report to: *${wardName || 'Ward'} Distribution Centre*\n⏰ Arrive by: *${etaTime}*\n👤 Contact: NGO Coordinator Desk\n📞 Helpline: 1800-XXX-XXXX\n\n⏱️ Estimated duration: 2-3 hours\n\n_Thank you for your service! 🙏_`,
      time: timeNow,
    },
  ];

  /* Animate messages appearing one by one */
  useEffect(() => {
    if (open) {
      setVisibleMessages(0);
      const timers = messages.map((_, i) =>
        setTimeout(() => setVisibleMessages(i + 1), (i + 1) * 800)
      );
      return () => timers.forEach(clearTimeout);
    }
  }, [open, wardName]);

  if (!open) return null;

  return (
    <div className="wa-overlay" onClick={onClose} id="whatsapp-overlay">
      <div className="wa-drawer" onClick={(e) => e.stopPropagation()} id="whatsapp-drawer">
        {/* Phone frame */}
        <div className="wa-phone">
          {/* Status bar */}
          <div className="wa-statusbar">
            <span>●●●○○</span>
            <span>{timeNow}</span>
            <span>🔋 87%</span>
          </div>

          {/* WhatsApp header */}
          <div className="wa-header">
            <button className="wa-close" onClick={onClose} id="wa-close-btn">
              <X size={18} />
            </button>
            <div className="wa-avatar">CP</div>
            <div className="wa-contact">
              <span className="wa-contact-name">CivicPulse Bot</span>
              <span className="wa-contact-status">online</span>
            </div>
          </div>

          {/* Chat area */}
          <div className="wa-chat" id="wa-chat-area">
            <div className="wa-date-chip">Today</div>

            {messages.slice(0, visibleMessages).map((msg, i) => (
              <div
                key={i}
                className={`wa-bubble wa-bubble--${msg.from} wa-bubble--animate`}
                style={{ animationDelay: `${i * 0.15}s` }}
              >
                <div className="wa-bubble-text">
                  {msg.text.split('\n').map((line, j) => (
                    <span key={j}>
                      {line.split(/\*([^*]+)\*/g).map((part, k) =>
                        k % 2 === 1 ? <strong key={k}>{part}</strong> : part
                      )}
                      {j < msg.text.split('\n').length - 1 && <br />}
                    </span>
                  ))}
                </div>
                <span className="wa-bubble-meta">
                  {msg.time}
                  {msg.from === 'user' && <CheckCheck size={12} className="wa-ticks" />}
                  {msg.from === 'bot' && <Check size={12} className="wa-ticks" />}
                </span>
              </div>
            ))}

            {visibleMessages < messages.length && (
              <div className="wa-typing">
                <span className="wa-typing-dot" />
                <span className="wa-typing-dot" />
                <span className="wa-typing-dot" />
              </div>
            )}
          </div>

          {/* Input bar */}
          <div className="wa-input-bar">
            <div className="wa-input-field">Type a message</div>
            <div className="wa-send-btn">🎤</div>
          </div>
        </div>

        {/* Info label */}
        <p className="wa-info-label">
          Preview of volunteer dispatch notification via WhatsApp Business API.
          Actual messages are sent through Meta Business Platform.
        </p>
      </div>
    </div>
  );
}
