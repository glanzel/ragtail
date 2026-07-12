import { Editor } from "@tiptap/core";
import Link from "@tiptap/extension-link";
import StarterKit from "@tiptap/starter-kit";
import { Markdown } from "tiptap-markdown";

const ICON_SVG =
  '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';

const TOOLBAR_ICONS = {
  bold: `${ICON_SVG}<path d="M6 4h8a4 4 0 0 1 0 8H6z"/><path d="M6 12h9a4 4 0 0 1 0 8H6z"/></svg>`,
  italic: `${ICON_SVG}<line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/></svg>`,
  strike: `${ICON_SVG}<path d="M16 4H9a3 3 0 0 0-2.83 4"/><path d="M14 12a4 4 0 0 1 0 8H6"/><line x1="4" y1="12" x2="20" y2="12"/></svg>`,
  link: `${ICON_SVG}<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`,
  bulletList: `${ICON_SVG}<line x1="9" y1="6" x2="20" y2="6"/><line x1="9" y1="12" x2="20" y2="12"/><line x1="9" y1="18" x2="20" y2="18"/><circle cx="4" cy="6" r="1.25" fill="currentColor" stroke="none"/><circle cx="4" cy="12" r="1.25" fill="currentColor" stroke="none"/><circle cx="4" cy="18" r="1.25" fill="currentColor" stroke="none"/></svg>`,
  orderedList: `${ICON_SVG}<line x1="10" y1="6" x2="20" y2="6"/><line x1="10" y1="12" x2="20" y2="12"/><line x1="10" y1="18" x2="20" y2="18"/><path d="M4 6h1v4"/><path d="M4 10h2"/><path d="M5 18H4c0-1 1-2 2-2s1-1 1-2-1-2-2-2"/></svg>`,
  blockquote: `${ICON_SVG}<path d="M7 7h10v10H7z"/><path d="M11 9v6"/><path d="M7 9h1"/><path d="M7 15h1"/></svg>`,
  undo: `${ICON_SVG}<path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6.36 2.64L3 13"/></svg>`,
  redo: `${ICON_SVG}<path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6.36 2.64L21 13"/></svg>`,
};

function toolbarButton(action, title, content, textButton = false) {
  const classes = textButton
    ? "richtext-toolbar-btn richtext-toolbar-btn--text"
    : "richtext-toolbar-btn";
  return `<button type="button" class="${classes}" data-action="${action}" title="${title}" aria-label="${title}">${content}</button>`;
}

export function runToolbarAction(editor, action) {
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
    case "link": {
      const previousUrl = editor.getAttributes("link").href;
      const url = window.prompt("URL", previousUrl);
      if (url === null) {
        break;
      }
      if (url === "") {
        editor.chain().focus().extendMarkRange("link").unsetLink().run();
      } else {
        editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
      }
      break;
    }
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

export function isToolbarActionActive(editor, action) {
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
    case "link":
      return editor.isActive("link");
    default:
      return false;
  }
}

export function bindToolbar(editor, toolbarMount) {
  const updateButtons = () => {
    toolbarMount.querySelectorAll("[data-action]").forEach((button) => {
      const action = button.getAttribute("data-action");
      button.classList.toggle("is-active", isToolbarActionActive(editor, action));
      button.disabled =
        (action === "undo" && !editor.can().undo()) ||
        (action === "redo" && !editor.can().redo());
    });
  };

  toolbarMount.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      runToolbarAction(editor, button.getAttribute("data-action"));
      updateButtons();
    });
  });

  editor.on("transaction", updateButtons);
  updateButtons();
}

export function createToolbarElement() {
  const toolbar = document.createElement("div");
  toolbar.className = "richtext-toolbar";
  toolbar.setAttribute("data-richtext-toolbar", "");
  toolbar.setAttribute("role", "toolbar");
  toolbar.setAttribute("aria-label", "Formatting");
  toolbar.innerHTML = `
    <div class="richtext-toolbar-group">
      ${toolbarButton("bold", "Bold", TOOLBAR_ICONS.bold)}
      ${toolbarButton("italic", "Italic", TOOLBAR_ICONS.italic)}
      ${toolbarButton("strike", "Strikethrough", TOOLBAR_ICONS.strike)}
      ${toolbarButton("link", "Link", TOOLBAR_ICONS.link)}
    </div>
    <span class="richtext-toolbar-separator" aria-hidden="true"></span>
    <div class="richtext-toolbar-group">
      ${toolbarButton("heading2", "Heading 2", "H2", true)}
    </div>
    <span class="richtext-toolbar-separator" aria-hidden="true"></span>
    <div class="richtext-toolbar-group">
      ${toolbarButton("bulletList", "Bullet list", TOOLBAR_ICONS.bulletList)}
      ${toolbarButton("orderedList", "Numbered list", TOOLBAR_ICONS.orderedList)}
      ${toolbarButton("blockquote", "Blockquote", TOOLBAR_ICONS.blockquote)}
    </div>
    <span class="richtext-toolbar-separator" aria-hidden="true"></span>
    <div class="richtext-toolbar-group">
      ${toolbarButton("undo", "Undo", TOOLBAR_ICONS.undo)}
      ${toolbarButton("redo", "Redo", TOOLBAR_ICONS.redo)}
    </div>
  `;
  return toolbar;
}

function linkExtension() {
  return Link.configure({
    openOnClick: false,
    autolink: true,
    linkOnPaste: true,
  });
}

export function createHtmlEditor({ mount, toolbarMount, initialHtml }) {
  const editor = new Editor({
    element: mount,
    extensions: [
      StarterKit.configure({
        codeBlock: false,
      }),
      linkExtension(),
    ],
    content: initialHtml || "",
  });
  bindToolbar(editor, toolbarMount);
  return editor;
}

export function createMarkdownEditor({ mount, toolbarMount, initialMarkdown }) {
  const editor = new Editor({
    element: mount,
    extensions: [
      StarterKit.configure({
        codeBlock: false,
      }),
      linkExtension(),
      Markdown.configure({
        html: false,
        transformPastedText: true,
        transformCopiedText: true,
      }),
    ],
    content: initialMarkdown || "",
  });
  bindToolbar(editor, toolbarMount);
  return editor;
}

export function decodeBase64Utf8(b64) {
  const bytes = Uint8Array.from(atob(b64), (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

export function normalizeLineEndings(value) {
  return (value || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

export function createModeToggleElement() {
  const wrapper = document.createElement("div");
  wrapper.className = "html-editor-mode-toggle";
  wrapper.setAttribute("role", "tablist");
  wrapper.setAttribute("aria-label", "Editor mode");
  wrapper.innerHTML = `
    <button type="button" class="html-editor-mode-btn is-active" data-html-mode="visual" role="tab" aria-selected="true">Visual</button>
    <button type="button" class="html-editor-mode-btn" data-html-mode="html" role="tab" aria-selected="false">HTML code</button>
  `;
  return wrapper;
}

export function initDualModeHtmlEditor(container, { initialHtml = "", onUpdate }) {
  let mode = "visual";
  const modeButtons = container.querySelectorAll("[data-html-mode]");
  const visualPanel = container.querySelector("[data-html-visual]");
  const sourceTextarea = container.querySelector("[data-html-source]");
  const mount = container.querySelector("[data-html-editor-mount]");
  const toolbarMount = container.querySelector("[data-richtext-toolbar]");

  const editor = createHtmlEditor({
    mount,
    toolbarMount,
    initialHtml,
  });
  sourceTextarea.value = initialHtml || "";

  function setMode(nextMode) {
    if (nextMode === mode) {
      return;
    }
    if (nextMode === "html") {
      sourceTextarea.value = editor.getHTML();
      visualPanel.hidden = true;
      sourceTextarea.hidden = false;
    } else {
      editor.commands.setContent(sourceTextarea.value || "", false);
      sourceTextarea.hidden = true;
      visualPanel.hidden = false;
    }
    mode = nextMode;
    modeButtons.forEach((button) => {
      const active = button.getAttribute("data-html-mode") === mode;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
    });
    onUpdate?.();
  }

  modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setMode(button.getAttribute("data-html-mode"));
    });
  });

  sourceTextarea.addEventListener("input", () => onUpdate?.());
  editor.on("update", () => onUpdate?.());

  return {
    getValue() {
      const value = mode === "html" ? sourceTextarea.value.trim() : editor.getHTML().trim();
      if (!value || value === "<p></p>") {
        return "";
      }
      return value;
    },
    destroy() {
      editor.destroy();
    },
  };
}
