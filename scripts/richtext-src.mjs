import { Editor } from "@tiptap/core";
import StarterKit from "@tiptap/starter-kit";
import { Markdown } from "tiptap-markdown";

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

function bindToolbar(editor, toolbarMount) {
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

function showEditorError(container, message) {
  const mount = container.querySelector("[data-richtext-mount]");
  if (!mount || mount.dataset.errorShown === "true") {
    return;
  }
  mount.dataset.errorShown = "true";
  mount.classList.add("border", "border-red-200", "bg-red-50", "text-red-700");
  mount.textContent = message;
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

    try {
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

      bindToolbar(editor, toolbarMount);

      const form = container.closest("form");
      if (form) {
        form.addEventListener("submit", () => {
          input.value = editor.getHTML();
        });
      }
    } catch (error) {
      console.error("Rich text editor failed to initialize", error);
      showEditorError(
        container,
        "Rich text editor could not be loaded. Formatting buttons remain visible, but editing may be limited.",
      );
    }

    container.dataset.richtextReady = "true";
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initRichTextEditors);
} else {
  initRichTextEditors();
}
