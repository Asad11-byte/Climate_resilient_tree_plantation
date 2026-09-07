import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * The backend's /chat answer is Groq's structured markdown (Recommendation
 * / Why / Environmental Context / Evidence / Sources / Uncertainty
 * sections, with headers, bold, and bullet lists) — this renders it
 * properly instead of dumping it as plain text with literal ** and #
 * characters. Every element is restyled to match the app's own type and
 * color tokens rather than react-markdown's unstyled defaults.
 */
export default function MarkdownAnswer({ children, className = "" }) {
  return (
    <div className={`text-sm leading-relaxed text-soil-900 ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h3 className="mt-3 font-[var(--font-display)] text-base font-semibold text-soil-900 first:mt-0">
              {children}
            </h3>
          ),
          h2: ({ children }) => (
            <h4 className="mt-3 text-[0.8rem] font-semibold uppercase tracking-wide text-leaf-700 first:mt-0">
              {children}
            </h4>
          ),
          h3: ({ children }) => (
            <h5 className="mt-2.5 text-sm font-semibold text-soil-900 first:mt-0">{children}</h5>
          ),
          p: ({ children }) => <p className="mt-2 first:mt-0">{children}</p>,
          ul: ({ children }) => <ul className="mt-2 list-disc space-y-1 pl-5">{children}</ul>,
          ol: ({ children }) => <ol className="mt-2 list-decimal space-y-1 pl-5">{children}</ol>,
          li: ({ children }) => <li className="pl-0.5">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-soil-900">{children}</strong>,
          em: ({ children }) => <em className="text-bark-700">{children}</em>,
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-leaf-600/40 underline-offset-2 hover:decoration-leaf-600"
            >
              {children}
            </a>
          ),
          code: ({ children }) => (
            <code className="rounded bg-panel px-1 py-0.5 font-[var(--font-mono)] text-[0.8em] text-soil-900">
              {children}
            </code>
          ),
          blockquote: ({ children }) => (
            <blockquote className="mt-2 border-l-2 border-leaf-600/30 pl-3 text-bark-700">{children}</blockquote>
          ),
          hr: () => <hr className="my-3 border-bark-500/15" />,
          table: ({ children }) => (
            <div className="mt-2 overflow-x-auto">
              <table className="w-full border-collapse text-sm">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border-b border-bark-500/20 px-2 py-1 text-left font-medium text-bark-700">
              {children}
            </th>
          ),
          td: ({ children }) => <td className="border-b border-bark-500/10 px-2 py-1">{children}</td>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}