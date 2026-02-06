import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  connect() {
    // Check if we are in debugging mode (no_poll=true)
    if (new URLSearchParams(window.location.search).has("no_poll")) return;

    // Refresh the frame every 2000 milliseconds (2 seconds)
    this.interval = setInterval(() => {
      this.element.reload()
    }, 2000)
  }

  disconnect() {
    // Clean up the timer when leaving the page
    if (this.interval) clearInterval(this.interval)
  }
}