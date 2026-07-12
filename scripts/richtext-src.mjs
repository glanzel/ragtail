import {
  createMarkdownEditor,
  decodeBase64Utf8,
  normalizeLineEndings,
} from "./editors-shared.mjs";

function readInitialMarkdown(container) {
  const b64 = container.getAttribute("data-initial-b64");
  if (!b64) {
    return "";
  }
  return normalizeLineEndings(decodeBase64Utf8(b64));
}

function syncMarkdownInput(editor, input) {
  input.value = editor.storage.markdown.getMarkdown();
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

    const storedMarkdown = readInitialMarkdown(container);
    input.value = storedMarkdown;
    container.removeAttribute("data-initial-b64");

    try {
      const editor = createMarkdownEditor({
        mount,
        toolbarMount,
        initialMarkdown: storedMarkdown,
      });

      const form = container.closest("form");
      if (form) {
        form.addEventListener("submit", () => {
          syncMarkdownInput(editor, input);
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
