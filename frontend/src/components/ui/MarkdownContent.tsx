import React from 'react';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

/**
 * Safe, zero-dependency Markdown renderer tailored for Copilot conversational outputs.
 * Parses headings, bullet/numbered lists, bold/italic formatting, inline code,
 * fenced code blocks, blockquotes, and comparison tables without dangerouslySetInnerHTML.
 */
export const MarkdownContent: React.FC<MarkdownContentProps> = ({ content, className = '' }) => {
  // Normalize and unpack if someone passes stringified JSON
  let normalized = content || '';
  if ((normalized.startsWith('{') && normalized.endsWith('}')) || (normalized.startsWith('[') && normalized.endsWith(']'))) {
    try {
      const parsed = JSON.parse(normalized);
      if (typeof parsed === 'object' && parsed !== null) {
        if ('answer' in parsed && typeof parsed.answer === 'string') {
          normalized = parsed.answer;
        } else if ('response' in parsed && typeof parsed.response === 'string') {
          normalized = parsed.response;
        } else if ('message' in parsed && typeof parsed.message === 'string') {
          normalized = parsed.message;
        } else {
          // Format keys as markdown
          normalized = Object.entries(parsed)
            .map(([k, v]) => {
              const title = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
              if (Array.isArray(v)) {
                return `### ${title}\n` + v.map((item) => `- ${item}`).join('\n');
              }
              if (typeof v === 'object' && v !== null) {
                return (
                  `### ${title}\n` +
                  Object.entries(v)
                    .map(([sk, sv]) => `- **${sk.replace(/_/g, ' ')}**: ${sv}`)
                    .join('\n')
                );
              }
              return `**${title}**: ${v}`;
            })
            .join('\n\n');
        }
      }
    } catch {
      // Not JSON, continue with raw string
    }
  }

  // Parse lines into high-level blocks
  const blocks = parseBlocks(normalized);

  return (
    <div className={`space-y-3 leading-relaxed text-slate-800 text-xs sm:text-sm ${className}`}>
      {blocks.map((block, i) => renderBlock(block, i))}
    </div>
  );
};

// ----------------------------------------------------------------------------
// Block Parser
// ----------------------------------------------------------------------------
type BlockType =
  | { type: 'heading'; level: number; text: string }
  | { type: 'code'; language: string; code: string }
  | { type: 'table'; headers: string[]; rows: string[][] }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] }
  | { type: 'blockquote'; text: string }
  | { type: 'hr' }
  | { type: 'paragraph'; text: string };

function parseBlocks(markdown: string): BlockType[] {
  const lines = markdown.split(/\r?\n/);
  const blocks: BlockType[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Empty lines
    if (!trimmed) {
      i++;
      continue;
    }

    // Fenced code block (```lang)
    if (trimmed.startsWith('```')) {
      const language = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++; // skip closing ```
      blocks.push({ type: 'code', language, code: codeLines.join('\n') });
      continue;
    }

    // Horizontal rule (--- or ***)
    if (trimmed === '---' || trimmed === '***' || trimmed === '___') {
      blocks.push({ type: 'hr' });
      i++;
      continue;
    }

    // Headings (#, ##, ###, ####)
    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      blocks.push({
        type: 'heading',
        level: headingMatch[1].length,
        text: headingMatch[2].trim(),
      });
      i++;
      continue;
    }

    // Blockquote (> )
    if (line.startsWith('>')) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].replace(/^>\s?/, ''));
        i++;
      }
      blocks.push({ type: 'blockquote', text: quoteLines.join(' ') });
      continue;
    }

    // Table detection (| col1 | col2 |)
    if (trimmed.startsWith('|') && trimmed.endsWith('|') && i + 1 < lines.length && lines[i + 1].includes('---')) {
      const headers = trimmed
        .split('|')
        .slice(1, -1)
        .map((h) => h.trim());
      i += 2; // skip header and divider line
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        const rowCells = lines[i]
          .trim()
          .split('|')
          .slice(1, -1)
          .map((c) => c.trim());
        rows.push(rowCells);
        i++;
      }
      blocks.push({ type: 'table', headers, rows });
      continue;
    }

    // Unordered List (- , * , • )
    if (/^[-*•]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*•]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*•]\s+/, ''));
        i++;
      }
      blocks.push({ type: 'ul', items });
      continue;
    }

    // Ordered List (1. , 2. )
    if (/^\d+\.\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s+/, ''));
        i++;
      }
      blocks.push({ type: 'ol', items });
      continue;
    }

    // Regular paragraph (accumulate consecutive non-empty lines)
    const paragraphLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith('#') &&
      !lines[i].trim().startsWith('```') &&
      !lines[i].trim().startsWith('>') &&
      !lines[i].trim().startsWith('|') &&
      !/^[-*•]\s+/.test(lines[i].trim()) &&
      !/^\d+\.\s+/.test(lines[i].trim()) &&
      lines[i].trim() !== '---'
    ) {
      paragraphLines.push(lines[i].trim());
      i++;
    }
    if (paragraphLines.length > 0) {
      blocks.push({ type: 'paragraph', text: paragraphLines.join(' ') });
    }
  }

  return blocks;
}

// ----------------------------------------------------------------------------
// Block Renderer
// ----------------------------------------------------------------------------
function renderBlock(block: BlockType, key: number) {
  switch (block.type) {
    case 'heading': {
      if (block.level === 1) {
        return (
          <h1 key={key} className="text-base sm:text-lg font-extrabold text-slate-900 mt-3 mb-1 border-b pb-1">
            {renderInline(block.text)}
          </h1>
        );
      }
      if (block.level === 2) {
        return (
          <h2 key={key} className="text-sm sm:text-base font-bold text-slate-900 mt-2.5 mb-1">
            {renderInline(block.text)}
          </h2>
        );
      }
      if (block.level === 3) {
        return (
          <h3 key={key} className="text-xs sm:text-sm font-semibold text-indigo-950 mt-2 mb-0.5">
            {renderInline(block.text)}
          </h3>
        );
      }
      return (
        <h4 key={key} className="text-xs font-semibold uppercase tracking-wider text-slate-700 mt-1.5 mb-0.5">
          {renderInline(block.text)}
        </h4>
      );
    }

    case 'code':
      return (
        <div key={key} className="my-2 rounded-xl overflow-hidden bg-slate-900 text-slate-100 font-mono text-[11px] sm:text-xs">
          {block.language && (
            <div className="bg-slate-800 px-3 py-1 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              {block.language}
            </div>
          )}
          <pre className="p-3 overflow-x-auto">
            <code>{block.code}</code>
          </pre>
        </div>
      );

    case 'table':
      return (
        <div key={key} className="my-3 overflow-x-auto border border-slate-200 rounded-xl">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold">
              <tr>
                {block.headers.map((h, hi) => (
                  <th key={hi} className="px-3 py-2">
                    {renderInline(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {block.rows.map((row, ri) => (
                <tr key={ri} className="hover:bg-slate-50/50">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-3 py-2 text-slate-700">
                      {renderInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

    case 'ul':
      return (
        <ul key={key} className="space-y-1.5 my-1.5 pl-1">
          {block.items.map((item, ii) => (
            <li key={ii} className="flex items-start gap-2 text-slate-700">
              <span className="text-indigo-600 font-bold shrink-0 mt-0.5">•</span>
              <span className="flex-1">{renderInline(item)}</span>
            </li>
          ))}
        </ul>
      );

    case 'ol':
      return (
        <ol key={key} className="space-y-1.5 my-1.5 pl-1">
          {block.items.map((item, ii) => (
            <li key={ii} className="flex items-start gap-2 text-slate-700">
              <span className="font-bold text-indigo-700 text-xs shrink-0 mt-0.5">{ii + 1}.</span>
              <span className="flex-1">{renderInline(item)}</span>
            </li>
          ))}
        </ol>
      );

    case 'blockquote':
      return (
        <blockquote
          key={key}
          className="border-l-4 border-indigo-400 bg-indigo-50/40 px-3.5 py-2 my-2 rounded-r-lg italic text-slate-700"
        >
          {renderInline(block.text)}
        </blockquote>
      );

    case 'hr':
      return <hr key={key} className="my-3 border-slate-200" />;

    case 'paragraph':
    default:
      return (
        <p key={key} className="text-slate-800 leading-relaxed my-1">
          {renderInline(block.text)}
        </p>
      );
  }
}

// ----------------------------------------------------------------------------
// Inline Parser (Bold, Italic, Inline Code, Safe Links)
// ----------------------------------------------------------------------------
function renderInline(text: string): React.ReactNode[] {
  if (!text) return [];

  // Match token patterns: bold, italic, code, link
  const tokenRegex = /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*]+\*|_[^_]+_)/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, index) => {
    if (!part) return null;

    // Bold (**text** or __text__)
    if ((part.startsWith('**') && part.endsWith('**')) || (part.startsWith('__') && part.endsWith('__'))) {
      return (
        <strong key={index} className="font-bold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      );
    }

    // Inline Code (`code`)
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={index}
          className="px-1.5 py-0.5 rounded bg-slate-100 text-indigo-700 font-mono text-[11px] border border-slate-200"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    // Link ([text](url)) - Only accept safe http/https schemes
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      const label = linkMatch[1];
      const url = linkMatch[2];
      const isSafe = /^https?:\/\//i.test(url);
      if (isSafe) {
        return (
          <a
            key={index}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 underline hover:text-indigo-800"
          >
            {label}
          </a>
        );
      }
      return <span key={index}>{label}</span>;
    }

    // Italic (*text* or _text_)
    if ((part.startsWith('*') && part.endsWith('*')) || (part.startsWith('_') && part.endsWith('_'))) {
      return (
        <em key={index} className="italic text-slate-700">
          {part.slice(1, -1)}
        </em>
      );
    }

    // Normal text segment
    return <span key={index}>{part}</span>;
  });
}
