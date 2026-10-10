// st.markdown strips <script>, so the Streamlit page can't run its own JS. This
// bundle already runs in a same-origin iframe (components.html), so it enhances
// the parent page: once-only scroll reveals for [data-reveal] and pointer-tracked
// spotlights for .spot. If this never runs, html.js-reveal is never set and the
// page renders every element in its final, fully visible state.

type ParentWindow = Window & typeof globalThis & { __fjdEnhanceCleanup?: () => void }

export function enhanceParent() {
  let win: ParentWindow
  let doc: Document
  try {
    win = window.parent as ParentWindow
    doc = win.document
  } catch {
    return
  }
  if (win === (window as Window)) return

  // Streamlit can remount this iframe; listeners owned by a dead iframe realm stop
  // working, so the newest iframe tears down the previous one's and takes over.
  win.__fjdEnhanceCleanup?.()

  const io = new win.IntersectionObserver(
    entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        entry.target.classList.add('in')
        io.unobserve(entry.target)
      }
    },
    { rootMargin: '0px 0px -12% 0px', threshold: 0.15 },
  )
  const scan = () => {
    doc.querySelectorAll('[data-reveal]:not(.in)').forEach(el => io.observe(el))
  }
  scan()
  // Streamlit re-renders markdown on reruns (e.g. after an example button click).
  const mo = new win.MutationObserver(scan)
  mo.observe(doc.body, { childList: true, subtree: true })
  doc.documentElement.classList.add('js-reveal')

  const finePointer = win.matchMedia('(hover: hover) and (pointer: fine)')
  const onMove = (ev: PointerEvent) => {
    if (!finePointer.matches) return
    const card = (ev.target as Element | null)?.closest?.('.spot') as HTMLElement | null
    if (!card) return
    const rect = card.getBoundingClientRect()
    card.style.setProperty('--mx', `${ev.clientX - rect.left}px`)
    card.style.setProperty('--my', `${ev.clientY - rect.top}px`)
  }
  doc.addEventListener('pointermove', onMove, { passive: true })

  const cleanup = () => {
    io.disconnect()
    mo.disconnect()
    doc.removeEventListener('pointermove', onMove)
    if (win.__fjdEnhanceCleanup === cleanup) win.__fjdEnhanceCleanup = undefined
  }
  win.__fjdEnhanceCleanup = cleanup
  window.addEventListener('pagehide', cleanup)
}
