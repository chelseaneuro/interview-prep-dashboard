class ProfileService {
  constructor() {
    this.profilePath = '/data/profile.json';
    this.cache = null;
    this.lastFetch = null;
    this.CACHE_DURATION = 30000; // 30 seconds
  }

  async getProfile(forceRefresh = false) {
    const now = Date.now();

    if (!forceRefresh && this.cache && (now - this.lastFetch < this.CACHE_DURATION)) {
      return this.cache;
    }

    try {
      const response = await fetch(this.profilePath + '?t=' + now);
      if (!response.ok) {
        throw new Error('Failed to load profile');
      }

      this.cache = await response.json();
      this.lastFetch = now;
      return this.cache;
    } catch (error) {
      console.error('Error loading profile:', error);
      throw error;
    }
  }
}

export default new ProfileService();
