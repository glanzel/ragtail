import { Editor } from "https://cdn.jsdelivr.net/npm/@tiptap/core@2.11.5/+esm";
import StarterKit from "https://cdn.jsdelivr.net/npm/@tiptap/starter-kit@2.11.5/+esm";

function initRichTextEditors() {
  document.querySelectorAll("[data-richtext]").forEach((container) => {
    if (container.dataset.richtextReady === "true") {
      return;
    }
    const mount = container.querySelector("[data-richtext-mount]");
    const input = container.querySelector("textarea");
    if (!mount || !input) {
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
