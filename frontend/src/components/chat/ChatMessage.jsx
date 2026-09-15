import SourceList from "./SourceList";
import MarkdownAnswer from "./MarkdownAnswer";
import SpeciesMentionChips from "./SpeciesMentionChips";

function UserAvatar() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-soil-700 text-xs font-semibold text-white">
      You
    </div>
  );
}

function AssistantAvatar() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-900">
      <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-brand-400">
        <path
          d="M12 3c-4 3-7 6.5-7 10.5A7 7 0 0 0 12 21a7 7 0 0 0 7-7.5C19 9.5 16 6 12 3Z"
          fill="currentColor"
          fillOpacity="0.9"
        />
        <path d="M12 21V11" stroke="#0f523b" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    </div>
  );
}

function UserBubble({ text }) {
  return (
    <div className="flex justify-end gap-2.5">
      <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-leaf-700 px-4 py-2.5 text-sm text-parchment-50 shadow-sm">
        {text}
      </div>
      <UserAvatar />
    </div>
  );
}

function NoEvidenceCard({ response }) {
  return (
    <div className="max-w-[85%] rounded-lg border border-amber-500/40 bg-warning-subtle px-4 py-3 shadow-sm">
      <div className="flex items-center gap-1.5">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-3.5 w-3.5 text-amber-500">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4M12 16.5h.01M10.3 3.9 2.5 17.5A1.8 1.8 0 0 0 4 20h16a1.8 1.8 0 0 0 1.55-2.5L13.7 3.9a1.8 1.8 0 0 0-3.1 0Z" />
        </svg>
        <p className="text-xs font-semibold uppercase tracking-wide text-amber-500">No evidence found</p>
      </div>
      <MarkdownAnswer className="mt-1.5">{response.answer}</MarkdownAnswer>
    </div>
  );
}

const PLANT_CATEGORIES = ["tree_species", "plantation"];

function LeafBadge() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-leaf-600 shrink-0">
      <path
        d="M12 3c-4 3-7 6.5-7 10.5A7 7 0 0 0 12 21a7 7 0 0 0 7-7.5C19 9.5 16 6 12 3Z"
        fill="currentColor"
        fillOpacity="0.9"
      />
      <path d="M12 21V11" stroke="var(--color-card)" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function AnswerCard({ response }) {
  const isPlantRecommendation = PLANT_CATEGORIES.includes(response.query_category);

  return (
    <div className="max-w-[85%] rounded-lg border border-bark-500/15 bg-card px-4 py-3 shadow-sm">
      {response.query_category && (
        <p className="flex items-center gap-1.5 text-[0.7rem] font-semibold uppercase tracking-wide text-leaf-700">
          {isPlantRecommendation && <LeafBadge />}
          {response.query_category.replace("_", " ")}
        </p>
      )}
      <MarkdownAnswer className="mt-1">{response.answer}</MarkdownAnswer>
      <SpeciesMentionChips species={response.mentioned_species} />
      <SourceList sources={response.sources} />
    </div>
  );
}

export default function ChatMessage({ message }) {
  if (message.role === "user") {
    return <UserBubble text={message.text} />;
  }

  const { response } = message;
  return (
    <div className="flex justify-start gap-2.5">
      <AssistantAvatar />
      {response.evidence_available ? <AnswerCard response={response} /> : <NoEvidenceCard response={response} />}
    </div>
  );
}