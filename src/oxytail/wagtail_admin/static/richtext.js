import { Editor } from "https://esm.sh/@tiptap/core@2.11.5";
import StarterKit from "https://esm.sh/@tiptap/starter-kit@2.11.5";

const TOOLBAR_BUTTONS = [
  { action: "bold", label: "B", title: "Bold" },
  { action: "italic", label: "I", title: "Italic" },
  { action: "strike", label: "S", title: "Strikethrough" },
  { action: "heading2", label: "H2", title: "Heading 2" },
  { action: "bulletList", label: "• List", title: "Bullet list" },
  { action: "orderedList", label: "1. List", title: "Numbered list" },
  { action: "blockquote", label: "\"", title: "Quote" },
  { action: "undo", label: "Undo", title: "Undo" },
  { action: "redo", label: "Redo", title: "Redo" },
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

function createToolbar(editor, toolbarMount) {
  toolbarMount.innerHTML = "";
  toolbarMount.className =
    "richtext-toolbar flex flex-wrap gap-1 border-b border-gray-200 bg-gray-50 p-2";

  const updateButtons = () => {
    toolbarMount.querySelectorAll("[data-action]").forEach((button) => {
      const action = button.getAttribute("data-action");
      button.classList.toggle("is-active", isToolbarActionActive(editor, action));
    });
  };

  TOOLBAR_BUTTONS.forEach(({ action, label, title }) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "richtext-toolbar-btn";
    button.dataset.action = action;
    button.title = title;
    button.textContent = label;
    button.addEventListener("click", () => {
      runToolbarAction(editor, action);
      updateButtons();
    });
    toolbarMount.appendChild(button);
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
      extensions: [StarterKit],
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
