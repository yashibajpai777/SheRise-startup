/**
 * SheRise Main Application Logic & View Controller
 */

class SheRiseApp {
  constructor() {
    this.selectedVentureId = null;
    this.selectedInvestorId = null;
    this.aiDoctorDraft = null;
  }

  async init() {
    console.log("🌸 SheRise Initializing...");

    // Check user session
    try {
      const user = await window.api.getMe();
      window.appState.setUser(user);
    } catch {
      window.appState.setUser(null);
    }

    // Set up listeners
    this.bindEvents();

    // Initial load
    await this.loadStats();
    await this.loadVentures();
    await this.loadInvestors();

    // Listen for state changes
    window.appState.on("user_changed", (user) => this.renderNavbarUser(user));
    window.appState.on("view_changed", (view) => this.renderView(view));
    window.appState.on("filters_changed", () => this.loadVentures());
    window.appState.on("investor_filters_changed", () => this.loadInvestors());
    window.appState.on("toast", (toast) => this.displayToast(toast.message, toast.type));

    // Render initial view
    this.renderView(window.appState.currentView);
  }

  bindEvents() {
    // Search input (debounce)
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
      let timeout;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          window.appState.setFilters({ search: e.target.value });
        }, 300);
      });
    }

    // Investor search input
    const invSearchInput = document.getElementById("investor-search-input");
    if (invSearchInput) {
      let timeout;
      invSearchInput.addEventListener("input", (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          window.appState.setInvestorFilters({ search: e.target.value });
        }, 300);
      });
    }
  }

  // --------------------------------------------------------------------------
  // Navigation & Views
  // --------------------------------------------------------------------------
  navigate(viewName) {
    window.appState.setView(viewName);
  }

  renderView(viewName) {
    const views = ["landing", "explore", "dashboard", "investors", "create-venture", "profile", "ai-doctor"];
    views.forEach(v => {
      const el = document.getElementById(`view-${v}`);
      if (el) {
        if (v === viewName) {
          el.classList.remove("hidden");
        } else {
          el.classList.add("hidden");
        }
      }
    });

    // Update active nav links
    document.querySelectorAll(".nav-link").forEach(link => {
      const target = link.getAttribute("data-view");
      if (target === viewName) {
        link.classList.add("text-purple-900", "font-bold", "border-b-2", "border-purple-700");
        link.classList.remove("text-slate-600");
      } else {
        link.classList.remove("text-purple-900", "font-bold", "border-b-2", "border-purple-700");
        link.classList.add("text-slate-600");
      }
    });

    // Refresh data if view is opened
    if (viewName === "dashboard") {
      this.loadDashboard();
    } else if (viewName === "profile") {
      this.loadProfile();
    } else if (viewName === "explore") {
      this.loadVentures();
    }
  }

  renderNavbarUser(user) {
    const unauthEl = document.getElementById("nav-unauthenticated");
    const authEl = document.getElementById("nav-authenticated");
    const dashLink = document.getElementById("nav-link-dashboard");
    const userNameEl = document.getElementById("nav-user-name");
    const userRoleEl = document.getElementById("nav-user-role");
    const userAvatarEl = document.getElementById("nav-user-avatar");

    if (user) {
      if (unauthEl) unauthEl.classList.add("hidden");
      if (authEl) authEl.classList.remove("hidden");
      if (dashLink) dashLink.classList.remove("hidden");
      if (userNameEl) userNameEl.textContent = user.name;
      if (userRoleEl) userRoleEl.textContent = user.role === "investor" ? "Investor" : "Founder";
      if (userAvatarEl && user.avatar) userAvatarEl.src = user.avatar;
    } else {
      if (unauthEl) unauthEl.classList.remove("hidden");
      if (authEl) authEl.classList.add("hidden");
      if (dashLink) dashLink.classList.add("hidden");
    }
  }

  // --------------------------------------------------------------------------
  // Data Loaders
  // --------------------------------------------------------------------------
  async loadStats() {
    try {
      const res = await window.api.getStats();
      window.appState.stats = res;
      const elCapital = document.getElementById("stat-capital");
      const elVentures = document.getElementById("stat-ventures");
      const elInvestors = document.getElementById("stat-investors");
      const elScore = document.getElementById("stat-readiness");

      if (elCapital) elCapital.textContent = Components.formatCurrency(res.total_capital_raised) + "+";
      if (elVentures) elVentures.textContent = res.total_ventures + " Ventures";
      if (elInvestors) elInvestors.textContent = res.total_investors + " Verified";
      if (elScore) elScore.textContent = res.avg_readiness_score + " / 100";
    } catch (e) {
      console.warn("Stats load error:", e);
    }
  }

  async loadVentures() {
    const container = document.getElementById("ventures-grid");
    const featuredContainer = document.getElementById("featured-ventures-grid");
    const loading = document.getElementById("ventures-loading");
    const emptyState = document.getElementById("ventures-empty");

    if (loading) loading.classList.remove("hidden");

    try {
      const res = await window.api.getVentures(window.appState.filters);
      window.appState.ventures = res.ventures || [];

      if (loading) loading.classList.add("hidden");

      if (window.appState.ventures.length === 0) {
        if (container) container.innerHTML = "";
        if (emptyState) emptyState.classList.remove("hidden");
      } else {
        if (emptyState) emptyState.classList.add("hidden");
        const cardsHtml = window.appState.ventures.map(v => Components.renderVentureCard(v)).join("");
        if (container) container.innerHTML = cardsHtml;
        if (featuredContainer) {
          // Show top 3 in featured
          featuredContainer.innerHTML = window.appState.ventures.slice(0, 3).map(v => Components.renderVentureCard(v)).join("");
        }
      }

      // Update count badge
      const countEl = document.getElementById("ventures-count");
      if (countEl) countEl.textContent = `${window.appState.ventures.length} ventures found`;

    } catch (err) {
      if (loading) loading.classList.add("hidden");
      window.appState.showToast(err.message, "error");
    }
  }

  async loadInvestors() {
    const container = document.getElementById("investors-grid");
    const featuredContainer = document.getElementById("featured-investors-grid");
    if (!container) return;

    try {
      const res = await window.api.getInvestors(window.appState.investorFilters);
      window.appState.investors = res.investors || [];

      const cardsHtml = window.appState.investors.map(inv => Components.renderInvestorCard(inv)).join("");
      container.innerHTML = cardsHtml;

      if (featuredContainer) {
        featuredContainer.innerHTML = window.appState.investors.slice(0, 3).map(inv => Components.renderInvestorCard(inv)).join("");
      }
    } catch (err) {
      console.error(err);
    }
  }

  async loadDashboard() {
    const user = window.appState.currentUser;
    if (!user) {
      this.openAuthModal("login");
      return;
    }

    try {
      const data = await window.api.getEntrepreneurDashboard();
      window.appState.dashboardData = data;

      // Update KPIs
      const elVenturesCount = document.getElementById("dash-kpi-ventures");
      const elViews = document.getElementById("dash-kpi-views");
      const elInterests = document.getElementById("dash-kpi-interests");
      const elScore = document.getElementById("dash-kpi-score");

      if (elVenturesCount) elVenturesCount.textContent = data.stats.ventures_count;
      if (elViews) elViews.textContent = data.stats.total_views;
      if (elInterests) elInterests.textContent = data.stats.total_interests;
      if (elScore) elScore.textContent = data.stats.avg_ai_score + "/100";

      // Render Ventures table / cards
      const container = document.getElementById("dash-my-ventures");
      if (container) {
        if (!data.ventures || data.ventures.length === 0) {
          container.innerHTML = `
            <div class="p-8 text-center bg-white/70 rounded-2xl border border-purple-100">
              <span class="text-3xl mb-2 block">💡</span>
              <h4 class="font-bold text-purple-950 mb-1">No Business Ideas Posted Yet</h4>
              <p class="text-xs text-slate-500 mb-4">Post your first venture to receive investor inquiries and AI readiness reviews.</p>
              <button onclick="window.app.navigate('create-venture')" class="px-4 py-2 rounded-xl text-xs font-bold text-white gradient-btn-primary">
                + Submit Venture
              </button>
            </div>
          `;
        } else {
          container.innerHTML = data.ventures.map(v => Components.renderVentureCard(v)).join("");
        }
      }

      // Render Inquiries
      const inqContainer = document.getElementById("dash-inquiries-list");
      if (inqContainer) {
        if (!data.inquiries || data.inquiries.length === 0) {
          inqContainer.innerHTML = `
            <p class="text-xs text-slate-500 italic p-4 text-center">No investor inquiries yet. Keep your pitch updated!</p>
          `;
        } else {
          inqContainer.innerHTML = data.inquiries.map(inq => `
            <div class="p-4 rounded-xl bg-purple-50/70 border border-purple-100 space-y-1">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-purple-950">${inq.investor_name}</span>
                <span class="text-[10px] text-slate-400">${new Date(inq.created_at).toLocaleDateString()}</span>
              </div>
              <p class="text-[11px] text-purple-700">${inq.investor_email}</p>
              <p class="text-xs text-slate-700 mt-1 italic">"${inq.message}"</p>
            </div>
          `).join("");
        }
      }
    } catch (err) {
      window.appState.showToast(err.message, "error");
    }
  }

  loadProfile() {
    const user = window.appState.currentUser;
    if (!user) {
      this.openAuthModal("login");
      return;
    }

    // Populate profile inputs
    document.getElementById("profile-name").value = user.name || "";
    document.getElementById("profile-email").value = user.email || "";
    document.getElementById("profile-title").value = user.title || "";
    document.getElementById("profile-bio").value = user.bio || "";
    document.getElementById("profile-location").value = user.location || "";
    document.getElementById("profile-company").value = user.company || "";
    document.getElementById("profile-linkedin").value = user.linkedin || "";
    document.getElementById("profile-website").value = user.website || "";

    const avatarEl = document.getElementById("profile-avatar-preview");
    if (avatarEl && user.avatar) avatarEl.src = user.avatar;
  }

  // --------------------------------------------------------------------------
  // Modals & Venture Detail
  // --------------------------------------------------------------------------
  async openVentureModal(ventureId) {
    this.selectedVentureId = ventureId;
    const modal = document.getElementById("modal-venture-detail");
    const content = document.getElementById("venture-modal-content");
    modal.classList.remove("hidden");

    content.innerHTML = `<div class="p-12 text-center text-purple-600 font-medium">Loading venture details...</div>`;

    try {
      const res = await window.api.getVenture(ventureId);
      const v = res.venture;
      const user = window.appState.currentUser;
      const isOwner = user && user.id === v.user_id;

      const percent = Math.min(100, Math.round((v.raised_funding / v.target_funding) * 100));

      content.innerHTML = `
        <div class="space-y-6">
          <!-- Top Badge & Actions -->
          <div class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-purple-100">
            <div class="flex items-center gap-2">
              <span class="px-3 py-1 rounded-full text-xs font-bold border ${Components.getCategoryColor(v.category)}">
                ${v.category}
              </span>
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-900 border border-purple-200">
                ${v.stage} Stage
              </span>
            </div>
            
            <div class="flex items-center gap-2">
              <button onclick="window.app.toggleBookmark(${v.id})" 
                      class="px-3 py-1.5 rounded-xl text-xs font-semibold border border-purple-200 hover:bg-purple-50 text-purple-900 transition flex items-center gap-1.5">
                <span>🔖</span> Bookmark
              </button>
              ${isOwner ? `
                <button onclick="window.app.deleteVenture(${v.id})" class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 transition">
                  Delete
                </button>
              ` : `
                <button onclick="window.app.openInterestModal(${v.id})" 
                        class="px-4 py-1.5 rounded-xl text-xs font-bold text-white gradient-btn-primary shadow flex items-center gap-1.5">
                  <span>🤝</span> Express Interest
                </button>
              `}
            </div>
          </div>

          <!-- Hero info -->
          <div>
            <h2 class="text-2xl md:text-3xl font-extrabold text-purple-950 mb-2 leading-tight">
              ${v.title}
            </h2>
            <p class="text-base text-slate-700 font-medium leading-relaxed">
              ${v.tagline}
            </p>
          </div>

          <!-- Founder card & Capital Target -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-purple-50/70 border border-purple-100">
            <div class="flex items-center gap-3">
              <img src="${v.founder_avatar || 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150'}" 
                   class="w-12 h-12 rounded-full object-cover ring-2 ring-purple-300" />
              <div>
                <span class="text-[11px] uppercase tracking-wider font-bold text-purple-700">Founder</span>
                <h4 class="font-bold text-purple-950 text-sm">${v.founder_name}</h4>
                <div class="flex items-center gap-2 mt-1">
                  ${v.website_url ? `<a href="${v.website_url}" target="_blank" class="text-xs text-purple-600 hover:underline">Website ↗</a>` : ''}
                  ${v.pitch_deck_url ? `<a href="${v.pitch_deck_url}" target="_blank" class="text-xs text-indigo-600 hover:underline">Pitch Deck ↗</a>` : ''}
                </div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-xs font-bold text-purple-950 mb-1">
                <span>Raised: ${Components.formatCurrency(v.raised_funding)}</span>
                <span>Goal: ${Components.formatCurrency(v.target_funding)}</span>
              </div>
              <div class="w-full bg-purple-200/60 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-purple-600 to-indigo-600 h-full rounded-full" style="width: ${percent}%;"></div>
              </div>
              <p class="text-[11px] text-slate-500 mt-1 text-right font-medium">${percent}% funded</p>
            </div>
          </div>

          <!-- The Pitch Details -->
          <div class="space-y-4 text-sm text-slate-800 leading-relaxed">
            <div class="p-4 rounded-xl bg-white border border-purple-100 shadow-sm">
              <h4 class="text-xs font-extrabold uppercase tracking-wider text-purple-900 mb-1 flex items-center gap-1.5">
                <span>🎯</span> The Problem
              </h4>
              <p>${v.problem}</p>
            </div>

            <div class="p-4 rounded-xl bg-white border border-purple-100 shadow-sm">
              <h4 class="text-xs font-extrabold uppercase tracking-wider text-purple-900 mb-1 flex items-center gap-1.5">
                <span>💡</span> Proposed Solution
              </h4>
              <p>${v.solution}</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="p-4 rounded-xl bg-white border border-purple-100 shadow-sm">
                <h4 class="text-xs font-extrabold uppercase tracking-wider text-purple-900 mb-1 flex items-center gap-1.5">
                  <span>🌍</span> Target Market
                </h4>
                <p>${v.target_market || "Market assessment in progress."}</p>
              </div>

              <div class="p-4 rounded-xl bg-white border border-purple-100 shadow-sm">
                <h4 class="text-xs font-extrabold uppercase tracking-wider text-purple-900 mb-1 flex items-center gap-1.5">
                  <span>📈</span> Traction & Milestones
                </h4>
                <p>${v.traction || "Early pilot cohort testing."}</p>
              </div>
            </div>
          </div>

          <!-- SheRise Gemini AI Section -->
          <div class="pt-2">
            ${Components.renderAiEvaluation(v.ai_feedback)}
          </div>
        </div>
      `;
    } catch (err) {
      content.innerHTML = `<div class="p-8 text-center text-rose-600 font-semibold">${err.message}</div>`;
    }
  }

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add("hidden");
  }

  // --------------------------------------------------------------------------
  // Create Venture & Inline AI Evaluation
  // --------------------------------------------------------------------------
  async triggerInlineAiReview() {
    const form = document.getElementById("form-create-venture");
    const formData = new FormData(form);

    const title = formData.get("title");
    const category = formData.get("category");
    const stage = formData.get("stage");
    const target_funding = Number(formData.get("target_funding") || 100000);
    const problem = formData.get("problem");
    const solution = formData.get("solution");
    const target_market = formData.get("target_market");
    const traction = formData.get("traction");

    if (!problem || problem.length < 15 || !solution || solution.length < 15) {
      window.appState.showToast("Please fill in at least the Problem and Solution fields before running AI Review.", "error");
      return;
    }

    const previewContainer = document.getElementById("inline-ai-preview");
    previewContainer.classList.remove("hidden");
    previewContainer.innerHTML = `
      <div class="p-6 rounded-2xl bg-purple-900 text-white text-center flex flex-col items-center justify-center gap-2">
        <div class="w-8 h-8 border-2 border-purple-300 border-t-transparent rounded-full animate-spin"></div>
        <span class="text-xs text-purple-200 font-medium">Gemini 4 Hydrogen is analyzing your pitch...</span>
      </div>
    `;

    try {
      const res = await window.api.runPitchDoctor({
        title, category, stage, target_funding, problem, solution, target_market, traction
      });
      previewContainer.innerHTML = Components.renderAiEvaluation(res.evaluation);
      window.appState.showToast("✨ AI Pitch Doctor analysis complete!");
    } catch (err) {
      previewContainer.innerHTML = `<div class="p-4 text-xs text-rose-300 bg-rose-950/60 rounded-xl">${err.message}</div>`;
    }
  }

  async handleCreateVentureSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const data = {
      title: formData.get("title"),
      tagline: formData.get("tagline"),
      category: formData.get("category"),
      stage: formData.get("stage"),
      target_funding: Number(formData.get("target_funding")),
      problem: formData.get("problem"),
      solution: formData.get("solution"),
      target_market: formData.get("target_market"),
      traction: formData.get("traction"),
      pitch_deck_url: formData.get("pitch_deck_url"),
      website_url: formData.get("website_url")
    };

    const submitBtn = document.getElementById("btn-submit-venture");
    submitBtn.disabled = true;
    submitBtn.textContent = "Publishing Venture...";

    try {
      const res = await window.api.createVenture(data);
      window.appState.showToast("🎉 Venture published successfully!");
      form.reset();
      document.getElementById("inline-ai-preview").classList.add("hidden");
      this.navigate("explore");
      await this.loadVentures();
    } catch (err) {
      window.appState.showToast(err.message, "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Publish Business Idea ✨";
    }
  }

  async deleteVenture(ventureId) {
    if (!confirm("Are you sure you want to delete this business idea?")) return;
    try {
      await window.api.deleteVenture(ventureId);
      window.appState.showToast("Venture deleted.");
      this.closeModal("modal-venture-detail");
      await this.loadVentures();
      if (window.appState.currentView === "dashboard") {
        await this.loadDashboard();
      }
    } catch (err) {
      window.appState.showToast(err.message, "error");
    }
  }

  async toggleBookmark(ventureId) {
    try {
      const res = await window.api.toggleBookmark(ventureId);
      window.appState.showToast(res.bookmarked ? "Venture bookmarked!" : "Bookmark removed.");
    } catch (err) {
      window.appState.showToast(err.message, "error");
    }
  }

  // --------------------------------------------------------------------------
  // Express Interest Modal
  // --------------------------------------------------------------------------
  openInterestModal(ventureId) {
    this.selectedVentureId = ventureId;
    const modal = document.getElementById("modal-interest");
    const user = window.appState.currentUser;
    if (user) {
      document.getElementById("interest-investor-name").value = user.name;
      document.getElementById("interest-investor-email").value = user.email;
    }
    modal.classList.remove("hidden");
  }

  async submitInterestForm(event) {
    event.preventDefault();
    const name = document.getElementById("interest-investor-name").value;
    const email = document.getElementById("interest-investor-email").value;
    const message = document.getElementById("interest-message").value;

    try {
      await window.api.expressInterest(this.selectedVentureId, { investor_name: name, investor_email: email, message });
      window.appState.showToast("🤝 Your interest was delivered to the founder!");
      this.closeModal("modal-interest");
      document.getElementById("interest-message").value = "";
    } catch (err) {
      window.appState.showToast(err.message, "error");
    }
  }

  // --------------------------------------------------------------------------
  // AI Tailored Investor Outreach Pitch Modal
  // --------------------------------------------------------------------------
  openInvestorPitchModal(investorId) {
    this.selectedInvestorId = investorId;
    const modal = document.getElementById("modal-investor-pitch");
    const select = document.getElementById("ai-pitch-venture-select");
    const resultBox = document.getElementById("ai-pitch-result-box");
    resultBox.classList.add("hidden");

    // Populate user's ventures or public ventures
    const ventures = window.appState.ventures;
    select.innerHTML = ventures.map(v => `<option value="${v.id}">${v.title} (${v.category})</option>`).join("");

    modal.classList.remove("hidden");
  }

  async generateInvestorPitchWithAi() {
    const ventureId = document.getElementById("ai-pitch-venture-select").value;
    const resultBox = document.getElementById("ai-pitch-result-box");
    const textArea = document.getElementById("ai-pitch-text");
    const btn = document.getElementById("btn-run-investor-pitch");

    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-1">⌛</span> Gemini is tailoring your outreach...`;

    try {
      const res = await window.api.generateInvestorPitch(ventureId, this.selectedInvestorId);
      resultBox.classList.remove("hidden");
      textArea.value = res.pitch_text;
      window.appState.showToast("✨ Personalized investor pitch generated!");
    } catch (err) {
      window.appState.showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<span>✨</span> Re-Generate Pitch`;
    }
  }

  copyPitchText() {
    const text = document.getElementById("ai-pitch-text").value;
    navigator.clipboard.writeText(text);
    window.appState.showToast("📋 Pitch copied to clipboard!");
  }

  // --------------------------------------------------------------------------
  // Standalone AI Pitch Doctor Page
  // --------------------------------------------------------------------------
  async runStandalonePitchDoctor(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const data = {
      title: formData.get("doc_title") || "My Venture",
      category: formData.get("doc_category"),
      stage: formData.get("doc_stage"),
      target_funding: Number(formData.get("doc_funding") || 250000),
      problem: formData.get("doc_problem"),
      solution: formData.get("doc_solution"),
      traction: formData.get("doc_traction")
    };

    const container = document.getElementById("standalone-ai-result");
    const btn = document.getElementById("btn-run-pitch-doc");

    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin mr-1">⌛</span> Evaluating Pitch with Gemini...`;
    container.classList.remove("hidden");
    container.innerHTML = `
      <div class="p-8 text-center text-purple-700 font-semibold bg-white/60 rounded-2xl border border-purple-200">
        Reviewing market opportunity, unit economics, and competitive moat...
      </div>
    `;

    try {
      const res = await window.api.runPitchDoctor(data);
      container.innerHTML = Components.renderAiEvaluation(res.evaluation);
      window.appState.showToast("✨ Pitch Doctor evaluation ready!");
    } catch (err) {
      container.innerHTML = `<div class="p-4 text-xs text-rose-600 bg-rose-50 rounded-xl">${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<span>✨</span> Run AI Pitch Doctor Analysis`;
    }
  }

  // --------------------------------------------------------------------------
  // Auth & Profile
  // --------------------------------------------------------------------------
  openAuthModal(mode = "login") {
    const modal = document.getElementById("modal-auth");
    this.switchAuthTab(mode);
    modal.classList.remove("hidden");
  }

  switchAuthTab(mode) {
    const loginTab = document.getElementById("tab-login-btn");
    const regTab = document.getElementById("tab-register-btn");
    const loginForm = document.getElementById("form-login");
    const regForm = document.getElementById("form-register");

    if (mode === "login") {
      loginTab.classList.add("text-purple-900", "border-b-2", "border-purple-800", "font-bold");
      loginTab.classList.remove("text-slate-400");
      regTab.classList.remove("text-purple-900", "border-b-2", "border-purple-800", "font-bold");
      regTab.classList.add("text-slate-400");
      loginForm.classList.remove("hidden");
      regForm.classList.add("hidden");
    } else {
      regTab.classList.add("text-purple-900", "border-b-2", "border-purple-800", "font-bold");
      regTab.classList.remove("text-slate-400");
      loginTab.classList.remove("text-purple-900", "border-b-2", "border-purple-800", "font-bold");
      loginTab.classList.add("text-slate-400");
      regForm.classList.remove("hidden");
      loginForm.classList.add("hidden");
    }
  }

  async handleLoginSubmit(event) {
    event.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    try {
      const res = await window.api.login({ email, password });
      window.appState.setUser(res.user);
      window.appState.showToast(`Welcome back, ${res.user.name}!`);
      this.closeModal("modal-auth");
    } catch (err) {
      window.appState.showToast(err.message, "error");
    }
  }

  async handleRegisterSubmit(event) {
    event.preventDefault();
    const name = document.getElementById("reg-name").value;
    const email = document.getElementById("reg-email").value;
    const password = document.getElementById("reg-password").value;
    const role = document.querySelector('input[name="reg_role"]:checked').value;
    const title = document.getElementById("reg-title").value;

    try {
      const res = await window.api.register({ name, email, password, role, title });
      window.appState.setUser(res.user);
      window.appState.showToast(`Welcome to SheRise, ${res.user.name}!`);
      this.closeModal("modal-auth");
    } catch (err) {
      window.appState.showToast(err.message, "error");
    }
  }

  async handleDemoLogin(role) {
    try {
      const res = await window.api.demoLogin(role);
      window.appState.setUser(res.user);
      window.appState.showToast(res.message);
      this.closeModal("modal-auth");
      this.navigate("dashboard");
    } catch (err) {
      window.appState.showToast(err.message, "error");
    }
  }

  logout() {
    window.api.logout();
    window.appState.setUser(null);
    window.appState.showToast("Signed out.");
    this.navigate("landing");
  }

  async handleProfileUpdate(event) {
    event.preventDefault();
    const data = {
      name: document.getElementById("profile-name").value,
      title: document.getElementById("profile-title").value,
      bio: document.getElementById("profile-bio").value,
      location: document.getElementById("profile-location").value,
      company: document.getElementById("profile-company").value,
      linkedin: document.getElementById("profile-linkedin").value,
      website: document.getElementById("profile-website").value
    };

    try {
      const res = await window.api.updateProfile(data);
      window.appState.setUser(res.user);
      window.appState.showToast("Profile updated successfully!");
    } catch (err) {
      window.appState.showToast(err.message, "error");
    }
  }

  // --------------------------------------------------------------------------
  // Gemini Settings Drawer / Modal
  // --------------------------------------------------------------------------
  openGeminiKeyModal() {
    const modal = document.getElementById("modal-gemini-key");
    const input = document.getElementById("input-gemini-key");
    input.value = window.api.getGeminiKey();
    modal.classList.remove("hidden");
  }

  saveGeminiKey() {
    const input = document.getElementById("input-gemini-key");
    window.api.setGeminiKey(input.value);
    window.appState.showToast(input.value ? "✨ Gemini API Key saved for this session!" : "API Key cleared. Using SheRise Heuristic Engine.");
    this.closeModal("modal-gemini-key");
  }

  // --------------------------------------------------------------------------
  // Toast notifications
  // --------------------------------------------------------------------------
  displayToast(msg, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    const isError = type === "error";

    toast.className = `toast-slide px-4 py-3 rounded-2xl shadow-xl border text-xs font-semibold flex items-center gap-2.5 max-w-sm ${
      isError 
        ? "bg-rose-900 text-rose-100 border-rose-700" 
        : "bg-purple-950 text-purple-100 border-purple-700"
    }`;

    toast.innerHTML = `
      <span>${isError ? "⚠️" : "✨"}</span>
      <span class="flex-1">${msg}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}

// Instantiate and initialize
window.app = new SheRiseApp();
document.addEventListener("DOMContentLoaded", () => {
  window.app.init();
});
