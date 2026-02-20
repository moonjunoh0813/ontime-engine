export default function PlacePicker({ open, title, options, onSelect, onClose }) {
  if (!open) {
    return null;
  }

  return (
    <div className="picker-overlay" onClick={onClose}>
      <div
        className="picker-sheet"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="picker-head">
          <strong>{title}</strong>
          <button type="button" className="ghost-btn" onClick={onClose}>
            닫기
          </button>
        </div>
        <div className="picker-options">
          {options.map((option) => (
            <button
              key={option}
              type="button"
              className="picker-option"
              onClick={() => {
                onSelect(option);
                onClose();
              }}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
