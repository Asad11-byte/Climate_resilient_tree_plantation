export default function LeafPlaceholderIcon({ className }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M11 20A7 7 0 0 1 4 13c0-6 5-11 15-11 0 10-5 15-11 15Z" />
      <path d="M4 20 15 9" />
    </svg>
  );
}