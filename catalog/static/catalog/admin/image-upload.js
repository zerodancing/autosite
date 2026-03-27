(function () {
  function getSignature(file) {
    return [file.name, file.size, file.lastModified].join("::");
  }

  function mergeFiles(existingFiles, incomingFiles) {
    const seen = new Set();
    const merged = [];

    existingFiles.concat(incomingFiles).forEach(function (file) {
      const signature = getSignature(file);
      if (seen.has(signature)) {
        return;
      }
      seen.add(signature);
      merged.push(file);
    });

    return merged;
  }

  function writeFiles(input, files) {
    const transfer = new DataTransfer();
    files.forEach(function (file) {
      transfer.items.add(file);
    });
    input.files = transfer.files;
    input._selectedFiles = files;
  }

  function createPreview(file) {
    const wrapper = document.createElement("div");
    wrapper.className = "admin-dropzone__preview-item";
    wrapper.dataset.fileSignature = getSignature(file);

    const image = document.createElement("img");
    image.alt = file.name;
    wrapper.appendChild(image);

    const caption = document.createElement("span");
    caption.textContent = file.name;
    wrapper.appendChild(caption);

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "admin-dropzone__remove";
    removeButton.textContent = "×";
    wrapper.appendChild(removeButton);

    const reader = new FileReader();
    reader.onload = function (event) {
      image.src = event.target.result;
    };
    reader.readAsDataURL(file);

    return wrapper;
  }

  function renderState(container, input) {
    const filesHost = container.querySelector("[data-dropzone-files]");
    const previewHost = container.querySelector("[data-dropzone-preview]");
    filesHost.innerHTML = "";
    previewHost.innerHTML = "";

    const files = Array.from(input.files || []);
    files.forEach(function (file) {
      const badge = document.createElement("span");
      badge.className = "admin-dropzone__file";
      badge.textContent = file.name;
      badge.dataset.fileSignature = getSignature(file);
      filesHost.appendChild(badge);

      if (file.type && file.type.startsWith("image/")) {
        const preview = createPreview(file);
        preview.querySelector(".admin-dropzone__remove").addEventListener("click", function () {
          const filtered = Array.from(input.files || []).filter(function (candidate) {
            return getSignature(candidate) !== preview.dataset.fileSignature;
          });
          writeFiles(input, filtered);
          renderState(container, input);
        });
        previewHost.appendChild(preview);
      }
    });
  }

  function attachDropzone(container) {
    const input = container.querySelector("input[type='file']");
    const surface = container.querySelector("[data-dropzone-surface]");
    if (!input || !surface) {
      return;
    }

    function appendFiles(newFiles) {
      const existing = Array.from(input._selectedFiles || []);
      const merged = input.multiple ? mergeFiles(existing, newFiles) : newFiles.slice(0, 1);
      writeFiles(input, merged);
      renderState(container, input);
    }

    surface.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        input.click();
      }
    });

    ["dragenter", "dragover"].forEach(function (eventName) {
      container.addEventListener(eventName, function (event) {
        event.preventDefault();
        container.classList.add("is-dragover");
      });
    });

    ["dragleave", "dragend", "drop"].forEach(function (eventName) {
      container.addEventListener(eventName, function (event) {
        event.preventDefault();
        container.classList.remove("is-dragover");
      });
    });

    container.addEventListener("drop", function (event) {
      appendFiles(Array.from(event.dataTransfer.files || []));
    });

    input.addEventListener("change", function () {
      appendFiles(Array.from(input.files || []));
    });

    renderState(container, input);
  }

  function decorateGalleryManager() {
    const group = document.getElementById("images-group");
    if (!group) {
      return;
    }

    group.classList.add("admin-gallery-manager");
    const rows = Array.from(group.querySelectorAll(".inline-related")).filter(function (row) {
      return !row.classList.contains("empty-form");
    });

    function syncOrderValues() {
      const currentRows = Array.from(group.querySelectorAll(".inline-related")).filter(function (row) {
        return !row.classList.contains("empty-form");
      });

      currentRows.forEach(function (row, index) {
        const orderInput = row.querySelector("input[name$='-order']");
        if (orderInput) {
          orderInput.value = String(index + 1);
        }
      });
    }

    rows.forEach(function (row) {
      if (row.querySelector(".admin-gallery-manager__controls")) {
        return;
      }

      const target = row.querySelector("h3") || row;
      const controls = document.createElement("div");
      controls.className = "admin-gallery-manager__controls";

      const up = document.createElement("button");
      up.type = "button";
      up.className = "admin-gallery-manager__button";
      up.textContent = "Вверх";

      const down = document.createElement("button");
      down.type = "button";
      down.className = "admin-gallery-manager__button";
      down.textContent = "Вниз";

      up.addEventListener("click", function () {
        const prev = row.previousElementSibling;
        if (prev && !prev.classList.contains("empty-form")) {
          row.parentNode.insertBefore(row, prev);
          syncOrderValues();
        }
      });

      down.addEventListener("click", function () {
        const next = row.nextElementSibling;
        if (next && !next.classList.contains("empty-form")) {
          row.parentNode.insertBefore(next, row);
          syncOrderValues();
        }
      });

      controls.appendChild(up);
      controls.appendChild(down);
      target.appendChild(controls);
    });

    syncOrderValues();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-admin-dropzone]").forEach(attachDropzone);
    decorateGalleryManager();
  });
})();
