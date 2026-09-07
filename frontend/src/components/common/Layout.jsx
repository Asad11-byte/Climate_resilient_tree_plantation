import NavBar from "./NavBar";

export default function Layout({ children }) {
  return (
    // h-screen + overflow-hidden here, with <main> as the ONE scrollable
    // region below — this is what prevents the double-scrollbar bug.
    // Previously the outer page could scroll AND a page's own internal
    // list could scroll independently; now there's exactly one scroll
    // container, and any page that needs the full available height (like
    // the chat) can use h-full against <main> and get an exact fit
    // instead of guessing a pixel offset for the nav's height.
    <div className="flex h-screen flex-col overflow-hidden bg-page text-soil-900">
      <NavBar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto h-full max-w-6xl px-4 py-6 sm:px-6 sm:py-8">{children}</div>
      </main>
    </div>
  );
}