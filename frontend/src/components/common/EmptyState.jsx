/**
 * Generic empty-state shell. Callers own the copy, since "no data seeded
 * yet" and "no evidence for this query" are different concepts and should
 * read differently — see title/description.
 */
export default function EmptyState({ title, description, action, className = "" }) {
  return (
    <div className={`rounded-lg border border-dashed border-bark-500/30 px-5 py-8 text-center ${className}`}>
      <p className="font-medium text-soil-900">{title}</p>
      {description && <p className="mt-1 text-sm text-bark-700">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
