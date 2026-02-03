import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  connect() {
    this.interval = setInterval(() => {
      // Reloads the Turbo Frame this controller is attached to
      this.element.reload() 
    }, 2000)
  }

  disconnect() {
    clearInterval(this.interval)
  }
}