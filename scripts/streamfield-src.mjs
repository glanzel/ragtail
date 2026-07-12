import { createModeToggleElement, createToolbarElement, initDualModeHtmlEditor } from "./editors-shared.mjs";

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function randomId() {
  return Math.random().toString(16).slice(2, 10);
}

function blockKindLabel(kind) {
  if (kind === "markdown") return "Markdown";
  if (kind === "html") return "HTML";
  if (kind === "image") return "Image";
  if (kind === "char") return "Text";
  if (kind === "url") return "URL";
  if (kind === "struct") return "Structured";
  return kind;
}

function findDefinition(definitions, type) {
  for (let i = 0; i < definitions.length; i += 1) {
    if (definitions[i].name === type) return definitions[i];
  }
  return null;
}

function readStructValue(blockEl) {
  const values = {};
  blockEl.querySelectorAll("[data-struct-field]").forEach((input) => {
    const name = input.getAttribute("data-struct-field");
    const val = input.value.trim();
    if (val) values[name] = val;
  });
  return Object.keys(values).length ? values : "";
}

function readBlockValue(blockEl, definition) {
  if (definition.block_kind === "image") {
    const imageInput = blockEl.querySelector("[data-streamfield-image-id]");
    const value = imageInput ? imageInput.value : "";
    if (!value) return "";
    return parseInt(value, 10);
  }
  if (definition.block_kind === "html") {
    return blockEl._htmlEditor ? blockEl._htmlEditor.getValue() : "";
  }
  if (definition.block_kind === "struct") {
    return readStructValue(blockEl);
  }
  if (definition.block_kind === "char" || definition.block_kind === "url") {
    const input = blockEl.querySelector("[data-streamfield-simple-field]");
    return input ? input.value.trim() : "";
  }
  const textarea = blockEl.querySelector("textarea[data-streamfield-markdown]");
  return textarea ? textarea.value.trim() : "";
}

function collectBlocks(root) {
  const blocks = [];
  root.querySelectorAll("[data-streamfield-block]").forEach((blockEl) => {
    const type = blockEl.getAttribute("data-block-type");
    const id = blockEl.getAttribute("data-block-id");
    const definition = findDefinition(root._definitions, type);
    if (!definition) return;
    const value = readBlockValue(blockEl, definition);
    if (value === "" || value === null || value === undefined) return;
    blocks.push({ id, type, value });
  });
  return blocks;
}

function syncInput(root) {
  const fieldName = root.getAttribute("data-field");
  const input = document.getElementById(`id_${fieldName}`);
  if (!input) return;
  input.value = JSON.stringify(collectBlocks(root));
}

function updateImagePreview(blockEl, id, title, url) {
  const preview = blockEl.querySelector("[data-streamfield-image-preview]");
  const imageInput = blockEl.querySelector("[data-streamfield-image-id]");
  if (imageInput) imageInput.value = id || "";
  if (!preview) return;
  if (url) {
    preview.innerHTML = `<img src="${escapeHtml(url)}" alt="${escapeHtml(
      title || "Selected image",
    )}" class="max-h-48 w-full object-contain" />`;
  } else {
    preview.innerHTML = '<p class="px-4 py-6 text-sm text-gray-500">No image selected</p>';
  }
  syncInput(blockEl.closest("[data-streamfield-root]"));
}

function createTextInput(label, value, placeholder, inputType, root) {
  const wrapper = document.createElement("div");
  const labelEl = document.createElement("label");
  labelEl.className = "mb-1 block text-xs font-semibold text-gray-600";
  labelEl.textContent = label;
  const input = document.createElement("input");
  input.type = inputType;
  input.className =
    "w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-ragtail-secondary focus:outline focus:outline-[3px] focus:outline-ragtail-focus";
  input.value = value || "";
  input.placeholder = placeholder;
  input.setAttribute("data-streamfield-simple-field", "1");
  input.addEventListener("input", () => syncInput(root));
  wrapper.appendChild(labelEl);
  wrapper.appendChild(input);
  return wrapper;
}

function createStructPanel(definition, value, root) {
  const wrapper = document.createElement("div");
  wrapper.className = "space-y-3";
  const fields = definition.fields || {};
  const current = value && typeof value === "object" ? value : {};
  Object.entries(fields).forEach(([fieldName, fieldDef]) => {
    const fieldWrapper = document.createElement("div");
    const label = document.createElement("label");
    label.className = "mb-1 block text-xs font-semibold text-gray-600";
    label.textContent = fieldDef.label || fieldName;
    const input = document.createElement("input");
    input.type = "text";
    input.className =
      "w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-ragtail-secondary focus:outline focus:outline-[3px] focus:outline-ragtail-focus";
    input.value = current[fieldName] || "";
    input.placeholder =
      fieldDef.block_kind === "url" ? "/about/ or https://example.com" : "";
    input.setAttribute("data-struct-field", fieldName);
    input.addEventListener("input", () => syncInput(root));
    fieldWrapper.appendChild(label);
    fieldWrapper.appendChild(input);
    wrapper.appendChild(fieldWrapper);
  });
  return wrapper;
}

function createHtmlEditorPanel(initialHtml, root, blockEl) {
  const wrapper = document.createElement("div");
  wrapper.className = "streamfield-html-editor";
  wrapper.setAttribute("data-streamfield-html-editor", "1");

  wrapper.appendChild(createModeToggleElement());

  const visualPanel = document.createElement("div");
  visualPanel.className =
    "overflow-hidden rounded border border-gray-200 bg-white focus-within:border-ragtail-secondary focus-within:outline focus-within:outline-[3px] focus-within:outline-ragtail-focus";
  visualPanel.setAttribute("data-html-visual", "1");

  const toolbar = createToolbarElement();
  visualPanel.appendChild(toolbar);

  const mount = document.createElement("div");
  mount.className = "min-h-[12rem] px-3 py-2 prose prose-sm max-w-none";
  mount.setAttribute("data-html-editor-mount", "1");
  visualPanel.appendChild(mount);
  wrapper.appendChild(visualPanel);

  const sourceTextarea = document.createElement("textarea");
  sourceTextarea.rows = 8;
  sourceTextarea.hidden = true;
  sourceTextarea.className =
    "w-full rounded border border-gray-300 px-3 py-2 font-mono text-sm text-gray-900 focus:border-ragtail-secondary focus:outline focus:outline-[3px] focus:outline-ragtail-focus";
  sourceTextarea.setAttribute("data-html-source", "1");
  sourceTextarea.placeholder = "Enter HTML…";
  wrapper.appendChild(sourceTextarea);

  const htmlEditor = initDualModeHtmlEditor(wrapper, {
    initialHtml: initialHtml || "",
    onUpdate: () => syncInput(root),
  });
  blockEl._htmlEditor = htmlEditor;
  blockEl._destroyEditor = () => htmlEditor.destroy();

  return wrapper;
}

function bindBlockControls(blockEl, root) {
  const controls = blockEl.querySelector(".streamfield-block-controls");
  if (!controls) return;

  controls.querySelector(".ragtail-streamfield-move-up")?.addEventListener("click", () => {
    const container = root.querySelector("[data-streamfield-blocks]");
    const previous = blockEl.previousElementSibling;
    if (previous) {
      container.insertBefore(blockEl, previous);
      syncInput(root);
    }
  });
  controls.querySelector(".ragtail-streamfield-move-down")?.addEventListener("click", () => {
    const container = root.querySelector("[data-streamfield-blocks]");
    const next = blockEl.nextElementSibling;
    if (next) {
      container.insertBefore(next, blockEl);
      syncInput(root);
    }
  });
  controls.querySelector(".ragtail-streamfield-remove")?.addEventListener("click", () => {
    blockEl._destroyEditor?.();
    blockEl.remove();
    syncInput(root);
  });
}

function renderBlock(root, block) {
  const definition = findDefinition(root._definitions, block.type);
  if (!definition) return null;

  const blockEl = document.createElement("div");
  blockEl.className = "ragtail-streamfield-block px-4 py-4";
  blockEl.setAttribute("data-streamfield-block", "1");
  blockEl.setAttribute("data-block-type", block.type);
  blockEl.setAttribute("data-block-id", block.id || randomId());

  const header = document.createElement("div");
  header.className = "mb-3 flex flex-wrap items-center justify-between gap-2";
  header.innerHTML = `
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-sm font-semibold text-gray-800">${escapeHtml(definition.label || block.type)}</span>
      <span class="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-500">${escapeHtml(
        blockKindLabel(definition.block_kind),
      )}</span>
    </div>
  `;

  const controls = document.createElement("div");
  controls.className = "streamfield-block-controls flex flex-wrap gap-2";
  controls.innerHTML = `
    <button type="button" class="ragtail-streamfield-move-up text-xs font-semibold text-gray-600 hover:text-gray-900">Up</button>
    <button type="button" class="ragtail-streamfield-move-down text-xs font-semibold text-gray-600 hover:text-gray-900">Down</button>
    <button type="button" class="ragtail-streamfield-remove text-xs font-semibold text-red-600 hover:text-red-800">Remove</button>
  `;
  header.appendChild(controls);
  blockEl.appendChild(header);

  if (definition.block_kind === "image") {
    const imageValue = block.value || "";
    const previewUrl = block.preview_url || "";
    const previewTitle = block.preview_title || "";
    const fieldName = root.getAttribute("data-field");
    const blockId = blockEl.getAttribute("data-block-id");
    const chooserField = `${fieldName}__${blockId}`;

    const preview = document.createElement("div");
    preview.className = "mb-3 overflow-hidden rounded-lg border border-gray-200 bg-gray-50";
    preview.setAttribute("data-streamfield-image-preview", "1");
    preview.innerHTML = previewUrl
      ? `<img src="${escapeHtml(previewUrl)}" alt="${escapeHtml(
          previewTitle || "Selected image",
        )}" class="max-h-48 w-full object-contain" />`
      : '<p class="px-4 py-6 text-sm text-gray-500">No image selected</p>';
    blockEl.appendChild(preview);

    const hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.setAttribute("data-streamfield-image-id", "1");
    hidden.value = imageValue ? String(imageValue) : "";
    blockEl.appendChild(hidden);

    const actions = document.createElement("div");
    actions.className = "flex flex-wrap gap-2";
    actions.innerHTML = `
      <button type="button" class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm font-semibold text-gray-800 hover:bg-gray-50 ragtail-image-choose-btn" data-field="${escapeHtml(
        chooserField,
      )}" data-chooser-url="/admin/images/chooser/?field=${encodeURIComponent(chooserField)}">Choose image</button>
      <button type="button" class="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm font-semibold text-gray-800 hover:bg-gray-50 ragtail-image-clear-btn" data-field="${escapeHtml(
        chooserField,
      )}">Clear</button>
    `;
    blockEl.appendChild(actions);
  } else if (definition.block_kind === "html") {
    blockEl.appendChild(createHtmlEditorPanel(block.value || "", root, blockEl));
  } else if (definition.block_kind === "struct") {
    blockEl.appendChild(createStructPanel(definition, block.value, root));
  } else if (definition.block_kind === "char") {
    blockEl.appendChild(
      createTextInput(definition.label, block.value || "", "Enter text…", "text", root),
    );
  } else if (definition.block_kind === "url") {
    blockEl.appendChild(
      createTextInput(
        definition.label,
        block.value || "",
        "/about/ or https://example.com",
        "text",
        root,
      ),
    );
  } else {
    const textarea = document.createElement("textarea");
    textarea.rows = 6;
    textarea.className =
      "w-full rounded border border-gray-300 px-3 py-2 font-mono text-sm text-gray-900 focus:border-ragtail-secondary focus:outline focus:outline-[3px] focus:outline-ragtail-focus";
    textarea.value = block.value || "";
    textarea.placeholder = "Enter Markdown…";
    textarea.setAttribute("data-streamfield-markdown", "1");
    textarea.addEventListener("input", () => syncInput(root));
    blockEl.appendChild(textarea);
  }

  bindBlockControls(blockEl, root);
  return blockEl;
}

function initRoot(root) {
  let definitions = [];
  let initialBlocks = [];
  try {
    definitions = JSON.parse(root.getAttribute("data-block-definitions") || "[]");
  } catch {
    definitions = [];
  }
  try {
    initialBlocks = JSON.parse(root.getAttribute("data-initial-blocks") || "[]");
  } catch {
    initialBlocks = [];
  }
  root._definitions = definitions;
  const container = root.querySelector("[data-streamfield-blocks]");
  if (!container) return;

  initialBlocks.forEach((block) => {
    const blockEl = renderBlock(root, block);
    if (blockEl) container.appendChild(blockEl);
  });

  root.querySelectorAll(".ragtail-streamfield-add-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const type = button.getAttribute("data-block-type");
      const definition = findDefinition(definitions, type);
      if (!definition) return;
      const blockEl = renderBlock(root, {
        id: randomId(),
        type,
        value: definition.block_kind === "struct" ? {} : "",
      });
      if (blockEl) {
        container.appendChild(blockEl);
        syncInput(root);
      }
    });
  });

  const form = root.closest("form");
  if (form) {
    form.addEventListener("submit", () => syncInput(root));
  }
}

function bindImageChooserEvents() {
  document.addEventListener("click", (event) => {
    const chooseBtn = event.target.closest(".ragtail-image-choose-btn");
    if (chooseBtn) {
      const field = chooseBtn.getAttribute("data-field");
      const url = chooseBtn.getAttribute("data-chooser-url");
      if (!field || !url) return;
      window.open(url, `ragtail-image-chooser-${field}`, "width=960,height=720");
      return;
    }

    const clearBtn = event.target.closest(".ragtail-image-clear-btn");
    if (!clearBtn) return;
    const field = clearBtn.getAttribute("data-field");
    if (!field) return;
    const blockEl = clearBtn.closest("[data-streamfield-block]");
    if (blockEl) {
      updateImagePreview(blockEl, "", "", "");
      return;
    }
    const input = document.getElementById(`id_${field}`);
    const preview = document.getElementById(`preview_${field}`);
    if (!input || !preview) return;
    input.value = "";
    preview.innerHTML = '<p class="px-4 py-6 text-sm text-gray-500">No image selected</p>';
  });

  window.addEventListener("message", (event) => {
    if (event.origin !== window.location.origin) return;
    const data = event.data;
    if (!data || data.type !== "ragtail-image-selected") return;

    const field = data.field || "";
    if (field.includes("__")) {
      const blockEl = document.querySelector(
        `[data-streamfield-block][data-block-id="${field.split("__").pop()}"]`,
      );
      if (blockEl) {
        updateImagePreview(blockEl, data.id, data.title, data.url);
        return;
      }
    }

    const input = document.getElementById(`id_${field}`);
    const preview = document.getElementById(`preview_${field}`);
    if (!input || !preview) return;
    input.value = data.id || "";
    if (data.url) {
      preview.innerHTML = `<img src="${data.url}" alt="${
        data.title || "Selected image"
      }" class="max-h-48 w-full object-contain" />`;
    } else {
      preview.innerHTML = '<p class="px-4 py-6 text-sm text-gray-500">No image selected</p>';
    }
  });
}

function initStreamFields() {
  document.querySelectorAll("[data-streamfield-root]").forEach(initRoot);
}

if (!window.__ragtailStreamfieldBound) {
  bindImageChooserEvents();
  window.__ragtailStreamfieldBound = true;
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initStreamFields);
} else {
  initStreamFields();
}
