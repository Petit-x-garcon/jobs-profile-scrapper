const SECTION =
  /^(?:#{1,6}\s+)?(?:\*\*)?((?:job\s+)?(?:description|requirements?|responsibilities|qualifications|benefits)|preferred qualifications|work location)\s*(?:\*\*)?\s*(?:[:–—-]\s*(?:\*\*\s*)?(.*))?$/i
const BULLET = /^(?:[-*+•▪◦●]|\d+[.)])\s+/

const LABEL = /^([^\s:][^:.!?]{0,64}:)(?:\s+(\S.*))?$/

type DescriptionBlock = {
  kind: "paragraph" | "bullets" | "numbered" | "label"
  lines: string[]
}

export function formatJobDescription(description: string) {
  const sections = [
    { title: "Job description", blocks: [] as DescriptionBlock[] },
  ]
  let section = sections[0]!
  let block: DescriptionBlock | undefined

  for (const rawLine of description.split(/\r?\n/)) {
    const line = rawLine.trim()
    const heading = line.match(SECTION)
    if (heading?.[1]) {
      section = { title: heading[1], blocks: [] }
      sections.push(section)
      block = undefined
      if (!heading[2]) continue
    }
    const content = heading?.[2] ?? line
    if (!content) {
      block = undefined
      continue
    }
    const label = content.match(LABEL)
    if (label && !label[2] && !BULLET.test(content)) {
      section.blocks.push({ kind: "label", lines: [content] })
      block = undefined
      continue
    }
    const kind = !BULLET.test(content)
      ? "paragraph"
      : /^\d/.test(content)
        ? "numbered"
        : "bullets"
    if (block?.kind !== kind) {
      block = { kind, lines: [] }
      section.blocks.push(block)
    }
    block.lines.push(content.replace(BULLET, ""))
  }

  return sections.filter(({ blocks }) => blocks.length)
}

function DescriptionLine({ line }: { line: string }) {
  const label = line.match(LABEL)
  return label?.[2] ? (
    <>
      <strong className="font-semibold text-foreground">{label[1]}</strong>{" "}
      {label[2]}
    </>
  ) : (
    line
  )
}

export function JobDescription({ description }: { description: string }) {
  const sections = formatJobDescription(description)

  if (!sections.length) {
    return <p className="text-muted-foreground">No description available.</p>
  }

  return sections.map(({ title, blocks }, index) => (
    <section key={index} className="space-y-3">
      <h2 className="text-base font-semibold capitalize">{title}</h2>
      {blocks.map(({ kind, lines }, index) => {
        if (kind === "label") {
          return (
            <h3
              key={index}
              className="mt-4 -mb-1 font-semibold text-foreground"
            >
              {lines[0]?.replace(/:$/, "")}
            </h3>
          )
        }
        // Scraped HTML lists can arrive as plain lines under a requirements heading.
        if (
          kind === "paragraph" &&
          lines.length > 1 &&
          /requirements?|qualifications/i.test(title)
        ) {
          kind = "bullets"
        }
        if (kind === "paragraph") {
          return (
            <div
              key={index}
              className="space-y-3 leading-relaxed text-muted-foreground"
            >
              {lines.map((line, index) => (
                <p key={index}>
                  <DescriptionLine line={line} />
                </p>
              ))}
            </div>
          )
        }
        const List = kind === "numbered" ? "ol" : "ul"
        return (
          <List
            key={index}
            className={
              kind === "numbered"
                ? "list-decimal space-y-1 pl-5 text-muted-foreground"
                : "list-disc space-y-1 pl-5 text-muted-foreground"
            }
          >
            {lines.map((line, index) => (
              <li key={index}>
                <DescriptionLine line={line} />
              </li>
            ))}
          </List>
        )
      })}
    </section>
  ))
}
