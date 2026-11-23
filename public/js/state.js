/**
 * SheRise Reactive State Store & Event Hub
 */

class StateManager {
  constructor() {
    this.currentUser = null;
    this.currentView = "landing";
    this.ventures = [];
    this.investors = [];
    this.dashboardData = null;
    this.stats = null;

    // Filters
    this.filters = {
      search: "",
      category: "All",
      stage: "All",
      sort: "newest"
    };

    this.investorFilters = {
      search: "",
      sector: "All"
    };

    // Subscriptions
    this.listeners = {};
  }

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }

  setUser(user) {
    this.currentUser = user;
    this.emit("user_changed", user);
  }

  setView(viewName) {
    this.currentView = viewName;
    window.scrollTo({ top: 0, behavior: "smooth" });
    this.emit("view_changed", viewName);
  }

  setFilters(newFilters) {
    this.filters = { ...this.filters, ...newFilters };
    this.emit("filters_changed", this.filters);
  }

  setInvestorFilters(newFilters) {
    this.investorFilters = { ...this.investorFilters, ...newFilters };
    this.emit("investor_filters_changed", this.investorFilters);
  }

  showToast(message, type = "success") {
    this.emit("toast", { message, type });
  }
}

window.appState = new StateManager();
