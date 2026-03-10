/* content.css — Overlay button styles injected on rule34.xxx */

.r34-bl-btn {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;

  padding: 3px 8px;
  font-size: 11px;
  font-family: sans-serif;
  font-weight: bold;
  line-height: 1.3;
  white-space: nowrap;

  color: #fff;
  background: rgba(20, 20, 20, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 4px;
  cursor: pointer;

  /* Hidden until parent is hovered — keeps the UI clean */
  opacity: 0;
  transition: opacity 0.15s ease, background 0.15s ease;
  pointer-events: none;
}

/* Show on hover of the parent thumb */
.thumb:hover .r34-bl-btn {
  opacity: 1;
  pointer-events: auto;
}

/* Already-blacklisted posts always show the button (so you can unblacklist) */
.r34-bl-btn--active {
  opacity: 1 !important;
  pointer-events: auto !important;
  background: rgba(180, 30, 30, 0.88) !important;
  border-color: rgba(255, 100, 100, 0.4) !important;
}

.r34-bl-btn:hover {
  background: rgba(180, 30, 30, 0.92);
}

/* Full view-page variant — larger, fixed position near the image */
.r34-bl-btn--view {
  position: absolute;
  top: 8px;
  left: 8px;
  bottom: auto;
  transform: none;
  font-size: 13px;
  padding: 5px 12px;
  opacity: 1;
  pointer-events: auto;
}
