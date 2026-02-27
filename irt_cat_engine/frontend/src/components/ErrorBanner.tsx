import type { Lang } from "../i18n/translations";

interface Props {
  lang: Lang;
  errorMessage: string | null;
  onClose: () => void;
}

export default function ErrorBanner({ lang, errorMessage, onClose }: Props) {
  if (!errorMessage) return null;

  return (
    <div style={{
      position: "fixed",
      top: "20px",
      left: "50%",
      transform: "translateX(-50%)",
      maxWidth: "500px",
      width: "90%",
      padding: "16px 20px",
      background: "#fee",
      border: "2px solid #f44336",
      borderRadius: "8px",
      boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
      zIndex: 1000,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "12px",
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: "600", color: "#c62828", marginBottom: "4px" }}>
          {lang === "ko" ? "오류" : "Error"}
        </div>
        <div style={{ fontSize: "14px", color: "#d32f2f" }}>
          {errorMessage}
        </div>
      </div>
      <button
        onClick={onClose}
        style={{
          background: "none",
          border: "none",
          fontSize: "20px",
          cursor: "pointer",
          color: "#c62828",
          padding: "4px 8px",
        }}
      >
        ✕
      </button>
    </div>
  );
}
