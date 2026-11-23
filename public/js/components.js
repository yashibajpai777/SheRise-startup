/**
 * SheRise UI Component Renderers
 * Generates beautiful, responsive components with lavender & deep purple styling.
 */

const Components = {
  // Helpers
  formatCurrency(val) {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(val);
  },

  getCategoryColor(cat) {
    const map = {
      "HealthTech": "bg-rose-50 text-rose-700 border-rose-200",
      "FinTech": "bg-emerald-50 text-emerald-700 border-emerald-200",
      "AI & SaaS": "bg-purple-50 text-purple-700 border-purple-200",
      "CleanTech & Climate": "bg-teal-50 text-teal-700 border-teal-200",
      "EdTech": "bg-amber-50 text-amber-700 border-amber-200",
      "E-commerce": "bg-blue-50 text-blue-700 border-blue-200",
      "BioTech": "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200"
    };
    return map[cat] || "bg-purple-50 text-purple-700 border-purple-200";
  },

  // 1. Venture Card
  renderVentureCard(v) {
    const percent = Math.min(100, Math.round((v.raised_funding / v.target_funding) * 100));
    const aiScore = v.ai_score || 88;
    const catClass = this.getCategoryColor(v.category);

    return `
      <div class="glass-panel glass-card-hover rounded-2xl p-6 flex flex-col justify-between cursor-pointer border border-purple-100/80 transition-all duration-300"
           onclick="window.app.openVentureModal(${v.id})">
        <div>
          <!-- Header tags -->
          <div class="flex items-center justify-between gap-2 mb-4">
            <span class="px-3 py-1 rounded-full text-xs font-semibold border ${catClass}">
              ${v.category}
            </span>
            <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-50 border border-purple-200 text-xs font-semibold text-purple-900">
              <span class="text-amber-500">✨</span>
              <span>AI Score: <strong>${aiScore}</strong></span>
            </div>
          </div>

          <!-- Title & Tagline -->
          <h3 class="text-xl font-bold text-purple-950 mb-2 leading-snug group-hover:text-purple-700 transition">
            ${v.title}
          </h3>
          <p class="text-sm text-slate-600 line-clamp-2 mb-4 leading-relaxed">
            ${v.tagline}
          </p>
        </div>

        <!-- Founder info & Progress -->
        <div class="pt-4 border-t border-purple-100/70">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2.5">
              <img src="${v.founder_avatar || 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150'}" 
                   alt="${v.founder_name}" 
                   class="w-8 h-8 rounded-full object-cover ring-2 ring-purple-200 shadow-sm" />
              <div>
                <p class="text-xs font-bold text-slate-900">${v.founder_name}</p>
                <p class="text-[11px] text-purple-700 font-medium">${v.stage} Stage</p>
              </div>
            </div>
            <div class="text-right">
              <span class="text-xs font-bold text-purple-950">${this.formatCurrency(v.raised_funding)}</span>
              <span class="text-[11px] text-slate-500 block">of ${this.formatCurrency(v.target_funding)}</span>
            </div>
          </div>

          <!-- Progress bar -->
          <div class="w-full bg-purple-100/80 h-2 rounded-full overflow-hidden">
            <div class="bg-gradient-to-r from-purple-600 to-indigo-600 h-full rounded-full transition-all duration-500"
                 style="width: ${percent}%;"></div>
          </div>

          <!-- Footer stats -->
          <div class="flex items-center justify-between mt-3 text-[11px] text-slate-500 font-medium">
            <span>${percent}% funded</span>
            <div class="flex items-center gap-3">
              <span>👁️ ${v.views_count || 0} views</span>
              <span>🤝 ${v.interests_count || 0} inquiries</span>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  // 2. Investor Card
  renderInvestorCard(inv) {
    const sectorsHtml = inv.sectors.map(s => `
      <span class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-purple-50 text-purple-800 border border-purple-100">
        ${s}
      </span>
    `).join("");

    const stagesHtml = inv.stages.map(st => `
      <span class="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700">
        ${st}
      </span>
    `).join("");

    const portfolioHtml = inv.portfolio.map(p => `
      <span class="text-[11px] text-slate-600 font-medium bg-white px-2 py-0.5 rounded border border-slate-200">
        ${p}
      </span>
    `).join("");

    return `
      <div class="glass-panel glass-card-hover rounded-2xl p-6 flex flex-col justify-between border border-purple-100/90 shadow-sm transition-all">
        <div>
          <!-- Header -->
          <div class="flex items-start gap-3.5 mb-4">
            <img src="${inv.avatar}" alt="${inv.name}" 
                 class="w-14 h-14 rounded-2xl object-cover ring-2 ring-purple-200 shadow-sm flex-shrink-0" />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-1.5">
                <h4 class="text-base font-bold text-purple-950 truncate">${inv.name}</h4>
                ${inv.verified ? '<span class="text-purple-600 text-xs" title="Verified SheRise Investor">✓</span>' : ''}
              </div>
              <p class="text-xs font-semibold text-purple-700">${inv.role}</p>
              <p class="text-xs text-slate-500 truncate">${inv.firm} • ${inv.location}</p>
            </div>
          </div>

          <!-- Thesis -->
          <div class="p-3 bg-purple-50/60 rounded-xl border border-purple-100/60 mb-4">
            <p class="text-xs text-purple-900 leading-relaxed font-medium italic">
              "${inv.thesis}"
            </p>
          </div>

          <!-- Focus details -->
          <div class="space-y-2 mb-4">
            <div>
              <span class="text-[11px] uppercase tracking-wider font-bold text-slate-400 block mb-1">Focus Sectors</span>
              <div class="flex flex-wrap gap-1">
                ${sectorsHtml}
              </div>
            </div>

            <div>
              <span class="text-[11px] uppercase tracking-wider font-bold text-slate-400 block mb-1">Stages</span>
              <div class="flex flex-wrap gap-1">
                ${stagesHtml}
              </div>
            </div>

            <div class="pt-1">
              <span class="text-[11px] uppercase tracking-wider font-bold text-slate-400 block mb-1">Check Size</span>
              <span class="text-xs font-bold text-purple-950">
                ${this.formatCurrency(inv.check_size_min)} – ${this.formatCurrency(inv.check_size_max)}
              </span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="pt-4 border-t border-purple-100 flex items-center justify-between gap-2">
          <div class="flex items-center gap-1 truncate max-w-[170px]">
            ${portfolioHtml}
          </div>
          <button onclick="window.app.openInvestorPitchModal(${inv.id})" 
                  class="px-3.5 py-1.5 rounded-xl text-xs font-bold text-white gradient-btn-primary shadow-sm hover:shadow flex items-center gap-1.5 flex-shrink-0">
            <span>✨</span>
            <span>Pitch with AI</span>
          </button>
        </div>
      </div>
    `;
  },

  // 3. AI Evaluation Box
  renderAiEvaluation(evalData) {
    if (!evalData) return "";

    const score = evalData.score || 88;
    const level = evalData.readiness_level || "High Investor Readiness";
    const strengths = evalData.strengths || [];
    const growthAreas = evalData.growth_areas || [];
    const questions = evalData.investor_questions || [];

    return `
      <div class="rounded-2xl p-6 bg-gradient-to-br from-purple-900 via-indigo-950 to-purple-950 text-white shadow-xl border border-purple-500/30">
        <!-- AI Header -->
        <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-purple-800/80">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-purple-600/50 flex items-center justify-center text-xl shadow-inner border border-purple-400/30">
              ✨
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h4 class="font-bold text-base text-purple-100">SheRise AI Pitch Doctor</h4>
                <span class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider bg-purple-500/20 text-purple-300 border border-purple-400/30">
                  Gemini Core
                </span>
              </div>
              <p class="text-xs text-purple-300">Venture Capital Readiness & Strategic Review</p>
            </div>
          </div>

          <div class="flex items-center gap-3 bg-purple-950/80 px-4 py-2 rounded-xl border border-purple-700/50">
            <div class="text-right">
              <span class="text-[11px] text-purple-300 block uppercase tracking-wider font-semibold">Investor Score</span>
              <span class="text-xs font-bold text-emerald-400">${level}</span>
            </div>
            <div class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-200 via-pink-200 to-amber-300">
              ${score}<span class="text-sm font-normal text-purple-400">/100</span>
            </div>
          </div>
        </div>

        <!-- Executive Pitch Hook -->
        ${evalData.executive_pitch ? `
          <div class="mt-4 p-4 rounded-xl bg-purple-900/40 border border-purple-700/40">
            <span class="text-[11px] font-bold uppercase tracking-wider text-purple-300 block mb-1">
              🎙️ 30-Second Executive Pitch
            </span>
            <p class="text-sm text-purple-100 font-medium leading-relaxed italic">
              "${evalData.executive_pitch}"
            </p>
          </div>
        ` : ''}

        <!-- Strengths & Growth Areas Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <!-- Strengths -->
          <div class="p-4 rounded-xl bg-purple-950/50 border border-purple-800/60">
            <h5 class="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <span>✓</span> Key Investor Strengths
            </h5>
            <ul class="space-y-2 text-xs text-purple-100 leading-relaxed">
              ${strengths.map(s => `<li class="flex items-start gap-2"><span class="text-emerald-400 font-bold">•</span><span>${s}</span></li>`).join("")}
            </ul>
          </div>

          <!-- Growth Areas -->
          <div class="p-4 rounded-xl bg-purple-950/50 border border-purple-800/60">
            <h5 class="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <span>⚡</span> Diligence Focus & Growth Areas
            </h5>
            <ul class="space-y-2 text-xs text-purple-100 leading-relaxed">
              ${growthAreas.map(g => `<li class="flex items-start gap-2"><span class="text-amber-400 font-bold">•</span><span>${g}</span></li>`).join("")}
            </ul>
          </div>
        </div>

        <!-- Diligence questions if present -->
        ${questions.length ? `
          <div class="mt-4 pt-3 border-t border-purple-800/60">
            <span class="text-[11px] font-bold uppercase tracking-wider text-purple-300 block mb-2">
              ❓ Anticipated Investor Questions
            </span>
            <div class="space-y-1.5">
              ${questions.map(q => `
                <div class="text-xs text-purple-200 bg-purple-900/30 px-3 py-1.5 rounded-lg border border-purple-800/40">
                  ${q}
                </div>
              `).join("")}
            </div>
          </div>
        ` : ''}

        <div class="mt-4 flex items-center justify-between text-[11px] text-purple-300 pt-2 border-t border-purple-800/40">
          <span>Engine: ${evalData.ai_engine || 'SheRise Intelligence Core'}</span>
          <span>Calibrated for Women-Led Ventures</span>
        </div>
      </div>
    `;
  }
};

window.Components = Components;
