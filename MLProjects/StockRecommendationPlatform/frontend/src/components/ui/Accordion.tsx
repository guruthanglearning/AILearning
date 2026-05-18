"use client";

import { useState } from "react";

interface AccordionProps {
  title: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export function Accordion({ title, children, defaultOpen = false }: AccordionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-200 bg-gray-900 hover:bg-gray-800 transition-colors"
      >
        <span>{title}</span>
        <span className={`transition-transform text-gray-500 ${open ? "rotate-180" : ""}`}>
          ▾
        </span>
      </button>
      {open && <div className="px-4 py-3 bg-gray-950">{children}</div>}
    </div>
  );
}
