/**
 * script.js — Smart Task Manager
 *
 * Provides lightweight, progressive-enhancement JavaScript:
 *   1. Client-side form validation before submission.
 *   2. Delete confirmation dialog.
 *   3. Auto-dismiss flash messages.
 */

"use strict";

// ---------------------------------------------------------------------------
// Delete confirmation
// ---------------------------------------------------------------------------

/**
 * Called by the delete form's onsubmit attribute.
 * Returns false to cancel if the user clicks Cancel.
 *
 * @returns {boolean}
 */
function confirmDelete() {
  return window.confirm("Are you sure you want to delete this task? This cannot be undone.");
}

// ---------------------------------------------------------------------------
// Client-side form validation
// ---------------------------------------------------------------------------

/**
 * Attach validation to a task form so that the server is only hit with
 * clean data. This is a UX improvement — the server always validates too.
 *
 * @param {string} formId - The id of the form element.
 */
function attachFormValidation(formId) {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener("submit", function (e) {
    const titleInput = form.querySelector('input[name="title"]');
    if (!titleInput) return;

    const title = titleInput.value.trim();
    if (!title) {
      e.preventDefault();
      showInlineError(titleInput, "Task title is required.");
      titleInput.focus();
      return;
    }

    const dueDateInput = form.querySelector('input[name="due_date"]');
    if (dueDateInput && dueDateInput.value) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const selected = new Date(dueDateInput.value);
      if (isNaN(selected.getTime())) {
        e.preventDefault();
        showInlineError(dueDateInput, "Please enter a valid date.");
        dueDateInput.focus();
      }
    }
  });
}

/**
 * Display an inline error message beneath an input element.
 * Removes any previously displayed error for that input first.
 *
 * @param {HTMLElement} input - The input that failed validation.
 * @param {string}      msg   - The error message text.
 */
function showInlineError(input, msg) {
  // Remove any existing error for this field
  const existing = input.parentElement.querySelector(".inline-error");
  if (existing) existing.remove();

  const error = document.createElement("span");
  error.className = "inline-error";
  error.style.cssText = "color:#ef4444;font-size:.8rem;display:block;margin-top:.2rem;";
  error.textContent = msg;
  input.parentElement.appendChild(error);

  // Clear the error when the user starts typing again
  input.addEventListener("input", () => error.remove(), { once: true });
}

// ---------------------------------------------------------------------------
// Auto-dismiss flash messages
// ---------------------------------------------------------------------------

function autoHideFlash(delayMs = 4000) {
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = "opacity .5s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    }, delayMs);
  });
}

// ---------------------------------------------------------------------------
// Initialisation
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  attachFormValidation("new-task-form");
  attachFormValidation("edit-task-form");
  autoHideFlash(4000);
});
