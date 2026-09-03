import SourceList from "./SourceList";

function UserBubble({ text }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-leaf-700 px-4 py-2.5 text-parchment-50">
        {text}
      </div>
    </div>
  );
}

function NoEvidenceCard({ response }) {
  return (
    <div className="max-w-[85%] rounded-lg border-2 border-dashed border-amber-500/50 bg-amber-500/5 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-500">No evidence found</p>
      <p className="mt-1.5 whitespace-pre-line text-sm text-soil-900">{response.answer}</p>
    </div>
  );
}

function AnswerCard({ response }) {
  return (
    <div className="max-w-[85%] rounded-lg border border-bark-500/15 bg-white/60 px-4 py-3">
      {response.query_category && (
        <p className="text-xs font-medium uppercase tracking-wide text-leaf-700">
          {response.query_category.replace("_", " ")}
        </p>
      )}
      <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-soil-900">{response.answer}</p>
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
    <div className="flex justify-start">
      {response.evidence_available ? <AnswerCard response={response} /> : <NoEvidenceCard response={response} />}
    </div>
  );
}
