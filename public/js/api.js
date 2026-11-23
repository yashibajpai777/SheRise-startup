/**
 * SheRise REST API Client
 * Manages all backend communications, authentication tokens, and Gemini API keys.
 */

const API_BASE = "";

class ApiService {
  constructor() {
    this.token = localStorage.getItem("sherise_token") || null;
    this.customGeminiKey = localStorage.getItem("sherise_gemini_key") || null;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem("sherise_token", token);
    } else {
      localStorage.removeItem("sherise_token");
    }
  }

  setGeminiKey(key) {
    this.customGeminiKey = key ? key.trim() : null;
    if (this.customGeminiKey) {
      localStorage.setItem("sherise_gemini_key", this.customGeminiKey);
    } else {
      localStorage.removeItem("sherise_gemini_key");
    }
  }

  getGeminiKey() {
    return this.customGeminiKey || "";
  }

  getHeaders() {
    const headers = {
      "Content-Type": "application/json"
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    if (this.customGeminiKey) {
      headers["X-Gemini-Key"] = this.customGeminiKey;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...(options.headers || {})
      }
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.error || (data.validation_errors ? data.validation_errors.join(", ") : "Request failed");
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || "GET"} ${endpoint}]:`, err);
      throw err;
    }
  }

  // Auth endpoints
  async register(userData) {
    const res = await this.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(userData)
    });
    if (res.token) this.setToken(res.token);
    return res;
  }

  async login(credentials) {
    const res = await this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials)
    });
    if (res.token) this.setToken(res.token);
    return res;
  }

  async demoLogin(role = "entrepreneur") {
    const res = await this.request("/api/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({ role })
    });
    if (res.token) this.setToken(res.token);
    return res;
  }

  async getMe() {
    if (!this.token) return null;
    try {
      const res = await this.request("/api/auth/me");
      return res.user;
    } catch {
      this.setToken(null);
      return null;
    }
  }

  async updateProfile(profileData) {
    return await this.request("/api/auth/profile", {
      method: "PUT",
      body: JSON.stringify(profileData)
    });
  }

  logout() {
    this.setToken(null);
  }

  // Stats
  async getStats() {
    return await this.request("/api/stats");
  }

  // Ventures
  async getVentures(filters = {}) {
    const params = new URLSearchParams();
    if (filters.search) params.append("search", filters.search);
    if (filters.category && filters.category !== "All") params.append("category", filters.category);
    if (filters.stage && filters.stage !== "All") params.append("stage", filters.stage);
    if (filters.sort) params.append("sort", filters.sort);

    const qs = params.toString() ? `?${params.toString()}` : "";
    return await this.request(`/api/ventures${qs}`);
  }

  async getVenture(id) {
    return await this.request(`/api/ventures/${id}`);
  }

  async createVenture(data) {
    return await this.request("/api/ventures", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  async updateVenture(id, data) {
    return await this.request(`/api/ventures/${id}`, {
      method: "PUT",
      body: JSON.stringify(data)
    });
  }

  async deleteVenture(id) {
    return await this.request(`/api/ventures/${id}`, {
      method: "DELETE"
    });
  }

  async expressInterest(ventureId, data) {
    return await this.request(`/api/ventures/${ventureId}/interest`, {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  async toggleBookmark(ventureId) {
    return await this.request(`/api/ventures/${ventureId}/bookmark`, {
      method: "POST"
    });
  }

  // Investors
  async getInvestors(filters = {}) {
    const params = new URLSearchParams();
    if (filters.search) params.append("search", filters.search);
    if (filters.sector && filters.sector !== "All") params.append("sector", filters.sector);

    const qs = params.toString() ? `?${params.toString()}` : "";
    return await this.request(`/api/investors${qs}`);
  }

  // Entrepreneur Dashboard
  async getEntrepreneurDashboard() {
    return await this.request("/api/dashboard/entrepreneur");
  }

  // Gemini AI features
  async runPitchDoctor(ventureData) {
    return await this.request("/api/ai/pitch-doctor", {
      method: "POST",
      body: JSON.stringify(ventureData)
    });
  }

  async generateInvestorPitch(ventureId, investorId) {
    return await this.request("/api/ai/investor-pitch", {
      method: "POST",
      body: JSON.stringify({ venture_id: ventureId, investor_id: investorId })
    });
  }

  async getAiStatus() {
    return await this.request("/api/ai/status");
  }
}

window.api = new ApiService();
