import { Editor } from "https://esm.sh/@tiptap/core@2.11.5";
import StarterKit from "https://esm.sh/@tiptap/starter-kit@2.11.5";
import { Markdown } from "https://esm.sh/tiptap-markdown@0.8.10";

const ICONS = {
  bold: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4h8a4 4 0 0 1 0 8H6z"/><path d="M6 12h9a4 4 0 0 1 0 8H6z"/></svg>`,
  italic: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/></svg>`,
  strike: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4H9a3 3 0 0 0-2.83 4"/><path d="M14 12a4 4 0 0 1 0 8H6"/><line x1="4" y1="12" x2="20" y2="12"/></svg>`,
  bulletList: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="9" y1="6" x2="20" y2="6"/><line x1="9" y1="12" x2="20" y2="12"/><line x1="9" y1="18" x2="20" y2="18"/><circle cx="4" cy="6" r="1.25" fill="currentColor" stroke="none"/><circle cx="4" cy="12" r="1.25" fill="currentColor" stroke="none"/><circle cx="4" cy="18" r="1.25" fill="currentColor" stroke="none"/></svg>`,
  orderedList: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="10" y1="6" x2="20" y2="6"/><line x1="10" y1="12" x2="20" y2="12"/><line x1="10" y1="18" x2="20" y2="18"/><path d="M4 6h1v4"/><path d="M4 10h2"/><path d="M5 18H4c0-1 1-2 2-2s1-1 1-2-1-2-2-2"/></svg>`,
  blockquote: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h10v10H7z"/><path d="M11 9v6"/><path d="M7 9h1"/><path d="M7 15h1"/></svg>`,
  undo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6.36 2.64L3 13"/></svg>`,
  redo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6.36 2.64L21 13"/></svg>`,
};

const TOOLBAR_GROUPS = [
  [
    { action: "bold", title: "Bold", icon: "bold" },
    { action: "italic", title: "Italic", icon: "italic" },
    { action: "strike", title: "Strikethrough", icon: "strike" },
  ],
  [
    { action: "heading2", title: "Heading 2", label: "H2", variant: "text" },
  ],
  [
    { action: "bulletList", title: "Bullet list", icon: "bulletList" },
    { action: "orderedList", title: "Numbered list", icon: "orderedList" },
    { action: "blockquote", title: "Blockquote", icon: "blockquote" },
  ],
  [
    { action: "undo", title: "Undo", icon: "undo" },
    { action: "redo", title: "Redo", icon: "redo" },
  ],
];

function runToolbarAction(editor, action) {
  const chain = editor.chain().focus();
  switch (action) {
    case "bold":
      chain.toggleBold().run();
      break;
    case "italic":
      chain.toggleItalic().run();
      break;
    case "strike":
      chain.toggleStrike().run();
      break;
    case "heading2":
      chain.toggleHeading({ level: 2 }).run();
      break;
    case "bulletList":
      chain.toggleBulletList().run();
      break;
    case "orderedList":
      chain.toggleOrderedList().run();
      break;
    case "blockquote":
      chain.toggleBlockquote().run();
      break;
    case "undo":
      chain.undo().run();
      break;
    case "redo":
      chain.redo().run();
      break;
    default:
      break;
  }
}

function isToolbarActionActive(editor, action) {
  switch (action) {
    case "bold":
      return editor.isActive("bold");
    case "italic":
      return editor.isActive("italic");
    case "strike":
      return editor.isActive("strike");
    case "heading2":
      return editor.isActive("heading", { level: 2 });
    case "bulletList":
      return editor.isActive("bulletList");
    case "orderedList":
      return editor.isActive("orderedList");
    case "blockquote":
      return editor.isActive("blockquote");
    default:
      return false;
  }
}

function createToolbarButton(editor, config, updateButtons) {
  const { action, title, icon, label, variant } = config;
  const button = document.createElement("button");
  button.type = "button";
  button.className =
    variant === "text"
      ? "richtext-toolbar-btn richtext-toolbar-btn--text"
      : "richtext-toolbar-btn";
  button.dataset.action = action;
  button.title = title;
  button.setAttribute("aria-label", title);

  if (icon && ICONS[icon]) {
    button.innerHTML = ICONS[icon];
  } else {
    button.textContent = label || "";
  }

  button.addEventListener("click", () => {
    runToolbarAction(editor, action);
    updateButtons();
  });
  return button;
}

function createToolbar(editor, toolbarMount) {
  toolbarMount.innerHTML = "";
  toolbarMount.className = "richtext-toolbar";

  const updateButtons = () => {
    toolbarMount.querySelectorAll("[data-action]").forEach((button) => {
      const action = button.getAttribute("data-action");
      button.classList.toggle("is-active", isToolbarActionActive(editor, action));
      button.disabled =
        (action === "undo" && !editor.can().undo()) ||
        (action === "redo" && !editor.can().redo());
    });
  };

  TOOLBAR_GROUPS.forEach((group, groupIndex) => {
    if (groupIndex > 0) {
      const separator = document.createElement("span");
      separator.className = "richtext-toolbar-separator";
      separator.setAttribute("aria-hidden", "true");
      toolbarMount.appendChild(separator);
    }

    const groupEl = document.createElement("div");
    groupEl.className = "richtext-toolbar-group";
    group.forEach((config) => {
      groupEl.appendChild(createToolbarButton(editor, config, updateButtons));
    });
    toolbarMount.appendChild(groupEl);
  });

  editor.on("transaction", updateButtons);
  updateButtons();
}

function initRichTextEditors() {
  document.querySelectorAll("[data-richtext]").forEach((container) => {
    if (container.dataset.richtextReady === "true") {
      return;
    }

    const toolbarMount = container.querySelector("[data-richtext-toolbar]");
    const mount = container.querySelector("[data-richtext-mount]");
    const input = container.querySelector("textarea");
    if (!toolbarMount || !mount || !input) {
      return;
    }

    const editor = new Editor({
      element: mount,
      extensions: [
        StarterKit,
        Markdown.configure({
          html: true,
          transformPastedText: true,
          transformCopiedText: true,
        }),
      ],
      content: input.value || "",
      onUpdate: ({ editor: activeEditor }) => {
        input.value = activeEditor.getHTML();
      },
    });

    createToolbar(editor, toolbarMount);

    const form = container.closest("form");
    if (form) {
      form.addEventListener("submit", () => {
        input.value = editor.getHTML();
      });
    }

    container.dataset.richtextReady = "true";
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initRichTextEditors);
} else {
  initRichTextEditors();
}
